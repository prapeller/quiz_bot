try:
    from .local import *
except ImportError:
    raise Exception("settings.local does not exist")