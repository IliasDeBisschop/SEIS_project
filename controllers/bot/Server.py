import socket
import threading

# Serverconfiguratie
HOST = '127.0.0.1'  # Luister op localhost
PORT = 65432        # Kies een poortnummer

# Drempelafstand voor het aanpassen van de snelheid
THRESHOLD_DISTANCE = 1.0  # in meters
DEFAULT_SPEED = 6.67      # standaard snelheid
REDUCED_SPEED = 0         # verlaagde snelheid

def handle_client(conn, addr):
    """Verwerk een inkomende verbinding."""
    print(f"Verbonden met {addr}")
    with conn:
        while True:
            data = conn.recv(1024)  # Ontvang gegevens (max 1024 bytes)
            if not data:
                print(f"Verbinding met {addr} verbroken.")
                break
            
            # Decodeer de ontvangen afstand
            try:
                distance = float(data.decode('utf-8'))
                print(f"[{addr}] Ontvangen afstand: {distance} meter")
                
                # Beslis de snelheden op basis van de afstand
                if distance < THRESHOLD_DISTANCE:
                    left_speed = REDUCED_SPEED
                    right_speed = REDUCED_SPEED
                    print(f"[{addr}] Afstand onder drempel, snelheden verlaagd.")
                else:
                    left_speed = DEFAULT_SPEED
                    right_speed = DEFAULT_SPEED
                    print(f"[{addr}] Afstand boven drempel, standaard snelheden.")

                # Stuur de snelheden terug naar de robot
                conn.sendall(f"{left_speed},{right_speed}".encode('utf-8'))
            except ValueError:
                print(f"[{addr}] Ongeldige gegevens ontvangen.")

# Maak een socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Server luistert op {HOST}:{PORT}...")

    while True:
        conn, addr = server_socket.accept()
        # Start een nieuwe thread voor elke client
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()