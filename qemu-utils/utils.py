#
# Copyright (C) 2022 Gagan Malvi
#
# Licensed under the Cartel Project License, Version 1.0 (the "License");
# you may not use this file except in compliance with the License.
# The license can be obtained at the root of this document.
#

import subprocess

# Utilities to interact with libvirt to retrieve
# information about the VM including
# - CPU usage
# - Memory usage
# - Disk usage
# - Network usage

def get_vm_data(vm_name):
    """Returns a dictionary containing the data about the VM"""
    vm_data = {}
    try:
        vm_data = subprocess.check_output(['virsh', 'dominfo', vm_name]).decode().split()
    except subprocess.CalledProcessError as e:
        print(e)
    return vm_data

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