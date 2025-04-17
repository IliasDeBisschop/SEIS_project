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

# Stel snelheid in
speed = 6.67  # pas aan naar wens

left_motor.setVelocity(speed)
right_motor.setVelocity(speed)

# Drempelafstand voor het detecteren van een muur (in meters)
threshold_distance = 1.0  # pas aan naar wens

# Laat de simulatie lopen
while robot.step(timestep) != -1:
    # Uitlezen van sensorgegevens
    range_image = lds.getRangeImage()  # Haal de afstandswaarden op
    
    # Pak alleen de afstand recht voor de robot (middelste waarde)
    front_distance = range_image[len(range_image) // 2]
    print("Afstand vooraan:", front_distance)
    
    # Controleer of de afstand onder de drempelafstand ligt
    if front_distance < threshold_distance:
        # Stop de robot als er een muur wordt gedetecteerd
        left_motor.setVelocity(0)
        right_motor.setVelocity(0)
        print("Muur recht voor! Robot gestopt.")
        break
    else:
        # Blijf rijden als er geen muur is
        left_motor.setVelocity(speed)
        right_motor.setVelocity(speed)