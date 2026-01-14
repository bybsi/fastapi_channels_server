from fastapi import (
    Cookie, Depends, FastAPI,
    Query, 
    WebSocket, WebSocketDisconnect, WebSocketException,
    status
)
import api.session as Session

class ClientManager:
    
    
    def __init__(self, logger):
        self.logger = logger

    
    async def connect(self, websocket: WebSocket):
        bs_sid = websocket.cookies.get('BS_SID', None)
        if bs_sid is None:
            self.logger.info("Invalid SID (None)")
            return None

        session_data = Session.load(bs_sid)
        if session_data is None:
            self.logger.info("Couldn't load session data")
            return None

        await websocket.accept()
        return session_data

    
    async def send_text(
        self, 
        websocket: WebSocket, 
        text: str, 
        name: str = 'system', 
        _type: str | None = None):

        data = {'time':'now', 'text':text}
        if name:
            data['name'] = name
        if _type:
            data['type'] = _type
        await websocket.send_json(data)
        

    async def send_ack(self, websocket: WebSocket, message_id : str):
        data = {'type':'ack'}
        if message_id:
            data['m_id'] = message_id
        await websocket.send_json(data)


    async def disconnect(self, websocket: WebSocket):
        await websocket.close()


