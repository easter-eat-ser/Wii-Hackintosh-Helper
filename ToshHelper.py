import os, subprocess, shutil
from Files import tui, disks

continue_loop = True
window_title = "WiiIntosh Helper"

inf_sys = os.uname().sysname
inf_selecteddisk = "None"
inf_selecteddisksize = "Unable to detect (unimplemented)"
inf_currentmap = "Unable to detect (unimplemented)"

location_sudo = "/usr/bin/sudo"
location_diskutil = "/usr/sbin/diskutil"
location_parted = "/usr/sbin/parted"
location_dd = "/bin/dd"

def query_disk_size_parted(disk):
	return (subprocess.check_output([location_sudo, location_parted, disk, "print"]).split(b'\n')[1].split(b': ')[1]).decode("utf-8")

def evaluate_disk():
	global inf_selecteddisk
	global inf_selecteddisksize
	global inf_currentmap
	# print("Superuser access is required to get disk properties")
	# subprocess.call(["/usr/bin/sudo", "command that fetches the mbr data"])
	# inf_selecteddisksize = str(psutil.disk_usage(inf_selecteddisk).total)


def select_disk():
	tui.print_header("Select disk")
	diskmenu_options = disks.query_disks_readable()
	diskmenu_selected_readable = tui.option_menu(list(diskmenu_options))
	diskmenu_selected = diskmenu_options[diskmenu_selected_readable]
	global inf_selecteddisk
	inf_selecteddisk = diskmenu_selected
	evaluate_disk()

def initialize_disk():
	global location_sudo
	global location_dd
	global location_diskutil
	global location_parted

	while not os.path.isfile(location_sudo):
		location_sudo = input("Sudo not found at " + location_sudo +"! Enter sudo path (including binary name:) ")
	while not os.path.isfile(location_dd):
		location_dd = input("DD not found at " + location_dd +"! Enter path (including binary name:) ")

	disk_util = "parted"
	process = None

	tui.print_header("Initialize disk")

	print("This process will automatically format and partition your USB drive as a hybrid APM/MBR. It will also save backups of the MBR and APM so you can show or hide the HFS partition anytime. Initializing again will erase any previous backups.")
	print("If you do not enter a partition size, the program will select the optimal default for a setup with minimal homebrew.")
	print("Using " + inf_selecteddisk)

	if inf_sys == "Darwin":
		print("Detected MacOS platform. Diskutil will be used.")
		disk_util = "diskutil"
		while not os.path.isfile(location_diskutil):
			input("Diskutil not found at " + location_diskutil +"! Enter path (including binary name:) ")
	else:
		print("Detected non-MacOS platform. GNU Parted will be used.")
		while not os.path.isfile(location_parted):
			input("Parted not found at " + location_parted +"! Enter path (including binary name:) ")

	disk_size = "4" # gigabytes fallback
	if disk_util == "diskutil":
		print("Unable to find disk size with diskutil! Using 4GB fallback.")
	else:
		disk_size = query_disk_size_parted(inf_selecteddisk)
	print("Disk size " + disk_size)

	disk_fat_size = input("[default 0.1] Size of the FAT (homebrew) partition: ")
	if disk_fat_size == "":
		disk_fat_size = "100MB"

	print("WH - Creating MBR partition table")
	if disk_util == "diskutil":
		process = subprocess.call([location_sudo, location_diskutil, "partitionDisk", inf_selecteddisk, "3", "MBR", "FREE", "%noformat%", "32768B", "FAT32", "FAT", str(disk_fat_size), "FREE", "%noformat%", "0"]) # i CANNOT get diskutil to line up the partitions. heeeelp
	else:
		process = subprocess.call([location_sudo, location_parted, inf_selecteddisk, "mktable", "msdos"])
		process = subprocess.call([location_sudo, location_parted, inf_selecteddisk, "mkpart", "primary", "fat32", "1048576b", disk_fat_size])

	if process != 0:
		input("Previous command encountered an error! Quitting...")
		return()

	print("WH - Saving MBR data")
	process = subprocess.call([location_sudo, location_dd, "if=" + inf_selecteddisk, "of=" + "wiiu_mbr.bin", "bs=512", "count=1"])

	if process != 0:
		input("Previous command encountered an error! Quitting...")
		return()

	print("WH - APM partitioning")
	if disk_util == "diskutil": # a bit of a run-on. sorry
		process = subprocess.call(["/usr/bin/sudo", location_diskutil, "partitionDisk", inf_selecteddisk, "4", "APM", "FREE", "%noformat%", "1985S", "FAT32", "%noformat%", str(disk_fat_size), "HFS+", "Installer", "650M", "HFS+", "Root", "0"])
	else:
		process = subprocess.call(["/usr/bin/sudo", location_parted, inf_selecteddisk, "mktable", "mac"])
		#process = subprocess.call(["/usr/bin/sudo", location_parted, inf_selecteddisk, "mkpart", "primary", "fat32", "32.8kB", "1048064b""]) Skip making empty partiton?
		process = subprocess.call(["/usr/bin/sudo", location_parted, inf_selecteddisk, "mkpart", "primary", "fat32", "1048576b", disk_fat_size])
		process = subprocess.call(["/usr/bin/sudo", location_parted, inf_selecteddisk, "mkpart", "primary", "hfs+", disk_fat_size, disk_fat_size])
		process = subprocess.call(["/usr/bin/sudo", location_parted, inf_selecteddisk, "mkpart", "primary", "hfs+", "1048576b", disk_fat_size])
	
	print("WH - Saving APM data")
	process = subprocess.call(["/usr/bin/sudo", location_dd, "if=" + inf_selecteddisk, "of=" + "wiiu_apm.bin", "bs=512", "count=1"])
	input("Finished")

def main_loop():
	tui.print_header(window_title)

	menu_options = {
		"Quit": "quit",
		"Select target disk": "disksel",
		"Initialize disk": "diskinit",
		"Toggle MBR partition map": "applymbr"
	}

	tui.print_info("Selected disk", inf_selecteddisk) # + " - " + inf_selecteddisksize)
	tui.print_info("Current partition map", inf_currentmap)

	selected_option_readable = tui.option_menu(list(menu_options))
	selected_option = menu_options[selected_option_readable]

	if selected_option == "quit":
		global continue_loop
		continue_loop = False
	elif selected_option == "disksel":
		select_disk()	
	elif selected_option == "diskinit":
		initialize_disk()
	else:
		print("Not valid command")

while continue_loop:
	main_loop()
