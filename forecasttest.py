import csv
from utils.forecaster import AR2Forecaster, EMAForecaster

with open('instance_0.csv') as f:
    rdr = csv.reader(f)
    cpu_readings = list((float(cpu) for cpu, _, _, _, _ in rdr if float(cpu) > 0))

# fc = AR2Forecaster()
fc = EMAForecaster()

for i in range(10, len(cpu_readings)):
    d1 = cpu_readings[i]
    d2 = fc.forecast(cpu_readings[:i])
    print(f'{d1:.2f} vs {d2:.2f}')
