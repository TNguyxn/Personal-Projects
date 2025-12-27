#!/usr/bin/env python3
# game_client.py
import asyncio
import json
from websockets.client import connect
from websockets.exceptions import ConnectionClosed
import os
import msvcrt  # Use msvcrt

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
def encode(msg: dict) -> str:
    return json.dumps(msg, separators=(",", ":"))

class GameClient:
    def __init__(self, ip, port,name):
        self.server = f"ws://{ip}:{port}"
        self.ws = None
        self.name = name
        self._stop = None   # future resolved when game ends or user quits
        self.phase="lobby"
        self.open=False
        self.current_winner=None
        self.q_idx=0
        self.q_total=0
        self.leaderboard=[]
        self.current_question=""
        self._ui_dirty = asyncio.Event()
    async def _receiver(self):
        try:
            async for raw in self.ws:
                try:
                    msg = json.loads(raw)
                except Exception:
                    continue

                t = msg.get("type")

                if t == "state":
                    self.phase = msg.get("phase")
                    self.open = msg.get("open")
                    self.current_winner = msg.get("winner")
                    self.q_idx = msg.get("q_id") or 0
                    self.q_total = msg.get("q_total") or 0
                    self.leaderboard = msg.get("leaderboard", [])
                    self._ui_dirty.set()
                elif t == "post_question":
                    self.current_question = msg.get("question") or ""
                    self._ui_dirty.set()
                elif t == "buzz_result":
                    self.current_winner = msg.get("winner")
                    self._ui_dirty.set()
                elif t == "game_end":
                    if self._stop and not self._stop.done():
                        self._stop.set_result("ended")
                else:
                    pass
        except ConnectionClosed:
            if self._stop and not self._stop.done():
                self._stop.set_result("disconnected")


    # game_client.py
    async def _console(self):
        # --- THIS IS THE NEW, FIXED CONSOLE LOOP ---
        
        # Start with a clean UI
        self._ui_dirty.set() 
        
        while True:
            # 1. RENDER (if needed)
            if self._ui_dirty.is_set():
                self._ui_dirty.clear()
                clear_screen()
                if self.phase == "lobby":
                    print("Successfully Connected" if self.ws else "Not connected yet")
                    print("Waiting for host to start the game…")
                    print("Commands: q (quit)")
                    print("> ", end="", flush=True) 
                else:
                    print("Leaderboard:")
                    if self.leaderboard:
                        for score, name in self.leaderboard:
                            print(f"  {name}: {score}")
                    else:
                        print("  (no scores yet)")
                    print("\nQuestion:")
                    print(f"  {self.current_question or '(waiting on question)'}\n")
                    if self.open:
                        print("Buzzers are OPEN.")
                        print("Commands: b (buzz), q (quit)")
                    else:
                        if self.current_winner:
                            me = (self.current_winner == self.name)
                            print("Buzzers CLOSED — " + ("You buzzed first!" if me else f"{self.current_winner} buzzed first."))
                        else:
                            print("Buzzers CLOSED.")
                        print("Commands: q (quit)")
                    print("> ", end="", flush=True)

            # 2. CHECK FOR INPUT (non-blocking)
            if msvcrt.kbhit():
                try:
                    key_bytes = msvcrt.getch()
                    cmd = key_bytes.decode('utf-8').strip().lower()
                except UnicodeDecodeError:
                    cmd = "" # Ignore special keys
                
                # --- Process Input ---
                if self.phase == "lobby":
                    if cmd == "q":
                        try:
                            await self.ws.close(code=1000, reason="Client quit")
                        except Exception:
                            pass
                        if self._stop and not self._stop.done():
                            self._stop.set_result("quit")
                        return # Exit console
                
                elif self.phase == "playing":
                    if cmd == "b" and self.open:
                        try:
                            await self.ws.send(encode({"type": "buzz"}))
                        except Exception:
                            if self._stop and not self._stop.done():
                                self._stop.set_result("disconnected")
                            return # Exit console
                    elif cmd == "q":
                        try:
                            await self.ws.close(code=1000, reason="Client quit")
                        except Exception:
                            pass
                        if self._stop and not self._stop.done():
                            self._stop.set_result("quit")
                        return # Exit console

            # 3. YIELD CONTROL
            # Sleep for a tiny duration to let other tasks run.
            # This makes the loop non-blocking and responsive.
            await asyncio.sleep(0.05)


    async def run(self):
        """Connect, play the session, then return control to caller."""
        print("[DEBUG] Client run() started.")
        self._stop = asyncio.get_running_loop().create_future()

        try:
            async with connect(self.server, ping_interval=20, ping_timeout=20) as ws:
                self.ws = ws
                await self.ws.send(encode({"type": "hello", "name": self.name}))
                print("[DEBUG] Client connected, starting tasks...")
                rx = asyncio.create_task(self._receiver(), name="receiver")
                ui = asyncio.create_task(self._console(), name="console")

                # Wait until game ends, user quits, or disconnect
                await self._stop
                print("[DEBUG] _stop Future resolved. Game is ending.")

                # Clean up tasks
                print("[DEBUG] Cancelling UI and Receiver tasks...")
                for t in (rx, ui):
                    t.cancel()
                await asyncio.gather(rx, ui, return_exceptions=True)
                print("[DEBUG] UI and Receiver tasks are fully cancelled.")

        except OSError as e:
            print(f"[error] Could not connect: {e}")
        except Exception as e:
            print(f"[DEBUG] An unexpected error occurred in run(): {e}")
        finally:
            if self.ws:
                try:
                    await self.ws.close()
                except Exception:
                    pass
                self.ws = None
            print("[DEBUG] Client run() is finished. Returning to menu.")

        return self.leaderboard