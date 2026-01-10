import re
from plugins.scrabble import Scrabble
from plugins.rpg import Rpg


class Plugins():

    def __init__(self, logger):
        self.logger = logger
        self.plugins = {
            'scrabble': Scrabble(logger),
            'rpg': {}
        }

        self.valid_commands = {
            'rpg':r'start|stop|[0-9]+'
        }

        for name, plugin in self.plugins.items():
            if isinstance(plugin, dict):
                continue
            if not plugin.start():
                logger.debug(f"Could not start plugin {name}")


    def __getitem__(self, key):
        if key in self.plugins:
            return self.plugins[key]
        return None


    def validate_command(self, plugin_name, command):
        return (plugin_name in self.valid_commands and
                re.fullmatch(self.valid_commands[plugin_name], command))


    def unload_plugins(self, user_id = None):
        for name, plugin in self.plugins.items():
            if isinstance(plugin, dict):
                for user_id in plugin:
                    try:
                        plugin[user_id].stop()
                    except Exception as e:
                        self.logger.error(f"Could not stop plugin for user {uid} during unload_plugins")
                    del plugin[user_id]
                continue

            try:
                plugin.stop()
            except Exception as e:
                pass


    def unload_plugins_for_user(self, user_id):
        for name, plugin in self.plugins.items():
            if isinstance(plugin, dict):
                if user_id in plugin:
                    try:
                        plugin[user_id].stop()
                    except Exception as e:
                        self.logger.error(f"Could not stop plugin for user {uid} during unload_plugins_for_user")
                    del plugin[user_id]


    # TODO use an instance manager for plugins
    # that will have instances for each user.
    # it can also be used to bridge instances.
    # for now just do this, because.
    def get_instance(self, instance_type, instance_id, instance_user):
        if instance_id not in self.plugins[instance_type]:
            if instance_type == 'rpg':
                instance = Rpg(self.logger, instance_user)
            else:
                return None
            self.plugins[instance_type][instance_id] = instance
        else:
            instance = self.plugins[instance_type][instance_id]
        return instance


    def del_instance(self, instance_type, instance_id):
        if instance_id in self.plugins[instance_type]:
            del self.plugins[instance_type][instance_id]


