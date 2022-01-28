from telegram.ext import Updater


class Bot():
    def __init__(self, token, *args, **kwargs):
        self.updater = Updater(token)
        self.dispatcher = self.updater.dispatcher
