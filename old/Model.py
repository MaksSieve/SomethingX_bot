class Model:
    __games = []
    __users = {}

    def create_game(self, name, password):
        game = Game(name, password)
        self.__games.append(game)
        return game

    def join_game(self, user_id, game_id):
        if len(self.__games) > game_id >= 0:
            self.__users[user_id] = game_id
            return self.__games[game_id]
        else:
            return None

    def in_game(self, user_id):
        if user_id in list(self.__users.keys()):
            return self.__users[user_id]
        else:
            return None

    def get_games(self):
        return self.__games


class Game:
    __name = ""
    __pass = ""
    __points = {}
    __teams = {}
    __resources = {}

    def __init__(self, name, password):
        self.__name = name
        self.__pass = password

    def isReady(self):
        return bool(self.__points) and bool(self.__teams) and bool(self.__resources)

    def get_points(self):
        return self.__points

    def is_unique(self, collection, name):
        f = True
        for i in collection:
            if collection[i].name == name: f = False
        return f

    def add_point(self, name, base_resource_id):
        keys = list(self.__points.keys())
        self.__points[keys[len(keys)]] = Point(game=self, name=name, base_resource_id=base_resource_id)


class Resource:
    name = ""
    production_per_minute = 1


class Point:

    def __init__(self, game, name, base_resource_id):
        self.name = name
        self.base_resource_id = base_resource_id

    def get_resource_price(self, resource_id):
        return 0

    def trade(self, team_id, resource_id, resource_amount):
        return 0


class Team:
    name = ""
    players = {}
    money = 0
