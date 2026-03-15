from tkinter import *
# from tkinter.filedialog import askopenfilename
try:
    from PIL import ImageTk, Image
except ImportError as er:
    print("Logo will not be drawn, ", er)
from tkinter.ttk import Progressbar
import os, subprocess, sys

# Conversion functions
def con_b2mb(value):
    return value / (10**6)

def con_b2gb(value):
    return value / (10**9)

def con_mb2b(value):
    return value * (10**6)

# Unused since PKEXEC is used instead of sudo
def sudo_check():
	subprocess.check_output(["sudo", "echo", "Hello from superuser!"])

# Assume basic programs like sudo, parted, python etc. are in path
# and that python3 is at least compatible with imparted.py
pa_python3 = "python3"

if "--sudo" in sys.argv: # Easier for testing since sudo does not ALWAYS prompt for password
    pa_sudo = "sudo"
else:
    pa_sudo = "pkexec"

def initializeDisk():
    pass

class base_window(Frame):
    def __init__(self, *args, **kwargs):
        Frame.__init__(self)
        self.inf_selected_disk = StringVar(root)

        try:
            self.image = ImageTk.PhotoImage(Image.open("Files/logo.png"))
            self.logo = Label(self, image=self.image)
            self.logo.pack()
        except NameError:
            pass

        self.button_disks = OptionMenu(self, self.inf_selected_disk, *kwargs["disks_readable"])

        self.group_tools = LabelFrame(self, text="Tools")
        self.button_initialize = Button(self.group_tools, text="Initialize disk", command=lambda: self.init_disk(self.inf_selected_disk.get(), kwargs))


        self.button_disks.pack()
        self.button_initialize.pack()
        self.group_tools.pack()

    def format_disk(self, selected_disk,disk_data,progress_bar,progress_label,disk_size): # Actual formatting process
        progress_label.set("Creating on " + selected_disk)
        progress_bar.set(1)

        mbr_command = [pa_sudo, pa_python3, os.path.dirname(os.path.realpath(__file__)) + "/Files/imparted.py", "create partition map", selected_disk, "msdos", ]
        subprocess.run(mbr_command)

    def init_disk(self, selected_disk, disk_data): # Disk init UI
        # self.lock() Prevent base window interaction
        target_disk_arrayid = disk_data["disks_readable"].index(selected_disk)
        target_disk = disk_data["disks_raw"][target_disk_arrayid]
        target_disk_size_b = disk_data["disks_size"][target_disk_arrayid]

        print(target_disk, target_disk_size_b, "ddds", disk_data["disks_size"])

        i_root = Toplevel(self)
        i_root.wm_title("Initialize disk " + target_disk)

        ## Variables used for disk formatting

        disk_fat_size_mb_STRING = StringVar(i_root, value="100")
        disk_fat_size_mb_STRING.trace('w', lambda name, index, mode, disk_fat_size_mb_STRING=disk_fat_size_mb_STRING: self.on_type(disk_fat_size_mb_STRING.get(), target_disk_size_b))

        disk_gui_label = StringVar(i_root, value="Ready to format")
        disk_gui_progress = IntVar(i_root, value=0)

        ##

        label_fat_size = Label(i_root, text="FAT size in MB:")
        button_fat_size = Entry(i_root, textvariable=disk_fat_size_mb_STRING)

        group_status = LabelFrame(i_root, text="Status") ### {
        label_progress = Label(group_status, textvariable=disk_gui_label)
        label_progressbar = Progressbar(group_status, variable=disk_gui_progress)
        button_format = Button(group_status, text="Start", command=lambda: self.format_disk(target_disk, disk_data, disk_gui_progress, disk_gui_label, target_disk_size_b, int(con_mb2b(disk_fat_size_mb_STRING.get()))))
        #################################################### }

        label_fat_size.pack(side=TOP)
        button_fat_size.pack(side=TOP)

        label_progress.pack(side=TOP)
        label_progressbar.pack(side=TOP)
        button_format.pack(side=TOP)
        group_status.pack(side=TOP)

if __name__ == "__main__":
    root = Tk()
    root.wm_title("U Mac Helper")

    inf_disks_command = [pa_sudo, pa_python3, os.path.dirname(os.path.realpath(__file__)) + "/Files/imparted.py", "query disks"]
    inf_disks_rawoutput = subprocess.check_output(inf_disks_command).decode().split(":~:")


    inf_disks_readable = inf_disks_rawoutput[0].split(",")
    inf_disks_raw = tuple(inf_disks_rawoutput[1].split(","))
    inf_disks_size = tuple(inf_disks_rawoutput[2].split(","))

    # print(inf_disks_readable)

    base = base_window(root, disks_readable=inf_disks_readable, disks_raw=inf_disks_raw, disks_size=inf_disks_size)

    base.pack(fill="both", expand=True)
    root.mainloop()
