import logging

from telebot import types

from core import bot
from core.db import User, Team
from core.menus import MenuBuilder
from core.config_loader import game

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG,
                    filename="log.log")
logger = logging.getLogger(__name__)

menu_builder = MenuBuilder()


@bot.message_handler(commands=['start'])
def start(user):
    chat_id = user.chat.id
    bot.send_message(chat_id, f"Welcome to {game['name']}", reply_markup=types.ReplyKeyboardRemove(selective=False))
    if User().get_by_chat_id(chat_id=chat_id) is None:  # if user hasn't used the "/start" command yet:
        bot.send_message(chat_id, "Hello, stranger, let me scan you...")
        User().new(chat_id=chat_id)
        command_help(user)  # show the new user the help page
        bot.send_message(chat_id, "Scanning complete, I know you now", reply_markup=menu_builder.common_user_menu())
    else:
        bot.send_message(chat_id, "I already know you, no need for me to scan you again!",
                         reply_markup=menu_builder.common_user_menu())


@bot.message_handler(commands=['help'])
def command_help(user):
    chat_id = user.chat.id
    help_text = "The following commands are available: \n"

    common_commands = {  # command description used in the "help" command
        'start': 'Get used to the bot',
        'help': 'Gives you information about the available commands',
        'gov': 'Login as governor, requires a password!',
        'admin': ' Login as admin, requires a password!',
    }

    for key in common_commands:  # generate help text out of the commands dictionary defined at the top
        help_text += "/" + key + ": "
        help_text += common_commands[key] + "\n"
    bot.send_message(chat_id, help_text)  # send the generated help page
