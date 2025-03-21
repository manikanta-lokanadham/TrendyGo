import os
from PIL import Image, ImageDraw, ImageFont
import textwrap

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def create_placeholder_image(width, height, text, output_path, bg_color=(240, 240, 240)):
    # Create a new image with a light gray background
    image = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, fallback to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    # Calculate text position to center it
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Draw the text
    draw.text((x, y), text, fill=(100, 100, 100), font=font)
    
    # Save the image
    image.save(output_path)

def main():
    # Create static/images directory if it doesn't exist
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    images_dir = os.path.join(static_dir, 'images')
    create_directory(images_dir)
    
    # Generate placeholder images
    images = [
        ('logo.png', 200, 50, 'LOGO'),
        ('hero1.jpg', 1920, 500, 'HERO 1'),
        ('hero2.jpg', 1920, 500, 'HERO 2'),
        ('no-image.png', 400, 400, 'NO IMAGE'),
        ('default-profile.png', 150, 150, 'PROFILE'),
    ]
    
    for filename, width, height, text in images:
        output_path = os.path.join(images_dir, filename)
        create_placeholder_image(width, height, text, output_path)
        print(f"Created {filename}")

if __name__ == '__main__':
    main() 