#!/usr/bin/env python3
# main_server.py
import asyncio
import argparse
from game_server import game

async def amain():
    parser = argparse.ArgumentParser(description="Run quiz server")
    parser.add_argument("--port", type=int, default=8891, help="Port to listen on (default: 8891)")
    args = parser.parse_args()

    qset = ["Capital of France?", "2 + 2 = ?", "Largest ocean?"]
    g = game(qset_name="test", qset=qset)

    # Run a single session; returns scoreboard (name -> score)
    scoreboard = await g.run(port=args.port)

    # Pretty-print final results
    print("\n=== FINAL SCOREBOARD ===")
    for name, score in sorted(scoreboard.items(), key=lambda x: x[1], reverse=True):
        print(f"{name}: {score}")
    print("========================\n")

if __name__ == "__main__":
    asyncio.run(amain())