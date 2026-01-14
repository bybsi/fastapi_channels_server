from typing import Literal, Union
from pydantic import BaseModel, TypeAdapter, Field
#from enum import Enum

class MTypeMessage(BaseModel):
    type: Literal['message']
    m_id: str = Field(min_length=1, max_length=6)
    text: str = Field(min_length=1, max_length=2048)

class MTypeScrabble(BaseModel):
    type: Literal['scrabble']
    m_id: str
    letters: str = Field(min_length=1, max_length=48, pattern=r'^[a-zA-Z ]+$')

class MTypeRPG(BaseModel):
    type: Literal['rpg']
    m_id: str
    command: str = Field(min_length=1, max_length=16, pattern=r'^[\w\s]+$')

class MTypeBanner(BaseModel):
    type: Literal['banner']
    banner: str = Field(min_length=0, max_length=512, pattern=r'^[\w\s]+$')

class MTypeMotd(BaseModel):
    type: Literal['motd']
    motd: str = Field(min_length=0, max_length=512, pattern=r'^[\w\s]+$')

class MTypeClose(BaseModel):
    type: Literal['close']

class MTypeKeepAlive(BaseModel):
    type: Literal['keepalive']

class MTypeJoin(BaseModel):
    type: Literal['join']
    channel_name: str = Field(min_length=1, max_length=32, pattern=r'^[\w \-]+$')

class MTypeRejoin(BaseModel):
    type: Literal['rejoin']

MTypes = TypeAdapter(Union[
    MTypeMessage,
    MTypeScrabble,
    MTypeRPG,
    MTypeClose,
    MTypeKeepAlive,
    MTypeBanner,
    MTypeMotd,
    MTypeJoin,
    MTypeRejoin
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

