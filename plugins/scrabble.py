
from plugins.plugin import Plugin

class Scrabble(Plugin):
    def __init__(self, logger):
        self.logger = logger 
        super().__init__(self.logger, name='Scrabble', executable='sc')

    def input(self, data : str) -> bool:
        # TODO add a lock
        if len(data) > 45:
            return False
        data = data.replace('0','o')
        return super().write(data)

    def start(self) -> bool:
        return super().start()

    def stop(self) -> None:
        try:
            self.input("0\n")
            super().stop()
        except Exception as exc:
            self.logger.error("Could not stop plugin: {}. {}".format(self.name, exc))
