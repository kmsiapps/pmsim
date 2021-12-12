from vm.basevm import VM
import csv

for x in range(50):
    print(f'Simulating VM {x}')
    instance = VM()
    for t in range(3600 * 3):
        instance.tick()

    f = open(f'./synthetic_logs/instance_{x}.csv', 'w', newline='')
    writer = csv.writer(f)
    writer.writerows(zip(instance.cpu_log, instance.mem_log, instance.io_log, instance.netw_log, instance.active_log))
    f.close()
