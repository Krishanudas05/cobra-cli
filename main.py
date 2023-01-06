import threading
import libvirt
import virt.constants
import virt.utils

vm_names = virt.utils.get_all_vm_names()
for vm_name in vm_names:
    b = []
    try:
        vm_data = virt.utils.get_vm_info(vm_name)
        print(vm_data)
        # put all data collection functions on different thread
        # and then join them
        t = threading.Thread(target=virt.utils.get_vm_data_live, args=(1, b, vm_name))
        t.start()
        t.join()
    except libvirt.libvirtError as e:
        print(e)
