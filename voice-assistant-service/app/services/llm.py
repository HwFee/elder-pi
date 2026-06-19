class LLMService:
    """大模型服务封装"""
    
    async def understand(self, text: str, contacts: list, context: list = None) -> dict:
        """理解用户意图，返回结构化结果"""
        pass
    
    async def generate_confirm(self, action: str, details: str) -> str:
        """生成确认语句"""
        pass
