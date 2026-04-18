"""Generate a sample MJPEG video file for the streaming lab.

Creates movie.Mjpeg with synthetic frames: each frame is a JPEG image
with a colored background and frame number overlay. The file format uses
a 5-byte ASCII length prefix before each JPEG frame.

Usage: python generate_mjpeg.py
"""

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import math
import os


def create_frame(frame_num, total_frames, width=320, height=240):
    """Generate a single JPEG frame with dynamic content."""
    # Cycle through colors based on frame number
    phase = frame_num / total_frames
    r = int(127 + 127 * math.sin(2 * math.pi * phase))
    g = int(127 + 127 * math.sin(2 * math.pi * phase + 2.094))
    b = int(127 + 127 * math.sin(2 * math.pi * phase + 4.189))

    img = Image.new('RGB', (width, height), (r, g, b))
    draw = ImageDraw.Draw(img)

    # Draw a moving circle
    cx = int(width * (0.2 + 0.6 * math.sin(2 * math.pi * phase)))
    cy = int(height * (0.3 + 0.4 * math.cos(2 * math.pi * phase)))
    radius = 30
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill='white', outline='black', width=2
    )

    # Draw frame number text
    text = f"Frame {frame_num}"
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except (IOError, OSError):
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (width - tw) // 2
    ty = height - th - 20
    draw.text((tx, ty), text, fill='white', font=font)

    # Draw border
    draw.rectangle([0, 0, width - 1, height - 1], outline='white', width=2)

    # Convert to JPEG bytes
    buf = BytesIO()
    img.save(buf, format='JPEG', quality=75)
    return buf.getvalue()


def main():
    total_frames = 500  # ~25 seconds at 20 fps
    output_file = os.path.join(os.path.dirname(__file__), "movie.Mjpeg")

    print(f"Generating {total_frames} frames...")
    with open(output_file, 'wb') as f:
        for i in range(1, total_frames + 1):
            jpeg_data = create_frame(i, total_frames)
            # Write 5-byte length prefix (ASCII, zero-padded)
            length_str = f"{len(jpeg_data):05d}"
            f.write(length_str.encode('ascii'))
            f.write(jpeg_data)
            if i % 50 == 0:
                print(f"  Generated frame {i}/{total_frames}")

    file_size = os.path.getsize(output_file) / 1024
    print(f"Done! Created {output_file} ({file_size:.0f} KB, "
          f"{total_frames} frames)")


if __name__ == "__main__":
    main()
