from datetime import datetime

from pymongo import MongoClient


class DB:

    def __init__(self):
        self.client = MongoClient('storage.loadtest.m1.tinkoff.cloud:27017')
        self.db = self.client.test_bot

    def get_user(self, cid):
        users = list(self.db.User.find({"chat_id": cid}))
        if bool(users):
            return users[0]
        else:
            return None

    def get_team(self, tid):
        users = list(self.db.Team.find({"id": int(tid)}))
        if bool(users):
            return users[0]
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


def extract_arg(arg):
    return arg.split()[1:]


def create_dump(game, db):
    return {'time': datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'),
            'points': game['points'],
            'teams': db.get_teams()
            }
