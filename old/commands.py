from telegram.ext import CommandHandler, MessageHandler, Filters

import model


def caps(bot, update, args):
    text_caps = ' '.join(args).upper()
    bot.send_message(chat_id=update.message.chat_id, text=text_caps)


def echo(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=update.message.text)


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Welcome to SomethingX!")


def help(bot, update):
    update.message.reply_text("Use /start to test this bot.")


def show_games(bot, update):
    games = model.get_games()
    msg = "Games:\n"
    if (bool(games)):
        for game in games:
            msg = msg + f"id: {games.index(game)} :: name: {game[name]}\n"
    else:
        msg = "There aren't any active game :(\n But you can create new!"
    bot.send_message(chat_id=update.message.chat_id, text=msg)
    return 0

def create_game(bot, update, args):
    if len(args) == 0: bot.send_message(chat_id=update.message.chat_id, text="Game needs a name! Use /creategame <name>.")
    else:




# def start_game(bot, update):
#     if game.isReady(): bot.send_message(chat_id=update.message.chat_id, text="Welcome to SomethingX! ")


# def error(bot, update, error):
#     """Log Errors caused by Updates."""
#     logger.warning('Update "%s" caused error "%s"', update, error)


start_handler = CommandHandler('start', start)
echo_handler = MessageHandler(Filters.text, echo)
caps_handler = CommandHandler('caps', caps, pass_args=True)
# buy_handler = CommandHandler('buy', buy, pass_args=True)
help_handler = CommandHandler('help', help)
show_games_handler = CommandHandler('showgames', show_games)
