from telegram.ext import Updater
import logging

from old.commands import start_handler, echo_handler, caps_handler, help_handler, show_games_handler

TOKEN = "653139396:AAGzQcC1h8SYPes8tr6en_Yu-Lw6xEObZWU"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

states = {0: "not ready", 1: "ready"}

state = states[0]


def init(upd):
    dp = upd.dispatcher

    dp.add_handler(start_handler)
    dp.add_handler(echo_handler)
    dp.add_handler(caps_handler)
    # dp.add_handler(buy_handler)
    dp.add_handler(help_handler)
    dp.add_handler(show_games_handler)

    return dp

if __name__ == '__main__':
    updater = Updater(token=TOKEN)

    dispatcher = init(updater)

    updater.start_polling()
