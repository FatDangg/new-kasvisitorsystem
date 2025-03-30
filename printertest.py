from PIL import Image, ImageDraw, ImageFont
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
from brother_ql.raster import BrotherQLRaster

# === Create a label image ===
label_text = "Welcome to KAS!"
width, height = 696, 100  # ~6.7mm = short label
image = Image.new('RGB', (width, height), 'white')
draw = ImageDraw.Draw(image)

try:
    font = ImageFont.truetype("arial.ttf", 100)
except:
    font = ImageFont.load_default()

bbox = draw.textbbox((0, 0), label_text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
text_position = ((width - text_width) // 2, (height - text_height) // 2)
draw.text(text_position, label_text, fill='black', font=font)

# === Printer and conversion settings ===
printer = 'usb://0x04f9:0x209b'  # Replace with your actual USB ID if needed
model = 'QL-800'
backend = 'pyusb'

qlr = BrotherQLRaster(model)
qlr.exception_on_warning = True

from PIL import Image

# Patch for compatibility with brother_ql expecting Image.ANTIALIAS
if not hasattr(Image, 'ANTIALIAS'):
    from PIL import Image as PIL_Image
    Image.ANTIALIAS = PIL_Image.Resampling.LANCZOS


instructions = convert(
    qlr=qlr,
    images=[image],
    label='62',        # 62mm continuous tape
    red=True,
    threshold=70.0,
    dither=False,
    compress=False,
    dpi_600=False,
    hq=False,
    cut=True
)


# === Send to printer ===
send(
    instructions=instructions,
    printer_identifier=printer,
    backend_identifier=backend,
#    blocking=True
    blocking=False
)

print("✅ Label printed successfully!")
