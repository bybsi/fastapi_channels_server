from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from api.main import api_router
from api.routes.channels import websocket_endpoint
import settings

# TODO run with uvicorn so --ws-max-size can be used.
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    # TODO on prod
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO prefix endpoints with settings.API_V#
#app.include_router(api_router)
# Must include websocket routes independently
app.add_api_websocket_route("/ws", websocket_endpoint)
