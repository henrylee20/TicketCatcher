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

    def __init__(self, yellow_bull_cores: list, cfg: dict):
        self.cylinder_list = list()

        for core in yellow_bull_cores:
            cylinder = YellowBullEngine.Cylinder(core, cfg)
            self.cylinder_list.append(cylinder)

    def run(self, interval_time=0.5):
        for cylinder in self.cylinder_list:
            cylinder.start()
            time.sleep(interval_time)

        for cylinder in self.cylinder_list:
            cylinder.join()


