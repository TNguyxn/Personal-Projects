#!/usr/bin/env python3
# main_client.py
import asyncio
import argparse
from client.rapidfire.game_client import GameClient

async def amain():
    parser = argparse.ArgumentParser(description="Run quiz client")
    parser.add_argument("--ip", required=True, help="Host IP (LAN IP shown by the server)")
    parser.add_argument("--port", type=int, default=8891, help="Host port (default: 8891)")
    parser.add_argument("--name", required=True, help="Your display name")
    args = parser.parse_args()

    client = GameClient(ip=args.ip, port=args.port,name=args.name)
    last_state = await client.run()

    # Show whatever the client kept as the last known state (optional)
    print("\nBack to main menu.")
    if last_state:
        print("Last known state:", last_state)

if __name__ == "__main__":
    asyncio.run(amain())
