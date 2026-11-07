"""知识模块错误；由工具和 Web 各自转换为对外响应。"""
class KnowledgeError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
