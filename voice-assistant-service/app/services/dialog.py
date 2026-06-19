class DialogEngine:
    """对话管理引擎"""
    
    async def process_turn(self, session_id: str, audio_path: str) -> dict:
        """处理一轮对话"""
        pass
    
    async def check_messages(self, device_id: str) -> list:
        """检查未读消息"""
        pass
