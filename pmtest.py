import matplotlib.pyplot as plt
import random
import csv
import os

from pm.pm import PM
from pm.vmmigrator import VM_Migrator, Naive_VM_Migrator
from vm.vm import VM_Naive_Max, VM_Naive_Mean, VM_Proposed

random.seed(0)

# Params ========================
MAX_VM = 50
FORECAST_PERIOD = 100
SIM_DURATION = 10000
dirname = "sim_results/migrator=proposed,vm=max"

# For plots =====================
total_usage = []
total_forecasts = []
num_pms = []
num_vms = []
avg_pm_loads = []
violations = []
violation_loads = []
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
        # vm = VM_Proposed(filename, lambda_param=1)
        # vm = VM_Naive_Mean(filename)
        vm = VM_Naive_Max(filename)
        
        # push vm into least-used pm
        target_pm = min(pm_list, key=lambda pm: pm.last_forecasted_loads[0])
        target_pm.push(vm)
        push_time += random.randint(30, 150)
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

    violations.append(sum(len(pm.overload_ticks) for pm in pm_history))
    violation_loads.append(sum(sum(pm.overload_loads) for pm in pm_history))
    migrations.append(sum(pm.migrations for pm in pm_history))

print('Sim done')

# Results ===========================

deployments = [machine.init_timestamp for machine in pm_history]
destroyed = [machine.init_timestamp + len(machine.cpu_log) for machine in pm_history]
timestamp = range(SIM_DURATION)

plt.title('Total usage vs forecasts')
plt.plot(timestamp, total_usage)
plt.plot(timestamp, total_forecasts)

# plt.show()

# =============

_, ax1 = plt.subplots()
ax2 = ax1.twinx()

plt.title('Average usage, # PMs, # VMs')
ax1.plot(timestamp, avg_pm_loads, 'y')
ax1.plot(timestamp, [100] * len(timestamp), 'r--')

ax2.plot(timestamp, num_pms, 'g')
ax2.plot(timestamp, num_vms, 'b')

# plt.show()

# =============

_, ax1 = plt.subplots()
ax2 = ax1.twinx()

plt.title('Violations and migrations')
ax1.plot(timestamp, violations, 'r')
ax2.plot(timestamp, migrations, 'b')

# plt.show()

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

    # plt.show()

    print(f'PM #{machine.id}, {machine.init_timestamp}~{machine.init_timestamp + len(machine.cpu_log)}, '
        f'# Overloads: {len(machine.overload_ticks)}, '
        f'Avg overloads: {sum(machine.overload_loads) / max(1, len(machine.overload_loads)):.2f}, '
        f'Avg load: {sum(machine.cpu_log)/len(machine.cpu_log):.2f}, '
        f'# of migrations: {machine.migrations}')

# Data save ===========================

if not os.path.isdir(f'./{dirname}'):
    os.mkdir(f'./{dirname}')

f = open(f"./{dirname}/overall_stat.csv", "w", newline='')
writer = csv.writer(f)
data = zip(timestamp, total_usage, total_forecasts, avg_pm_loads, num_pms, num_vms, violations, violation_loads, migrations)
writer.writerow(['Timestamp', 'TotalUsage', 'TotalForecasts', 'AvgPMLoads', 'NumPMs', 'NumVMs', 'Violations', 'ViolationSum', 'Migrations'])
writer.writerows(data)
f.close()

f = open(f'./{dirname}/deployments.csv', 'w', newline='')
writer = csv.writer(f)
writer.writerow(['DeploymentTime'])
for dp in deployments:
    writer.writerow([dp])
f.close()

f = open(f'./{dirname}/destroyed.csv', 'w', newline='')
writer = csv.writer(f)
writer.writerow(['DestroyedTime'])
for ds in destroyed:
    writer.writerow([ds])
f.close()


for pm in pm_history:
    if not os.path.isdir(f'./{dirname}/pm{pm.id}'):
        os.mkdir(f'./{dirname}/pm{pm.id}')

    f = open(f"./{dirname}/pm{pm.id}/cpulogs.csv", "w", newline='')
    writer = csv.writer(f)
    timestamp = range(machine.init_timestamp, machine.init_timestamp + len(machine.cpu_log))
    data = zip(timestamp, pm.cpu_log)
    writer.writerow(['Timestamp', 'CPUUsage'])
    writer.writerows(data)
    f.close()

    f = open(f"./{dirname}/pm{pm.id}/forecasts.csv", "w", newline='')
    writer = csv.writer(f)
    data = zip(pm.forecast_timestamps, pm.forecasts[0])
    writer.writerow(['Timestamp', 'CPUForecasts'])
    writer.writerows(data)
    f.close()

    f = open(f"./{dirname}/pm{pm.id}/migrations.csv", "w", newline='')
    writer = csv.writer(f)
    writer.writerow(['MigrationTime'])
    for mt in pm.migration_timestamp:
        writer.writerow([mt])
    f.close()

    f = open(f"./{dirname}/pm{pm.id}/stats.txt", "w")
    f.write(
        f'PM #{pm.id}, {pm.init_timestamp}~{pm.init_timestamp + len(pm.cpu_log)}\n'
        f'# Overloads: {len(pm.overload_ticks)}\n'
        f'Avg overloads: {sum(pm.overload_loads) / max(1, len(pm.overload_loads)):.2f}\n'
        f'Avg load: {sum(pm.cpu_log)/len(pm.cpu_log):.2f}\n'
        f'# of migrations: {pm.migrations}\n'
    )
    f.close()
