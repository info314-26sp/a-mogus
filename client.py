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
    if len(sys.argv) < 3:
        print("Usage: client.py <color> <role>")
        sys.exit(1)

    color = sys.argv[1]
    role = sys.argv[2]

    print(f"\n[client] Started as '{color}' ({role})")

    # TODO: reconnect to server here for actual game loop
    # currently to test im just showing the player their menu so i can see if this even works
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_HOST, SERVER_PORT))
    # reconnected, but next steps should be the following:
        # get the game state (await STATE)
        # tell user to pick action (differentiate between imposter and crewmate again)
        # depending on what they choose, present followup things (e.g. if they choose to move, where are they moving to?, if we implement task, how does that work? etc.)
        # send player responses to server
        # wait for the round result and then maybe just close sock? idk what else cause game loop is in server

    show_menu(role)
    print("\n(not implemented yet)")


if __name__ == "__main__":
    main()
