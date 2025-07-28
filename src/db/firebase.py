import pyrebase
from config.config import Config


class Firebase:
    """
    A class to handle Firebase operations.
    """

    def __init__(self):
        firebase = pyrebase.initialize_app(Config.FIREBASE_CONF)
        self.db = firebase.database()
        self.auth = firebase.auth()
        self.bot_auth = self.auth.sign_in_with_email_and_password(Config.FIREBASE_USER, Config.FIREBASE_PASSWORD)
        self.bot_db_token = self.bot_auth['idToken']
        
    
    def get_user(self, user_id):
        data = self.db.child(f"{Config.BOT_DB_PATH}/users/{user_id}").get(self.bot_db_token).val()
        if data:
            return dict(data)
        else:
            return None
        
    def get_all_users(self):
        data = self.db.child(f"{Config.BOT_DB_PATH}/users").get(self.bot_db_token).val()
        if data:
            return dict(data)
        else:
            return None
   
    def get_user_language(self, user_id):
        data = self.db.child(f"{Config.BOT_DB_PATH}/users/{user_id}/language").get(self.bot_db_token).val()
        if data:
            return str(data)
        else:
            return None
    
    def get_selected_language(self, user_id):
        data = self.db.child(f"{Config.BOT_DB_PATH}/users/{user_id}/selected_language").get(self.bot_db_token).val()
        if data:
            return data
        else:
            return None
        
    def update_selected_language(self, user_id, language):
        self.db.child(f"{Config.BOT_DB_PATH}/users/{user_id}").update({"selected_language": language}, self.bot_db_token)
    
    def delete_selected_language(self, user_id):
        self.db.child(f"{Config.BOT_DB_PATH}/users/{user_id}/selected_language").remove(self.bot_db_token)
    
    def update_language(self, user_id, language):
        self.db.child(f"{Config.BOT_DB_PATH}/users/{user_id}").update({"language": language}, self.bot_db_token)