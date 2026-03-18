import os, re, sys, subprocess
import parted

# This script assumes it is already running as sudo.

# Conversions. ConR = int rounding, Con = float
def con_b2mb(value):
    return int(value) / (10**6)

def con_b2gb(value):
    return int(value) / (10**9)

def con_mb2b(value): # NO FRACTIONAL MB INPUTS! They will be rounded to MB
    return int(value) * (10**6)

def conr_b2s(value):
	return int(value) // 512 # I think Parted always uses 512-byte sectors? If this is somehow actually related to block size, then many USBs won't work.

def conr_s2b(value):
	return int(value) * 512  # Same here of course

def format_partition(target_partition_path, filesystem, label): # Only takes 'hfs+' and 'fat32', as strings
	command = None
	print("Formatting ", label)
	if filesystem == "hfs+":
		command = ["mkfs.hfsplus", "-v", label, target_partition_path]
	elif filesystem == "fat32":
		command = ["mkfs.fat", "-F", "32", "-n", label, target_partition_path]
	subprocess.run(command)
	print("Done! Moving on.")

def unmount_all_partitions(target_disk): # Takes a Disk object, NOT a disk name
	print("Unmounting...")
	for partition in target_disk.partitions:
		print("Object ", partition)
		subprocess.run(["umount", partition.path])

def clear_all_disk_partition_data(target_disk_name):
	with open( target_disk_name, "wb" ) as d:
		d.write(bytearray(1024))

def query_disks():  # Query /dev for sdX or mmcblkX disks (matched with RegEx)
                    # ask libparted for disk sizes, then return readable, raw, and disk sizes as
                    # parseable string for Helper to consume

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

def create_map(device_name, map_type, disk_length_b, fat_length_b, osx_path):
	device = parted.getDevice(device_name)
	disk = parted.freshDisk(device, "msdos") # MBR

	# c = compute d = disk f = function
	print("Defining all partition bounds")
	# Compute all partition beginnings and endings, in sectors;
	c_EMPTY_start = 64 # 32768 bytes = 64 512-byte sectors
	c_EMPTY_end = 2047 # 1048064 bytes = 2047 512-byte sectors

	c_FAT_start = 2048 # 1048576 bytes etc etc, unsure why it's one more than the end of the other partition but w/e it works
	c_FAT_end = conr_b2s(round(float(fat_length_b))) # Techically, the FAT partition is always one megabyte short. Who cares??

	c_Installer_start = c_FAT_end + 1 # One-block space, otherwise the partitions will overlap and that is really bad
	c_Installer_end = c_FAT_end + conr_b2s(con_mb2b(700)) # 10.2 installer is 650MB, unsure about others so I will be safe

	c_Root_start = c_Installer_end + 1
	c_Root_end = conr_b2s(disk_length_b) - 1

	# Define Geometry, Filesystem, and Partition objects for libparted to format with

	print("Defining MBR partition details to libparted")

	# FAT partition (MBR & APM)
	d_geom_FAT = parted.Geometry(device=device, start=c_FAT_start, end=c_FAT_end) # Partition size (reusable for APM)
	d_fs_FAT = parted.FileSystem(type="fat32", geometry=d_geom_FAT)                   # Partition format ^
	d_part_FAT = parted.Partition(disk=disk, type=parted.PARTITION_NORMAL, fs=d_fs_FAT, geometry = d_geom_FAT)
	# A fun limitation of the Pyparted mappings is that we can't rename the disk without using the direct _ped bindings.
	# I'm not going to do that

	print("Creating partition (in memory)")
	disk.addPartition(d_part_FAT)
	print("Wiping partition tables")
	clear_all_disk_partition_data(device_name)
	print("Applying pcreate_map(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])artition table")
	disk.commit()
	unmount_all_partitions(disk) # Should work? It better

	############## apm time babeyyyyy ##############
	print("Saving MBR to wiiu_mbr.bin...") # No need for sudo, this script is already root
	f_dd_mbr_save_command = ["dd", "if=" + device_name, "of=" + "wiiu_mbr.bin", "bs=512", "count=1"]
	subprocess.run(f_dd_mbr_save_command)

	disk = parted.freshDisk(device, "mac")

	print("Defining APM partition details to libparted")

	# Empty partition for whatever reason
	d_geom_EMPTY = parted.Geometry(device=device, start=c_EMPTY_start, end=c_EMPTY_end)
	d_fs_EMPTY = parted.FileSystem(type="fat32", geometry=d_geom_EMPTY) # Format doesn't matter, parted ignores formatting options
	d_part_EMPTY = parted.Partition(disk=disk, type=parted.PARTITION_NORMAL, fs=d_fs_EMPTY, geometry = d_geom_EMPTY)

	# The FAT partition needs to be redefined, otherwise Parted complains about reused partitions.
	d_geom_FAT = parted.Geometry(device=device, start=c_FAT_start, end=c_FAT_end) # Partition size (reusable for APM)
	d_fs_FAT = parted.FileSystem(type="fat32", geometry=d_geom_FAT)                   # Partition format ^
	d_part_FAT = parted.Partition(disk=disk, type=parted.PARTITION_NORMAL, fs=d_fs_FAT, geometry = d_geom_FAT)

	d_geom_Installer = parted.Geometry(device=device, start=c_Installer_start, end=c_Installer_end)
	d_fs_Installer = parted.FileSystem(type="hfs+", geometry=d_geom_Installer)
	d_part_Installer = parted.Partition(disk=disk, type=parted.PARTITION_NORMAL, fs=d_fs_Installer, geometry=d_geom_Installer)

	d_geom_Root = parted.Geometry(device=device, start=c_Root_start, end=c_Root_end)
	d_fs_Root = parted.FileSystem(type="hfs+", geometry=d_geom_Root)
	d_part_Root = parted.Partition(disk=disk, type=parted.PARTITION_NORMAL, fs=d_fs_Root, geometry=d_geom_Root)

	print("Creating partitions (in memory)")
	disk.addPartition(d_part_EMPTY)
	disk.addPartition(d_part_FAT)
	disk.addPartition(d_part_Installer)
	disk.addPartition(d_part_Root)
	print("Applying partition table")
	disk.commit()
	print("Committed to disk!")
	print("Format time.")

	format_partition(d_part_FAT.path, "fat32", "UFAT")
	format_partition(d_part_Installer.path, "hfs+", "Installer")
	format_partition(d_part_Root.path, "hfs+", "Root")

	if osx_path != "":
		print("OSX mount provided! Copying files...")
		try:
			os.mkdir("/mnt/UIS")
		except FileExistsError:
			print("/mnt/UIS exists, using directory")
		mount_media_command = ["mount", d_part_Installer.path, "/mnt/UIS"]
		rsync_osx_copy_command = ["rsync", "-av", osx_path, "/mnt/UIS"] # path better include a trailing slash, or else this copies a folder to root
		unmount_media_command = ["umount", d_part_Installer.path]

		subprocess.run(mount_media_command)
		subprocess.run(rsync_osx_copy_command)

	print("Finished!")

command = sys.argv[1]

if command == "query disks": # Spaces are used so it is harder to accidentally call something manually.
	print(query_disks())
elif command == "create partition map":
	# print("create partition map...")
	if sys.argv[6]:
		create_map(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
	else:
		print("OSX path isn't even a string! What are we doing here...")
		create_map(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], "")
else:
	print("Don't call this program by itself!")
