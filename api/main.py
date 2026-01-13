from fastapi import APIRouter
from api.routes import channels
#from api.routes import activities
#from api.routes import music

api_router = APIRouter()
#api_router.include_router(music.router)
#api_router.include_router(activities.router)

# This is done in app/main.py because it's a websocket route
#api_router.include_router(channels.router)

