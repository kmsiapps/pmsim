import matplotlib.pyplot as plt
import csv

from vm.vm import VM_Proposed, VM_Naive_Max, VM_Naive_Mean

for k in range(2, 3):
    filename = f'./synthetic_logs/instance_{k}.csv'
    lambda_param = 1

    idx = []
    loads = []

    active_log = False
    i = 0
    # get groundtruth activate ticks
    with open(filename) as f:
        rdr = csv.reader(f)
        for load, _, _, _, active in rdr:
            active = True if active == 'True' else False
            if active and not active_log:
                idx.append(i)
                loads.append(float(load))
            active_log = active
            i += 1

    instance = VM_Proposed(filename, lambda_param=lambda_param)
    # instance = VM_Naive_Max(filename)
    # instance = VM_Naive_Mean(filename)

    timestamp = []
    prediction = []
    t = 0
    while True:
        try:
            instance.tick()
            if t % 100 == 0:
                timestamp.append(instance.timestamp)
                prediction.append(instance.forecast_usage(0, 100)[0])
                # print(f'{instance.timestamp}~{instance.timestamp + 100}: {instance.forecast_usage(0, 100)[0]:.2f}')
        except StopIteration:
            print('Sim done')
            break
        t += 1

    plt.plot(timestamp, prediction, 'lightblue')
    plt.stem(idx, loads, linefmt='g', markerfmt='gx', basefmt=' ')

    timestamp_responsible = [0]
    prediction_responsible = [prediction[0]]

    for i in idx:
        for t, p in zip(timestamp, prediction):
            if t <= i < t + 100:
                timestamp_responsible.append(t)
                prediction_responsible.append(p)

    plt.plot(timestamp_responsible, prediction_responsible, 'rx')
    plt.show()

f = open('./sim_results/proposed_forecasts_timeseries.csv', 'w', newline='')
writer = csv.writer(f)
writer.writerow(['Timestamp', 'Forecasts'])
writer.writerows(zip(timestamp, prediction))
f.close()

f = open('./sim_results/proposed_load_timeseries.csv', 'w', newline='')
writer = csv.writer(f)
writer.writerow(['Timestamp', 'Loads'])
writer.writerows(zip(idx, loads))
f.close()
