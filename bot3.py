import json
import logging
from datetime import datetime

import telebot
from pymongo import MongoClient

API_TOKEN = "653139396:AAGzQcC1h8SYPes8tr6en_Yu-Lw6xEObZWU"
bot = telebot.TeleBot(API_TOKEN)

client = MongoClient('storage.loadtest.m1.tinkoff.cloud:27017')
db = client.test_bot

logging.logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO,
                            filename="log.log")
logger = logging.getLogger(__name__)

with open('game.json') as file:
    game = json.loads(file.read())

commands = {  # command description used in the "help" command
    'start': 'Get used to the bot',
    'help': 'Gives you information about the available commands',
    'gov': 'Login as governor, requires a password!',
    'admin': ' Login as admin, requires a password!',
    'logout': ' Login as admin, requires a password!',
}


def extract_arg(arg):
    return arg.split()[1:]


def get_user(cid):
    return list(db.User.find({"chat_id": cid}))[0]


def get_team(tid):
    return list(db.Team.find({"id": int(tid)}))[0]


def create_dump():
    return {'time': datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'),
            'points': game['points'],
            'teams': list(db.Team.find())
            }


def get_price(point_id, res_id):
    amount = game['points'][point_id]["resources"][res_id]
    k = game["resources"][res_id]['k']
    min_price = game["resources"][res_id]['min_price']
    max_amount = game["resources"][res_id]['max_amount']
    f = amount * k + min_price - max_amount * k
    return max(f, min_price)


@bot.message_handler(commands=['start'])
def start(m):
    cid = m.chat.id
    bot.send_message(cid, f"Welcome to {game['name']}")
    if len(list(db.User.find({"chat_id": cid}))) == 0:  # if user hasn't used the "/start" command yet:
        bot.send_message(cid, "Hello, stranger, let me scan you...")
        db.User.insert_one({"chat_id": cid, "auth": 0})
        bot.send_message(cid, "Scanning complete, I know you now")
        command_help(m)  # show the new user the help page
    else:
        bot.send_message(cid, "I already know you, no need for me to scan you again!")


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
    user = get_user(cid)
    if len(args) != 2:  # if wrong number of arguments
        bot.send_message(chat_id=cid, text=f"Wrong number of arguments!\nUse /gov <password> <point_id>.")
    elif args[0] != game['gov_pass']:  # if wrong password
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
    user = get_user(cid)
    if len(args) != 1:
        bot.send_message(chat_id=cid, text=f"Wrong number of arguments!\nUse /admin <password>.")
    elif args[0] != game['adm_pass']:
        bot.send_message(chat_id=cid, text=f"Wrong password!")
    elif user['auth'] == 2:
        bot.send_message(chat_id=cid, text=f"You are already logged in as admin!")
    else:
        db.User.update_one({"chat_id": cid}, {"$set": {"auth": 2}})
        bot.send_message(chat_id=cid, text=f"You are successfully logged in as admin!")


@bot.message_handler(commands=['start_game'])
def start_game(m):
    cid = m.chat.id
    user = get_user(cid)
    if user['auth'] != 2:
        bot.send_message(chat_id=cid, text=f"You are not an admin!")
    else:
        game['state'] = 1
        for user in list(db.User.find({"chat_id": cid})):
            bot.send_message(chat_id=user['chat_id'], text=f"Game started!")


@bot.message_handler(commands=['end_game'])
def end_game(m):
    cid = m.chat.id
    user = get_user(cid)
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
        msg = msg + f"{points.index(point)} - {point['name']}: " \
                    f"{game['resources'][point['base_resource']]['name']}\n"
    bot.send_message(chat_id=cid, text=msg)


# deprecated
#
# @bot.message_handler(commands=['newteam'])
# def new_team(m):
#     args = extract_arg(m.text)
#     cid = m.chat.id
#     user = get_user(cid)
#     if len(args) != 1:
#         bot.send_message(chat_id=cid, text=f"Wrong number of arguments!\nUse /team <name> .")
#     elif user['auth'] < 1:
#         bot.send_message(chat_id=cid, text=f"You are not a governor or an admin!")
#     elif len(list(db.Team.find({"name": cid}))) == 0:
#         db.Team.insert_one({"id": db.Team.count(),
#                             "name": args[0],
#                             "money": 1000,
#                             "storage": [0 for r in game['resources']]
#                             })
#         bot.send_message(cid, f"Team {args[0]} registered!")
#     else:
#         bot.send_message(cid, f"Team {args[0]} already registered!")


@bot.message_handler(commands=['teams'])
def teams(m):
    cid = m.chat.id
    msg = "id - name\n"
    for team in list(db.Team.find()):
        msg = msg + f"{team['id']} - {team['name']}\n"
    bot.send_message(cid, msg)


@bot.message_handler(commands=['team'])
def team(m):
    args = extract_arg(m.text)
    cid = m.chat.id
    if len(args) != 2:
        bot.send_message(chat_id=cid, text=f"Wrong number of arguments!\nUse /team <id> <password>.")
    else:
        team = get_team(args[0])
        if not team:
            bot.send_message(chat_id=cid, text=f"Wrong team id!")
        elif team['pass'] != args[1]:
            bot.send_message(chat_id=cid, text=f"Wrong password!")
        else:
            db.User.update_one({"chat_id": cid}, {"$set": {"auth": 4, "team_id": team['id']}})
            bot.send_message(chat_id=cid, text=f"You are successfully logged in as member of team "
                                               f"\"{team['name']}\"")


@bot.message_handler(commands=['me'])
def me(m):
    cid = m.chat.id
    user = get_user(cid)
    msg = ""
    if user['auth'] == 0:
        msg += "You are common user"
    elif user['auth'] == 1:
        point = game['points'][user['point_id']]
        msg += f"You are a governor.\nYour point: {point['name']}"
    elif user['auth'] == 2:
        msg += f"You are an admin."
    elif user['auth'] == 4:
        team = get_team(user['team_id'])
        msg += f"You are a member of team {team['id']}-{team['name']}.\nYour balance: {team['money']}\n"
        if sum(team['storage']) == 0:
            msg += "Your storage is empty."
        else:
            msg += "In your storage:\n"
            for res in team['storage']:
                team_id = team['storage'].index(res)
                name = game['resources'][team_id]['name']
                amount = res
                msg += f"{id} - {name} - {amount}\n"
    bot.send_message(chat_id=cid, text=msg)


@bot.message_handler(commands=['buy'])
# купить у команды (уменьшить ресурс у команды и дать денег)
def buy(m):
    args = extract_arg(m.text)
    cid = m.chat.id
    user = get_user(cid)
    if game['state'] != 1:
        bot.send_message(chat_id=cid, text=f"Game is not active!")
    elif len(args) != 3:
        bot.send_message(chat_id=cid, text=f"Wrong number of arguments!\nUse /trade <team> <resource> <amount>.")
    elif user['auth'] < 1:
        bot.send_message(chat_id=cid, text=f"You are not a governor or an admin!")
    elif bool(list(db.Team.find({"id", int(args[0])}))) and int(args[1]) < len(game['resources']):
        team = list(db.Team.find({"id", int(args[0])}))[0]
        point = game['points'][user['point_id']]
        res_id = int(args[1])
        amount = int(args[2])
        price = get_price(user['point_id'], res_id)

        if team['storage'][res_id] - amount < 0:
            bot.send_message(chat_id=cid, text=f"Team has not enough resource!")
        else:
            team['storage'][res_id] = team['storage'][res_id] - amount
            team['money'] = team['money'] + amount * price
            point['resources'][res_id] = point['resources'][res_id] + amount
            db.Team.update_one({"id": int(args[0])}, {"$set": {"storage": team['storage'],
                                                               "money": team['money']}})
            bot.send_message(chat_id=cid, text=f"Deal!")
            dump = create_dump()
            logger.info(dump.__str__())

    else:
        bot.send_message(chat_id=cid, text=f"Something wrong with parameters")


@bot.message_handler(commands=['sell'])
# продать команде (увеличить ресурс у команды и забрать денег)
def sell(m):
    args = extract_arg(m.text)
    cid = m.chat.id
    user = get_user(cid)
    if game['state'] != 1:
        bot.send_message(chat_id=cid, text=f"Game is not active!")
    elif len(args) != 3:
        bot.send_message(chat_id=cid, text=f"Wrong number of arguments!\nUse /trade <team> <resource> <amount>.")
    elif user['auth'] < 1:
        bot.send_message(chat_id=cid, text=f"You are not a governor!")
    elif bool(list(db.Team.find({"id": int(args[0])}))) and int(args[1]) < len(game['resources']):
        team = list(db.Team.find({"id": int(args[0])}))[0]
        point = game['points'][user['point_id']]
        res_id = int(args[1])
        amount = int(args[2])
        price = get_price(user['point_id'], res_id)

        if amount * price > team['money']:
            bot.send_message(chat_id=cid, text=f"Team has not enough money!")
        elif point['resources'][res_id] - amount < 0:
            bot.send_message(chat_id=cid, text=f"There is not enough resource in the point!")
        else:
            team['storage'][res_id] = team['storage'][res_id] + amount
            team['money'] = team['money'] - amount * price
            point['resources'][res_id] = point['resources'][res_id] - amount
            db.Team.update_one({"id": int(args[0])}, {"$set": {"storage": team['storage'],
                                                               "money": team['money']}})
            bot.send_message(chat_id=cid, text=f"Deal!")
            dump = create_dump()
            logger.info(dump.__str__())
    else:
        bot.send_message(chat_id=cid, text=f"Something wrong with parameters")


@bot.message_handler(commands=['prices'])
def prices(m):
    cid = m.chat.id
    user = get_user(cid)
    if user['auth'] < 1:
        bot.send_message(chat_id=cid, text=f"You are not a governor!")
    else:
        resources = game['points'][user['point_id']]['resources']
        msg = "id - name - amount - price\n"
        for res in resources:
            res_id = resources.index(res)
            msg = msg + f"{res_id} - " \
                        f"{game['resources'][res_id]['name']} - " \
                        f"{res} - " \
                        f"{get_price(user['point_id'], res_id)}\n"

        bot.send_message(chat_id=cid, text=msg)


if __name__ == '__main__':
    bot.polling()
