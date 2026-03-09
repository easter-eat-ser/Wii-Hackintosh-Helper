import os, re, subprocess, psutil

#def query_disks_readable():	PSUtil can only get partitions, and we need actual devices - especially on Mac since they have volumes and stuff
#	disks_toparse = psutil.disk_partitions()    I will remove the PSUtil import someday
#	disks_readable = {}
#
#	for disk in disks_toparse:
#		disks_readable[disk.device + " format " + disk.fstype + " mounted at " + disk.mountpoint] = disk.device
#	return disks_readable

def query_disks_readable():
	disks_readable = {}

	if os.uname().sysname == "Darwin":
		for this_file in os.listdir("/dev/"):
			if re.search("(?=^[^s]+s[^s]+$)^rdisk", this_file): # this one line took hours. regex is magic
				disks_readable["Device " + this_file] = this_file
	if os.uname().sysname == "Linux":
		for this_file in os.listdir("/dev/"):
			if re.search("^sd[a-z]$|^mmcblk[0-9]$", this_file): # only about 5min to make :> getting better
				disks_readable["Device " + this_file] = this_file
	return disks_readable
