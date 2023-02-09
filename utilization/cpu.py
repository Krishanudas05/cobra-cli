#
# Copyright (C) 2022 Gagan Malvi
#
# Licensed under the Cartel Project License, Version 1.0 (the "License");
# you may not use this file except in compliance with the License.
# The license can be obtained at the root of this document.
#

# Utilities for CPU

# Convert CPU time to percentage using the formula:
# ((current_cpu_time - previous_cpu_time) * 100.0) / ((current_time - previous_time) * 1000 * 1000 * 1000)
# @param: current_cpu_time - Current CPU time
# @param: previous_cpu_time - Previous CPU time
# @param: current_time - Current time
# @param: previous_time - Previous time
def convert_cpu_time_to_percentage(current_cpu_time: int, previous_cpu_time: int, current_time: int, previous_time: int, num_cpus: int):
    """Converts CPU time to percentage"""
    pcentbase = ((current_cpu_time - previous_cpu_time) * 100.0) / ((current_time - previous_time) * 1000 * 1000 * 1000)
    # Under RHEL-5.9 using a XEN HV guestcpus can be 0 during shutdown
    # so play safe and check it.
    cpuGuestPercent = num_cpus > 0 and pcentbase / num_cpus or 0
    return cpuGuestPercent