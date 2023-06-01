# delaymon

This is a simple script that can use the built-in TWAMP functionality in EOS to 
measure the delay of a link in a topology and update the min-delay setting of 
said interface to be used in Traffic Engineering use cases (specifically IS-IS 
FlexAlgo).

For this to operate, a few prerequisite commands need to be applied. This activates 
the device's TWAMP functionality (for receiving sessions from the remote side) as well 
as the local API interface for executing commands from the script itself.

```
twserver
!
management api http-commands
   protocol unix-socket
   no shutdown
```

# Usage

To leverage this script, simply copy via an method (SCP, etc.) to the flash: of an 
EOS device.

The script is meant to be executed using a CLI Schedule in EOS. This will allow it to 
execute on a pre-set interval that is configurable by the user. A unique schedule 
needs to be created per interface being monitored. Ideally, these would be set on staggered 
intervals to lessen the load on the platform, but overall, scale shouldn't be a concern.

The interval minimum is 2 minutes up to a 24 hour window. The number of logs to be kept is up 
to the user (including 0 logs). The timeout value should be set a 1 minute. It should never take 
longer than a few seconds to fully complete.

```
schedule et47delaymon interval 2 timeout 1 max-log-files 30 command bash python3 /mnt/flash/delayMon.py --ip 1.1.1.2 --interface Ethernet47
```

A logfile will be created each time the script is running displaying the results. These 
can be inspected in the /mnt/flash/schedule directory on a per-schedule basis.

```
CHI-7280SRA-1#bash zcat /mnt/flash/schedule/et47delaymon/CHI-7280SRA-1_et47delaymon_2023-06-01.1118.log.gz
Min-delay setting on Ethernet47 successfully updated to 250
```