import socket
import threading
import random

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

COLORS = ["red", "blue", "green", "yellow", "purple", "orange"]


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
        players[color] = {"conn": conn, "role": None, "confirmed": False}
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

    conn.sendall(b"MSG text=All players confirmed. Game starting!\n")
    print(f"[server] All players confirmed. Game ready!")

    # TODO: start game loop (how tf...)


def main():
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
