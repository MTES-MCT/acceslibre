from colorama import Fore, Style


def print_error(*args):
    print(Fore.RED, *args)
    print(Style.RESET_ALL)


def print_success(*args):
    print(Fore.GREEN, *args)
    print(Style.RESET_ALL)


def print_warning(*args):
    print(Fore.YELLOW, *args)
    print(Style.RESET_ALL)
