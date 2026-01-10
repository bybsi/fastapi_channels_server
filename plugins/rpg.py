from plugins.plugin import Plugin

class Rpg(Plugin):
    def __init__(self, logger, username):
        self.running = False
        self.logger = logger 
        super().__init__(self.logger, name='RPG', executable='rpg.pl', username=username)

    def input(self, data : str) -> bool:
        # TODO add a lock
        if len(data) > 2:
            return False
        return super().write(data)

    def start(self) -> bool:
        if super().start():
            self.running = True
            return True
        return False

    def stop(self) -> None:
        if not self.running:
            return
        try:
            self.write("#sq\n")
            saved = self.read()
            super().stop()
        except Exception as exc:
            self.logger.error(f"Could not stop plugin: {self.name}. {exc}")
#
#import logging
#l = logging.getLogger(__name__)
#logging.basicConfig(filename='test.log', level=logging.DEBUG)
#r = Rpg(l)

#r.start()

#while True:
#    while True:
#        line = r.read()
#        if '[wait]' in line:
#            break
#        print(line)
#    
#    inp = input("input: ")
#    r.input(inp)
