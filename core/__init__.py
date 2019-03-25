from telebot import TeleBot

from core.config_loader import config


class SomethingXBot(TeleBot):

    def start(self):
        self.infinity_polling()


bot = SomethingXBot(config.get('Common', 'API_TOKEN'))

from core.controller import *
