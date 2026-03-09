from tkinter import *
from Files import imparted
import os, subprocess

root = Tk()

inf_disks = list(imparted.query_disks())
inf_selected_disk = StringVar(root)

print(inf_disks)

button_disks = OptionMenu(root, inf_selected_disk, inf_disks)
button_initialize = Button(root, text="Initialize disk")

button_disks.pack()
button_initialize.pack()

root.mainloop()
