-- PostgreSQL 13+ / pgvector。初始DDL；应用只在knowledge schema尚未建表时执行。
-- 当前选择 BGE-base-zh-v1.5：768 维。改用其他维度模型时需迁移向量列。
BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS knowledge;

-- 原文件存对象存储或文件系统，这里保存引用。
-- knowledge_base_id 由上层知识库管理分配；本简版暂不建知识库配置表。
CREATE TABLE knowledge.document (
    id                  bigserial PRIMARY KEY,
    knowledge_base_id   text NOT NULL,
    file_name           text NOT NULL,
    file_uri            text NOT NULL,
    file_hash           text NOT NULL
                        CHECK (file_hash ~ '^[0-9a-f]{64}$'),
    file_size           bigint NOT NULL CHECK (file_size >= 0),
    mime_type           text,
    status              text NOT NULL DEFAULT 'uploaded'
                        CHECK (status IN (
                            'uploaded', 'parsed', 'chunked',
                            'embedding', 'ready', 'failed'
                        )),
    active_chunk_set_id uuid,
    processing_config   jsonb NOT NULL DEFAULT '{}'::jsonb
                        CHECK (jsonb_typeof(processing_config) = 'object'),
    metadata            jsonb NOT NULL DEFAULT '{}'::jsonb
                        CHECK (jsonb_typeof(metadata) = 'object'),
    error_message       text,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now(),

    -- 简版策略：同一知识库的相同文件字节只保留一份，可跨知识库复用上传。
    CONSTRAINT document_file_unique UNIQUE (knowledge_base_id, file_hash)
);

CREATE TABLE knowledge.document_chunk (
    id                  bigserial PRIMARY KEY,
    document_id         bigint NOT NULL
                        REFERENCES knowledge.document(id) ON DELETE CASCADE,
    chunk_set_id        uuid NOT NULL,
    parent_id           bigint,
    chunk_role          text NOT NULL DEFAULT 'child' CHECK (chunk_role IN ('parent', 'child')),
    title               text NOT NULL DEFAULT '',
    ordinal             integer NOT NULL CHECK (ordinal >= 0),
    content             text NOT NULL CHECK (length(btrim(content)) > 0),
    content_hash        text NOT NULL
                        CHECK (content_hash ~ '^[0-9a-f]{64}$'),
    embedding_model     text NOT NULL,  -- 例：BAAI/bge-base-zh-v1.5
    embedding_profile   text NOT NULL,  -- 固定模型revision/池化/预处理配置的标识
    embedding_text      text,           -- 实际送入模型的文本，含拼接的标题/表头
    input_hash          text CHECK (input_hash ~ '^[0-9a-f]{64}$'),
    embedding           vector(768),
    embedding_status    text NOT NULL DEFAULT 'pending'
                        CHECK (embedding_status IN ('pending', 'ready', 'failed', 'not_required')),
    metadata            jsonb NOT NULL DEFAULT '{}'::jsonb
                        CHECK (jsonb_typeof(metadata) = 'object'),
    error_message       text,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now(),

    -- 父块和子块在同一张表；父块不向量化，子块通过自关联取父正文。
    CONSTRAINT document_chunk_parent_fk
        FOREIGN KEY (parent_id, document_id, chunk_set_id)
        REFERENCES knowledge.document_chunk (id, document_id, chunk_set_id)
        ON DELETE CASCADE,
    CONSTRAINT document_chunk_position_unique
        UNIQUE (document_id, chunk_set_id, chunk_role, ordinal),
    UNIQUE (id, document_id, chunk_set_id),
    CONSTRAINT document_chunk_role_check CHECK (
        (chunk_role = 'parent' AND parent_id IS NULL AND embedding_status = 'not_required')
        OR (chunk_role = 'child' AND parent_id IS NOT NULL AND embedding_status <> 'not_required')
    ),
    CONSTRAINT document_chunk_ready_vector CHECK (
        (embedding_status = 'ready'
         AND embedding IS NOT NULL
         AND vector_norm(embedding) > 0
         AND embedding_text IS NOT NULL
         AND length(btrim(embedding_text)) > 0
         AND input_hash IS NOT NULL)
        OR (embedding_status <> 'ready' AND embedding IS NULL)
    )
);

-- 上面的唯一索引已覆盖按document_id/batch查询和关联删除，无需重复建索引。
CREATE INDEX document_chunk_parent_idx ON knowledge.document_chunk(parent_id, ordinal);

CREATE INDEX document_list_idx
    ON knowledge.document (knowledge_base_id, created_at DESC);

-- 检索使用该视图：旧批次、草稿和失败的块不参与检索。
-- 新批次处理期间，不依赖document.status过滤，旧的生效批次仍可提供服务。
CREATE VIEW knowledge.searchable_chunk AS
SELECT c.*, d.knowledge_base_id, d.file_name, d.file_uri
FROM knowledge.document_chunk c
JOIN knowledge.document d ON d.id = c.document_id
                        AND d.active_chunk_set_id = c.chunk_set_id
WHERE c.chunk_role = 'child' AND c.embedding_status = 'ready';

COMMENT ON COLUMN knowledge.document.file_hash IS '原始文件字节SHA-256；小写64位十六进制';
COMMENT ON COLUMN knowledge.document.active_chunk_set_id IS '生效批次；应用在事务中校验该文档批次完整就绪后切换，空值表示尚未发布';
COMMENT ON COLUMN knowledge.document.processing_config IS '本次解析器版本、切块大小、重叠等配置；如需历史配置，写入对应批次Chunk的metadata';
COMMENT ON COLUMN knowledge.document.metadata IS '作者、来源系统、原始URL等扩展属性；检索过滤和关联字段使用明确列';
COMMENT ON COLUMN knowledge.document_chunk.parent_id IS '子块指向本表父块；应用写入时确保目标角色为parent';
COMMENT ON COLUMN knowledge.document_chunk.chunk_set_id IS '一次切块发布批次UUID；重试复用，重新切块新建';
COMMENT ON COLUMN knowledge.document_chunk.content_hash IS '正文SHA-256，不设置全局唯一，保留不同来源与重复位置';
COMMENT ON COLUMN knowledge.document_chunk.input_hash IS '实际embedding_text的SHA-256，模型配置另由embedding_profile区分';
COMMENT ON COLUMN knowledge.document_chunk.metadata IS '页码、标题路径、工作表、行范围、坐标、块类型等来源信息';
COMMENT ON COLUMN knowledge.document_chunk.embedding_profile IS '同一标识必须对应不可变的编码配置；查询向量必须使用相同配置';

-- 先使用精确余弦检索，不创建HNSW；候选增多且实测有需要时再加。
-- updated_at及hash由应用写入；DDL不自动校验hash是否匹配文本。
COMMIT;
