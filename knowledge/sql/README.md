# 两张表：文档与父子块

[schema.sql](schema.sql) 使用PostgreSQL 13 + pgvector的独立knowledge schema。应用首次检测表不存在时执行，不自动删除或迁移已有数据。

|对象|用途|
|---|---|
|document|已确认文档的文件信息、hash、编码配置和生效批次|
|document_chunk|父块和子块；chunk_role区分角色，parent_id自关联|
|searchable_chunk视图|仅生效批次、child角色、ready向量的子块|

父块保存title、完整content和来源metadata，parent_id为空、embedding为空、embedding_status=not_required。子块的parent_id非空，生成768维向量后以ready状态写入。模型和profile列在父块上使用not_applicable，占位但不参与检索。

外键(parent_id, document_id, chunk_set_id)引用本表，保证父子在同文档、同批次；应用只让子块引用parent角色。父、子块分别按(document_id, chunk_set_id, chunk_role, ordinal)去重。删除父块级联删除子块，删除文档级联删除全部块。

## 入库边界

- 上传、解析、预览、删块、重新切块只改data/drafts/临时文件，不向两张PG表写记录。
- 点最终确认后生成全部向量，然后单事务写文档、父块、子块和生效批次。生成向量失败或事务失败，PG不会留下半份内容。
- 已入库文档的编辑也是临时草稿，确认前旧版保持不变。发布校验原生效版本，避免旧编辑覆盖新版本；成功后清理旧批次。
- 同知识库原文件SHA-256重复时打开已有文档编辑，不重复创建。Chunk内容hash不全局唯一。

file_hash是原始文件SHA-256；content_hash是正文UTF-8字节SHA-256；input_hash是含标题与表头的实际编码文本SHA-256。embedding_profile固定权重、池化和预处理配置。metadata记录来源、字符范围、token数及切分原因。

## 子查父

```sql
SELECT c.id AS chunk_id, c.parent_id, c.file_name,
       c.content AS matched_content, p.content AS parent_content,
       1 - (c.embedding <=> $1::vector(768)) AS similarity
FROM knowledge.searchable_chunk c
JOIN knowledge.document_chunk p ON p.id=c.parent_id AND p.chunk_role='parent'
WHERE c.knowledge_base_id=$2 AND c.embedding_profile=$3
ORDER BY c.embedding <=> $1::vector(768)
LIMIT 5;
```

应用按parent_id去重，直接返回已保存的父正文，不再拼接子块。默认BGE-base 768维、精确余弦检索；TopK不保证完整枚举所有相关内容。
