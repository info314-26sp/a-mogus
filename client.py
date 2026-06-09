import socket
import sys

SERVER_HOST = "localhost"
SERVER_PORT = 8080

# action selection menu things 
CREWMATE_ACTIONS = ["MOVE", "TASK", "WAIT", "EMERGENCY"] # are we still doing task? forgot what the convo ended up being
IMPOSTER_ACTIONS  = ["MOVE", "KILL", "SABOTAGE", "VENT", "WAIT"] # remove vent? determine what sabotage does/implement it

def show_menu(role):
    """Print available actions based on role."""
    actions = IMPOSTER_ACTIONS if role == "imposter" else CREWMATE_ACTIONS
    print("\n--- Your Actions ---")
    for i, action in enumerate(actions):
        print(f"  {i + 1}. {action}")
    print("--------------------")


def main():
    if len(sys.argv) < 4:
        print("Usage: client.py <color> <role> <socket_fd>")
        sys.exit(1)

    color = sys.argv[1]
    role = sys.argv[2]
    sock_fd = int(sys.argv[3])

    print(f"\n[client] Started as '{color}' ({role})")

    sock = socket.socket(fileno=sock_fd)

    # TODO: reconnect to server here for actual game loop
    # currently to test im just showing the player their menu so i can see if this even works
    # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.connect((SERVER_HOST, SERVER_PORT))
    # reconnected, but next steps should be the following:
        # get the game state (await STATE)
        # tell user to pick action (differentiate between imposter and crewmate again)
        # depending on what they choose, present followup things (e.g. if they choose to move, where are they moving to?, if we implement task, how does that work? etc.)
        # send player responses to server
        # wait for the round result and then maybe just close sock? idk what else cause game loop is in server
        # ── evil game loop section  ─────
    while True:
        data = sock.recv(4096).decode().strip()

        if data.startswith("STATE"):
            parts = dict(p.split("=") for p in data.split()[1:])
            current_room = parts["room"]
            options = parts["options"].split(",")
            round_num = parts["round"]

            show_map(current_room)
            print(f"Round {round_num}  |  You ({color}) are in: {current_room.upper()}\n")
            print("  0. Stay here (WAIT)")
            for i, room in enumerate(options, 1):
                print(f"  {i}. Move to {room}")

            print("Press the number corresponding to your move choice, or 0 to wait. Then press Enter.")
            choice = input("\nYour move: ").strip()

            if choice == "0" or not choice:
                sock.sendall(b"WAIT\n")
            else:
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(options):
                        sock.sendall(f"MOVE {options[idx]}\n".encode())
                    else:
                        print("Invalid — waiting.")
                        sock.sendall(b"WAIT\n")
                except ValueError:
                    print("Invalid — waiting.")
                    sock.sendall(b"WAIT\n")

        elif data.startswith("ROUND_RESULT"):
            idx = data.find("events=")
            events_str = data[idx + 7:] if idx >= 0 else ""
            print("\n── What happened ──────────────────────")
            for event in events_str.split(";"):
                print(f"  {event}")
            print("───────────────────────────────────────\n")

        elif not data:
            print("Disconnected.")
            break

# Helper function to display the map with the current room highlighted
def show_map(current_room):
    def fmt(name):
        return f"*{name.upper()}*" if name == current_room else name

    print(f"\n{'─' * 48}")
    print(f"  {fmt('cafeteria')} ─── {fmt('hallway')} ─── {fmt('reactor')}")
    print(f"                        │")
    print(f"                     {fmt('medbay')} ─── {fmt('electrical')}")
    print(f"{'─' * 48}\n")


if __name__ == "__main__":
    main()
