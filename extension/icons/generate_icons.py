import os
import cairosvg

def generate_icons():
    sizes = [16, 48, 128]
    svg_path = os.path.join(os.path.dirname(__file__), 'icon.svg')
    
    for size in sizes:
        output_path = os.path.join(os.path.dirname(__file__), f'icon{size}.png')
        cairosvg.svg2png(
            url=svg_path,
            write_to=output_path,
            output_width=size,
            output_height=size
        )
        print(f"Generated {size}x{size} icon: {output_path}")

if __name__ == "__main__":
    generate_icons() 