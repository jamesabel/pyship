from platform import system


def is_windows():
    return system() == "Windows"
