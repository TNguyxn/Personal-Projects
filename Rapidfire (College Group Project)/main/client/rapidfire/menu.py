import os
import msvcrt  # Windows-only
import winsound
import json
import asyncio
from rapidfire.game_server import game
from rapidfire.game_client import GameClient
from rapidfire.api import API
from rapidfire.sha256 import SHA256

class UI():
    def __init__(self, user):
        self.user = user

        self.currentOption = 0
        self.menuOptions = [
            "Join a Game", # Enter Game Code
            "Host a Game", #  Set game name/code, choose question set
            "Create Question Set",
            "Leaderboard",
            "User Account", # Link to user account
            "Settings", # Sound effects, name color, etc
            "Quit",
        ]

        self.menuActions = {
            "Join a Game": self.JoinGame,
            "Host a Game": self.HostGame,
            "Create Question Set": self.CreateQuestionSet,
            "Leaderboard": self.Leaderboard,
            "User Account": self.UserAccountMenu,
            "Settings": self.Settings,
            "Quit": None,  # Special case
        }

        # check if settings.json exists
        self.userSettings = {"sounds": True}

        settings_file = "settings.json"
        if os.path.exists(settings_file):
            # Load existing settings
            with open(settings_file, "r", encoding="utf-8") as f:
                try:
                    self.userSettings = json.load(f)
                except json.JSONDecodeError:
                    # If file is corrupted, fallback to defaults
                    userSettings = {"sounds": True}
        else:
            # File doesn't exist, create defaults
            userSettings = {"sounds": True}
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(userSettings, f, indent=4)

        

    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def play_sound(self, file_name):
        if not (self.userSettings['sounds']): # if disabled
            return

        full_path = "./resources/audio/" + file_name
        winsound.PlaySound(full_path, winsound.SND_FILENAME | winsound.SND_ASYNC)


    def draw_logo(self):
        self.clear()
        print(r'''

        __________    _____ __________.___________  ___________.________________________ 
        \______   \  /  _  \\______   \   \______ \ \_   _____/|   \______   \_   _____/ 
        |       _/ /  /_\  \|     ___/   ||    |  \ |    __)  |   ||       _/|    __)_  
        |    |   \/    |    \    |   |   ||    `   \|     \   |   ||    |   \|        \ 
        |____|_  /\____|__  /____|   |___/_______  /\___  /   |___||____|_  /_______  / 
                \/         \/                     \/     \/                \/        \/  
                                                                                        
                                                                                        
        ______   ______   ______   ______   ______   ______   ______   ______   ______ 
        /_____/  /_____/  /_____/  /_____/  /_____/  /_____/  /_____/  /_____/  /_____/ 

                                                                              
        ''')
        


    def draw_menu(self):
        self.clear()
        self.draw_logo()

        print(f"Welcome to RapidFire, \033[36m{ self.user.get_username()}\033[0m!\nUse the arrow keys to navigate.\n")

        for i in range(0,len(self.menuOptions)):
            if i == self.currentOption:
                print(f"> \033[92m{self.menuOptions[i]}\033[0m <")
                continue
            print(f"[{self.menuOptions[i]}]")

    def get_key(self):
        """Read a single keypress on Windows"""
        key = msvcrt.getch()
        if key == b'\xe0':  # Special keys (arrows, f keys, etc.)
            key2 = msvcrt.getch()
            if key2 == b'H':  # Up arrow
                self.play_sound("select.wav")
                return 'UP'
            elif key2 == b'P':  # Down arrow
                self.play_sound("select.wav")
                return 'DOWN'
            elif key2 == b'M':  # Right arrow
                self.play_sound("select.wav")
                return 'RIGHT'
            elif key2 == b'K':  # Left arrow
                self.play_sound("select.wav")
                return 'LEFT'
        elif key == b'\r':  # Enter
            self.play_sound("select.wav")
            return 'ENTER'
        
        self.play_sound("error.wav")
        return None
    
    def home(self):
        while True:
            self.draw_menu()
            key = self.get_key()
            if key == 'UP':
                self.currentOption = (self.currentOption - 1) % len(self.menuOptions)
            elif key == 'DOWN':
                self.currentOption = (self.currentOption + 1) % len(self.menuOptions)
            elif key in ('ENTER', 'RIGHT'):
                selected = self.menuOptions[self.currentOption]
                self.clear()
                print(f"You selected: {selected}")
                action = self.menuActions.get(selected)
                if action:
                    action()
                if selected == "Quit":
                    break
            elif key == 'LEFT':
                break

    async def Client(self,ip):
        client = GameClient(ip=ip, port=8891,name=self.user.username)
        leaderboard = await client.run()
        print("\n=== FINAL LEADERBOARD ===")
        for score, name in leaderboard:
            print(f"  {name}: {score}")
        print("========================\n")
        
    def JoinGame(self):
        if not os.path.exists("login.json"):
            self.clear()
            self.draw_logo()
            input("\nPlease login or register before joining a gane. \nPress Enter to return to menu...")
            return
        self.clear()
        self.draw_logo()
        ip=input("Enter Host IP (enter q to quit): ")
        if ip=="q" or ip=="Q":
            return 
        asyncio.run(self.Client(ip))
        input("\nPress Enter to return to menu...")
        

    async def Server(self,qset_name,qset):
        g = game(qset_name=qset_name, qset=qset)
        leaderboard = await g.run(port=8891)
        print("\n=== FINAL LEADERBOARD ===")
        for score, name in leaderboard:
            print(f"  {name}: {score}")
        print("========================\n")

    def HostGame(self):
        if not os.path.exists("login.json"):
            self.clear()
            self.draw_logo()
            input("\nPlease login or register before hosting a gane. \nPress Enter to return to menu...")
            return
        
        self.user.LoadQuestionJson() 

        options=list(self.user.question_sets.keys())+["Back"]
        cur_idx=0
        while True:
            self.clear()
            self.draw_logo()
            questions = list(self.user.question_sets.keys())
            actions = ["Back"]
            options = questions + actions
            print(f"Use the arrow keys to navigate.\n")

            for i in range(len(questions)):
                if i == cur_idx:
                    print(f"> \033[92m{options[i]}\033[0m <")
                else:
                    print(f"[{options[i]}]")
            print()  # Blank line between questions and actions
            # Print actions
            for i in range(len(questions), len(options)):
                if i == cur_idx:
                    print(f"> \033[92m{options[i]}\033[0m <")
                else:
                    print(f"[{options[i]}]")

            key = self.get_key()
            if key == 'UP':
                cur_idx = (cur_idx - 1) % len(options)
            elif key == 'DOWN':
                cur_idx = (cur_idx + 1) % len(options)
            elif key in ('ENTER', 'RIGHT'):
                selected = options[cur_idx]
                if selected=="Back":
                    break
                else:
                    asyncio.run(self.Server(selected,self.user.question_sets[selected]))
                    input("\nPress Enter to return to menu...")
        
    
    def CheckQuestionSetChange(self):
        if not os.path.exists("questions.json"):
            temp={}
            with open("questions.json", "w", encoding="utf-8") as f:
                json.dump(temp, f, ensure_ascii=False, indent=4)
        with open("questions.json", "r", encoding="utf-8") as f:
            old_question_sets = json.load(f)
        
        if len(old_question_sets.keys()) != len(self.user.question_sets.keys()):
            return True
        for k in old_question_sets.keys():
            if k not in self.user.question_sets.keys():
                return True
            if len(old_question_sets[k])!=len(self.user.question_sets[k]):
                return True
        for k in old_question_sets.keys():
            for i in range(len(old_question_sets[k])):
                if old_question_sets[k][i]!=self.user.question_sets[k][i]:
                    return True
        return False
                
    def ModifyQuestion(self,question):
        options=["Modify","Delete","Back"]
        cur_idx=0
        while True:
            self.clear()
            self.draw_logo()
            print(f"\nQuestion: {question}\n")
            for i in range(len(options)):
                if i == cur_idx:
                    print(f"> \033[92m{options[i]}\033[0m <")
                else:
                    print(f"[{options[i]}]")
            key = self.get_key()
            if key == 'UP':
                cur_idx = (cur_idx - 1) % len(options)
            elif key == 'DOWN':
                cur_idx = (cur_idx + 1) % len(options)
            elif key in ('ENTER', 'RIGHT'):
                selected = options[cur_idx]
                self.clear()
                self.draw_logo()
                print(f"\nCurrent Question: {question}\n")
                if selected=="Back":
                    return 0,question
                elif selected=="Delete":
                    confirmation=input(f"\nWarning: You are about to delete this question. Enter Y to confirm:")
                    if confirmation=="Y" or confirmation=="y":
                        input(f"\nQuestion deleted...")
                        return -1,""
                elif selected=="Modify":
                    q_input=input("Enter the new question: ")
                    if q_input in self.user.reserved_word:
                        input("\nYou have entered a reserved word. Press Enter to continue")
                    else:
                        return 1,q_input

    def ModifyQuestionSet(self, q_set_name):
        cur_idx = 0
        while True:
            self.clear()
            self.draw_logo()

            questions = self.user.question_sets[q_set_name]
            actions = ["Add Question", "Rename Question Set", "Delete Question Set", "Back"]
            options = questions + actions  # No indent

            print(f"Use the arrow keys to navigate.\n")
            print(f"Qustion Set Editing: {q_set_name}\n")
            # Print questions
            for i in range(len(questions)):
                if i == cur_idx:
                    print(f"> \033[92m{options[i]}\033[0m <")
                else:
                    print(f"[{options[i]}]")
            print()  # Blank line between questions and actions
            # Print actions
            for i in range(len(questions), len(options)):
                if i == cur_idx:
                    print(f"> \033[92m{options[i]}\033[0m <")
                else:
                    print(f"[{options[i]}]")

            key = self.get_key()
            if key == 'UP':
                cur_idx = (cur_idx - 1) % len(options)
            elif key == 'DOWN':
                cur_idx = (cur_idx + 1) % len(options)
            elif key in ('ENTER', 'RIGHT'):
                selected = options[cur_idx]
                self.clear()
                self.draw_logo()
                print(f"Qustion Set Editing: {q_set_name}")

                questions = self.user.question_sets[q_set_name]
                actions = ["Add Question", "Save", "Delete Question Set", "Back"]
                options = questions + actions

                if selected == "Back":
                    break
                elif selected == "Delete Question Set":
                    print(f'\n\033[91mWARNING!\033[0m You are about to delete {q_set_name}.')
                    confirmation = input("Enter Y to confirm: ")
                    if confirmation.lower() == "y":
                        del self.user.question_sets[q_set_name]
                        input(f"\nQuestion set {q_set_name} deleted...")
                        break
                elif selected == "Add Question":
                    q_input = input("Enter the question: ")
                    if q_input in self.user.reserved_word:
                        input("\nYou have entered a reserved word. Press Enter to continue")
                    else:
                        self.user.question_sets[q_set_name].append(q_input)
                elif selected in questions:
                    res, q_input = self.ModifyQuestion(selected)
                    idx = questions.index(selected)
                    if res < 0:
                        self.user.question_sets[q_set_name].pop(idx)
                    elif res > 0:
                        self.user.question_sets[q_set_name][idx] = q_input
                elif selected == "Rename Question Set":
                    new_name = input(f"\nEnter a new name for '{q_set_name}': ").strip()

                    if not new_name:
                        input("\nName cannot be empty. Press Enter to continue...")
                    elif new_name in self.user.question_sets:
                        input("\nA question set with that name already exists! Press Enter to continue...")
                    elif new_name in self.user.reserved_word:
                        input("\nThat name is reserved. Press Enter to continue...")
                    else:
                        # Rename by creating a new entry and deleting the old
                        self.user.question_sets[new_name] = self.user.question_sets.pop(q_set_name)
                        q_set_name = new_name  # Update the local reference
                        input(f"\nQuestion set renamed to '{new_name}'! Press Enter to continue...")

    def CreateQuestionSet(self):
        if not os.path.exists("login.json"):
            self.clear()
            self.draw_logo()
            input("\nPlease login or register before creating a problem set. \nPress Enter to return to menu...")
            return
        
        self.user.LoadQuestionJson() #Perhaps on login?

        options=list(self.user.question_sets.keys())+["Add new qustion set","Save","Back"]
        cur_idx=0
        while True:
            self.clear()
            self.draw_logo()


            questions = list(self.user.question_sets.keys())
            actions = ["Add new qustion set", "Save", "Back"]
            options = questions + actions
            print(f"Use the arrow keys to navigate.\n")

            for i in range(len(questions)):
                if i == cur_idx:
                    print(f"> \033[92m{options[i]}\033[0m <")
                else:
                    print(f"[{options[i]}]")
            print()  # Blank line between questions and actions
            # Print actions
            for i in range(len(questions), len(options)):
                if i == cur_idx:
                    print(f"> \033[92m{options[i]}\033[0m <")
                else:
                    print(f"[{options[i]}]")

            key = self.get_key()
            if key == 'UP':
                cur_idx = (cur_idx - 1) % len(options)
            elif key == 'DOWN':
                cur_idx = (cur_idx + 1) % len(options)
            elif key in ('ENTER', 'RIGHT'):
                selected = options[cur_idx]
                self.clear()
                self.draw_logo()
                options=list(self.user.question_sets.keys())+["Add new qustion set","Save","Quit"]
                if selected=="Back":
                    if self.CheckQuestionSetChange():
                        confirmation=input(f"\nDo you wish to save your changes? Enter Y to confirm:")
                        if confirmation=="Y" or confirmation=="y":
                            self.user.SaveQuestionJson()
                            input("\nQuestion Updated. Press Enter to continue...")
                    break
                elif selected=="Save":
                    if self.CheckQuestionSetChange():
                        self.user.SaveQuestionJson()
                        input("\nQuestion Updated...")
                    else:
                        input("\nNothing was changed...")
                    break
                elif selected=="Add new qustion set":
                    name=input("Enter the name of the question set: ")
                    if name in self.user.reserved_word:
                        input("\nInvalid name. Press Enter to continue")
                    elif name in self.user.question_sets.keys():
                        input(f"\nQuestion set {name} already exists. Press Enter to continue")
                    else:
                        self.user.question_sets[name]=[]     
                else:
                    self.ModifyQuestionSet(selected)
                

    def Leaderboard(self):
        self.clear()
        self.draw_logo()
        print("Leaderboard selected!\n")

        leaderboard = API().getLeaderboard()
        entries = leaderboard['leaderboard']

        if not entries:
            print("No scores available yet.")
            input("\nPress Enter to return to menu...")
            return

        # Determine column widths
        rank_width = len(str(len(entries))) + 6
        username_width = max(len(user['username']) for user in entries) + 4
        score_width = max(len(str(user['score'])) for user in entries) + 4

        # Print header
        print(f"{'Rank':<{rank_width}}{'Username':<{username_width}}{'Score':<{score_width}}")
        print('-' * (rank_width + username_width + score_width))

        # ANSI color codes for top 3
        colors = ["\033[31m", "\033[35m", "\033[96m"]  # gold, white, red

        # Print leaderboard
        for idx, user in enumerate(entries, start=1):
            color = colors[idx - 1] if idx <= 3 else ""  # apply color for top 3
            reset = "\033[0m" if idx <= 3 else ""
            print(f"{color}{idx:<{rank_width}}{user['username']:<{username_width}}{user['score']:<{score_width}}{reset}")

        input("\nPress Enter to return to menu...")


    def UserAccountMenu(self):
        current = 0

        while True:
            options = ["Register", "Login", "Logout", "Back"]
            if self.user.logged_in:
                options.pop(1)  # Remove Login if already logged in
            else:
                options.pop(2) # Remove Logout if not logged in
            self.clear()
            self.draw_logo()
            
            user = self.user.get_username()
            print(f"User Account Options for \033[36m{user}\033[0m\n")

            for i, option in enumerate(options):
                if i == current:
                    print(f"> \033[92m{option}\033[0m <")
                else:
                    print(f"[{option}]")
            key = self.get_key()
            if key == 'UP':
                current = (current - 1) % len(options)
            elif key == 'DOWN':
                current = (current + 1) % len(options)
            elif key in ('ENTER', 'RIGHT'):
                selected = options[current]
                if selected == "Register":
                    self.Register()
                elif selected == "Login":
                    self.Login()
                elif selected == "Logout":
                    self.logout()
                elif selected == "Back":
                    break

    def Register(self):
        self.clear()
        self.draw_logo()
        print("User Registration selected!\n")
        # MYSQL API CALLS HERE TO REGISTER/LOGIN to check if user exists
        username = input("Enter username: ")
        password = input("Enter password: ")
        confirm_password = input("Confirm password: ")

        if password != confirm_password:
            print("\033[91mPassword's do not match!\033[0m")
            input("\nPress Enter to try again...")
            self.Register()
            return
        
        hashed = SHA256.hash(password)
        # Call API to register user
        response = self.user.register(username, hashed)

        if response['status'] == 'error':
            print(f"Registration unsuccessful!\n\033[91m{response['message']}\033[0m")
            input("\nPress Enter to try again...")
            return

        # Successful registration
        print(f"\033[92m{response['message']}\033[0m")

        input("\nPress Enter to return to menu...")

    def Login(self):
        self.clear()
        self.draw_logo()
        print("Login selected!\n")
        # MYSQL API CALLS HERE TO REGISTER/LOGIN to check if user exists

        # Check if login.json exists and has a valid token
        if os.path.exists("login.json"):
            with open("login.json", 'r') as file:
                data = json.load(file)
                token = data.get("auth_token")
                if token:
                    auth_response = self.user.authenticate(token)
                    if auth_response.get("status") == "success":
                        print(f"Welcome back, {auth_response.get('username')}!")
                        self.user.initialize_user()
                        input("\nPress Enter to return to menu...")
                        return

        username = input("Enter username: ")
        password = input("Enter password: ")

        # Call API to login user
        hashed = SHA256.hash(password)
        response = self.user.login(username, hashed)

        if response['status'] == 'error':
            print(f"Login unsuccessful!\n\033[91m{response['message']}\033[0m")
            input("\nPress Enter to continue...")
            return

        print(f"\033[92m{response['message']}\033[0m")
        input("\nPress Enter to return to menu...")

    def logout(self):
        self.user.logout()
        print("You have been logged out.")
        input("\nPress Enter to return to menu...")
        return

        
    def Settings(self):
        # List of settings and their labels
        settings_options = [
            {"key": "sounds", "label": "Sounds"}
            # You can add more settings here
        ]

        current = 0

        while True:
            self.clear()
            self.draw_logo()
            print("Settings Menu\n")

            # Display settings with their current values
            for i, opt in enumerate(settings_options):
                value = "ON" if self.userSettings.get(opt["key"], True) else "OFF"
                if i == current:
                    print(f"> \033[92m{opt['label']}: {value}\033[0m <")
                else:
                    print(f"[{opt['label']}: {value}]")

            # Add exit option
            exit_index = len(settings_options)
            if current == exit_index:
                print(f"> \033[91mBack\033[0m <")
            else:
                print("[Back]")

            # Get key input
            key = self.get_key()
            if key == 'UP':
                current = (current - 1) % (len(settings_options) + 1)
            elif key == 'DOWN':
                current = (current + 1) % (len(settings_options) + 1)
            elif key in ('ENTER', 'RIGHT'):
                if current == exit_index:
                    # Exit selected
                    break
                else:
                    # Toggle the selected setting
                    key_name = settings_options[current]["key"]
                    self.userSettings[key_name] = not self.userSettings.get(key_name, True)
                    # Save changes immediately
                    with open("settings.json", "w", encoding="utf-8") as f:
                        json.dump(self.userSettings, f, indent=4)


    def _save_settings(self):
        """Save current settings to file."""
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(self.userSettings, f, indent=4)