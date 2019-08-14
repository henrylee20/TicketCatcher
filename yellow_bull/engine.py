import time
import threading
from .core.core import YellowBullCore


class YellowBullEngine:
    class Cylinder(threading.Thread):
        def __init__(self, core: YellowBullCore, cfg: dict):
            super().__init__()
            self.core = core
            self.cfg = cfg

        def run(self):
            self.core.catch_ticket(self.cfg)

    def __init__(self, core: YellowBullCore, cfg: dict, thread_num=1):
        self.cylinder_list = list()

        for i in range(thread_num):
            cylinder = YellowBullEngine.Cylinder(core, cfg)
            self.cylinder_list.append(cylinder)

    def run(self, interval_time=0.5):
        for cylinder in self.cylinder_list:
            cylinder.start()
            time.sleep(interval_time)

        for cylinder in self.cylinder_list:
            cylinder.join()


