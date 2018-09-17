import json
import math

import telebot
from pymongo import MongoClient

API_TOKEN = "653139396:AAGzQcC1h8SYPes8tr6en_Yu-Lw6xEObZWU"
bot = telebot.TeleBot(API_TOKEN)

client = MongoClient('storage.loadtest.m1.tinkoff.cloud:27017')
db = client.test_bot

with open('game.json') as file:
    game = json.loads(file.read())

passwords = {
    1: "qazwsx",
    2: "xswzaq"
}

commands = {  # command description used in the "help" command
    'start': 'Get used to the bot',
    'help': 'Gives you information about the available commands',
    'gov': 'Login as governor, requires a password!',
    'admin': ' Login as admin, requires a password!',
    'logout': ' Login as admin, requires a password!',
}


class User:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.auth = 0

    def set_auth(self, auth):
        self.auth = auth
        return self


class Team:

    def __init__(self, name, id):
        self.id = id
        self.name = name
        self.storage = [0 for resource in game['resources']]
        self.money = 1000

    # продать команде (увеличить ресурс у команды и забрать денег)
    def sell(self, resource_id, amount, price):
        if amount * price > self.money:
            return -1
        else:
            self.storage[resource_id] = self.storage[resource_id] + amount
            self.money = self.money - amount * price


def extract_arg(arg):
    return arg.split()[1:]


def getUser(cid):
    return list(db.User.find({"chat_id": cid}))[0]


def getTeam(cid):
    return list(db.Team.find({"chat_id": cid}))[0]


@bot.message_handler(commands=['start'])
def command_start(m):
    cid = m.chat.id
    if len(list(db.User.find({"chat_id": cid}))) == 0:  # if user hasn't used the "/start" command yet:
        bot.send_message(cid, "Hello, stranger, let me scan you...")
        user = User(cid)  # save user id, so you could brodcast messages to all users of this bot later
        db.User.insert_one(user.__dict__)
        bot.send_message(cid, "Scanning complete, I know you now")
        command_help(m)  # show the new user the help page
    else:
        bot.send_message(cid, "I already know you, no need for me to scan you again!")
    bot.send_message(cid, f"Welcome to {game['name']}")


@bot.message_handler(commands=['help'])
def command_help(m):
    cid = m.chat.id
    help_text = "The following commands are available: \n"
    for key in commands:  # generate help text out of the commands dictionary defined at the top
        help_text += "/" + key + ": "
        help_text += commands[key] + "\n"
    bot.send_message(cid, help_text)  # send the generated help page


@bot.message_handler(commands=['gov'])
def gov(m):
    args = extract_arg(m.text)
    cid = m.chat.id
    user = getUser(cid)
    if len(args) != 2:
        bot.send_message(chat_id=cid, text=f"Wrong number of arguments!\nUse /gov <password> <point_id>.")
    elif args[0] != passwords[1]:
        bot.send_message(chat_id=cid, text=f"Wrong password!")
    elif len(list(db.User.find({"point_id": int(args[1])}))):
        bot.send_message(chat_id=cid, text=f"This point already have a governor")
    elif user['auth'] == 1:
        bot.send_message(chat_id=cid, text=f"You are already logged in as governor!")
    else:
        db.User.update_one({"chat_id": cid}, {"$set": {"auth": 1, "point_id": int(args[1])}})
        bot.send_message(chat_id=cid, text=f"You are successfully logged in as governor!")


@bot.message_handler(commands=['admin'])
def admin(m):
    args = extract_arg(m.text)
    cid = m.chat.id
    user = getUser(cid)
    if len(args) != 1:
        bot.send_message(chat_id=cid, text=f"Wrong number of arguments!\nUse /admin <password>.")
    elif args[0] != passwords[2]:
        bot.send_message(chat_id=cid, text=f"Wrong password!")
    elif user['auth'] == 2:
        bot.send_message(chat_id=cid, text=f"You are already logged in as admin!")
    else:
        db.User.update_one({"chat_id": cid}, {"$set": {"auth": 2}})
        bot.send_message(chat_id=cid, text=f"You are successfully logged in as admin!")


@bot.message_handler(commands=['start_game'])
def start_game(m):
    cid = m.chat.id
    user = getUser(cid)
    if user['auth'] != 2:
        bot.send_message(chat_id=cid, text=f"You are not an admin!")
    else:
        game['state'] = 1
        for user in list(db.User.find({"chat_id": cid})):
            bot.send_message(chat_id=user['chat_id'], text=f"Game started!")


@bot.message_handler(commands=['end_game'])
def end_game(m):
    cid = m.chat.id
    user = getUser(cid)
    if user['auth'] != 2:
        bot.send_message(chat_id=cid, text=f"You are not an admin!")
    else:
        game['status'] = 0
        for user in list(db.User.find({"chat_id": cid})):
            bot.send_message(chat_id=user['chat_id'], text=f"Game ended!")


@bot.message_handler(commands=['points'])
def points(m):
    cid = m.chat.id
    msg = "id - name: base resource\n"
    points = game['points']
    for point in points:
        msg = msg + f"{points.index(point)} - {point['name']}: {game['resources'][point['base_resource']]['name']}\n"
    bot.send_message(chat_id=cid, text=msg)


@bot.message_handler(commands=['newteam'])
def new_team(m):
    args = extract_arg(m.text)
    cid = m.chat.id
    user = getUser(cid)
    teams = list(db.Team.find())
    if len(args) != 1:
        bot.send_message(chat_id=cid, text=f"Wrong number of arguments!\nUse /team <name>.")
    elif user['auth'] < 1:
        bot.send_message(chat_id=cid, text=f"You are not a governor or an admin!")
    elif len(list(db.Team.find({"name": cid}))) == 0:
        team = Team(args[0], len(teams))
        db.Team.insert_one(team.__dict__)
        bot.send_message(cid, f"Team {args[0]} registered!")
    else:
        bot.send_message(cid, f"Team {args[0]} already registered!")


@bot.message_handler(commands=['teams'])
def teams(m):
    cid = m.chat.id
    msg = "id - name\n"
    for team in list(db.Team.find()):
        msg = msg + f"{team['id']} - {team['name']}\n"
    bot.send_message(cid, msg)


def getPrice(point_id, res_id):
    amount = game['points'][point_id]["resources"][res_id]
    k = game["resources"][res_id]['k']
    min_price = game["resources"][res_id]['min_price']
    max_amount = game["resources"][res_id]['max_amount']
    A = amount * k + min_price - max_amount * k
    return max(A, min_price)


@bot.message_handler(commands=['buy'])
# купить у команды (уменьшить ресурс у команды и дать денег)
def buy(m):
    args = extract_arg(m.text)
    cid = m.chat.id
    user = getUser(cid)
    if game['state'] != 1:
            bot.send_message(chat_id=cid, text=f"Game is not active!")
    elif len(args) != 3:
        bot.send_message(chat_id=cid, text=f"Wrong number of arguments!\nUse /trade <team> <resource> <amount>.")
    elif user['auth'] == 1:
        bot.send_message(chat_id=cid, text=f"You are not a governor or an admin!")
    elif bool(list(db.Team.find({"id", int(args[0])}))) and int(args[1]) < len(game['resources']):
        team = list(db.Team.find({"id", int(args[0])}))[0]
        point = game['points'][user['point_id']]
        res_id = int(args[1])
        amount = int(args[2])
        price = getPrice(user['point_id'], res_id)

        if team['storage'][res_id] - amount < 0:
            bot.send_message(chat_id=cid, text=f"Team has not enough resource!")
        else:
            team['storage'][res_id] = team['storage'][res_id] - amount
            team['money'] = team['money'] + amount * price
            point['resources'][res_id] = point['resources'][res_id] + amount
            db.Team.update_one({"id": int(args[0])}, {"$set": {"storage": team['storage'], "money": team['money']}})
            bot.send_message(chat_id=cid, text=f"Deal!")
    else:
        bot.send_message(chat_id=cid, text=f"Something wrong with parameters")


@bot.message_handler(commands=['sell'])
# продать команде (увеличить ресурс у команды и забрать денег)
def sell(m):
    args = extract_arg(m.text)
    cid = m.chat.id
    user = getUser(cid)
    if game['state'] != 1:
            bot.send_message(chat_id=cid, text=f"Game is not active!")
    elif len(args) != 3:
        bot.send_message(chat_id=cid, text=f"Wrong number of arguments!\nUse /trade <team> <resource> <amount>.")
    elif user['auth'] != 1:
        bot.send_message(chat_id=cid, text=f"You are not a governor!")
    elif bool(list(db.Team.find({"id": int(args[0])}))) and int(args[1]) < len(game['resources']):
        team = list(db.Team.find({"id": int(args[0])}))[0]
        point = game['points'][user['point_id']]
        res_id = int(args[1])
        amount = int(args[2])
        price = getPrice(user['point_id'], res_id)

        if amount * price > team['money']:
            bot.send_message(chat_id=cid, text=f"Team has not enough money!")
        elif point['resources'][res_id] - amount < 0:
            bot.send_message(chat_id=cid, text=f"There is not enough resource in the point!")
        else:
            team['storage'][res_id] = team['storage'][res_id] + amount
            team['money'] = team['money'] - amount * price
            point['resources'][res_id] = point['resources'][res_id] - amount
            db.Team.update_one({"id": int(args[0])}, {"$set": {"storage": team['storage'], "money": team['money']}})
            bot.send_message(chat_id=cid, text=f"Deal!")
    else:
        bot.send_message(chat_id=cid, text=f"Something wrong with parameters")

@bot.message_handler(commands=['prices'])
def prices(m):
    cid = m.chat.id
    user = getUser(cid)
    if user['auth'] != 1:
        bot.send_message(chat_id=cid, text=f"You are not a governor!")
    else:
        resources = game['points'][user['point_id']]['resources']
        msg = "id - name - amount - price\n"
        for res in resources:
            res_id = resources.index(res)
            msg = msg + f"{res_id} - {game['resources'][res_id]['name']} - {res} - {getPrice(user['point_id'], res_id)}\n"

        bot.send_message(chat_id=cid, text=msg)





if __name__ == '__main__':
    bot.polling()
