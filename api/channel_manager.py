from sqlalchemy.orm.exc import NoResultFound
from collections import defaultdict
#import threading

class User:
    __slots__ = [
        'display_name', 'user_id', 'socket'
    ]


    def __init__(self):
        self.display_name = ""
        self.user_id = 0
        self.socket = None


class Channel:
    __slots__ = [
        'users', 'banner', 'motd', 
        'passcode', 'owner_id', 'name', 'status']

    #channel_lock = threading.Lock()

    def __init__(self):
        self.users = defaultdict(User)
        self.banner = ""
        self.motd = ""
        self.passcode = ""
        self.owner_id = 0
        self.name = ""
        self.status = "U"


    def add_user(self, session_data, socket):
        user = self.users[session_data['user_id']]
        user.display_name = session_data['display_name']
        user.user_id = session_data['user_id']
        user.socket = socket


    def del_user(self, user_id):
        try:
            del self.users[user_id]
        except Exception as e:
            # Don't care.
            pass


    def get_flags(self, user):
        return 'A' if user.display_name == self.name or int(user.user_id) == 1 else 'G'


    def get_user(self, user_id):
        user = self.users[user_id]
        #flag = 'A' if user.display_name == self.name or int(user.user_id) == 1 else 'G'
        flag = self.get_flags(user)
        return [user.user_id, user.display_name, flag]


    def get_user_list(self):
        # Temp permissions implementation 
        # until I re add this feature.
        result = []
        for user in self.users.values():
            # user_id is parsed as an int but just cast it here
            # incase I change it later on and forget about this.
            # 'A' admin
            #flag = 'A' if user.display_name == self.name or int(user.user_id) == 1 else 'G'
            flag = self.get_flags(user)
            result.append([user.user_id, user.display_name, flag])
        return result


    def get_meta_data(self):
        return {
            'type': 'meta_data',
            'banner': self.banner, 
            'motd': self.motd,
            'channel_name':self.name
        }


    def has_owner(self):
        return self.owner_id != 0


    def __call__(self):
        return {
            'name':self.name,
            'banner':self.banner,
            'motd':self.motd,
            'passcode':self.passcode,
            'created_by':self.owner_id,
            'status':self.status
        }


    async def broadcast_message(self, message, session_data):
        for user in self.users.values():
            if user.user_id != session_data['user_id']:
                try:
                    await user.socket.send_json({
                        'time': 'now',
                        'text': message,
                        'name': session_data['display_name']
                    })
                except Exception as e:
                    print(f"message {e}")

    
    async def broadcast_data(self, _type, data, session_data):
        data['type'] = _type
        for user in self.users.values():
            if user.user_id != session_data['user_id']:
                try:
                    await user.socket.send_json(data)
                except Exception as e:
                    print(f"data {e}")
    
    
    async def broadcast_data_all(self, _type, data):
        data['type'] = _type
        for user in self.users.values():
            try:
                await user.socket.send_json(data)
            except Exception as e:
                print(f"data_all {e}")

    # decorator for broadcast.

class ChannelManager:
    def __init__(self, logger, db, client_manager):
        self.logger = logger
        self.db = db
        self.channels = defaultdict(Channel)
        self.client_manager = client_manager
        self.load_channels()

    
    def load_channels(self):
        try:
            rows = self.db.tbl_channel.all()
            for row in rows:
                channel = self.channels[row.name]
                channel.banner = row.banner or "" 
                channel.motd = row.motd or ""
                channel.passcode = row.passcode or ""
                channel.owner_id = row.created_by
                channel.name = row.name
                channel.status = row.status
        except Exception as exc:
            self.logger.error(f"Could not load channel {exc}")

    
    def get_channel_list(self):
        return [[k, v.status] for k,v in self.channels.items()]


    async def rejoin_channel(self, session_data, websocket):
        channel = session_data['channel']
        if channel:
            await websocket.send_json({'multi':[channel.get_meta_data()]})


    async def join_channel(self, channel_name: str, session_data, websocket):
        if session_data['channel']:
            if session_data['channel'].name == channel_name:
                # User is already in the channel
                return
            # Leave the current channel
            await self.leave_channel(session_data)

        channel = self.channels[channel_name]
        channel.add_user(session_data, websocket)
        # Channels that don't persist have no owner,
        # they don't get loaded from the database.
        if not channel.has_owner():
            if not channel.name:
                # New channel
                channel.name = channel_name

            if session_data['username'] == channel_name:
                # This channel belongs to the user that joined it.
                # They are now the OP of the channel and the
                # channel will persist.
                await self.add_channel_to_db(channel, session_data['user_id'])

        # The users active channel.
        session_data['channel'] = channel
        await websocket.send_json({'multi': [
            {
                'type': 'user_list',
                'data': channel.get_user_list()
            },
            channel.get_meta_data()
        ]})

        await channel.broadcast_data(
            'user_joined', 
            {'user':channel.get_user(session_data['user_id'])},
            session_data)


    async def leave_channel(self, session_data):
        channel = session_data['channel']
        session_data['channel'] = None
        

        await channel.broadcast_data(
            'user_left', 
            {'user':channel.get_user(session_data['user_id'])},
            session_data)
        
        channel.del_user(session_data['user_id'])


    async def add_channel_to_db(self, channel, user_id):
        channel.owner_id = user_id
        self.db.tbl_channel.insert(**channel())
        if not self.db.safe_commit():
            channel.owner_id = 0
            self.logger.error(f"Could not add channel to DB: {channel_name}")
            await client_manager.send_text(websocket, "Could not create channel.")
        else:
            await self.broadcast_data_all(
                'new_channel', 
                {'channel':[channel.name, channel.status]})


    async def update_metadata(self, session_data, data):
        channel = session_data['channel']
        if not channel:
            return

        if channel.owner_id == session_data['user_id']:
            try:
                self.db.tbl_channel.filter_by(name=channel.name).update(data)
            except Exception as exc:
                self.logger.error(f"Could not update channel meta data (exc): {channel.name} {exc}")
                return
            
            if not self.db.safe_commit():
                self.logger.error(f"Could not update channel meta data (commit): {channel.name}")
                return

            if 'banner' in data:
                channel.banner = data['banner']
            if 'motd' in data:
                channel.motd = data['motd']

            await channel.broadcast_data_all('meta_data', data)
            

    async def broadcast_data_all(self, _type, data):
        for channel in self.channels.values():
            await channel.broadcast_data_all(_type, data)
                











