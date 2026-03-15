import os, re, sys
import parted

# This script assumes it is already running as sudo.

# Conversions. ConR = int rounding, Con = float
def con_b2mb(value):
    return value / (10**6)

def con_b2gb(value):
    return value / (10**9)

def con_mb2b(value):
    return value * (10**6)

def conr_b2s(value):
	return value // 512

def conr_s2b(value):
	return value * 512

def query_disks():

	disks_readable = []
	disks_raw = []
	disks_size = []

	if os.uname().sysname == "Darwin":
		for this_file in os.listdir("/dev/"):
			if re.search("(?=^[^s]+s[^s]+$)^rdisk", this_file):
				disks_readable["Device " + this_file] = this_file

	if os.uname().sysname == "Linux":
		for this_file in os.listdir("/dev/"):
			if re.search("^sd[a-z]$|^mmcblk[0-9]$", this_file):
				device = parted.getDevice("/dev/" + this_file) # Get reference to Device object
				disks_readable.append(this_file + " - " + str(round(con_b2gb(device.length * device.sectorSize), 1)) + "GB " + device.model)
				disks_raw.append("/dev/" + this_file)
				disks_size.append(str(device.length * device.sectorSize))
				device.removeFromCache()

	return ":~:".join([",".join(disks_readable), ",".join(disks_raw), ",".join(disks_size)])

def create_map(device_name, map_type, fat_length_b):
	device = parted.getDevice(device_name)
	disk = parted.freshDisk(device, "msdos")

	# Compute all partition beginnings and endings, in sectors;
	c_start


	d_geom_FAT = parted.Geometry(device=device, start=2048, end=conr_b2s(fat_length_b)) # Partition size (reusable for APM)
	d_fs_FAT = parted.FileSystem(type="fat", geometry=geometry)							# Partition format ^
	d_part_FAT = parted.Partition(disk=disk, type=parted.PARTITION_NORMAL, fs=d_fs_FAT, geometry = d_geom_FAT)
	disk.addPartition()

command = sys.argv[1]

if command == "query disks": # Spaces are used so it is harder to accidentally call something manually.
	print(query_disks())
elif command == "create partition map":
	print("create partition map...")
	print(create_map(sys.argv[2], sys.argv[3], sys.argv[4]))
else:
	print("Don't call this program by itself!")
