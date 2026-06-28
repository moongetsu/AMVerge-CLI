"""Discord Rich Presence integration.

Shows how to use the DiscordRPC class for live status updates.
Uses the same application ID as the AMVerge desktop app, so your
status appears under "Playing AMVerge" in Discord.

Usage:
    pip install amverge[discord]
    python 01_basic_rpc.py
"""

import time
from amverge import RPC_AVAILABLE, DiscordRPC

if not RPC_AVAILABLE:
    print("pypresence not installed. Run: pip install amverge[discord]")
    print("This example will not show any Discord status.")
    exit(0)

print("Connecting to Discord...")
rpc = DiscordRPC()
rpc.connect()

print("Setting status to 'Detecting'...")
rpc.update_detecting("episode.mp4")

time.sleep(3)

print("Setting status to 'Exporting'...")
rpc.update_exporting("episode.mp4")

time.sleep(3)

print("Setting status to 'Complete'...")
rpc.update_complete()

time.sleep(2)

rpc.clear_presence()
rpc.disconnect()
print("Done. Check your Discord status!")
