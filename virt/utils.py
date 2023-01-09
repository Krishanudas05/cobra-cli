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
import virt.constants
import utils.misc
import utilization.cpu
from xml.dom import minidom
from xml.etree import ElementTree

# Utilities to interact with libvirt to retrieve
# information about the VM including
# - CPU usage
# - Memory usage
# - Disk usage
# - Network usage

# Utilities to retrieve information about the VM
# using libvirt.

# Get all VM names
def get_all_vm_names():
    """Returns a list of all the VMs running on the host"""
    vm_names = []
    try:
        vm_names = libvirt.open(virt.constants.QEMU_PATH).listAllDomains()
        if len(vm_names) != 0: 
            vm_names = [vm.name() for vm in vm_names]
        print(vm_names)
    except subprocess.CalledProcessError as e:
        print(e)
    return vm_names

# Get VM information
# @param: vm_name - Name of the VM
def get_vm_info(vm_name: str):
    """Returns a dictionary containing the data about the VM"""
    vm_data = {}
    try:
        conn = libvirt.open(virt.constants.QEMU_PATH)
        if not conn: 
            print('Failed to open connection to qemu:///system')
            exit(1)
        dom = conn.lookupByName(vm_name)
        if not dom: 
            print('Failed to find the domain ' + vm_name)
            exit(1)
        raw_xml = dom.XMLDesc()
        xml = minidom.parseString(raw_xml)
        vm_data['name'] = dom.name()
        vm_data['uuid'] = dom.UUIDString()
        vm_data['state'] = dom.state()[0]
        vm_data['max_memory'] = dom.maxMemory()
        vm_data['memory'] = dom.memoryStats()['rss']
        vm_data['vcpus'] = dom.maxVcpus()
        vm_data['cpu_time'] = dom.getCPUStats(True)[0]['cpu_time']
        vm_data['os_type'] = xml.getElementsByTagName('os')[0].getElementsByTagName('type')[0].firstChild.data
        vm_data['os_arch'] = xml.getElementsByTagName('os')[0].getElementsByTagName('type')[0].getAttribute('arch')
        vm_data['os_machine'] = xml.getElementsByTagName('os')[0].getElementsByTagName('type')[0].getAttribute('machine')
        vm_data['os_boot'] = xml.getElementsByTagName('os')[0].getElementsByTagName('boot')[0].getAttribute('dev')
        vm_data['disk_image'] = xml.getElementsByTagName('disk')[0].getElementsByTagName('source')[0].getAttribute('file')
    except subprocess.CalledProcessError as e:
        print(e)
    return vm_data

# Get VM data live
# @param: delay - Delay between each data collection
#         dataset - List to store the data
#         vm_name - Name of the VM
def get_vm_data_live(delay: int, vm_name: str):
    conn = libvirt.open(virt.constants.QEMU_PATH)
    if conn == None:
        print('Failed to open connection to qemu:///system')
        exit(1)
    
    dom = conn.lookupByName(vm_name)
    if dom == None:
        print('Failed to find the domain ' + vm_name)
        exit(1)
    
    running = True
    tree = ElementTree.fromstring(dom.XMLDesc())

    while running: 
        # Check if the VM is still running
        if dom.state()[0] != libvirt.VIR_DOMAIN_RUNNING:
            running = False
            break

        # Get CPU and memory usage
        cpu_usage = {}
        cpu = dom.getCPUStats(True)[0]
        cpu_usage['cpu_time'] = cpu['cpu_time']
        cpu_usage['system_time'] = cpu['system_time']
        cpu_usage['user_time'] = cpu['user_time']
        mem_usage = dom.memoryStats()['rss']    

        # Get current network usage in bytes
        iface = tree.find('devices/interface/target').get('dev')
        interface_stats = dom.interfaceStats(iface)
        net_usage = {
            'rx_bytes': interface_stats[0],
            'rx_packets': interface_stats[1],
            'rx_errs': interface_stats[2],
            'rx_drop': interface_stats[3],
            'tx_bytes': interface_stats[4],
            'tx_packets': interface_stats[5],
            'tx_errs': interface_stats[6],
            'tx_drop': interface_stats[7]
        }

        # I/O usage
        block_device = tree.find('devices/disk/source').get('file')
        (rd_req, rd_bytes, wr_req, wr_bytes, errs) = dom.blockStats(block_device)
        io_usage = {
            'rd_req': rd_req,
            'rd_bytes': rd_bytes,
            'wr_req': wr_req,
            'wr_bytes': wr_bytes,
            'errs': errs
        }

        # Store the data in a tuple
        data = str([cpu_usage, mem_usage, net_usage, io_usage])
        print(data)

        # Append the data to the dataset
        DATASET_PATH = virt.constants.CONFIG_PATH + dom.name() + ".dat"
        utils.misc.write_to_file(DATASET_PATH, data)

        # Sleep for the specified delay
        time.sleep(delay)
    
    conn.close()