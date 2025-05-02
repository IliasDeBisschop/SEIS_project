import os

# Define the list of (z, y) coordinates

def genrate_coordinates():
    coordinates = []
    for i in range(15):
        for j in range(10):
            if i == 6: continue
            if i == 7: continue
            if i == 8: continue
            coordinates.append((i*0.6-4.2, j*0.6-1.8))
    return coordinates

# Path to the Webots world file
# world_file_path = r"c:\Users\dmsep\Documents\school\SEIS_project\worlds\seis_project.wbt"
world_file_path = r"C:\Users\ilias\Desktop\School\2024-2025\sem2\SEIS\taak\SEIS_project\worlds\seis_project.wbt"


# Function to generate Wall nodes
def generate_wall_nodes(coordinates):
    nodes = []
    for z, y in coordinates:
        node = f"""
Wall {{
  translation {y} {z} 0
  size 0.6 0.3 0.5
  rotation 0 0 1 1.5708  # Rotates the wall 90 degrees around the Z-axis
  appearance PBRAppearance {{
    baseColor 0.5 0.5 0.5
  }}
}}
"""
        nodes.append(node)
    return "\n".join(nodes)

# Generate coordinates
coordinates = genrate_coordinates()

# Read the existing world file
with open(world_file_path, "r") as file:
    world_content = file.readlines()

# Find the insertion point for the new walls
insertion_index = len(world_content)  # Default to appending at the end
for i, line in enumerate(world_content):
    if "TexturedBackground {" in line:  # Insert before this section
        insertion_index = i
        break

# Generate the new wall nodes
wall_nodes = generate_wall_nodes(coordinates)

# Insert the new nodes into the world file content
updated_content = (
    world_content[:insertion_index]
    + [wall_nodes]
    + world_content[insertion_index:]
)

# Write the updated content back to the world file
with open(world_file_path, "w") as file:
    file.writelines(updated_content)

print("Walls have been placed at the specified coordinates!")