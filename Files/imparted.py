import os, subprocess, re
from parted import *

def query_disks():
	disks_readable = {}

	if os.uname().sysname == "Darwin":
		for this_file in os.listdir("/dev/"):
			if re.search("(?=^[^s]+s[^s]+$)^rdisk", this_file): # this one line took hours. regex is magic
				disks_readable["Device " + this_file] = this_file
	if os.uname().sysname == "Linux":
		for this_file in os.listdir("/dev/"):
			if re.search("^sd[a-z]$|^mmcblk[0-9]$", this_file): # no nvme because why
				disk_looking_at = Device.get("/dev/" + this_file)
				ped_device_open(disk_looking_at)
				disks_readable[this_file + " - " + ped_device_get_constraint(disk_looking_at)] = this_file
				ped_device_close(disk_looking_at)
	return disks_readable
