from utils.forecaster import EMAForecaster
from vm.replayvm import ReplayVM
from utils.helper import get_stat, gaussian_pdf


class VM_Naive_Max(ReplayVM):
    def forecast_usage(self, time_after, duration):
        max_cpu = max(self.cpu_log)
        max_mem = max(self.mem_log)
        max_io = max(self.io_log)
        max_netw = max(self.netw_log)
        
        predicted_loads = [max_cpu, max_mem, max_io, max_netw]
        self.last_forecasted_loads = predicted_loads
        return predicted_loads


class VM_Naive_Mean(ReplayVM):
    def forecast_usage(self, time_after, duration):
        max_cpu = sum(self.cpu_log) / len(self.cpu_log)
        max_mem = sum(self.mem_log) / len(self.mem_log)
        max_io = sum(self.io_log) / len(self.io_log)
        max_netw = sum(self.netw_log) / len(self.netw_log)

        predicted_loads = [max_cpu, max_mem, max_io, max_netw]
        self.last_forecasted_loads = predicted_loads
        return predicted_loads


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
        
        return period, period_s


    def forecast_usage(self, time_after, duration):
        try:
            time_after = time_after + duration

            # 1) p95 load usage
            # load_usages = self.get_load_usage(percentile=95)

            # 1) Calculate average period and its sigma
            loadticks = self.load_ticks[:]
            load_period, load_s = self.get_period(loadticks)

            load_period = int(load_period)
            load_s /= self.lambda_param

            # 2) sum over load period
            load_usages = [sum(self.cpu_log[:load_period]),
                           sum(self.mem_log[:load_period]),
                           sum(self.io_log[:load_period]),
                           sum(self.netw_log[:load_period]),
                          ]

            # 3) Calculate 95th load duration
            d = self.load_durations[:]
            d.sort()
            load_duration = d[round((len(d) - 1) / 100 * 95)]
            
            predicted_loads = []
            for load_usage in load_usages:
                # for each resources (cpu, mem, netw, ...)
                predicted_load = [0] * time_after

                # conservative approach: if predicted load before but not yet,
                # retain load predictions
                if loadticks[-1] + load_period < self.timestamp:
                    predicted_loads.append(min(load_usage * gaussian_pdf(0, 0, load_s), 100))
                    continue

                start = self.load_ticks[-1]

                for t_target in range(start,
                                    self.timestamp + time_after + load_period, load_period):
                    # for each predicted load duration,
                    for i in range(time_after):
                        # predict load with gaussian pdfs
                        t = i + self.timestamp + 1
                        if t < t_target: 
                            predicted_load[i] = min(
                                predicted_load[i] + load_usage * gaussian_pdf(t, t_target, load_s),
                                100)
                        elif t_target + load_duration > t >= t_target:
                            predicted_load[i] = min(load_usage * gaussian_pdf(0, 0, load_s), 100)
                        else:
                            predicted_load[i] = min(
                                predicted_load[i] + load_usage * gaussian_pdf(t, t_target + load_duration, load_s),
                                100)

                predicted_load = predicted_load[-1 * duration:]
                predicted_load.sort()
                predicted_95th = predicted_load[round((len(predicted_load) - 1) / 100 * 95)]

                predicted_loads.append(min(predicted_95th, 100))
                
                # print(f'{load_usage * gaussian_pdf(0, 0, load_s):.2f}, {sum(self.cpu_log) / max(len(self.cpu_log), 1):.2f}')
        except:
            # if no sufficient data, return mean
            predicted_loads = [sum(self.cpu_log) / max(len(self.cpu_log), 1),
                               sum(self.mem_log) / max(len(self.mem_log), 1),
                               sum(self.io_log) / max(len(self.io_log), 1),
                               sum(self.netw_log) / max(len(self.netw_log), 1),
                              ]

        self.last_forecasted_loads = predicted_loads
        return predicted_loads
