from PIL import Image

def reduce_image_resolution(input_path, output_path, block_size=25):
    # Open the image
    img = Image.open(input_path).convert("L")  # Convert to grayscale
    width, height = img.size

    # Calculate new dimensions
    new_width = width // block_size
    new_height = height // block_size

    # Create a new image for the reduced resolution
    reduced_img = Image.new("L", (new_width, new_height))

    # Process each block
    for y in range(new_height):
        for x in range(new_width):
            # Get the block of pixels
            block = img.crop((
                x * block_size,
                y * block_size,
                (x + 1) * block_size,
                (y + 1) * block_size
            ))

            # Calculate the average brightness
            avg_brightness = sum(block.getdata()) / (block_size * block_size)

            # Determine the color (white if light, black if dark)
            color = 255 if avg_brightness > 127 else 0

            # Set the pixel in the reduced image
            reduced_img.putpixel((x, y), color)

    # Save the reduced image
    reduced_img.save(output_path)

# Example usage
input_image_path = "output_image_processed.jpg"  # Replace with your input image path
output_image_path = "output_image.png"  # Replace with your desired output path
reduce_image_resolution(input_image_path, output_image_path)