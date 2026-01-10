import os

class PidFile:
    def __init__(self, pid_file):
        self.pid_file = pid_file

    def get_pid(self):
        try:
            with open(self.pid_file, 'r') as pid_fp:
                pid = int(pid_fp.read().strip())
        except IOError:
            pid = None
        except:
            self.remove_pidfile()
            pid = None
        else:
            if not self.alive(pid):
                self.remove_pidfile()
                pid = None
        return pid
    
    def remove_pidfile(self):
        if os.path.exists(self.pid_file):
            os.remove(self.pid_file)

    def write_pidfile(self, pid):
        with open(self.pid_file, 'wt') as pid_fp:
            pid_fp.write(str(pid))
    
    def alive(self, pid):
        try:
            os.kill(pid, 0)
        except OSError as exc:
            return False
        return True
