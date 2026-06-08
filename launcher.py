import os
import socket
import sys
import time
import subprocess

# switched the os.exec to subprocess and popen (after MUCH research...)
# docs for reference: https://docs.python.org/3/library/subprocess.html#popen-objects
# 

def main():
    # had to look this up and use a bit of ai cause i didnt know how to make host using host IP
    # basically, host will have to find their local IP address (LOL) and then everyone uses that to hop on game
    raw = input("Enter server IP (or press Enter for localhost): ").strip() or "localhost"
    if ":" in raw:
        SERVER_HOST, port = raw.split(":")
        SERVER_PORT = int(port)
    else:
        SERVER_HOST = raw
        SERVER_PORT = 8080


    print("[launcher] Connecting to server...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_HOST, SERVER_PORT))

    # send CONNECT
    sock.sendall(b"CONNECT\n")
    print("[launcher] Sent: CONNECT")

    # await ASSIGN
    data = sock.recv(1024).decode().strip()
    print(f"[launcher] Received: {data}")

    if data.startswith("ERROR"):
        print(f"[launcher] Server rejected connection: {data}")
        sock.close()
        return

    if not data.startswith("ASSIGN"):
        print(f"[launcher] Unexpected message: {data}")
        sock.close()
        return

    # parse ASSIGN color=red role=crew
    parts = dict(p.split("=") for p in data.split()[1:])
    color = parts["color"]
    role = parts["role"]
    print(f"[launcher] You are '{color}', role: '{role}'")

    # send CONFIRMROLE
    confirm_msg = f"CONFIRMROLE color={color} role={role}\n"
    sock.sendall(confirm_msg.encode())
    print(f"[launcher] Sent: {confirm_msg.strip()}")

    # await WAIT (or, though i hope not, ERROR)
    data = sock.recv(1024).decode().strip()
    print(f"[launcher] Received: {data}")

    if data.startswith("ERROR"):
        print(f"[launcher] Server error: {data}")
        sock.close()
        return

    # await game start message
    data = sock.recv(1024).decode().strip()
    print(f"[launcher] Received: {data}")
    print(f"\n{data}\n")

    #removed and replaced with os.execvp which just transfers the connection over to the client
    # sock.close()

    # launch the client scripts
    # pass color and role as commandline args so the client knows who it is
    fd = sock.fileno()
    os.set_inheritable(fd, True)


    if role == "imposter":
        print("[launcher] Launching imposter client...")
        process = subprocess.Popen(
            [sys.executable, "client.py", color, role, str(fd)],
            close_fds=False,
            #had to use AI to debug the need for the following three lines to connect directly to terminal
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        process.wait()
    else:
        print("[launcher] Launching crewmate client...")
        process = subprocess.Popen(
            [sys.executable, "client.py", color, role, str(fd)],
            close_fds=False,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        process.wait()
if __name__ == "__main__":
    main()
