#!/usr/bin/env python3

# BSD 3-Clause License
#
# Copyright (c) 2023, Arista Networks EOS+
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name Arista nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
"""
This is a simple script that can use the built-in TWAMP functionality in EOS to 
measure the delay of a link in a topology and update the min-delay setting of 
said interface to be used in Traffic Engineering use cases (specifically IS-IS 
FlexAlgo).

It is meant to be executed using a CLI Schedule in EOS.  This will allow it to 
execute on a pre-set interval that is configurable by the user.  A unique schedule 
needs to be created per interface being monitored. Ideally, these would be set on staggered 
intervals to lessen the load on the platform, but overall, scale shouldn't be a concern.

schedule et47delaymon interval 2 timeout 1 max-log-files 30 command bash python3 /mnt/flash/delaymon.py --ip 1.1.1.2 --interface Ethernet47

Created by Dimitri Capetz - dcapetz@arista.com
"""

import argparse
import re
from jsonrpclib import Server

# Set up global API Socket for ease of use/re-use
switch = Server("unix:/var/run/command-api.sock")

# Standard function to parse options passed in execution
def parseargs():
    parser = argparse.ArgumentParser(
        description="Link delay monitoring for use in config")
    parser.add_argument("--ip", dest="ip", required=True,
                        action="store", help="Remote IP of link to monitor")
    parser.add_argument("--interface", dest="interface", required=True,
                        action="store", help="Interface to monitor")
    args = parser.parse_args()
    return args

#
def twamp_test(endpoint):
    ''' Execute TWAMP Test via eAPI Socket
        
        Args:
            endpoint (str): The IP endpoint to use as the target of the twping
        
        Returns:
            current_delay (int): The median delay result of the twping in microseconds
    '''
    twping_output = switch.runCmds(1, ["twping address {} port 50099".format(endpoint)])
    # Since the output of the command is just text, parse out the delay from the output
    # Once this is available in SysDB, simply call the correct path
    raw_ouput = twping_output[0]["messages"][0]
    current_delay_str = re.search("Round-trip time median: (.*) ms", raw_ouput)
    current_delay_float = float(current_delay_str.group(1))*1000
    current_delay = int(current_delay_float)
    return current_delay

def update_min_delay(target_interface, min_delay):
    ''' Update min-delay setting of an ethernet interface
        
        Args:
            target_interface (str): The interface name to be updated
            min_delay (int): The delay setting to be applied to the config
        
        Returns:
            result (str): The result of the config operation
    '''
    config_output = switch.runCmds(1, ["enable",
                                "configure",
                                "interface {}".format(target_interface),
                                "traffic-engineering min-delay static {} microseconds".format(min_delay)])
    config_result = ""
    for cmd_result in config_output:
        if cmd_result != {}:
            config_result += "Error applying command: {}\n".format(cmd_result)
    if config_result == "":
        result = "Min-delay setting on {} successfully updated to {} microseconds".format(target_interface, min_delay)
    else:
        result = config_result
    return result

def main():
    options = parseargs()
    new_delay = twamp_test(options.ip)
    if not isinstance(new_delay, int):
        print("Error in measuring delay...no changes will be made.")
        print("twping result: {}".format(new_delay))
    else:
        config_result = update_min_delay(options.interface, new_delay)
        print(config_result)

if __name__ == "__main__":
    main()