"""模型 tokenizer 与 token 计数，供文档切分和向量输入校验共用。"""
from functools import lru_cache
from config import MODEL_DIR


@lru_cache
def tokenizer():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(MODEL_DIR / 'tokenizer', local_files_only=True)


def tokens(text):
    return len(tokenizer().encode(text, add_special_tokens=True))
