from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from api.main import api_router
from api.routes.channels import websocket_endpoint
import settings

# TODO run with uvicorn so --ws-max-size can be used.
app = FastAPI(
 # TODO
 #   title=settings.PROJECT_NAME,
 #   openapi_url=f"{settings.API_V1_STR}/openapi.json",
 #   generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if True:#if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router) #prefix=settings.API_V1_STR)
# Must include websocket route independently
app.add_api_websocket_route("/ws", websocket_endpoint)
