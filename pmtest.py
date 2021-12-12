import matplotlib.pyplot as plt
import random

from pm.pm import PM
from pm.vmmigrator import VM_Migrator, Naive_VM_Migrator
from vm.vm import VM_Naive_Max, VM_Naive_Mean, VM_Proposed


k = 0
push_time = 0
MAX_VM = 50
FORECAST_PERIOD = 100
SIM_DURATION = 5000

pm_list = [PM()]

forecast_timestamp = []
forecasts = []

migrator = VM_Migrator()
# migrator = Naive_VM_Migrator()

for t in range(SIM_DURATION):
    # push vm
    if k < MAX_VM and t >= push_time:
        filename = f'./synthetic_logs/instance_{k}.csv'
        # vm = VM_Proposed(filename, lambda_param=1)
        # vm = VM_Naive_Max(filename)
        vm = VM_Naive_Mean(filename)

        # push vm into least-used pm
        target_pm = min(pm_list, key=lambda pm: pm.last_forecasted_loads[0])
        target_pm.push(vm)
        push_time += random.randint(5, 60)
        k += 1

    # vm usage forecast
    for machine in pm_list:
        if t % FORECAST_PERIOD == 0:
            machine.forecast_usage(0, 100)
    
    # pm placement
    pm_list = migrator.migrate(pm_list)

    # tick
    for machine in pm_list:
        machine.tick()
    
    if t % 1000 == 0:
        print(f'{t}/{SIM_DURATION}')

print('Sim done')
deployments = [machine.init_timestamp for machine in pm_list]

for machine in pm_list:
    for mt in machine.migration_timestamp:
        plt.axvline(mt, color='lightgray', linestyle='--')
    
    for dp in deployments:
        plt.axvline(dp, color='lightblue', linestyle='-')

    plt.plot(range(machine.init_timestamp, SIM_DURATION + 1), [100] * len(machine.cpu_log), 'r--')
    plt.plot(range(machine.init_timestamp, SIM_DURATION + 1), machine.cpu_log)
    plt.plot(machine.forecast_timestamps, machine.forecasts[0])

    plt.show()

    print(f'PM #{machine.id}, '
        f'# of violations: {len(machine.overload_ticks)}, '
        f'avg violations: {sum(machine.overload_loads) / max(1, len(machine.overload_loads)):.2f}, '
        f'avg load: {sum(machine.cpu_log)/len(machine.cpu_log):.2f}, '
        f'# of migrations: {machine.migrations}')

# TODO:
# 3) Experiments:
#    max vs mean vs naive (# of violations, # of pms, pm cpu usages)
#    lambda_param vs. # of violations, pm cpu usages (efficiency); proposed ~ max as lambda goes lower
#    naive vs propopsed placement: # of migrations
