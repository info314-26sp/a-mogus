import socket
import sys

SERVER_HOST = "localhost"
SERVER_PORT = 8080

# action selection menu things 
CREWMATE_ACTIONS = ["MOVE", "TASK", "WAIT", "EMERGENCY"]
IMPOSTER_ACTIONS  = ["MOVE", "KILL", "SABOTAGE", "VENT", "WAIT"]

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

    show_menu(role)
    print("\n(not implemented yet)")


if __name__ == "__main__":
    main()
