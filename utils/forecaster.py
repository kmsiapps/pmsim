class AR2Forecaster():
    def __init__(self):
        pass

    def forecast(self, data):
        # data(t) = a1 * data(t-1) + a2 * data(t-2)
        a1, a2 = self.get_parameters(data)
        return a1 * data[-1] + a2 * data[-2]
    
    def get_parameters(self, data):
        # get a1, a2
        variance = self.get_delayed_cov(data, 0)
        r1 = self.get_delayed_cov(data, 1) / variance
        r2 = self.get_delayed_cov(data, 2) / variance
        a1 = r1 * (1 - r2) / (1 - r1**2)
        a2 = (r2 - r1**2) / (1 - r1**2)
        return a1, a2
        
    def get_delayed_cov(self, data, delay):
        mean = sum(data) / len(data)
        mul = list((data[i] - mean) * (data[i + delay] - mean)
                    for i in range(len(data) - delay))
        return sum(mul) / len(data)


class EMAForecaster():
    def __init__(self):
        pass

    def forecast(self, data):
        # data(t) = gamma * data(t-1) + (1 - gamma) * data(t-2)
        gamma = 0.95
        d = data[0]
        for x in data[1:]:
            d = gamma * x + (1 - gamma) * d
        return d
   

