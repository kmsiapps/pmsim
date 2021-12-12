import matplotlib.pyplot as plt
import random

from pm.pm import PM
from pm.vmmigrator import VM_Migrator, Naive_VM_Migrator
from vm.vm import VM_Naive_Max, VM_Naive_Mean, VM_Proposed

random.seed(0)

# Params ========================
MAX_VM = 50
FORECAST_PERIOD = 100
SIM_DURATION = 10000

# For plots =====================
total_usage = []
total_forecasts = []
num_pms = []
num_vms = []
avg_pm_loads = []
violations = []
migrations = []

# Simulations ===================

pm_list = [PM()]
pm_history = set(pm_list[:])

migrator = VM_Migrator()
# migrator = Naive_VM_Migrator()

k = 0
push_time = 0
for t in range(SIM_DURATION):
    # push vm
    if k < MAX_VM and t >= push_time:
        filename = f'./synthetic_logs/instance_{k}.csv'
        vm = VM_Proposed(filename, lambda_param=1)
        # vm = VM_Naive_Max(filename)
        # vm = VM_Naive_Mean(filename)

        # push vm into least-used pm
        target_pm = min(pm_list, key=lambda pm: pm.last_forecasted_loads[0])
        target_pm.push(vm)
        push_time += random.randint(30, 300)
        k += 1

    # vm usage forecast
    for machine in pm_list:
        if t % FORECAST_PERIOD == 0:
            machine.forecast_usage(0, 100)
    
    # pm placement
    pm_list = migrator.migrate(pm_list)
    pm_history = pm_history.union(set(pm_list))

    # tick
    for machine in pm_list:
        machine.tick()
    
    if t % 1000 == 0:
        print(f'{t}/{SIM_DURATION}')
    
    # For plot:
    total_usage.append(sum(pm.cpu_usage for pm in pm_list))
    total_forecasts.append(sum(pm.last_forecasted_loads[0] for pm in pm_list))
    num_pms.append(len(pm_list))
    num_vms.append(sum(len(pm.VM_list) for pm in pm_list))
    avg_pm_loads.append(sum(pm.cpu_usage for pm in pm_list) / len(pm_list))
    violations.append(sum(len(pm.overload_ticks) for pm in pm_list))
    migrations.append(sum(pm.migrations for pm in pm_list))

print('Sim done')

# Results ===========================

deployments = [machine.init_timestamp for machine in pm_list]
timestamp = range(SIM_DURATION)

plt.title('Total usage vs forecasts')
plt.plot(timestamp, total_usage)
plt.plot(timestamp, total_forecasts)

plt.show()

# =============

_, ax1 = plt.subplots()
ax2 = ax1.twinx()

plt.title('Average usage, # PMs, # VMs')
ax1.plot(timestamp, avg_pm_loads, 'y')
ax1.plot(timestamp, [100] * len(timestamp), 'r--')

ax2.plot(timestamp, num_pms, 'g')
ax2.plot(timestamp, num_vms, 'b')

plt.show()

# =============

_, ax1 = plt.subplots()
ax2 = ax1.twinx()

plt.title('Violations and migrations')
ax1.plot(timestamp, violations, 'r')
ax2.plot(timestamp, migrations, 'b')

plt.show()

# Per-machine results ===============

for machine in pm_history:
    for mt in machine.migration_timestamp:
        # plt.axvline(mt, color='lightgray', linestyle='--')
        pass
    
    for dp in deployments:
        plt.axvline(dp, color='lightblue', linestyle='-')

    plt.plot(range(machine.init_timestamp, machine.init_timestamp + len(machine.cpu_log)), [100] * len(machine.cpu_log), 'r--')
    plt.plot(range(machine.init_timestamp, machine.init_timestamp + len(machine.cpu_log)), machine.cpu_log)
    plt.plot(machine.forecast_timestamps, machine.forecasts[0])

    plt.show()

    print(f'PM #{machine.id}, {machine.init_timestamp}~{machine.init_timestamp + len(machine.cpu_log)}, '
        f'# Overloads: {len(machine.overload_ticks)}, '
        f'Avg overloads: {sum(machine.overload_loads) / max(1, len(machine.overload_loads)):.2f}, '
        f'Avg load: {sum(machine.cpu_log)/len(machine.cpu_log):.2f}, '
        f'# of migrations: {machine.migrations}')

# TODO:
# 3) Experiments:
#    max vs mean vs naive (# of violations, # of pms, pm cpu usages)
#    lambda_param vs. # of violations, pm cpu usages (efficiency); proposed ~ max as lambda goes lower
#    naive vs propopsed placement: # of migrations
