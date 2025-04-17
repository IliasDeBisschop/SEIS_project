import socket
from controller import Robot

robot = Robot()

possible_devices = [
    "LDS-01", "left wheel motor", "right wheel motor"]
timestep = int(robot.getBasicTimeStep())

# Activeer de LiDAR-sensor
lds = robot.getDevice("LDS-01")
lds.enable(timestep)

# Zoek de twee motoren (kan verschillen per robot)
left_motor = robot.getDevice("left wheel motor")
right_motor = robot.getDevice("right wheel motor")

# Zet motoren op velocity mode
left_motor.setPosition(float('inf'))
right_motor.setPosition(float('inf'))

# Socketconfiguratie
HOST = '127.0.0.1'  # Serveradres
PORT = 65432        # Poortnummer

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect((HOST, PORT))
    print(f"Verbonden met server op {HOST}:{PORT}")

    # Laat de simulatie lopen
    while robot.step(timestep) != -1:
        # Uitlezen van sensorgegevens
        range_image = lds.getRangeImage()  # Haal de afstandswaarden op
        
        # Pak alleen de afstand recht voor de robot (middelste waarde)
        front_distance = range_image[len(range_image) // 2]
        print("Afstand vooraan:", front_distance)
        
        # Stuur de afstand naar de server
        client_socket.sendall(f"{front_distance}".encode('utf-8'))
        
        # Ontvang de snelheden van de server
        data = client_socket.recv(1024)
        if not data:
            print("Verbinding met server verbroken.")
            break
        
        # Pas de snelheden toe op de motoren
        try:
            # Verwacht een string in het formaat "left_speed,right_speed"
            print("Ontvangen snelheden van server:", data.decode('utf-8'))
            speeds = data.decode('utf-8').split(',')
            left_speed = float(speeds[0])
            right_speed = float(speeds[1])
            
            left_motor.setVelocity(left_speed)
            right_motor.setVelocity(right_speed)
            print(f"Nieuwe snelheden ontvangen: left={left_speed}, right={right_speed}")
        except (ValueError, IndexError):
            print("Ongeldige snelheden ontvangen.")