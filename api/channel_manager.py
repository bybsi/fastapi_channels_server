from collections import defaultdict
import threading


class Channel:
    __slots__ = [
        'users', 'banner', 'motd', 
        'passcode', 'owner_id', 'name']

    #channel_lock = threading.Lock()

    def __init__(self):
        self.users = {}
        self.banner = ""
        self.motd = ""
        self.passcode = ""
        self.owner_id = 0
        self.name = ""

    def add_user(self, user_id, socket):
        self.users[user_id] = socket

    def del_user(self, user_id):
        try:
            del self.users[user_id]
        except Exception as e:
            # Don't care.
            pass
    
    def has_owner(self):
        return self.owner_id != 0

    def __call__(self):
        return {
            'name':self.name,
            'banner':self.banner,
            'motd':self.motd,
            'passcode':self.passcode,
            'created_by':self.owner_id
        }
    
    async def broadcast_message(self, message, session_data):
        for user_id, socket in self.users.items():
            if user_id != session_data['user_id']:
                await socket.send_json({
                    'time': 'now',
                    'text': message,
                    'name': session_data['display_name']
                })

    async def broadcast_data(self, _type, data, session_data):
        data['type'] = _type
        for user_id, socket in self.users.items():
            if user_id != session_data['user_id']:
                await socket.send_json(data)

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
            rows = db.tbl_channel.all()
            for row in rows:
                channel = self.channels[row.name]
                channel.banner = row.banner
                channel.motd = row.motd
                channel.passcode = row.passcode
                channel.owner_id = row.created_by
                channel.name = row.name
        except Exception as exc:
            self.logger.error("Could not load channel {exc}")

    
    async def join_channel(self, channel_name: str, session_data, websocket):
        if session_data['channel']:
            if session_data['channel'].name == channel_name:
                # User is already in the channel
                return
            # Leave the current channel
            self.leave_channel(channel_name, session_data)

        channel = self.channels[channel_name]
        channel.add_user(session_data['user_id'], websocket)
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
                self.add_channel_to_database(channel, session_data['user_id'])

        # The users active channel.
        session_data['channel'] = channel
        self.logger.info("Sending channel list and meta data")
        await websocket.send_json([{
            'type': 'channel_list',
            'data': self.channels.keys()
        }, {
            'type': 'meta_data',
            'data': {
                'banner': self.channel.banner, 
                'motd': self.channel.motd
            }
        }])

        self.logger.info("Sending new user to others")
        await channel.broadcast_data(
            'user_joined', 
            {'username':session_data['username']},
            session_data)


    async def leave_channel(self, channel_name: str, session_data):
        channel = self.channels[channel_name]
        channel.del_user(session_data['user_id'])
        session_data['channel'] = None
        
        await channel.broadcast_data(
            'user_left', 
            {'username':session_data['username']},
            session_data)


    async def add_channel_to_db(self, channel, user_id):
        channel.owner_id = user_id
        db.tbl_channel.insert(**Channel())
        if not db.safe_commit():
            channel.owner_id = 0
            self.logger.error("Could not add channel to DB: {channel_name}")
            await client_manager.send_text(websocket, "Could not create channel.")


    async def update_metadata(self, session_data, data):
        channel = session_data['channel']
        if not channel:
            return

        if channel.owner_id == session_data['user_id']:
            db.tbl_channel.update(**data)
            if not db.safe_commit():
                self.logger.error(f"Could not update channel meta data: {channel.name}")
                return

            if 'banner' in data:
                channel.banner = data['banner']
            if 'motd' in data:
                channel.motd = data['motd']

            await channel.broadcast_data_all(
                'meta_data',
                {'data': data})
                











