from rapidfire.api import API
import os
import json

class User():
    def __init__(self):
        self.api = API()

        self.logged_in = False
        self.username = "Guest"
        self.score = 0
        self.userid = None
        self.auth_token = None

        self.initialize_user()

        self.reserved_word=set(["Add Question","Save","Delete Question Set","Quit","Add new qustion set"])
        self.question_sets={}
        

    def get_username(self):
        return self.username


    def initialize_user(self):
        if os.path.exists("login.json"):
            with open("login.json", 'r') as file:

                data = json.load(file)
                token = data.get("auth_token")
                if token:
                    auth_response = self.authenticate(token)
                    if auth_response.get("status") == "success":
                        # Token is valid, load user data
                        self.username = auth_response.get("username")
                        self.userid = auth_response.get("user_id")
                        self.role = auth_response.get("role")
                        self.score = auth_response.get("score")
                        self.auth_token = token
                        self.logged_in = True

                    else:
                        print("Invalid token. Please log in again.")
                        # Prompt for login/registration
                else:
                    print("No token found. Please log in.")
                    # Prompt for login/registration
        else:
            # No login.json file, user is not logged in
            self.logged_in = False
            self.userid = None
            self.auth_token = None
            self.username = "Guest"
            self.score = 0

    def getUserID(self):
        return self.userid

    def getScore(self):
        if not self.logged_in:
            return self.score  # Return local score for guest users
        
        #Else fetch from backend
        return self.api.getInfo(self.userid)['score']

    def login(self, username, password):
        response = self.api.login_user(username, password)

        if response['status'] == 'error':
            return response
        # Save token
        with open("login.json", 'w') as file:
            json.dump({"auth_token": response['auth_token']}, file)
       
        self.initialize_user() # Update user state
        return response
    
    def register(self, username, password):
        response = self.api.register_user(username, password)
        if response['status'] == 'error':
            return response
        # Save token
        with open("login.json", 'w') as file:
            json.dump({"auth_token": response['auth_token']}, file)
        self.initialize_user()  # Update user state

        return response
    
    def authenticate(self, token):
        response = self.api.authenticate_token(token)
        return response
    
    def logout(self):
        self.logged_in = False
        self.username = "Guest"
        self.score = 0
        self.userid = None
        self.auth_token = None

        if os.path.exists("login.json"):
            os.remove("login.json")

    def LoadQuestionJson(self):

        # If path doesnt exist, create questions
        if not os.path.exists("questions.json"):

            # If user logged in, get data from DB
            if(self.logged_in):
                response = self.api.getInfo(self.userid)
                if(response['status'] != "success"):
                    print(response['status'])
                    return
                
                #All checks passed, load from DB
                dataFromDB = response['question_set']
                self.question_sets = json.loads(dataFromDB)

                # Write to DB
                with open("questions.json", "w", encoding="utf-8") as f:
                    json.dump(self.question_sets, f, ensure_ascii=False, indent=4)
                return
            # otherwise create empty questions.json
            temp={}
            with open("questions.json", "w", encoding="utf-8") as f:
                json.dump(temp, f, ensure_ascii=False, indent=4)
        
        with open("questions.json", "r", encoding="utf-8") as f:
            self.question_sets = json.load(f)

    def SaveQuestionJson(self):
        with open("questions.json", "w", encoding="utf-8") as f:
            json.dump(self.question_sets, f, ensure_ascii=False, indent=4)

        response = self.api.saveInfo(self.auth_token, self.question_sets)
        
        if(response['status'] == "error"):
            print(response['message'])
            input("ERROR")
            return False
        
        return True

            
        