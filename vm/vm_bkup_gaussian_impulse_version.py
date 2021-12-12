from utils.forecaster import EMAForecaster
from vm.replayvm import ReplayVM
from utils.helper import get_stat, gaussian_pdf

import matplotlib.pyplot as plt

class VM_Proposed(ReplayVM):
    def __init__(self, filename, lambda_param=5):
        super().__init__(filename)
        self.active_pred = False
        self.active_pred_log = [self.active_pred]
        self.load_ticks = []
        self.load_durations = []
        self.lambda_param = lambda_param


    def internal_tick(self):
        # predict if this vm is active
        # 5 is active threshold (magic num)
        if self.cpu_usage > 5 and not self.active_pred:
            self.active_pred = True
            self.load_ticks.append(self.timestamp)
        elif self.cpu_usage < 5 and self.active_pred:
            self.active_pred = False
            self.load_durations.append(self.timestamp - self.load_ticks[-1])
        self.active_pred_log.append(self.active_pred)
    

    def get_load_usage(self, percentile=95):
        forecaster = EMAForecaster()
        data_list = []

        for data in (self.cpu_log, self.mem_log, self.io_log, self.netw_log):
            # get active usage log
            data = zip(data, self.active_pred_log)
            data = list(num for num, _ in filter(lambda x: x[1], data))

            data.sort()
            p95 = data[round((len(data) - 1) / 100 * percentile)]
            data_list.append(p95)
        
        return data_list

    def get_period(self, data, magic_num=500):
        if len(data) < 2:
            periods = [magic_num] # magic number
        else:
            periods = [data[i] - data[i-1]
                       for i in range(1, len(data))]

        period, period_s = get_stat(periods)
        if period_s == 0:
            # when there is no sufficient data, use magic number instead
            period_s = period / 5
        
        return period, period_s, periods


    def forecast_usage(self, time_after, duration):
        # if no sufficient data, return magic value
        if len(self.cpu_log) <= 10:
            return [20] * 4

        time_after = time_after + duration

        # 1) p95 load usage
        load_usages = self.get_load_usage()

        # 2) Calculate average period and its sigma
        loadticks = self.load_ticks[:]
        avg_load_period, load_s, load_periods = self.get_period(loadticks)

        if self.timestamp > self.load_ticks[-1] + avg_load_period:
            loadticks.append(self.timestamp)
            avg_load_period, load_s, load_periods = self.get_period(loadticks)

        load_s /= self.lambda_param

        # 3) Calculate 95th load duration
        d = self.load_durations[:]
        d.sort()
        load_duration = d[round((len(d) - 1) / 100 * 95)]
        
        predicted_loads = []
        for load_usage in load_usages:
            portional_load_usage = load_usage / len(load_periods)
            for load_period in load_periods:
                # for each resources (cpu, mem, netw, ...)
                predicted_load = [0] * time_after

                start = self.load_ticks[-1]

                for t_target in range(start,
                                    self.timestamp + time_after + load_period, load_period):
                    # for each predicted load duration,
                    for i in range(time_after):
                        # predict load with gaussian pdfs
                        t = i + self.timestamp + 1
                        if t < t_target: 
                            predicted_load[i] = min(
                                load_usage,
                                predicted_load[i] + portional_load_usage * gaussian_pdf(t, t_target, load_s))
                        elif t_target + load_duration > t >= t_target:
                            predicted_load[i] = min(
                                load_usage,
                                predicted_load[i] + portional_load_usage)
                        else:
                            predicted_load[i] = min(
                                load_usage,
                                predicted_load[i] + portional_load_usage * gaussian_pdf(t, t_target + load_duration, load_s))
            
            '''
            if len(predicted_loads) == 0:
                plt.plot(range(self.timestamp, self.timestamp + time_after), predicted_load)
                plt.ylim((0, 100))
                plt.show()
            '''
            
            predicted_load = predicted_load[-1 * duration:]
            predicted_load.sort()
            predicted_loads.append(predicted_load[round((len(predicted_load) - 1) / 100 * 95)])

        return predicted_loads
