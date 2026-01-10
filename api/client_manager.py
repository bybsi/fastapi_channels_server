from fastapi import (
    Cookie, Depends, FastAPI,
    Query, 
    WebSocket, WebSocketDisconnect, WebSocketException,
    status
)
import api.session as Session

class ClientManager:
    def __init__(self):
        # user id -> websocket
        self.clients: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        bs_sid = websocket.cookies.get('BS_SID', None)
        if bs_sid == None:
            print(f"Invalid SID (None)")
            raise WebSocketException(code=status.HTTP_403_FORBIDDEN)

        session_data = Session.load(bs_sid)
        if not session_data:
            raise WebSocketException(code=status.HTTP_403_FORBIDDEN)

        await websocket.accept()
        self.clients[session_data['user_id']] = websocket
        return session_data

    def disconnect(self, user_id: str):
        if user_id in self.clients:
            del self.clients[user_id]

    async def send_text(self, websocket: WebSocket, text: str, name: str = None, _type=None):
        #session_data = self.session.get_session(websocket.cookies.get('BS_SID', None))
        #if not session_data:
        #    print(f"Invalid SID in send_text")
        #    return

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

    async def broadcast(self, message: str, user_id: str, name: str):
        for client_user_id, websocket in self.clients.items():
            if client_user_id == user_id:
                continue
            await self.send_json(websocket, message, name)


