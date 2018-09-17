import json
import telebot

from old.Model import Model

API_TOKEN = "653139396:AAGzQcC1h8SYPes8tr6en_Yu-Lw6xEObZWU"

bot = telebot.TeleBot(API_TOKEN)

users_in_games = {}

model = Model()
with open('game.json') as file:
    model.get_games().append(json.loads(file.read()))


def extract_arg(arg):
    return arg.split()[1:]


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Howdy, how are you doing?")


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(chat_id=message.chat.id, text="Use /start to test this bot.")


@bot.message_handler(commands=['showgames'])
def show_games(message):
    games = model.get_games()
    msg = "Games:\n"
    if bool(games):
        for game in games:
            msg = msg + f"id: {games.index(game)} - {game['name']}\n"
    else:
        msg = "There isn't any active game :(\nBut you can create new!\nUse /creategame <name> <password>"
    bot.send_message(chat_id=message.chat.id, text=msg)
    return 0


@bot.message_handler(commands=['join'])
def join_game(message):
    args = extract_arg(message.text)
    if len(args) == 1:
        users_in_games[message.chat.id] = int(args[0])
        bot.send_message(chat_id=message.chat.id, text=f"You entered {model.get_games()[int(args[0])]['name']}!")
    else:
        bot.send_message(chat_id=message.chat.id, text=f"Wrong number of arguments!\nUse /joingame <game_id>.")


@bot.message_handler(commands=['points'])
def points(message):
    if not message.chat.id in list(users_in_games.keys()):
        bot.send_message(chat_id=message.chat.id,
                         text="Join some game before. Use /showgames to see list of active games.")
    else:
        msg = "Points:\nid-name: base resource\n"
        game = model.get_games()[users_in_games[message.chat.id]]
        points = game['points']
        for point in points:
            msg = msg + f"{points.index(point)}-{point['name']}: {game['resources'][point['base_resource']]['name']}\n"
        bot.send_message(chat_id=message.chat.id, text=msg)

@bot.message_handler(commands=['buy'])
def trade(message):
    args = extract_arg(message.text)
    if len(args) != 4:
        bot.send_message(chat_id=message.chat.id, text=f"Wrong number of arguments!\nUse /buy <team_id> <point_id> <resource_id> <amount>.")
    else:
        try:
            game = model.get_games()[users_in_games[message.chat.id]]
            team = game['teams'][int(args[0])]
            point = game['points'][int(args[1])]
            resource = game[''][int(args[0])]

        except(Exception):
            bot.send_message(chat_id=message.chat.id, text=f"Something goes wrong!")


if __name__ == '__main__':
    bot.polling()
