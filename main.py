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

vm_names = virt.utils.get_all_vm_names()
for vm_name in vm_names:
    try:
        # put all data collection functions on different thread
        # and then join them
        delay = int(configs.read_configs.read_value('DATA_COLLECTION', 'delay', virt.constants.VM_CONFIG))
        t = threading.Thread(target=virt.utils.get_vm_data_live, args=(delay, vm_name))
        t.start()
        t.join()
    except libvirt.libvirtError as e:
        print(e)
