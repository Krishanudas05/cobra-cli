#
# Copyright (C) 2022 Gagan Malvi
#
# Licensed under the Cartel Project License, Version 1.0 (the "License");
# you may not use this file except in compliance with the License.
# The license can be obtained at the root of this document.
#

# Miscellaneous utilities used by vm-mgr-cli

import os

def read_lists_from_file(file_path: str):
    """
    Reads from a file and returns a list of lines.
    If the given file path does not exist, it will return an empty list.
    """
    if not os.path.isfile(file_path):
        return []
    
    with open(file_path, 'r') as f:
        d = []
        for line in f:
            row = eval(line)
            d.append(row)
        return d

# Write to file
def write_to_file(file_path: str, data):
    """
    Writes to a file, in append mode.
    If the given file path does not exist, it will create the file and then write to it.
    """
    if not os.path.isfile(file_path):
        os.mknod(file_path)
    
    with open(file_path, 'a') as f:
        f.write(data + "\n")