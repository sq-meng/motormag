from datetime import datetime


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def color_print(message, color=None):
    message = str(datetime.now()) + ": " + message
    if color is None:
        print(message)
    else:
        print(color + message + bcolors.ENDC)


def log(message):
    color_print(message)


def fail(message):
    color_print(message, bcolors.FAIL)


def warn(message):
    color_print(message, bcolors.WARNING)