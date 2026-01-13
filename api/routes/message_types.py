from typing import Literal, Union
from pydantic import BaseModel, TypeAdapter
#from enum import Enum

class MTypeMessage(BaseModel):
    type: Literal['message']
    m_id: str
    text: str


class MTypeScrabble(BaseModel):
    type: Literal['scrabble']
    m_id: str
    letters: str


class MTypeRPG(BaseModel):
    type: Literal['rpg']
    m_id: str
    command: str


class MTypeClose(BaseModel):
    type: Literal['close']


class MTypeKeepAlive(BaseModel):
    type: Literal['keepalive']

class MTypeJoin(BaseModel):
    type: Literal['join']
    channel_name: str

MTypes = TypeAdapter(Union[
    MTypeMessage,
    MTypeScrabble,
    MTypeRPG,
    MTypeClose,
    MTypeKeepAlive,
])

'''
class MessageType(str, Enum):
    MESSAGE = 'message'
    SCRABBLE = 'scrabble'
    RPG = 'rpg'
    CLOSE = 'close'
    KEEPALIVLE = 'keepalive'


class Message(BaseModel):
    type: MessageType
    text: str | None
    m_id: str | None
    letters: str | None
    command: str | None

    @model_validator(mode='after'):
    def validate_required_fields(self) -> 'Message':
'''        

