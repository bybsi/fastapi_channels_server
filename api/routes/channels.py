from typing import Annotated
from pydantic import ValidationError

from fastapi import (
    WebSocket, WebSocketDisconnect, WebSocketException,
    status
)
from api.routes.message_types import MTypes
from api.client_manager import ClientManager
from api.channel_manager import ChannelManager
from core.logger import Logger
from plugins import Plugins

import settings
from sqlalchemy.orm.exc import NoResultFound
from core.db import DB
from core.db.decrypt import DBCrypt

logger = Logger('channels')

db = DB(
    engine=DBCrypt().decrypt(settings.DB_ENGINE),
    logger=logger
)
# This file gets included twice in dev mode!
# Make sure to use run mode for production!
#logger.info("Here1")

client_manager = ClientManager(logger)
channel_manager = ChannelManager(logger, db, client_manager)

channel_plugins = Plugins(logger)
scrabble = channel_plugins['scrabble']

'''
async def ack(fn):
    async def ackfirst(recv_data, session_data, websocket):
        await client_manager.send_ack(websocket, recv_data['m_id'])
        fn(recv_data, session_data_websocket)
    return ackfirst
'''


async def websocket_endpoint(websocket: WebSocket):
    session_data = await client_manager.connect(websocket)
    if not session_data:
        # Websocket never connected
        return

    try:
        # Join the global channel by default.
        await channel_manager.join_channel('global', session_data, websocket)
        await websocket.send_json({
            'type':'channel_list',
            'data': channel_manager.get_channel_list()
        })

        while True:
            data = await websocket.receive_json()
            try:
                #logger.info(f"{data}")
                MTypes.validate_python(data)
            except ValidationError as e:
                logger.warn(f"Invalid data received from client ... {session_data['username']}")
                await client_manager.send_text(websocket, 'Invalid command.', 'system')
                continue
                #raise WebSocketException(code=status.HTTP_403_FORBIDDEN)

            method_name = 'response_' + data['type']
            await globals()[method_name](data, session_data, websocket)
    except WebSocketException:
        try:
            await client_manager.disconnect(websocket)
        except Exception as exc:
            logger.error(f"Error trying to disconnect after WebSocketException {exc}")
    except WebSocketDisconnect:
        logger.error(f"Client disconnected")
    except Exception as exc:
        logger.error(f"Unknown exception {exc}")

#@ack
async def response_message(recv_data, session_data, websocket):
    await client_manager.send_ack(websocket, recv_data['m_id'])
    await session_data['channel'].broadcast_message(
        recv_data['text'], session_data)


#@ack
async def response_join(recv_data, session_data, websocket):
    # TODO pydantic match regexes in model type.
    channel_name = recv_data['channel_name']
    await channel_manager.join_channel(channel_name, session_data, websocket)


async def response_rejoin(recv_data, session_data, websocket):
    await channel_manager.rejoin_channel(session_data, websocket)


async def response_banner(recv_data, session_data, websocket):
    await channel_manager.update_metadata(
        session_data, {'banner':recv_data['banner']})


async def response_motd(recv_data, session_data, websocket):
    await channel_manager.update_metadata(
        session_data, {'motd':recv_data['motd']})


#@ack
async def response_scrabble(recv_data, session_data, websocket):
    await client_manager.send_ack(websocket, recv_data['m_id'])

    letters = recv_data['letters']
    if len(letters) > 45:
        return
    if scrabble.input(letters):
        response = scrabble.read()
        await client_manager.send_text(websocket, response, 'scrabblesteve')
    else:
        await client_manager.send_text(websocket, 'scrabble error.', 'system')


async def response_rpg(recv_data, session_data, websocket):
    await client_manager.send_ack(websocket, recv_data['m_id'])

    command = recv_data['command']
    if len(command) > 16:
        return

    response = None
    uid = session_data['user_id']
    uname = session_data['username']
    # TODO set logger
    if channel_plugins.validate_command('rpg', command):
        instance = channel_plugins.get_instance('rpg', uid, uname)
        if command == 'start':
            instance.start()
            response = instance.read_block()
        elif command == 'stop':
            instance.stop()
            channel_plugins.del_instance('rpg', uid)
            response = "RPG was saved and stopped."
        elif command.isdigit() and len(command) < 3:
            if command == '6':
                instance.stop()
                channel_plugins.del_instance('rpg', uid)
                response = "RPG was saved and stopped."
            else:
                instance.input(command)
                response = instance.read_block()
    else:
        response = "Invalid command. /rpg start|stop|[0-9]"

    await client_manager.send_text(websocket, response, 'rpgGee', 'pre')


async def response_close(recv_data, session_data, websocket):
    #TODO delete more stuff.
    channel_plugins.unload_plugins_for_user(session_data['user_id'])
    raise WebSocketDisconnect()


async def response_keepalive(recv_data, session_data, websocket):
    pass


