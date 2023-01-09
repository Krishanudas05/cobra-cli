#
# Copyright (C) 2022 Gagan Malvi
#
# Licensed under the Cartel Project License, Version 1.0 (the "License");
# you may not use this file except in compliance with the License.
# The license can be obtained at the root of this document.
#

import configparser

# Read constants and other paths defined in cli-config.ini
def read_value(domain: str, config: str, path: str):
    """
    Read values from an INI file specified in path.
    Returns the value for a given config.
    """
    conf = configparser.ConfigParser()
    conf.read(path)
    return conf.get(domain, config)