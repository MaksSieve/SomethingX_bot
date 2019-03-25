import json
import logging

import telebot
from telebot import types
from configparser import ConfigParser

from util import DB, extract_arg, get_resources_on_point_string, MenuBuilder

config = ConfigParser()
config.read('config.cfg')

bot = telebot.TeleBot(config.get('Common', 'API_TOKEN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO,
                    filename="log.log")
logger = logging.getLogger(__name__)

with open('game.json') as file:
    game = json.loads(file.read())

common_commands = {  # command description used in the "help" command
    'start': 'Get used to the bot',
    'help': 'Gives you information about the available commands',
    'gov': 'Login as governor, requires a password!',
    'admin': ' Login as admin, requires a password!',
}

db = DB(config.get('Common', 'DB_URL'))

menu_builder = MenuBuilder()


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


@bot.message_handler(commands=["connect"])
def connect(m):
    cid = m.chat.id
    tid = db.get_user(cid)['team_id']
    bot.send_message(cid, "Choose point to connect:", reply_markup=menu_builder.connect_menu(game, tid))


@bot.callback_query_handler(func=lambda call: "connect_req" in call.data)
def connect_request_inline(call):
    cid = call.message.chat.id
    mid = call.message.message_id
    pid = list(call.data.split("_"))[2]
    tid = list(call.data.split("_"))[3]
    gov = db.get_governor_by_point(pid)
    bot.delete_message(cid, mid)
    if bool(gov):
        bot.send_message(gov['chat_id'],
                         f"Connection request by team {db.get_team(tid)['name']}.",
                         reply_markup=menu_builder.approve_connect_menu(pid, tid))
    else:
        bot.send_message(cid,
                         "There is no governor for this point(",
                         reply_markup=menu_builder.team_select_back_menu(cid))


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
        bot.send_message(cap_cid, 'Your connection request approved!',
                         reply_markup=menu_builder.connected_team_menu(pid=pid))
    else:
        bot.send_message(cap_cid, 'Your connection request declined!')


@bot.message_handler(commands=['start'])
def start(m):
    cid = m.chat.id
    bot.send_message(cid, f"Welcome to {game['name']}", reply_markup=types.ReplyKeyboardRemove(selective=False))
    if db.get_user(cid) is None:  # if user hasn't used the "/start" command yet:
        bot.send_message(cid, "Hello, stranger, let me scan you...")
        db.insert_user({"chat_id": cid, "auth": 0})
        command_help(m)  # show the new user the help page
        bot.send_message(cid, "Scanning complete, I know you now", reply_markup=menu_builder.common_user_menu())
    else:
        bot.send_message(cid, "I already know you, no need for me to scan you again!", reply_markup=menu_builder.common_user_menu())


@bot.message_handler(commands=['help'])
def command_help(m):
    cid = m.chat.id
    help_text = "The following commands are available: \n"
    for key in common_commands:  # generate help text out of the commands dictionary defined at the top
        help_text += "/" + key + ": "
        help_text += common_commands[key] + "\n"
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
        bot.send_message(chat_id=cid, text=f"You are successfully logged in as governor!", reply_markup=menu_builder.governor_menu(int(args[1])))


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
        bot.send_message(chat_id=cid, text=f"You are successfully logged in as admin!", reply_markup=menu_builder.admin_menu())


@bot.message_handler(commands=['logout'])
def logout(m):
    cid = m.chat.id
    user = db.get_user(cid)
    if user['auth'] == 0:
        bot.send_message(chat_id=cid, text=f"You are not logged in as character.", reply_markup=menu_builder.common_user_menu())
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
        msg = msg + f"{point['name']}: " \
                    f"{game['resources'][point['base_resource']]['name']}\n"
    bot.send_message(chat_id=cid, text=msg)


@bot.message_handler(commands=['teams'])
def teams(m):
    cid = m.chat.id
    msg = "id - name\n"
    for team in list(db.get_teams()):
        msg = msg + f"{team['id']} - {team['name']}\n"
    bot.send_message(cid, msg)


@bot.message_handler(commands=['team'])
def team(m):
    cid = m.chat.id
    bot.send_message(cid, "Select a team:", reply_markup=menu_builder.team_select_menu(list(db.get_teams()), cid))


@bot.callback_query_handler(func=lambda call: "enter_team" in call.data)
def enter_team(call):
    cid = call.message.chat.id
    mid = call.message.message_id
    data = call.data.split("_")
    if data[2] == "back":
        db.update_user(cid, {"auth": 0})
        bot.delete_message(cid, mid)
        bot.send_message(cid, f"Welcome to {game['name']}!", reply_markup=menu_builder.common_user_menu())
    else:
        tid = int(data[2])
        cid = int(data[3])
        team = db.get_team(tid)
        if db.team_has_captain(team['id']):
            bot.send_message(chat_id=cid, text=f"Some one already logged as a captain of team {team['name']}!\n"
                                               f"If you has not logged in tell Admin!")
        else:
            bot.delete_message(cid, mid)
            db.update_user(cid, {"auth": 3, "team_id": tid})
            bot.send_message(cid, "Enter password:", reply_markup=menu_builder.team_select_back_menu(cid))


@bot.message_handler(commands=['disconnect'])
def diconnect(m):
    cid = m.chat.id
    user = db.user_with_field(cid, 'team_id')
    if not user:
        bot.send_message(cid, "You are not a team captain.")
    else:
        tid = db.get_team(user['team_id'])['id']
        db.update_team(tid, {"connected": -1})
        bot.send_message(cid, f"You are disconnected from point.", reply_markup=menu_builder.team_menu())


@bot.message_handler(commands=['me'])
def me(m):
    cid = m.chat.id
    user = db.get_user(cid)
    msg = ""
    if user['auth'] == 0:
        msg += "You are common user"
    elif user['auth'] == 1:
        point = game['points'][user['point_id']]
        msg += f"You are a governor.\nYour point: {point['name']}\n"
        msg += get_resources_on_point_string(game, user['point_id'])
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
                res_id = team['storage'].index(res)
                name = game['resources'][res_id]['name']
                amount = res
                msg += f"{name}: {amount}\n"
    bot.send_message(chat_id=cid, text=msg)


@bot.message_handler(commands=['trade'])
def start_trade(m):
    cid = m.chat.id
    user = db.user_with_field(cid, "team_id")
    if not user:
        bot.send_message(cid, "You are not a team captain.")
    else:
        t = db.get_team(user['team_id'])
        if t['connected'] == -1:
            bot.send_message(cid, "You are not connected to a point.")
        else:
            pid = t['connected']
            con_id = len(list(db.get_contracts()))
            db.create_contract({"tid": t['id'], "pid": pid, "status": "pending0", "id": con_id})
            bot.send_message(cid, "Welcome to market!")
            bot.send_message(cid, get_resources_on_point_string(game, pid),
                             reply_markup=types.ReplyKeyboardRemove(selective=False))
            menu = types.InlineKeyboardMarkup()
            menu.add(types.InlineKeyboardButton("Buy", callback_data=f"trade0_buy_{con_id}"))
            menu.add(types.InlineKeyboardButton("Sell", callback_data=f"trade0_sell_{con_id}"))
            menu.add(types.InlineKeyboardButton(f"back", callback_data=f"trade0_back_{con_id}"))
            bot.send_message(cid, "Select action:", reply_markup=menu)


@bot.callback_query_handler(func=lambda call: "trade0" in call.data)
def select_resource(call):
    cid = call.message.chat.id
    mid = call.message.message_id
    data = call.data.split("_")
    con_type = data[1]
    con_id = int(data[2])
    db.update_contract(con_id, {"type": con_type, "status": "pending1"})
    contract = db.get_contract(con_id)
    if con_type == "back":
        db.delete_contract(con_id)
        bot.delete_message(cid, mid)
        bot.send_message(cid, "Back to point menu.",
                         reply_markup=menu_builder.connected_team_menu(contract['pid']))
    else:
        point = game['points'][contract['pid']]

        menu = types.InlineKeyboardMarkup()
        for res in point['resources']:
            res_id = point['resources'].index(res)
            menu.add(types.InlineKeyboardButton(f"{game['resources'][res_id]['name']}",
                                                callback_data=f"trade1_{con_id}_{res_id}"))

        menu.add(types.InlineKeyboardButton(f"back", callback_data=f"trade1_{con_id}_back"))
        bot.edit_message_text("Select resource:", cid, mid, reply_markup=menu)


@bot.callback_query_handler(func=lambda call: "trade1" in call.data)
def select_amount(call):
    cid = call.message.chat.id
    mid = call.message.message_id
    data = call.data.split("_")
    con_id = int(data[1])
    contract = db.get_contract(con_id)
    if data[2] == "back":
        db.delete_contract(con_id)
        bot.delete_message(cid, mid)
        bot.send_message(cid, "Back to point menu.",
                         reply_markup=menu_builder.connected_team_menu(contract['pid']))
    else:
        res_id = int(data[2])
        con_type = contract['type']
        t = db.get_team(contract['tid'])
        price = game['points'][contract['pid']]['resources'][res_id]['price']
        if con_type == "sell":
            if t['storage'][res_id] == 0:
                bot.answer_callback_query(call.id, f"You have not {game['resources'][res_id]['name']}!")
            else:
                db.update_contract(con_id, {"rid": res_id, "status": "pending2", "price": price})
                bot.delete_message(cid, mid)
                bot.send_message(cid, "Enter amount")
        elif con_type == "buy":
            point = game['points'][contract['pid']]
            if point['resources'][res_id]['amount'] == 0:
                bot.answer_callback_query(call.id, f"Point has not {game['resources'][res_id]['name']}!")
            elif t['money'] < point['resources'][res_id]['price']:
                bot.answer_callback_query(call.id,
                                          f"You have not enough money even for 1 unit of {game['resources'][res_id]['name']}!")
            else:
                db.update_contract(con_id, {"rid": res_id, "status": "pending2", "price": price})
                bot.delete_message(cid, mid)
                bot.send_message(cid, "Enter amount")
        else:
            raise Exception(f'Unknown contract type. Contract: {con_id}')


@bot.message_handler(func=lambda m: m.text.isdigit())
def check_amount(m):
    cid = m.chat.id
    amount = int(m.text)
    tid = db.is_captain(cid)
    t = db.get_team(tid)
    if t:
        contracts = db.get_pending_contracts_by_team(tid, 2)
        if contracts:
            if len(contracts) == 1:
                contract = contracts[0]
                con_type = contract['type']
                con_id = contract['id']
                pid = contract['pid']
                res_id = contract['rid']
                gov = db.get_governor_by_point(pid)

                menu = types.InlineKeyboardMarkup()
                row = menu.row()
                row.add(types.InlineKeyboardButton(f"Approve", callback_data=f"trade_resp_approved_{con_id}"))
                row.add(types.InlineKeyboardButton(f"Decline", callback_data=f"trage_resp_declined_{con_id}"))
                if con_type == "sell":
                    if t['storage'][res_id] >= amount:
                        db.update_contract(con_id, {"amount": amount, "status": "requested"})
                        bot.send_message(gov['chat_id'],
                                         f"Trade request by team {t['name']}.\n"
                                         f"{con_type.upper()} {amount} of {game['resources'][res_id]['name']} "
                                         f"with price {contract['price']}\n"
                                         f"Total: {amount * contract['price']}",
                                         reply_markup=menu)
                    else:
                        bot.reply_to(m, f"You have not enough {game['resources'][res_id]['name']}")

                elif con_type == "buy":
                    resources = game['points'][pid]['resources']
                    # blocked = game['points'][pid]['blocked']

                    if resources[res_id]['amount'] >= amount:
                        # blocked[res_id] += amount
                        if amount * contract['price'] <= t['money']:
                            db.update_contract(con_id, {"amount": amount, "status": "requested"})
                            bot.send_message(gov['chat_id'],
                                             f"Trade request by team {t['name']}.\n"
                                             f"{con_type.upper()} {amount} of {game['resources'][res_id]['name']} "
                                             f"with price {contract['price']}\n"
                                             f"Total: {amount * contract['price']}",
                                             reply_markup=menu)
                        else:
                            bot.reply_to(m, f"You have no enough money\n"
                                            f"You have: {t['money']}\n"
                                            f"Total cost: {amount * contract['price']}")
                    else:
                        bot.reply_to(m, f"Point has not enough {game['resources'][res_id]['name']}")

                else:
                    raise Exception(f'Unknown contract type. Contract: {con_id}')

            else:
                raise Exception(f"More then 1 pending2 contracts with team {tid}")
        else:
            bot.send_message(cid, "Unknown command, try again or use /help")
    else:
        bot.send_message(cid, "Unknown command, try again or use /help")


@bot.callback_query_handler(func=lambda call: "trade_resp" in call.data)
def trade_response(call):
    cid = call.message.chat.id
    mid = call.message.message_id
    data = call.data.split("_")
    answer = data[2]
    con_id = int(data[3])
    contract = db.get_contract(con_id)
    cap = db.get_captain_by_team(contract['tid'])
    point = game['points'][contract['pid']]

    if answer == "decline":
        db.update_contract(con_id, {"status": "declined"})
        bot.delete_message(cid, mid)
        bot.send_message(cid, "Request declined.")
        bot.send_message(cap['chat_id'], f"Your trade request is declined!\nReport to governor of {point['name']}.")
        bot.send_message(cid, "Contract declined!")
    else:
        db.update_contract(con_id, {"status": "approved"})
        con_type = contract['type']
        t = db.get_team(contract['tid'])
        if con_type == "sell":
            storage = t['storage']
            storage[contract['rid']] -= contract['amount']
            db.update_team(t['id'], {"storage": storage, "money": t['money'] + contract['amount'] * contract['price']})
            bot.send_message(cap['chat_id'], f"Your trade request is approved!\n"
                                             f"Storage: -{contract['amount']} {game['resources'][contract['rid']]['name']}\n"
                                             f"Money: + {contract['amount'] * contract['price']}",
                             reply_markup=menu_builder.connected_team_menu(pid=t['connected']))
            bot.send_message(cid, "Contract approved! Deal!")
        elif con_type == "buy":
            point['resources'][contract['rid']]['amount'] += contract['amount']
            team_storage = t['storage']
            team_storage[contract['rid']] += contract['amount']
            db.update_team(t['id'],
                           {"storage": team_storage, "money": t['money'] - contract['amount'] * contract['price']})
            bot.send_message(cap['chat_id'], f"Your trade request is approved!\n"
                                             f"Storage: +{contract['amount']} {game['resources'][contract['rid']]['name']}\n"
                                             f"Money: - {contract['amount'] * contract['price']}",
                             reply_markup=menu_builder.connected_team_menu(pid=t['connected']))
            bot.delete_message(cid, mid)
            bot.send_message(cid, "Contract approved! Deal!")
        else:
            raise Exception(f'Unknown contract type. Contract: {con_id}')


@bot.message_handler(commands=['prices'])
def prices(m):
    cid = m.chat.id
    args = extract_arg(m.text)
    bot.send_message(chat_id=cid, text=get_resources_on_point_string(game, int(args[0])))


@bot.message_handler(commands=['connected'])
def connected(m):
    cid = m.chat.id
    args = extract_arg(m.text)
    connected_teams = db.get_teams()
    msg = ""
    for c_team in connected_teams:
        if c_team['connected'] == int(args[0]):
            msg = msg + f"{c_team['name']}\n"

    bot.send_message(chat_id=cid, text=msg)


@bot.message_handler(func=lambda m: True)
def check_password(m):
    cid = m.chat.id
    user = db.get_user(cid)
    if user['auth'] == 3:
        team = db.get_team(user['team_id'])
        if m.text == team['pass']:
            db.update_user(cid, {"auth": 4, "team_id": team['id']})
            bot.send_message(chat_id=cid, text=f"You are successfully logged in as a captain of team "
                                               f"\"{team['name']}\"")
            bot.send_message(cid, "Choose action", reply_markup=menu_builder.team_menu())
        else:
            bot.send_message(cid, "Wrong password!", reply_markup=menu_builder.team_select_back_menu(cid))
    else:
        pass


if __name__ == '__main__':
    try:
        bot.stop_polling()
        bot.polling()
    except Exception as e:
        admins = db.get_admins()
        if bool(admins):
            for admin in admins:
                bot.send_message(admin['chat_id'], f"ERROR:\n{e}")
