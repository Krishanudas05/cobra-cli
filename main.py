#
# Copyright (C) 2022 Gagan Malvi
#
# Licensed under the Cartel Project License, Version 1.0 (the "License");
# you may not use this file except in compliance with the License.
# The license can be obtained at the root of this document.
#

import configs
import threading
import libvirt
import virt.constants
import virt.utils

print("[-] Initializing Cobra Hypervisor IPS Agent...")
print("[-] Before proceeding, please make sure that you have started the VM instances you want to monitor.")

def begin_monitoring():
    vm_names = virt.utils.get_all_vm_names()
    for vm_name in vm_names:
        try:
            # put all data collection functions on different thread
            # and then join them
            print("[+] Starting data collection for VM: " + vm_name)
            t = threading.Thread(target=virt.utils.get_vm_data_live, args=(int(configs.read_configs.read_value('DATA_COLLECTION', 'delay', virt.constants.VM_CONFIG)), vm_name))
            t.daemon = True
            t.start()
            t.join()
        except Exception as e:
            print("[-] Failed to start monitoring. Read the above log for details, or turn on debug options. Exception: ", e)

def console():
    while True:
        command = input("[main@cobra]~$ ")
        if command == "help":
            print("[-] Available commands:")
            print("     help: Displays this help message")
            print("     start: Starts monitoring the VMs")
            print("     stop: Stops monitoring the VMs")
            print("     exit: Exits the program")
        elif command == "start":
            print("[-] Starting monitoring...")
            begin_monitoring()
        elif command == "stop":
            print("[-] Stopping monitoring...")
        elif command == "exit":
            print("[-] Exiting...")
            exit(0)
        else :
            print("[-] Invalid command. Type 'help' to see available commands.")

if __name__ == "__main__":
    console()