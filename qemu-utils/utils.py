#
# Copyright (C) 2022 Gagan Malvi
#
# Licensed under the Cartel Project License, Version 1.0 (the "License");
# you may not use this file except in compliance with the License.
# The license can be obtained at the root of this document.
#

import libvirt
import subprocess
import time
import constants

# Utilities to interact with libvirt to retrieve
# information about the VM including
# - CPU usage
# - Memory usage
# - Disk usage
# - Network usage

# Utilities to retrieve information about the VM
# using virsh.

def get_all_vm_names():
    """Returns a list of all the VMs running on the host"""
    vm_names = []
    try:
        vm_names = subprocess.check_output(['virsh', 'list', '--name']).decode().split()
    except subprocess.CalledProcessError as e:
        print(e)
    return vm_names

def get_vm_info(vm_name: str):
    """Returns a dictionary containing the data about the VM"""
    vm_data = {}
    try:
        data = subprocess.check_output(['virsh', 'dominfo', vm_name]).decode().split()
        vm_data['id'] = data[1]
        vm_data['name'] = data[3]
        vm_data['state'] = data[5]
        vm_data['max_mem'] = data[18]
        vm_data['cpus'] = data[12]
        vm_data['cpu_time'] = data[15]
    except subprocess.CalledProcessError as e:
        print(e)
    return vm_data

def get_vm_data_live(delay: int, dataset: list, vm_name: str):
    conn = libvirt.open(constants.QEMU_PATH)
    if conn == None:
        print('Failed to open connection to qemu:///system')
        exit(1)
    
    dom = conn.lookupByName(vm_name)
    if dom == None:
        print('Failed to find the domain ' + vm_name)
        exit(1)
    
    running = True

    while running: 
        # Get CPU and memory usage
        cpu_usage = dom.getCPUStats(True)[0]['cpu_time']
        mem_usage = dom.memoryStats()['rss']    

        # Get current network usage in bytes
        interface_stats = dom.interfaceStats()
        net_usage = interface_stats['rx_bytes'] + interface_stats['tx_bytes']

        # Store the data in a tuple
        data = (cpu_usage, mem_usage, net_usage)
        print(data)

        # Append the data to the dataset
        dataset.append(data)

        # Sleep for the specified delay
        time.sleep(delay)
    
    conn.close()