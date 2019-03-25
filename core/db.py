from mongoengine import *

from core.config_loader import config

db = connect(
    db=config.get('Common', 'db_name'),
    host='mongodb://'+config.get('Common', 'db_url') + '/' + config.get('Common', 'db_name')
)


class AuthTypes:

    __types = {
        "common": 0,
        "governor": 1,
        "admin": 2,
        "team": 3,
    }

    def common(self):
        return self.__types.get("common")

    def governor(self):
        return self.__types.get("governor")

    def admin(self):
        return self.__types.get("admin")

    def team(self):
        return self.__types.get("team")

    def get_all(self):
        return list(self.__types.values())


class User(Document):
    meta = {'collection': 'User'}

    chat_id = IntField(required=True)
    auth = IntField(required=True, enum=list(AuthTypes().get_all()))
    team_id = ReferenceField('Team')
    point = IntField()

    def new(self, chat_id):
        self.chat_id = chat_id
        self.auth = AuthTypes().common()
        self.save()
        return self

    def get_by_chat_id(self, chat_id):
        return self.objects(chat_id=chat_id).all()[0]

    def authorize_as_team(self, team_oid):
        self.auth = AuthTypes().team()
        self.team = team_oid
        self.save()

    def authorize_as_admin(self):
        self.auth = AuthTypes().admin()
        self.save()

    def authorize_as_governor(self):
        self.auth = AuthTypes().governor()
        self.save()

    def get_admins(self):
        return self.objects(auth=AuthTypes().admin()).all()

    def get_captain_by_team(self, team_oid):
        return self.objects(team=team_oid).all()[0]


class Team(Document):
    meta = {'collection': 'Team'}

    name = StringField(required=True, unique=True)
    password = StringField(required=True)
    money = IntField(required=True)
    storage = ListField(IntField(), required=True)


