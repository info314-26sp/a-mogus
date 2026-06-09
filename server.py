import socket
import threading
import random
import time
from collections import Counter

# AI assitance used for the IP config thing so host just has to copy paste the IP instead of looking it up themselves
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
print(f"[server] Share this with players: {local_ip}:8080")

# num players that have to join before game starts
# i put it at 3 rn to test easier (only need 3 terminals open) but we can change later 
MIN_PLAYERS = 3

# game state
# for players: color -> { "conn": ..., "role": ..., "confirmed": False }
players = {}      
players_lock = threading.Lock()
game_ready = threading.Event()

COLORS = ["red", "blue", "green", "yellow", "purple", "orange"]

'''
EDIT: updated to make it so that its more branching and allows 
for the new game to be played well, disregard below comment


this is the current map layout bc i say so

cafeteria ── hallway ── reactor
               │
             medbay ── electrical
'''
MAP = {
    "cafeteria":   ["hallway_a", "hallway_b"],
    "hallway_a":   ["cafeteria", "reactor", "medbay"],
    "hallway_b":   ["cafeteria", "weapons", "electrical"],
    "reactor":     ["hallway_a", "storage"],
    "medbay":      ["hallway_a", "storage"],
    "weapons":     ["hallway_b", "nav"],
    "electrical":  ["hallway_b", "nav"],
    "storage":     ["reactor", "medbay"],
    "nav":         ["weapons", "electrical"],
}

STARTING_ROOM = "cafeteria"

def handle_client(conn, addr):
    """One thread per connected client."""
    print(f"[server] Connection from {addr}")

    # await CONNECT message
    data = conn.recv(1024).decode().strip()
    if not data.startswith("CONNECT"):
        conn.sendall(b"ERROR invalid first message\n")
        conn.close()
        return

    # assign color to player that joined
    with players_lock:
        used_colors = set(players.keys())
        available = [c for c in COLORS if c not in used_colors]

        if not available:
            conn.sendall(b"ERROR lobby is full\n")
            conn.close()
            return

        color = random.choice(available)
        players[color] = {"conn": conn, "role": None, "confirmed": False, "room": STARTING_ROOM, "alive": True}
        current_count = len(players)

    print(f"[server] Assigned color '{color}' to {addr}. Players: {current_count}")

    # ensure enough players before assigning things
    while True:
        with players_lock:
            if len(players) >= MIN_PLAYERS:
                break

    # assign imposter/crewmate
    # first thread assigns all roles
    with players_lock:
        unassigned = [c for c, p in players.items() if p["role"] is None]
        if unassigned:
            # random imposter
            imposter_color = random.choice(unassigned)
            for c in unassigned:
                players[c]["role"] = "imposter" if c == imposter_color else "crew"

    # send player ASSIGN
    with players_lock:
        role = players[color]["role"]

    msg = f"ASSIGN color={color} role={role}\n"
    conn.sendall(msg.encode())
    print(f"[server] Sent to {color}: {msg.strip()}")

    # await CONFIRMROLE
    data = conn.recv(1024).decode().strip()
    print(f"[server] Received from {color}: {data}")

    if data.startswith("CONFIRMROLE"):
        # verify it looks llike below
        # expected: CONFIRMROLE color=red role=crew
        parts = dict(p.split("=") for p in data.split()[1:])
        if parts.get("color") == color and parts.get("role") == role:
            with players_lock:
                players[color]["confirmed"] = True
            conn.sendall(b"WAIT\n")
            print(f"[server] {color} confirmed their role. Sending WAIT.")
        else:
            conn.sendall(b"ERROR confirmrole mismatch\n")
    else:
        conn.sendall(b"ERROR expected CONFIRMROLE\n")

    # await all confirmations and then start game
    while True:
        with players_lock:
            all_confirmed = all(p["confirmed"] for p in players.values())
            if all_confirmed:
                break


    # set lobby_done for this player and check if all are done
    with players_lock:
        players[color]["lobby_done"] = True
        if all(p.get("lobby_done") for p in players.values()):
            game_ready.set()
    



def game_loop():
    game_ready.wait()

    # send start message to everyone
    with players_lock:
        for p in players.values():
            p["conn"].sendall(b"MSG text=All players confirmed. Game starting!\n")

    time.sleep(1)  # let clients receive the start msg before round 1

    round_num = 1
    while True:
        print(f"[server] === Round {round_num} ===")

        # snapshot so we're not holding the lock during network I/O
        with players_lock:
            snapshot = {c: {"room": p["room"], "conn": p["conn"]}
                        for c, p in players.items()}

        # send each player their STATE with valid move options
        for color, p in snapshot.items():
            room = p["room"]
            options = ",".join(MAP[room])
            msg = f"STATE color={color} room={room} options={options} round={round_num}\n"
            try:
                p["conn"].sendall(msg.encode())
            except Exception as e:
                print(f"[server] {color} disconnected during state send: {e}")

        # collect one action from each player (blocking)
        actions = {}
        dead = []
        for color, p in snapshot.items():
            try:
                data = p["conn"].recv(1024).decode().strip()
                actions[color] = data
                print(f"[server] {color}: {data}")
            except Exception as e:
                print(f"[server] lost {color}: {e}")
                dead.append(color)

        with players_lock:
            for color in dead:
                players.pop(color, None)

        # only process actions for still-connected players
        actions = {c: a for c, a in actions.items() if c not in dead}

        # resolve
        events = []
        for color, action in actions.items():
            current = snapshot[color]["room"]
            if action.startswith("MOVE"):
                parts = action.split()
                target = parts[1] if len(parts) >= 2 else ""
                if target in MAP.get(current, []):
                    with players_lock:
                        players[color]["room"] = target
                    events.append(f"{color} moved to {target}")
                else:
                    events.append(f"{color} stayed in {current}")
            else:
                events.append(f"{color} waited in {current}")

            #everyone in a room with 2 people in it gets eliminated            
        room_counts = Counter(players[c]["room"] for c in players if players[c].get("alive", True))
        for room, count in room_counts.items():
            if count == 2:
                tagged = [c for c in players if players[c]["room"] == room and players[c].get("alive", True)]
                for c in tagged:
                    players[c]["alive"] = False
                    events.append(f"{c} was eliminated in {room}!")
        alive_players = [c for c in players if players[c].get("alive", True)]
        if len(alive_players) <= 1:
            winner = alive_players[0] if alive_players else "nobody"
            events.append(f"{winner} wins!")
            result_msg = f"ROUND_RESULT round={round_num} events={';'.join(events)}\n"
            for p in snapshot.values():
                try: p["conn"].sendall(result_msg.encode())
                except: pass
            return
        # redoing snapshot so that the status is actually updated
        with players_lock:
            updated_snapshot = {c: {"room": p["room"], "conn": p["conn"]}
                for c, p in players.items()}
        # broadcast results
        events_str = ";".join(events)
        result_msg = f"ROUND_RESULT round={round_num} events={events_str}\n"
        dead = []
        for color, p in updated_snapshot.items():
            try:
                if not players[color].get("alive", True):
                    continue
                p["conn"].sendall(result_msg.encode())
            except Exception as e:
                print(f"[server] {color} disconnected during result: {e}")
                dead.append(color)

        with players_lock:
            for color in dead:
                players.pop(color, None)

        print(f"[server] Round {round_num} done: {events_str}")
        time.sleep(10)  # wait 10 seconds before next round
        round_num += 1


def main():
    game_thread = threading.Thread(target=game_loop, daemon=True)
    game_thread.start()

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(("", 8080))
    server_sock.listen(10)
    print(f"[server] Listening on port 8080. Waiting for {MIN_PLAYERS} players...")

    while True:
        conn, addr = server_sock.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr))
        t.daemon = True
        t.start()


if __name__ == "__main__":
    main()
