import csv
from vm.basevm import VM

class ReplayVM(VM):
    def __init__(self, filepath):
        self.f = open(filepath)
        self.rdr = csv.reader(self.f)
        cpu_usage, mem_usage, io_usage, netw_usage, active = next(self.rdr)

        cpu_usage = float(cpu_usage)
        mem_usage = float(mem_usage)
        io_usage = float(io_usage)
        netw_usage = float(netw_usage)
        active = True if active == 'True' else False

        self.cpu_usage = cpu_usage
        self.mem_usage = mem_usage
        self.io_usage = io_usage
        self.netw_usage = netw_usage
        self.active = active

        self.MAX_LOG_LENGTH = 1000
        self.cpu_log = [cpu_usage]
        self.mem_log = [mem_usage]
        self.io_log = [io_usage]
        self.netw_log = [netw_usage]
        self.active_log = [self.active]

        self.last_forecasted_loads = [20, 20, 20, 20]

        self.timestamp = 0
        self.last_load_tick = 0

        self.id = VM.id
        VM.id += 1
    
    
    def __del__(self):
        self.f.close()
    

    def tick(self, duration=1):
        for _ in range(duration):
            self.timestamp += 1

            self.internal_tick()
            self.log_usage()

            cpu_usage, mem_usage, io_usage, netw_usage, active = next(self.rdr)
            cpu_usage = float(cpu_usage)
            mem_usage = float(mem_usage)
            io_usage = float(io_usage)
            netw_usage = float(netw_usage)
            active = True if active == 'True' else False

            self.cpu_usage = cpu_usage
            self.mem_usage = mem_usage
            self.io_usage = io_usage
            self.netw_usage = netw_usage
            self.active = active
