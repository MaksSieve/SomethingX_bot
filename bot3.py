import json
import logging
from datetime import datetime

import telebot
from pymongo import MongoClient
from telebot import types

from util import DB, extract_arg

API_TOKEN = "653139396:AAGzQcC1h8SYPes8tr6en_Yu-Lw6xEObZWU"
bot = telebot.TeleBot(API_TOKEN)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO,
                    filename="log.log")
logger = logging.getLogger(__name__)

with open('game.json') as file:
    game = json.loads(file.read())

commands = {  # command description used in the "help" command
    'start': 'Get used to the bot',
    'help': 'Gives you information about the available commands',
    'gov': 'Login as governor, requires a password!',
    'admin': ' Login as admin, requires a password!',
    'logout': ' Logout',
}

db = DB()


def team_menu():
    menu = types.ReplyKeyboardMarkup()
    connect_btn = types.KeyboardButton('/connect')
    points_btn = types.KeyboardButton('/points')
    me_btn = types.KeyboardButton('/me')
    menu.add(connect_btn, points_btn, me_btn)
    return menu


def connected_team_menu(pid, tid):
    menu = types.ReplyKeyboardMarkup()
    prices_btn = types.KeyboardButton(f'/prices {pid}')
    buy_btn = types.KeyboardButton('/trade')
    connected_btn = types.KeyboardButton(f'/connected {pid}')
    disconnect_btn = types.KeyboardButton(f'/disconnect')
    menu.add(prices_btn, buy_btn, connected_btn, disconnect_btn)

    return menu


def approve_menu(pid, tid):
    menu = types.InlineKeyboardMarkup()
    row = menu.row()
    row.add(types.InlineKeyboardButton(f"Approve",
                                       callback_data=f"connect_resp_approved_{pid}_{tid}"))
    row.add(types.InlineKeyboardButton(f"Decline",
                                       callback_data=f"connect_resp_declined_{pid}_{tid}"))
    return menu


@bot.message_handler(commands=["connect"])
def connect(m):
    cid = m.chat.id
    team_id = db.get_user(cid)['team_id']
    connect_menu = types.InlineKeyboardMarkup()
    points_row = connect_menu.row()
    for point in game['points']:
        cb_data = f"connect_req_{game['points'].index(point)}_{team_id}"
        points_row.add(types.InlineKeyboardButton(f"{point['name']}", callback_data=cb_data))
    bot.send_message(cid, "Choose point to connect:", reply_markup=connect_menu)


@bot.callback_query_handler(func=lambda call: "connect_req" in call.data)
def connect_request_inline(call):
    cid = call.message.chat.id
    mid = call.message.message_id
    point_id = list(call.data.split("_"))[2]
    team_id = list(call.data.split("_"))[3]
    gov = db.get_governor_by_point(point_id)
    bot.delete_message(cid, mid)
    bot.send_message(gov['chat_id'],
                     f"Connection request by team {db.get_team(team_id)['name']}.", reply_markup=approve_menu(point_id, team_id))


@bot.callback_query_handler(func=lambda call: "connect_resp" in call.data)
def connect_response_inline(call):
    gov_mid = call.message.message_id
    gov_cid = call.message.chat.id
    data = list(call.data.split("_"))
    team_id = data[4]
    cap_cid = db.get_captain_by_team(int(team_id))['chat_id']
    pid = data[3]
    if data[2] == "approved":
        db.update_team(team_id, {"connected": int(data[3])})
        bot.delete_message(gov_cid, gov_mid)
        bot.send_message(gov_cid, "Connection approved.")
        bot.send_message(cap_cid, 'Your connection request approved!', reply_markup=connected_team_menu(pid=pid, tid=team_id))
    else:
        bot.send_message(cap_cid, 'Your connection request declined!')


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
    bot.send_message(cid, f"Welcome to {game['name']}", reply_markup=types.ReplyKeyboardRemove(selective=False))
    if db.get_user(cid) is None:  # if user hasn't used the "/start" command yet:
        bot.send_message(cid, "Hello, stranger, let me scan you...")
        db.insert_user({"chat_id": cid, "auth": 0})
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
    user = db.get_user(cid)
    if len(args) != 2:  # if wrong number of arguments
        bot.send_message(chat_id=cid, text=f"Wrong number of arguments!\nUse /gov <password> <point_id>.")
    elif args[0] != game['gov_pass']:  # if wrong password
        bot.send_message(chat_id=cid, text=f"Wrong password!")
    elif db.point_has_governor(int(args[1])):
        bot.send_message(chat_id=cid, text=f"This point already have a governor")
    elif user['auth'] == 1:
        bot.send_message(chat_id=cid,
                         text=f"You are already logged in as governor of {game['points'][user['point_id']]['name']}")
    else:
        db.update_user(cid, {"auth": 1, "point_id": int(args[1])})
        bot.send_message(chat_id=cid, text=f"You are successfully logged in as governor!")


@bot.message_handler(commands=['admin'])
def admin(m):
    args = extract_arg(m.text)
    cid = m.chat.id
    user = db.get_user(cid)
    if len(args) != 1:
        bot.send_message(chat_id=cid, text=f"Wrong number of arguments!\nUse /admin <password>.")
    elif args[0] != game['adm_pass']:
        bot.send_message(chat_id=cid, text=f"Wrong password!")
    elif user['auth'] == 2:
        bot.send_message(chat_id=cid, text=f"You are already logged in as admin!")
    else:
        db.update_user(cid, {"auth": 2})
        bot.send_message(chat_id=cid, text=f"You are successfully logged in as admin!")


@bot.message_handler(commands=['logout'])
def logout(m):
    cid = m.chat.id
    user = db.get_user(cid)
    if user['auth'] == 0:
        bot.send_message(chat_id=cid, text=f"You are not logged in as character.")
    else:
        db.update_user(cid, {"auth": 0})
        db.delete_user_fields(cid, {"point_id": "", "team_id": 0})
        bot.send_message(chat_id=cid, text=f"You are successfully logged out.")


@bot.message_handler(commands=['start_game'])
def start_game(m):
    cid = m.chat.id
    user = db.get_user(cid)
    if user['auth'] != 2:
        bot.send_message(chat_id=cid, text=f"You are not an admin!")
    else:
        game['state'] = 1
        for user in list(db.get_users()):
            bot.send_message(chat_id=user['chat_id'], text=f"Game started!")


@bot.message_handler(commands=['end_game'])
def end_game(m):
    cid = m.chat.id
    user = db.get_user(cid)
    if user['auth'] != 2:
        bot.send_message(chat_id=cid, text=f"You are not an admin!")
    else:
        game['status'] = 0
        for user in db.get_users():
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
    for team in list(db.get_teams()):
        msg = msg + f"{team['id']} - {team['name']}\n"
    bot.send_message(cid, msg)


@bot.message_handler(commands=['team'])
def team(m):
    args = extract_arg(m.text)
    cid = m.chat.id
    if len(args) != 2:
        bot.send_message(chat_id=cid, text=f"Wrong number of arguments!\nUse /team <id> <password>.")
    else:
        team = db.get_team(args[0])
        if not team:
            bot.send_message(chat_id=cid, text=f"Wrong team id!")
        elif team['pass'] != args[1]:
            bot.send_message(chat_id=cid, text=f"Wrong password!")
        elif db.team_has_captain(team['id']):
            bot.send_message(chat_id=cid, text=f"Some one already logged as a captain of team {team['name']}!\n"
                                               f"If you has not logged in tell Admin!")
        else:
            db.update_user(cid, {"auth": 4, "team_id": team['id']})
            bot.send_message(chat_id=cid, text=f"You are successfully logged in as a captain of team "
                                               f"\"{team['name']}\"")
            bot.send_message(cid, "Choose action", reply_markup=team_menu())

@bot.message_handler(commands=['disconnect'])
def diconnect(m):
    cid = m.chat.id
    user = db.user_with_field(cid, 'team_id')
    if not user:
        bot.send_message(cid, "You are not a team captain.")
    else:
        tid = db.get_team(user['team_id'])['id']
        db.update_team(tid, {"connected": -1})
        bot.send_message(cid, f"You are disconnected from point.", reply_markup=team_menu())

@bot.message_handler(commands=['me'])
def me(m):
    cid = m.chat.id
    user = db.get_user(cid)
    msg = ""
    if user['auth'] == 0:
        msg += "You are common user"
    elif user['auth'] == 1:
        point = game['points'][user['point_id']]
        msg += f"You are a governor.\nYour point: {point['name']}"
    elif user['auth'] == 2:
        msg += f"You are an admin."
    elif user['auth'] == 4:
        team = db.get_team(user['team_id'])
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

@bot.message_handler(commands=['trade'])
def start_trade(m):
    cid = m.chat.id
    user = db.user_with_field(cid, "team_id")
    if not user:
        bot.send_message(cid, "You are not a team captain.")
    else:
        t = db.get_team(user['team'])
        if t['connected'] == -1:
            bot.send_message(cid, "You are not connected to a point.")
        else:
            pid = t['connected']
            point = game['points'][pid]
            bot.send_message(cid, "Welcome to market!")
            prices(m)
            select_resource(cid, t['id'], point)


def select_resource(cid, tid, point):
    try:
        menu = types.InlineKeyboardMarkup()
        for res in point['resources']:
            menu.add(types.InlineKeyboardButton(f"{game['resources'][res]['name']}",
                                       callback_data=f"trade1_{tid}_{point['resources'].index(res)}"))
        bot.send_message(cid, "Choose resource:", reply_markup=menu)
    except Exception as e:
        bot.send_message(cid, e)

@bot.callback_query_handler(func=lambda call: "trade1" in call.data)
def select_amount(call):
    cid = call.message.chat.id
    mid = call.message.message_id
    data = call.data.split("_")
    tid = data[1]
    rid = data[2]
    t = db.get_team(tid)
    if rid >= len(t['storage']):
        bot.delete_message(cid, mid)
        bot.send_message(cid, 'You have not this resource!')



# @bot.message_handler(commands=['buy'])
# # купить у команды (уменьшить ресурс у команды и дать денег)
# def buy(m):
#     args = extract_arg(m.text)
#     cid = m.chat.id
#     user = get_user(cid)
#     if game['state'] != 1:
#         bot.send_message(chat_id=cid, text=f"Game is not active!")
#     elif len(args) != 3:
#         bot.send_message(chat_id=cid, text=f"Wrong number of arguments!\nUse /trade <team> <resource> <amount>.")
#     elif user['auth'] < 1:
#         bot.send_message(chat_id=cid, text=f"You are not a governor, an admin or a team capitan!")
#     elif bool(list(db.Team.find({"id": int(args[0])}))) and int(args[1]) < len(game['resources']):
#         team = list(db.Team.find({"id": int(args[0])}))[0]
#         point = game['points'][user['point_id']]
#         res_id = int(args[1])
#         amount = int(args[2])
#         price = get_price(user['point_id'], res_id)
#
#         if team['storage'][res_id] - amount < 0:
#             bot.send_message(chat_id=cid, text=f"Team has not enough resource!")
#         else:
#             team['storage'][res_id] = team['storage'][res_id] - amount
#             team['money'] = team['money'] + amount * price
#             point['resources'][res_id] = point['resources'][res_id] + amount
#             db.Team.update_one({"id": int(args[0])}, {"$set": {"storage": team['storage'],
#                                                                "money": team['money']}})
#             bot.send_message(chat_id=cid, text=f"Deal!")
#             dump = create_dump()
#             logger.info(dump.__str__())
#
#     else:
#         bot.send_message(chat_id=cid, text=f"Something wrong with parameters")
#
#
# @bot.message_handler(commands=['sell'])
# # продать команде (увеличить ресурс у команды и забрать денег)
# def sell(m):
#     args = extract_arg(m.text)
#     cid = m.chat.id
#     user = get_user(cid)
#     if game['state'] != 1:
#         bot.send_message(chat_id=cid, text=f"Game is not active!")
#     elif len(args) != 3:
#         bot.send_message(chat_id=cid, text=f"Wrong number of arguments!\nUse /trade <team> <resource> <amount>.")
#     elif user['auth'] < 1:
#         bot.send_message(chat_id=cid, text=f"You are not a governor!")
#     elif bool(list(db.Team.find({"id": int(args[0])}))) and int(args[1]) < len(game['resources']):
#         team = list(db.Team.find({"id": int(args[0])}))[0]
#         point = game['points'][user['point_id']]
#         res_id = int(args[1])
#         amount = int(args[2])
#         price = get_price(user['point_id'], res_id)
#
#         if amount * price > team['money']:
#             bot.send_message(chat_id=cid, text=f"Team has not enough money!")
#         elif point['resources'][res_id] - amount < 0:
#             bot.send_message(chat_id=cid, text=f"There is not enough resource in the point!")
#         else:
#             team['storage'][res_id] = team['storage'][res_id] + amount
#             team['money'] = team['money'] - amount * price
#             point['resources'][res_id] = point['resources'][res_id] - amount
#             db.Team.update_one({"id": int(args[0])}, {"$set": {"storage": team['storage'],
#                                                                "money": team['money']}})
#             bot.send_message(chat_id=cid, text=f"Deal!")
#             dump = create_dump()
#             logger.info(dump.__str__())
#     else:
#         bot.send_message(chat_id=cid, text=f"Something wrong with parameters")

@bot.message_handler(commands=['prices'])
def prices(m):
    cid = m.chat.id
    args = extract_arg(m.text)
    resources = game['points'][int(args[0])]['resources']
    msg = "id - name - amount - price\n"
    for res in resources:
        res_id = resources.index(res)
        msg = msg + f"{res_id} - " \
                    f"{game['resources'][res_id]['name']} - " \
                    f"{res['amount']} - " \
                    f"{get_price(int(args[0]), res_id)}\n"

    bot.send_message(chat_id=cid, text=msg)

@bot.message_handler(commands=['connected'])
def connected(m):
    cid = m.chat.id
    args = extract_arg(m.text)
    connected_teams = db.get_teams()
    msg = "id - name \n"
    for c_team in connected_teams:
        if c_team['connected'] == int(args[0]):
            msg = msg + f"{c_team['id']} - " \
                        f"{c_team['name']}\n"

    bot.send_message(chat_id=cid, text=msg)


if __name__ == '__main__':
    bot.polling()
