from io import TextIOWrapper
from typing import Union
from subprocess import PIPE, Popen
from threading import Thread
from queue import Queue, Empty
from core.logger import Logger
from core.pidfile import PidFile
from signal import SIGTERM
from time import sleep
import re
import os
import settings
import sys

def read_stdout(stdout : TextIOWrapper, data_q : Queue) -> None:
    for line in stdout:
        data_q.put(line.rstrip())
    stdout.close()

class Plugin():
    name = ''

    def __init__(self, logger : Logger, **kwargs) -> None:

        if not os.path.exists(settings.VAR_DIR):
            os.makedirs(settings.VAR_DIR)
        
        if ('executable' not in kwargs and 
            'name' not in kwargs):
            print("executable, name, and logger are required arguments")
            os.exit(1)
            
        if re.search(r"[^\w.]", kwargs['executable']):
            print(r"Invalid executable name (only [\w.] is allowed): {}".format(executable))
            os.exit(1)

        self.name = kwargs['name']
        self.executable = kwargs['executable']
        self.username = kwargs.get('username','')
        self.logger = logger
        self.process = None
        self.pid_file = PidFile(os.path.join(settings.VAR_DIR, 'plugin_{}.pid'.format(self.name)))

    def start(self) -> bool:
        try:
            if self.executable.endswith('.pl'):
                cmd_a = ['perl', self.executable, self.username] 
            else:
                cmd_a = ['./'+self.executable]
            self.logger.info("Running {} for user {}".format(self.executable, self.username))
            self.process = Popen(
                    cmd_a,
                    cwd = settings.PLUGIN_DIR,
                    stdin=PIPE,
                    stdout=PIPE,
                    text=True)
        except Exception as exc:
            self.logger.error("Could not create subprocess for plugin \"{}\". {}".format(self.name, exc))
            return False

        #(o,e) = self.process.communicate();
        #print("{},{}".format(o,e))
        self.pid_file.write_pidfile(self.process.pid)

        self.data_q = Queue()
        self.read_t = Thread(target=read_stdout, args=(self.process.stdout, self.data_q))
        self.read_t.daemon = True
        self.read_t.start()
        
        try:
            startup = self.data_q.get(timeout=10)
        except Empty:
            self.logger.error("Plugin \"{}\" took to long to load.".format(self.name))
            self.stop()
            return False
        else:
            if 'Error' in startup:
                self.logger.error("Could not load the plugin named \"{}\". {}".format(self.name, startup))
                self.stop()
                return False
            elif '100%' in startup:
                self.logger.info("Plugin \"{}\" started.".format(self.name))

        return True

    def write(self, data : str) -> bool:
        try:
            # Important that we are always sending a newline
            # with our plugin commands. 10000% CPU otherwise,
            # also we'll just never get a response.
            self.process.stdin.write(data)
            if not data.endswith("\n"):
                self.process.stdin.write("\n")
            self.process.stdin.flush()
        except Exception as exc:
            self.logger.info("Could not send input to plugin \"{}\". {}".format(self.name, exc))
            return False
        return True

    def read(self) -> str:
        try:
            data = self.data_q.get()
        except Exception as exc:
            self.logger.error("Error reading data from plugin \"{}\". {}".format(self.name, exc))
        return data
    
    # marker signals the end of a block.
    def read_block(self, marker : str = '[wait]') -> str:
        lines = ""
        try:
            # TODO Put this in a thread so we can time it out
            while True:
                line = self.data_q.get()
                #if "[sequence]" in line:
                    # See channel_server.py for
                    # how this will work later on.
                    #return self.sequencer()
                #    while True:
                #        line = self.data_q.get()
                #        if "[/sequence]" in line:
                #            break
                #        lines += line + "\n"
                #    continue

                if "[wait]" in line:
                    break
                # TODO for now re add lines here,
                # but we should create instance with a different type
                # of reader thread to keep new lines.
                lines += line + "\n"
        except Exception as exc:
            self.logger.error("Error reading block data from plugin \"{}\", {}".format(self.name, exc))
        return lines

    def sequencer(self):
        while True:
            line = self.data_q.get()
            if "[/sequence]" in line:
                self.logger.error("end sequence found")
                break
            yield line

    def stop(self) -> None:
        self.logger.info("Stopping \"{}\" plugin. username: {}".format(self.name, self.username))
        if self.process:
            try:
                self.process.terminate()
                self.process.wait()
            except Exception as exc:
                self.logger.info("Error stopping \"{}\" plugin. {}".format(self.naem, exc))
        else:
            pid = self.pid_file.get_pid()
            if pid is None:
                return
            self.logger.info("got pid {}".format(pid))
            try:
                os.kill(pid, SIGTERM)
            except OSError as e:
                self.logger.info("Error stopping {}:{}".format(self.name, e))
                sys.exit(0)
            self.logger.info("{} stopped.".format(self.name))
            self.pid_file.remove_pidfile()

