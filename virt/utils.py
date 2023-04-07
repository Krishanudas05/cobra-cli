#
# Copyright (C) 2022-23 Gagan Malvi
#
# Licensed under the Cartel Project License, Version 1.0 (the "License");
# you may not use this file except in compliance with the License.
# The license can be obtained at the root of this document.
#

import libvirt
import subprocess
import time
import configs.read_configs
import csv
import virt.constants
import utilization.cpu
import utils.misc
from xml.dom import minidom
from xml.etree import ElementTree

# Define debug status
debug = configs.read_configs.read_value('DEFAULT', 'debug', virt.constants.CLI_CONFIG)

# Utilities to interact with libvirt to retrieve
# information about the VM including
# - CPU usage
# - Memory usage
# - Disk usage
# - Network usage

QEMU_PATH = configs.read_configs.read_value('QEMU', 'uri', virt.constants.VM_CONFIG)

# Utilities to retrieve information about the VM
# using libvirt.

# Get all VM names
def get_all_vm_names():
    """Returns a list of all the VMs running on the host"""
    vm_names = []
    try:
        vm_names = libvirt.open(QEMU_PATH).listAllDomains()
        if len(vm_names) != 0: 
            vm_names = [vm.name() for vm in vm_names]
    except libvirt.libvirtError:
        print('[!] Failed to open connection to ' + QEMU_PATH)
    return vm_names

# Get VM information
# @param: vm_name - Name of the VM
def get_vm_info(vm_name: str):
    """Returns a dictionary containing the data about the VM"""
    vm_data = {}
    try:
        conn = libvirt.open(QEMU_PATH)
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

# Turn off the VM
# @param: vm_name - Name of the VM
def turn_off_vm(vm_name: str):
    conn = libvirt.open(QEMU_PATH)
    if conn == None:
        print('[!] Failed to open connection to ' + QEMU_PATH)
        exit(1)
    print('[+] Connected to ' + QEMU_PATH)
    dom = conn.lookupByName(vm_name)
    if dom == None:
        print('Failed to find the domain ' + vm_name)
        exit(1)
    dom.destroy()
    conn.close()

# Get VM data live, and check for intrusions
# @param: delay - Delay between each data collection
#         dataset - List to store the data
#         vm_name - Name of the VM
def get_vm_data_live(delay: int, vm_name: str):
    conn = libvirt.open(QEMU_PATH)
    if conn == None:
        print('[!] Failed to open connection to ' + QEMU_PATH)
        return
    print('[+] Connected to ' + QEMU_PATH)
    dom = conn.lookupByName(vm_name)
    if dom == None:
        print('Failed to find the domain ' + vm_name)
        return
    if dom.state()[0] != libvirt.VIR_DOMAIN_RUNNING:
        print('[!] VM ' + vm_name + ' is not running.')
        return

    running = True
    tree = ElementTree.fromstring(dom.XMLDesc())

    while running: 
        # Check if the VM is still running
        if dom.state()[0] != libvirt.VIR_DOMAIN_RUNNING:
            running = False
            break

        # Get current network usage in bytes
        iface = tree.find('devices/interface/target').get('dev')
        prev_interface_stats = dom.interfaceStats(iface)
        
        # I/O usage
        block_device = tree.find('devices/disk/source').get('file')
        (prev_rd_req, prev_rd_bytes, prev_wr_req, prev_wr_bytes, prev_errs) = dom.blockStats(block_device)

        # Get CPU usage, parse into percentage
        previous_cpu_usage = {}
        previous_cpu = dom.getCPUStats(True)[0]
        previous_cpu_usage['cpu_time'] = previous_cpu['cpu_time']
        previous_timestamp = time.time()

        delay = int(configs.read_configs.read_value('DATA_COLLECTION', 'delay', virt.constants.VM_CONFIG))
        time.sleep(delay)

        current_cpu_usage = {}
        current_cpu = dom.getCPUStats(True)[0]
        current_cpu_usage['cpu_time'] = current_cpu['cpu_time']
        current_timestamp = time.time()

        if (debug == True): print(dom.memoryStats())

        num_cpus = dom.maxVcpus()

        cpu_usage_percentage = {
            'cpu_usage_percentage': utilization.cpu.convert_cpu_time_to_percentage(current_cpu_usage['cpu_time'], previous_cpu_usage['cpu_time'], current_timestamp, previous_timestamp, num_cpus)
        }   

        # Get current network usage in bytes
        iface = tree.find('devices/interface/target').get('dev')
        cur_interface_stats = dom.interfaceStats(iface)
        net_usage = {
            'rx_bytes': cur_interface_stats[0] - prev_interface_stats[0],
            'rx_packets': cur_interface_stats[1] - prev_interface_stats[1],
            'tx_bytes': cur_interface_stats[4] - prev_interface_stats[4],
            'tx_packets': cur_interface_stats[5] - prev_interface_stats[5],
        }

        # I/O usage
        block_device = tree.find('devices/disk/source').get('file')
        (rd_req, rd_bytes, wr_req, wr_bytes, errs) = dom.blockStats(block_device)
        io_usage = {
            'rd_req': rd_req - prev_rd_req,
            'rd_bytes': rd_bytes - prev_rd_bytes,
            'wr_req': wr_req - prev_wr_req,
            'wr_bytes': wr_bytes - prev_wr_bytes,
        }

        # Store the data in a tuple
        data = {
            "cpu_usage_percentage": cpu_usage_percentage['cpu_usage_percentage'],
            "rx_bytes": net_usage['rx_bytes'],
            "rx_packets": net_usage['rx_packets'],
            "tx_bytes": net_usage['tx_bytes'],
            "tx_packets": net_usage['tx_packets'],
            "rd_req": io_usage['rd_req'],
            "rd_bytes": io_usage['rd_bytes'],
            "wr_req": io_usage['wr_req'],
            "wr_bytes": io_usage['wr_bytes'],
        }
        if (debug == True): print(data)         

        # Write to CSV
        title = ['cpu_usage_percentage', 'rx_bytes', 'rx_packets', 'tx_bytes', 'tx_packets', 'rd_req', 'rd_bytes', 'wr_req', 'wr_bytes']
        with open(configs.read_configs.read_value('DEFAULT', 'dataset_path', virt.constants.CLI_CONFIG) + dom.name() + ".csv", 'a') as f:
            writer = csv.DictWriter(f, fieldnames=title)
            writer.writerow(data)
            f.close()

        if (cpu_usage_percentage['cpu_usage_percentage'] > 100):
            print('[!] CPU usage is above 100%')
            print('[!] CPU usage is ' + str(cpu_usage_percentage['cpu_usage_percentage']) + '%')
            print('[!] Suspected intrusion detected.')
            print('[!] Shutting down VM...')
            turn_off_vm(vm_name)
        elif (net_usage['rx_bytes'] > 1500000 or net_usage['tx_bytes'] > 1500000):
            print('[!] Network usage is above 1.5MB/s')
            print('[!] Suspected intrusion detected.')
            print('[!] Shutting down VM...')
            turn_off_vm(vm_name)
        elif (net_usage['rx_packets'] > 20000 or net_usage['tx_packets'] > 20000):
            print('[!] Network usage is above 20K packets/s')
            print('[!] Suspected intrusion detected.')
            print('[!] Shutting down VM...')
            turn_off_vm(vm_name)
        elif (io_usage['rd_bytes'] > 15000000 or io_usage['wr_bytes'] > 15000000):
            print('[!] I/O usage is above 15MB/s')
            print('[!] Suspected intrusion detected.')
            print('[!] Shutting down VM...')
            turn_off_vm(vm_name)
        
        if (io_usage['rd_req'] > 20000 or io_usage['wr_req'] > 20000):
            print('[!] I/O usage is above 20K requests/s')
            print('[!] Suspected intrusion detected.')
            print('[!] Shutting down VM...')
            turn_off_vm(vm_name)

    conn.close()
