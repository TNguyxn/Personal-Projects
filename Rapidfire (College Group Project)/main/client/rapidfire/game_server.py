import socket
import asyncio
import json
import signal
import argparse
from websockets.server import serve
from websockets.exceptions import ConnectionClosed
import os
import msvcrt  # <-- 1. Use msvcrt
from rapidfire.api import API
import time

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "127.0.0.1"
    return ip
def encode(msg: dict) -> str:
    return json.dumps(msg, separators=(",", ":"))




seed = int(time.time())  # current timestamp in seconds
def rand():
    global seed
    seed = (1103515245 * seed + 12345) % (2**31)
    return seed


def random_string(length=16):
    chars = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    )
    result = ""
    for _ in range(length):
        index = rand() % len(chars)
        result += chars[index]
    return result



class game:
    def __init__(self,qset_name,qset):
        self.api = API()

        self.ip=get_local_ip()
        self.qset_name=qset_name
        self.qset=qset
        self.q_idx=0
        self.phase= "lobby"
        self.open=False
        self.current_winner=None
        self.CLIENTS={}
        self.scoreboard={}
        self.leaderboard=[]
        self.game_id=random_string()
        self._result = None
        self._server_dirty = asyncio.Event()

        # POST REQUEST TO API TO CREATE GAME SESSION
        # print("Creating game session with ID:", self.game_id)
        self.api.createGameSession(self.game_id)
        self.api.phaseGameSession(self.game_id, self.phase)


    async def broadcast(self, msg):
        if not self.CLIENTS:
            return
        data = encode(msg)
        targets = list(self.CLIENTS.keys())   # snapshot
        await asyncio.gather(*(ws.send(data) for ws in targets), return_exceptions=True)
    
    async def announce_state(self):
        self._server_dirty.set() 
        await self.broadcast(
            {
                "type": "state",
                "phase": self.phase,
                "open": self.open,
                "winner": self.current_winner,
                "q_id": self.q_idx,
                "q_total": len(self.qset),
                "leaderboard": self.leaderboard,
            },
        )
        # POST REQUEST TO API TO UPDATE PHASE
        self.api.phaseGameSession(self.game_id, self.phase)
    
    async def handle_client(self,ws):
        name = None
        try:
            hello_raw = await asyncio.wait_for(ws.recv(), timeout=10)
            hello = json.loads(hello_raw)
            if hello.get("type") != "hello" or "name" not in hello:
                await ws.close(code=1002, reason="Expected hello with name")
                return
        except Exception:
            await ws.close()
            return
        
        name = hello["name"].strip()
        self.CLIENTS[ws]=name
        self.scoreboard[name]=0
        
        await ws.send(encode({"type": "hello_ack", "name": name}))
        await self.announce_state()
        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except Exception:
                    continue

                t = msg.get("type")

                if t == "buzz":
                    if self.phase == "playing" and self.open and self.current_winner is None:
                        winner = self.CLIENTS[ws]
                        self.open=False
                        self.current_winner=winner
                        await self.announce_state()
                    else:
                        pass
                        
        except ConnectionClosed:
            pass
        finally:
            name = self.CLIENTS.pop(ws, None)
            if name:
                if name == self.current_winner:
                    self.current_winner = None
                    self.open = True
            await self.announce_state()
            
    async def end_game(self):
        print("Game Ended. Back to Main Menu.")
        self.phase = "end_game"
        self.open = False
        self.current_winner = None
        print("[end] Back to lobby — buzzers CLOSED.")
        
        await self.broadcast({"type": "game_end"})
        
        for ws in list(self.CLIENTS.keys()):
            try:
                await ws.close(code=1001, reason="Server shutting down")
            except Exception:
                pass
        await asyncio.sleep(0.2)
        
        if hasattr(self, "_stop") and self._stop and not self._stop.done():
            self._stop.set_result(None)

        if self._result and not self._result.done():
            self._result.set_result(self.leaderboard)

        # POST REQUEST TO API TO END GAME SESSION AND SAVE SCORES
        # print(self.scoreboard)
        self.api.endGameSession(self.game_id, self.scoreboard)

        return self.leaderboard

   

    async def console(self):
        loop = asyncio.get_running_loop()
        input_task = None
        def draw_logo():
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
        def spawn_input():
            # --- 2. THE CHANGE ---
            # Use msvcrt.getch() to read a single character
            return loop.run_in_executor(None, msvcrt.getch)

        while True:
            # 1. RENDER
            clear_screen()
            draw_logo()
            if self.phase == "lobby":
                print(
                    f"Join Game at {self.ip}/8891\n"
                    "\nLobby commands:\n"
                    "  s : start game (opens Q1 buzzers)\n"
                    "  q : quit server\n"
                )
                print("Current Question Set:",self.qset_name)
                players = list(self.CLIENTS.values())
                print("\nCurrent participants:")
                for name in players:
                    print("  •", name)
                print("> ", end="", flush=True) 
            
            elif self.phase == "playing":
                print("Current Question is:", self.qset[self.q_idx])
                print("Current score and player")
                if self.leaderboard:
                    for score,name in self.leaderboard:
                       print(f"  {name}: {score}")
                else:
                    print("  (no scores yet)")
                
                winner = self.current_winner
                if winner is None:
                    print(
                        "\nBuzzers are OPEN. Waiting for a buzz...\n"
                        "  q : quit server\n"
                    )
                else:
                    print(
                        f"\nWinner: {winner}\n"
                        f"Please check in person if {winner}'s answer is correct.\n"
                        "Playing commands:\n"
                        "  y : correct → next question (opens buzzers)\n"
                        "  n : incorrect → redo same question (re-opens buzzers)\n"
                        "  q : quit server\n"
                    )
                print("> ", end="", flush=True)

            # 2. WAIT
            if input_task is None or input_task.done():
                input_task = spawn_input()

            ui_task = asyncio.create_task(self._server_dirty.wait())
            
            done, pending = await asyncio.wait(
                {input_task, ui_task}, 
                timeout=0.5,
                return_when=asyncio.FIRST_COMPLETED
            )
            ui_task.cancel()

            # 3. HANDLE STATE CHANGE
            if ui_task in done or self._server_dirty.is_set():
                self._server_dirty.clear()
                continue 

            # 4. HANDLE TIMEOUT
            if not done:
                continue 

            # 5. HANDLE KEYBOARD INPUT
            key_bytes = input_task.result() # This is now a byte string (e.g., b's')
            input_task = None
            try:
                cmd = key_bytes.decode('utf-8').strip().lower() # Decode it
            except UnicodeDecodeError:
                cmd = "" # Ignore special keys
            
            # 6. PROCESS
            if self.phase == "lobby":
                if cmd == "s":
                    self.phase = "playing"
                    self.q_idx = 0
                    self.open = True
                    self.current_winner = None
                    await self.broadcast({"type": "post_question", "question": self.qset[self.q_idx]})
                    await self.announce_state()
                    
                elif cmd == "q":
                    return await self.end_game()
            
            elif self.phase == "playing":
                winner = self.current_winner
                
                if winner is None:
                    if cmd == "q":
                        return await self.end_game()
                
                else:
                    if cmd == "y":
                        self.scoreboard[self.current_winner]+=1
                        self.leaderboard = sorted(
                            [(score, name) for name, score in self.scoreboard.items()],
                            reverse=True
                        )
                        if self.q_idx!=len(self.qset)-1:
                            self.q_idx += 1
                            self.open = True
                            self.current_winner = None
                            await asyncio.sleep(1)
                            await self.broadcast({"type": "post_question", "question": self.qset[self.q_idx]})
                            await self.announce_state()
                        else:
                            await self.announce_state()
                            return await self.end_game()
                    elif cmd == "n":
                        self.open = True
                        self.current_winner = None
                        await self.announce_state()
                    elif cmd == "q":
                        return await self.end_game()

    async def run(self, port=8891):
        loop = asyncio.get_running_loop()
        self._stop = loop.create_future()
        self._result = loop.create_future()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._stop.set_result, None)
            except NotImplementedError:
                pass

        async with serve(self.handle_client, "0.0.0.0", port, ping_interval=20, ping_timeout=20):
            print(f"Host server listening on ws://{self.ip}:{port}")
            print("Please log in first.")
            print("Go to 'Join a Game' and enter the host information.")

            console_task = asyncio.create_task(self.console())

            done, pending = await asyncio.wait(
                {self._stop, self._result, console_task}, 
                return_when=asyncio.FIRST_COMPLETED
            )
            if self._result in done:
                result = self._result.result()
            else:
                result = await self.end_game()

            for t in pending:
                t.cancel()
            await asyncio.gather(console_task, return_exceptions=True)

        return result