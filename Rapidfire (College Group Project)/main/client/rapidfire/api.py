import requests
import json

class API():
    def __init__(self):
        pass


    def post(self, php, data):
        baseURL = "https://smashhub.dev/rapidfire/"
        url = baseURL + php
        response = requests.post(url, data=data)
        # return response.json()

        
        ### DEBUGGING CODE BLOCK
        try:
            return response.json()
        except Exception as e:
            print(f"ERROR from {php}: {e}")
            print("RAW RESPONSE:", response)  # <-- ADD THIS
            return {"status": "error", "message": "API CALL FAILED"}
        ###
        


    def register_user(self, username, password):
        return self.post("register.php", {"username": username, "password": password})

    def login_user(self, username, password):
        return self.post("login.php", {"username": username, "password": password})
    
    def authenticate_token(self, token):
        return self.post("auth.php", {"token": token})
    
    def getInfo(self, user_id):
        return self.post("getInfo.php", {"user_id": user_id})
    
    def saveInfo(self, auth_token, question_set):
        return self.post("saveQuestions.php", {"auth_token": auth_token, 'question_set':json.dumps(question_set)})
    
    def createGameSession(self, game_id):
        return self.post("createGameSession.php", {"game_id": game_id})
    
    def phaseGameSession(self, game_id, game_phase):
        return self.post("phaseGameSession.php", {"game_id": game_id, "game_status":game_phase})

    def endGameSession(self, game_id, game_scores):
        return self.post("endGameSession.php", {"game_id": game_id, "game_scores": json.dumps(game_scores)})
    
    def getLeaderboard(self):
        return self.post("leaderboard.php", {})
    