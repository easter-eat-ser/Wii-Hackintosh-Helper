import os

optionmenu_keys = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z","1","2","3","4","5","6","7","8","9","!","@","#","$","%","^","&","*","(",")"]
terminal_size = os.get_terminal_size() # width first height second

def print_header(title):
	os.system("clear")
	title_spacing = int(((terminal_size[0] / 2) - len(title)) // 2)
	print("=" * (terminal_size[0] // 4), end="")
	print((" " * title_spacing) + title + (" " * title_spacing), end="")
	print("=" * (terminal_size[0] // 4), end="\n\n")

def print_info(caption, value):
	print(caption + ": " + value)

def print_option(index, label):
	print("  " + optionmenu_keys[index] + ") " + label)

def option_menu(options):
	selection_success = False
	for option_index in range(0, len(options)):
		print_option(option_index, options[option_index])
	while not(selection_success):
		user_input = input("Choose an option: ").capitalize()
		if len(user_input) == 1:
			if optionmenu_keys.index(user_input) < len(options):
				return options[optionmenu_keys.index(user_input)]
