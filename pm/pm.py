from vm.basevm import VM

class PM:
    id = 0

    def __init__(self, cpu_capa = 100, mem_capa = 100,
                 io_capa = 100, netw_capa = 100,
                 max_overload = 0.10, init_timestamp = 0):
        self.VM_list = []

        self.cpu_usage = 0
        self.mem_usage = 0
        self.io_usage = 0
        self.netw_usage = 0

        self.cpu_log = [0]
        self.mem_log = [0]
        self.io_log = [0]
        self.netw_log = [0]

        self.last_forecasted_loads = [0, 0, 0, 0]
        self.forecasts = [[0], [0], [0], [0]]
        self.forecast_timestamps = [init_timestamp]

        self.cpu_capa = cpu_capa
        self.mem_capa = mem_capa
        self.io_capa = io_capa
        self.netw_capa = netw_capa

        self.overloaded = False

        self.max_pred_overload = max_overload
        self.overload_ticks = []
        self.overload_loads = []

        self.migrations = 0
        self.migration_timestamp = []

        self.init_timestamp = init_timestamp
        self.timestamp = init_timestamp
        
        self.id = PM.id
        PM.id += 1
    
    
    def push(self, vm:VM):
        vm.PM = self
        self.VM_list.append(vm)
    

    def pop(self, vm:VM):
        idx = self.VM_list.index(vm)
        return self.VM_list.pop(idx)
    

    def migrate(self, vm:VM, dest):
        # dest: instance of PM
        self.migrations += 1
        if not self.timestamp in self.migration_timestamp:
            self.migration_timestamp.append(self.timestamp)
        
        for i in range(len(dest.last_forecasted_loads)):
                self.last_forecasted_loads[i] -= vm.last_forecasted_loads[i]
                dest.last_forecasted_loads[i] += vm.last_forecasted_loads[i]
        
        dest.push(self.pop(vm))
    

    def check_overload(self):
        if self.cpu_usage > self.cpu_capa:
            self.overloaded = True
            self.overload_ticks.append(self.timestamp)
            self.overload_loads.append(self.cpu_usage / self.cpu_capa * 100 - 100)
    

    def forecast_usage(self, time_after, duration):
        cpu_usage_fc = 0
        mem_usage_fc = 0
        netw_usage_fc = 0
        io_usage_fc = 0
        for vm in self.VM_list:
            cpu, mem, netw, io = vm.forecast_usage(time_after, duration)
            cpu_usage_fc += cpu
            mem_usage_fc += mem
            netw_usage_fc += netw
            io_usage_fc += io
        
        forecasted_loads = [cpu_usage_fc, mem_usage_fc, netw_usage_fc, io_usage_fc]

        self.last_forecasted_loads = forecasted_loads
        self.forecast_timestamps.append(self.timestamp)
        for i in range(len(forecasted_loads)):
            self.forecasts[i].append(forecasted_loads[i])

        return forecasted_loads


    def tick(self, duration=1):
        self.cpu_usage = 0
        self.mem_usage = 0
        self.io_usage = 0
        self.netw_usage = 0

        for _ in range(duration):
            self.timestamp += 1

            for vm in self.VM_list:
                vm.tick()
                self.cpu_usage += vm.cpu_usage
                self.mem_usage += vm.mem_usage
                self.io_usage += vm.io_usage
                self.netw_usage += vm.netw_usage
            
            self.log_usage()
            self.check_overload()


    def log_usage(self):
        self.cpu_log.append(self.cpu_usage)
        self.mem_log.append(self.mem_usage)
        self.netw_log.append(self.netw_usage)
        self.io_log.append(self.io_usage)


    def __repr__(self):
        return f"PM #{self.id} (CPU: {self.cpu_usage:6.2f}, " \
               f"RAM: {self.mem_usage:6.2f}, IO: {self.io_usage:6.2f}, " \
               f"NET: {self.netw_usage:6.2f}, # of VMs: {len(self.VM_list):3})"
