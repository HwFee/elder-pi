class SignalingClient:
    """调用 signaling-server 内部 API"""
    
    async def get_contacts(self, device_id: str) -> list:
        """获取设备联系人列表"""
        pass
    
    async def initiate_call(self, call_id: str, caller_device_id: str, callee_device_id: str, offer: dict) -> dict:
        """发起通话"""
        pass
