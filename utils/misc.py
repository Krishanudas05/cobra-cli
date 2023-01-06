#
# Copyright (C) 2022 Gagan Malvi
#
# Licensed under the Cartel Project License, Version 1.0 (the "License");
# you may not use this file except in compliance with the License.
# The license can be obtained at the root of this document.
#

# Miscellaneous utilities used by vm-mgr-cli

# Write to file
def write_to_file(file_path: str, data):
    """Writes data to a file"""
    with open(file_path, 'a') as f:
        f.write(data + "\n")