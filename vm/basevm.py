import random
from math import log

from utils.helper import confine, correlated_lognorm

class VM:
    '''
    VM class for timeseries simulation
    '''
    id = 0

    def __init__(self, cpu_usage = -1, mem_usage = -1,
                 io_usage = -1, netw_usage = -1):
        if cpu_usage < 0:
            cpu_usage = confine(5 + random.lognormvariate(log(20), log(2)))
        
        if mem_usage < 0:
            mem_usage = confine(correlated_lognorm(0.2, cpu_usage, 20, 2))

        if io_usage < 0:
            io_usage = confine(correlated_lognorm(0.15, cpu_usage, 20, 2))
        
        if netw_usage < 0:
            netw_usage = confine(correlated_lognorm(0.1, cpu_usage, 20, 2))
        
        self.cpu_usage = cpu_usage
        self.mem_usage = mem_usage
        self.io_usage = io_usage
        self.netw_usage = netw_usage

        self.active_cpu_usage = cpu_usage
        self.active_mem_usage = mem_usage
        self.active_io_usage = io_usage
        self.active_netw_usage = netw_usage
        self.active = True

        self.MAX_LOG_LENGTH = 1000
        self.cpu_log = []
        self.mem_log = []
        self.io_log = []
        self.netw_log = []
        self.active_log = []

        self.load_duration = 10 + random.lognormvariate(log(60), log(3))
        self.load_duration_sigma = random.lognormvariate(log(10), log(2))

        self.load_period = 50 + self.load_duration + random.lognormvariate(log(600), log(3))
        self.load_period_sigma = random.lognormvariate(log(10), log(2))

        self.timestamp = 0
        self.last_load_tick = 0

        self.id = VM.id
        self.pm = None
        VM.id += 1


    def internal_tick(self):
        # For overriding. Executed for each tick
        pass


    def set_pm(self, PM):
        self.PM = PM
    

    def migrate(self, target):
        if self.PM == target:
            return
        self.PM.migrate(self, target)


    def tick(self, duration=1):
        for _ in range(duration):
            self.timestamp += 1

            self.internal_tick()
            self.log_usage()

            # random activate/deactivate (some periodic behavior)
            self.load_period = confine(
                self.load_period + random.normalvariate(0, self.load_period_sigma),
                max(300, 4 * self.load_duration), 10000)
            self.load_duration =  confine(
                self.load_duration + 
                random.normalvariate(0, self.load_duration_sigma),
                10, 100)

            if not self.active and self.timestamp - self.last_load_tick > self.load_period:
                self.activate()
            elif self.active and self.timestamp - self.last_load_tick > self.load_duration:
                self.deactivate()
            elif not self.active:
                self.cpu_usage = confine(self.cpu_usage +
                                         random.normalvariate(0, 0.1), end=2)
                self.mem_usage = confine(self.mem_usage +
                                         random.normalvariate(0, 0.1), end=2)
                self.io_usage = confine(self.io_usage +
                                        random.normalvariate(0, 0.1), end=2)
                self.netw_usage = confine(self.netw_usage +
                                          random.normalvariate(0, 0.1), end=2)
            else:
                self.cpu_usage = confine(self.cpu_usage +
                                         random.normalvariate(0, 0.5))
                self.mem_usage = confine(self.mem_usage +
                                         random.normalvariate(0, 0.5))
                self.io_usage = confine(self.io_usage +
                                        random.normalvariate(0, 0.5))
                self.netw_usage = confine(self.netw_usage +
                                          random.normalvariate(0, 0.5))


    def log_usage(self):
        self.cpu_log.append(self.cpu_usage)
        self.mem_log.append(self.mem_usage)
        self.io_log.append(self.io_usage)
        self.netw_log.append(self.netw_usage)
        self.active_log.append(self.active)
    

    def activate(self):
        self.active = True
        self.last_load_tick = self.timestamp

        self.cpu_usage = self.active_cpu_usage
        self.mem_usage = self.active_mem_usage
        self.io_usage = self.active_io_usage
        self.netw_usage = self.active_netw_usage
    

    def deactivate(self):
        self.active = False

        self.active_cpu_usage = self.cpu_usage
        self.active_mem_usage = self.mem_usage
        self.active_io_usage = self.io_usage
        self.active_netw_usage = self.netw_usage

        self.cpu_usage = random.lognormvariate(log(2), log(1.5))
        self.mem_usage = random.lognormvariate(log(2), log(1.5))
        self.io_usage = random.lognormvariate(log(2), log(1.5))
        self.netw_usage = random.lognormvariate(log(2), log(1.5))
    

    def forecast_usage(self, time_after, duration):
        raise NotImplementedError()


    def __repr__(self):
        return f"VM #{self.id} (CPU: {self.cpu_usage:6.2f}, " \
               f"RAM: {self.mem_usage:6.2f}, IO: {self.io_usage:6.2f}, " \
               f"NET: {self.netw_usage:6.2f}, ACTIV: {self.active})" 
