from telebot.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

class MenuBuilder:

    def team_menu(self):
        menu = ReplyKeyboardMarkup(resize_keyboard=True)
        menu.add(KeyboardButton('/connect'),
                 KeyboardButton('/points'),
                 KeyboardButton('/me'),
                 KeyboardButton('/logout'))
        return menu

    def connected_team_menu(self, pid):
        menu = ReplyKeyboardMarkup(resize_keyboard=True)
        menu.add(KeyboardButton(f'/prices {pid}'),
                 KeyboardButton('/trade'),
                 KeyboardButton(f'/connected {pid}'),
                 KeyboardButton(f'/disconnect'),
                 KeyboardButton(f'/me'))
        return menu

    def common_user_menu(self):
        menu = ReplyKeyboardMarkup(resize_keyboard=True)
        menu.add(KeyboardButton(f'/me'),
                 KeyboardButton(f'/team'),
                 KeyboardButton(f'/teams'),
                 KeyboardButton(f'/points'))
        return menu

    def governor_menu(self, pid):
        menu = ReplyKeyboardMarkup(resize_keyboard=True)
        menu.add(KeyboardButton(f'/me'),
                 KeyboardButton(f'/teams'),
                 KeyboardButton(f'/connected {pid}'),
                 KeyboardButton(f'/prices {pid}'),
                 KeyboardButton(f'/logout'))
        return menu

    def admin_menu(self):
        menu = ReplyKeyboardMarkup(resize_keyboard=True)
        menu.add(KeyboardButton(f'/me'),
                 KeyboardButton(f'/register_team'),
                 KeyboardButton(f'/start_game'),
                 KeyboardButton(f'/teams'),
                 KeyboardButton(f'/points'),
                 KeyboardButton(f'/logout'))
        return menu

    def connect_menu(self, game, tid):
        menu = InlineKeyboardMarkup()
        points_row = menu.row()
        for point in game['points']:
            cb_data = f"connect_req_{game['points'].index(point)}_{tid}"
            points_row.add(InlineKeyboardButton(f"{point['name']}", callback_data=cb_data))
        return menu

    def approve_connect_menu(self, pid, tid):
        menu = InlineKeyboardMarkup()
        menu.add(InlineKeyboardButton(f"Approve", callback_data=f"connect_resp_approved_{pid}_{tid}"),
                 InlineKeyboardButton(f"Decline", callback_data=f"connect_resp_declined_{pid}_{tid}"))
        return menu

    def team_select_menu(self, teams, cid):
        menu = InlineKeyboardMarkup()
        points_row = menu.row()
        for team in teams:
            points_row.add(InlineKeyboardButton(f"{team['name']}", callback_data=f"enter_team_{team['id']}_{cid}"))
        points_row.add(InlineKeyboardButton(f"back", callback_data=f"enter_team_back"))
        return menu

    def team_select_back_menu(self, cid ):
        menu = InlineKeyboardMarkup()
        menu.add(InlineKeyboardButton(f"back", callback_data=f"enter_team_back"))
        return menu
