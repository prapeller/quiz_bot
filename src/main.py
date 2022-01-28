from .settings.base import TOKEN
from .bot import Bot
from .quiz_handler import quiz_handler


def main() -> None:
    bot = Bot(TOKEN)
    bot.dispatcher.add_handler(quiz_handler)
    bot.updater.start_polling()
    bot.updater.idle()
