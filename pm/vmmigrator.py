from pm.pm import PM

MIN_LOAD_THRESHOLD = 40
MIN_PM_LIFE = 500

def get_best_fit_vm(pm, vm_list):
    target = list(filter(lambda vm: pm.last_forecasted_loads[0] \
                        - vm.last_forecasted_loads[0] - 100 * (1 + pm.max_pred_overload) < 0,
                        vm_list))
    
    # if there's no best-fit vm, then migrate heaviest vm
    if len(target) == 0:
        return max(vm_list, key=lambda vm: vm.last_forecasted_loads[0])
    
    return min(target,
               key=lambda vm: abs(pm.last_forecasted_loads[0])\
                   - vm.last_forecasted_loads[0] - 100 * (1 + pm.max_pred_overload))


def get_best_fit_pm(vm, pm_list):
    target = list(filter(lambda pm: pm.last_forecasted_loads[0] \
                        + vm.last_forecasted_loads[0] <= 100 * (1 + pm.max_pred_overload),
                        pm_list))
    
    # if there's no best-fit vm, then return None
    if len(target) == 0:
        return None

    return min(target,
               key=lambda pm: abs(pm.last_forecasted_loads[0])\
                   + vm.last_forecasted_loads[0] - 100 * (1 + pm.max_pred_overload))


class VM_Migrator():
    def migrate(self, pm_list_origin):
        '''
        Migrates each VMs to PMs, based on their last forecasted load usage
        '''

        pm_list = pm_list_origin[:]
        pm_list.sort(key=lambda pm: pm.last_forecasted_loads[0], reverse=True)

        placement_target = []

        # Remove underutilized pms
        avg_util = sum((pm.last_forecasted_loads[0] for pm in pm_list)) / len(pm_list)
        while len(pm_list) > 1 and avg_util < MIN_LOAD_THRESHOLD and \
              min(len(pm.cpu_log) for pm in pm_list) >= MIN_PM_LIFE:
            print(f'{pm_list[0].timestamp}: PM #{pm_list[-1].id} Removed! on {avg_util:.2f}%')
            placement_target += pm_list[-1].VM_list
            pm_list = pm_list[:-1]
            avg_util = sum((pm.last_forecasted_loads[-1] for pm in pm_list)) / len(pm_list)
        
        # get target VMs
        # loads[0] for cpu (loads: [cpu, mem, io, netw])
        overloaded_pm_list = list(filter(lambda pm: \
                                        pm.last_forecasted_loads[0] > 100 * (1 + pm.max_pred_overload),
                                        pm_list))
        
        while overloaded_pm_list:
            for overloaded_pm in overloaded_pm_list:
                target = get_best_fit_vm(overloaded_pm, overloaded_pm.VM_list)
                placement_target.append((target))

                for i in range(len(overloaded_pm.last_forecasted_loads)):
                    overloaded_pm.last_forecasted_loads[i] -= target.last_forecasted_loads[i]
            
                    overloaded_pm_list = list(filter(lambda pm: \
                                        pm.last_forecasted_loads[0] > 100 * (1 + pm.max_pred_overload),
                                        pm_list))

        # sort target VMs in descending order
        placement_target.sort(key=lambda vm: vm.last_forecasted_loads[0],
                            reverse=True)
        
        while placement_target:
            # put vm into best-fit pm
            new_placement_target = []
            for vm in placement_target:
                best_fit_pm = get_best_fit_pm(vm, pm_list)

                if best_fit_pm:
                    vm.migrate(best_fit_pm)
                else:
                    new_placement_target.append(vm)

            placement_target = new_placement_target

            # if placement_target is not empty, deploy new pm
            if placement_target:
                new_pm = PM(init_timestamp=pm_list[0].timestamp)
                pm_list.append(new_pm)

                avg_util = sum((pm.last_forecasted_loads[0] for pm in pm_list)) / len(pm_list)
                print(f'{pm_list[0].timestamp}: PM #{new_pm.id} Added! on {avg_util:.2f}%')
        
        return pm_list


class Naive_VM_Migrator():
    def migrate(self, pm_list):
        '''
        Naive version of VM Migrator.
        Migrates greedily without any consideration of # of migrations
        '''
        pm_list = pm_list[:]
        placement_target = []
        pm_fc_loads = {}


        pm_list.sort(key=lambda pm: pm.last_forecasted_loads[0], reverse=True)

        # Remove underutilized pms
        avg_util = sum((pm.last_forecasted_loads[0] for pm in pm_list)) / len(pm_list)
        while len(pm_list) > 1 and avg_util < MIN_LOAD_THRESHOLD and \
              min(len(pm.cpu_log) for pm in pm_list) >= MIN_PM_LIFE:
            print(f'{pm_list[0].timestamp}: PM #{pm_list[-1].id} Removed! on {avg_util:.2f}%')
            placement_target += pm_list[-1].VM_list
            pm_list = pm_list[:-1]
            avg_util = sum((pm.last_forecasted_loads[-1] for pm in pm_list)) / len(pm_list)

        # Clear each PMs and pull out every VMs for migration
        for pm in pm_list:
            placement_target = placement_target + pm.VM_list
            pm_fc_loads[pm.id] = 0
        
        # Heavist VM first
        placement_target.sort(key=lambda vm: vm.last_forecasted_loads[0], reverse=True)

        while placement_target:
            # into busiest PM first
            success = False
            pm_list.sort(key=lambda pm: pm_fc_loads[pm.id], reverse=True)
            vm = placement_target[0]
            for pm in pm_list:
                if pm_fc_loads[pm.id] + vm.last_forecasted_loads[0] <= 100:
                    vm.migrate(pm)
                    pm_fc_loads[pm.id] += vm.last_forecasted_loads[0]
                    del placement_target[0]
                    success = True
                    break
            
            if not success:
                # add new pm on any failure
                new_pm = PM(init_timestamp=pm_list[0].timestamp)
                pm_list.append(new_pm)
                pm_fc_loads[new_pm.id] = 0

                avg_util = sum((pm.last_forecasted_loads[0] for pm in pm_list)) / len(pm_list)
                print(f'{pm_list[0].timestamp}: PM #{new_pm.id} Added! on {avg_util:.2f}%')
            

        return pm_list
