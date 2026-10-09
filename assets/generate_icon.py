from pathlib import Path
from math import cos, pi, sin

from PIL import Image, ImageDraw


SIZE = 512
HERE = Path(__file__).resolve().parent

image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)

draw.rounded_rectangle((24, 24, 488, 488), radius=106, fill="#1b3027")
draw.rounded_rectangle(
    (105, 85, 397, 430), radius=32, outline="#ffffff", width=28,
)
for y, right in ((219, 310), (287, 335), (355, 292)):
    draw.rounded_rectangle((157, y, right, y + 23), radius=11, fill="#ffffff")

center_x, center_y = 382, 125
points = []
for index in range(10):
    angle = -pi / 2 + index * pi / 5
    radius = 66 if index % 2 == 0 else 30
    points.append((center_x + radius * cos(angle),
                   center_y + radius * sin(angle)))
draw.ellipse((310, 53, 454, 197), fill="#1b3027")
draw.polygon(points, fill="#f6ca68")

image.save(HERE / "boletim.png")
image.save(HERE / "boletim.ico", sizes=[(16, 16), (24, 24), (32, 32),
                                      (48, 48), (64, 64), (128, 128),
                                      (256, 256)])
