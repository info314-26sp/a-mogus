How to Run
Requirements: Python 3, at least 3 players (configurable via MIN_PLAYERS in server.py)
1. Start the server
On the host machine, run:
python server.py
The server will print a local IP and port (e.g. 192.168.1.5:8080). Share this with all players.
2. Each player launches the game
Every player (including the host if they're playing) runs:
python launcher.py
When prompted, enter the IP from step 1, or just press Enter to use localhost if everyone is on the same machine.
3. Wait for the lobby
Once 3 players have connected, roles are assigned automatically. Each player will be told their color and whether they're crew or imposter.
4. Play
Each round, you'll see the map with your current location highlighted and a numbered list of rooms to move to. Enter a number and press Enter to move, or 0 to wait.

Testing locally: Open 3 separate terminals on the same machine, start the server in one, and run launcher.py in each of the other two (plus one more if the host is also playing). Use localhost for the IP on all of them.

Link to Proposal
https://docs.google.com/document/d/1R3IeVOisjw1Q1rUK3ScaNMAIc993Os-xqN9vzOpsJww/edit?usp=sharing 