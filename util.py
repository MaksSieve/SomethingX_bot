from datetime import datetime

from pymongo import MongoClient
from telebot import types


class DB:

    def __init__(self, db_url):
        self.client = MongoClient(db_url)
        self.db = self.client.test_bot

    def get_user(self, cid):
        users = list(self.db.User.find({"chat_id": cid}))
        if bool(users):
            return users[0]
        else:
            return None

    def get_team(self, tid):
        teams = list(self.db.Team.find({"id": int(tid)}))
        if bool(teams):
            return teams[0]
        else:
            return None

    def user_with_field(self, cid, field):
        users = list(self.db.User.find({"chat_id": cid, field: {"$exists": True}}))
        if bool(users):
            return users[0]
        else:
            return None

    def team_with_field(self, tid, field):
        teams = list(self.db.Team.find({"chat_id": tid, field: {"$exists": True}}))
        if bool(teams):
            return teams[0]
        else:
            return None

    def teams_with_field(self, field):
        return list(self.db.Team.find({field: {"$exists": True}}))

    def get_users(self):
        return list(self.db.User.find())

    def get_teams(self):
        return list(self.db.Team.find())

    def insert_user(self, user_dict):
        return self.db.User.insert_one(user_dict)

    def get_governor_by_point(self, pid):
        gov_list = list(self.db.User.find({"point_id": int(pid)}))
        if len(gov_list) > 0:
            return gov_list[0]
        else:
            return None

    def get_captain_by_team(self, tid):
        cap_list = list(self.db.User.find({"team_id": int(tid)}))
        if len(cap_list) > 0:
            return cap_list[0]
        else:
            return None

    def point_has_governor(self, pid):
        return bool(list(self.db.User.find({"point_id": int(pid)})))

    def update_user(self, cid, update_dict):
        return self.db.User.update_one({"chat_id": int(cid)}, {"$set": update_dict})

    def update_team(self, tid, update_dict):
        return self.db.Team.update_one({"id": int(tid)}, {"$set": update_dict})

    def team_has_captain(self, tid):
        return bool(list(self.db.User.find({"team_id": int(tid)})))

    def delete_user_fields(self, cid, update_dict):
        return self.db.User.update_one({"chat_id": int(cid)}, {"$unset": update_dict})

    def create_contract(self, contract_dict):
        return self.db.Contract.insert_one(contract_dict)

    def get_contracts(self):
        return self.db.Contract.find()

    def get_contract(self, con_id):
        contracts = list(self.db.Contract.find({"id": con_id}))
        if bool(contracts):
            return contracts[0]
        else:
            return None

    def update_contract(self, con_id, update_dict):
        return self.db.Contract.update_one({"id": con_id}, {"$set": update_dict})

    def is_captain(self, cid):
        user = self.user_with_field(cid, "team_id")
        if user:
            return user['team_id']
        else:
            return -1

    def get_pending_contracts_by_team(self, tid, step):
        contracts = list(self.db.Contract.find({"tid": tid, "status": f"pending{step}"}))
        if bool(contracts):
            return contracts
        else:
            return None

    def get_admins(self):
        return list(self.db.User.find({"auth": 2}))

    def delete_contract(self, con_id):
        return self.db.Contract.delete_one({"id": con_id})


class MenuBuilder:

    def team_menu(self):
        menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        menu.add(types.KeyboardButton('/connect'),
                 types.KeyboardButton('/points'),
                 types.KeyboardButton('/me'),
                 types.KeyboardButton('/logout'))
        return menu

    def connected_team_menu(self, pid):
        menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        menu.add(types.KeyboardButton(f'/prices {pid}'),
                 types.KeyboardButton('/trade'),
                 types.KeyboardButton(f'/connected {pid}'),
                 types.KeyboardButton(f'/disconnect'),
                 types.KeyboardButton(f'/me'))
        return menu

    def common_user_menu(self):
        menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        menu.add(types.KeyboardButton(f'/me'),
                 types.KeyboardButton(f'/team'),
                 types.KeyboardButton(f'/teams'),
                 types.KeyboardButton(f'/points'))
        return menu

    def governor_menu(self, pid):
        menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        menu.add(types.KeyboardButton(f'/me'),
                 types.KeyboardButton(f'/teams'),
                 types.KeyboardButton(f'/connected {pid}'),
                 types.KeyboardButton(f'/prices {pid}'),
                 types.KeyboardButton(f'/logout'))
        return menu

    def admin_menu(self):
        menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        menu.add(types.KeyboardButton(f'/me'),
                 types.KeyboardButton(f'/start_game'),
                 types.KeyboardButton(f'/start_game'),
                 types.KeyboardButton(f'/teams'),
                 types.KeyboardButton(f'/points'),
                 types.KeyboardButton(f'/logout'))
        return menu

    def connect_menu(self, game, tid):
        menu = types.InlineKeyboardMarkup()
        points_row = menu.row()
        for point in game['points']:
            cb_data = f"connect_req_{game['points'].index(point)}_{tid}"
            points_row.add(types.InlineKeyboardButton(f"{point['name']}", callback_data=cb_data))
        return menu

    def approve_connect_menu(self, pid, tid):
        menu = types.InlineKeyboardMarkup()
        menu.add(types.InlineKeyboardButton(f"Approve", callback_data=f"connect_resp_approved_{pid}_{tid}"),
                 types.InlineKeyboardButton(f"Decline", callback_data=f"connect_resp_declined_{pid}_{tid}"))
        return menu

    def team_select_menu(self, teams, cid):
        menu = types.InlineKeyboardMarkup()
        points_row = menu.row()
        for team in teams:
            points_row.add(types.InlineKeyboardButton(f"{team['name']}", callback_data=f"enter_team_{team['id']}_{cid}"))
        points_row.add(types.InlineKeyboardButton(f"back", callback_data=f"enter_team_back"))
        return menu

    def team_select_back_menu(self, cid ):
        menu = types.InlineKeyboardMarkup()
        menu.add(types.InlineKeyboardButton(f"back", callback_data=f"enter_team_back"))
        return menu

def extract_arg(arg):
    return arg.split()[1:]


def create_dump(game, db):
    return {'time': datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'),
            'points': game['points'],
            'teams': db.get_teams()
            }


def get_resources_on_point_string(game, pid):
    resources = game['points'][pid]['resources']
    msg = "name - amount - price\n"
    for res in resources:
        res_id = resources.index(res)
        msg = msg + f"{game['resources'][res_id]['name']} - " \
                    f"{res['amount']} - " \
                    f"{res['price']}\n"
    return msg


def is_enough_resource_on_point(game, pid, rid, amount):
    return game['points'][pid]['resources'][rid][amount] <= amount


def get_price(game, pid, rid):
    amount = game['points'][pid]["resources"][rid]
    k = game["resources"][rid]['k']
    min_price = game["resources"][rid]['min_price']
    max_amount = game["resources"][rid]['max_amount']
    f = amount * k + min_price - max_amount * k
    return max(f, min_price)
