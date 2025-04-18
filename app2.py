#!/usr/bin/env python
import os
import base64
from datetime import datetime

from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# === PIL and patch for newer Pillow versions (ANTIALIAS -> Resampling) ===
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    from PIL import Image as PIL_Image
    Image.ANTIALIAS = PIL_Image.Resampling.LANCZOS

# === Brother QL imports ===
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
from brother_ql.raster import BrotherQLRaster

# === ReportLab imports for PDF creation ===
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app, resources={r"/*": {"origins": "*"}})

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///visitors.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Create directories if they don't exist
PDF_DIR = "pdfs"
PHOTO_DIR = "photos"
if not os.path.exists(PDF_DIR):
    os.makedirs(PDF_DIR)
if not os.path.exists(PHOTO_DIR):
    os.makedirs(PHOTO_DIR)

# === Database Model for Visitor ===
class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name  = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(150), nullable=False)
    phone      = db.Column(db.String(20), nullable=False)
    purpose    = db.Column(db.String(100), nullable=False)
    finding    = db.Column(db.String(100), nullable=False)
    photo_path = db.Column(db.String(200), nullable=False)
    pdf_path   = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

def save_photo(photo_base64, identifier):
    """
    Decode the base64 photo and save it to PHOTO_DIR.
    Uses 'identifier' (e.g. phone) for naming.
    """
    try:
        if "," in photo_base64:
            photo_base64 = photo_base64.split(",")[1]
        photo_data = base64.b64decode(photo_base64)
        filename = f"visitor_{identifier}_{int(datetime.utcnow().timestamp())}.png"
        file_path = os.path.join(PHOTO_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(photo_data)
        return file_path
    except Exception as e:
        print("Error saving photo:", e)
        return None

def generate_pdf(pdf_file_path, first_name, last_name, purpose, finding, visitor_photo_path, school_logo_path):
    """
    Generate a badge PDF sized 62mm x 62mm that includes:
      1. Visitor's full name (top center)
      2. Purpose of visit, date of visit (YYYY-MM-DD), who they are meeting
      3. Visitor's photo (bottom right)
      4. School logo (bottom left)
    """
    page_size = 62 * mm
    margin = 3 * mm
    available_width = page_size - 2 * margin

    c = canvas.Canvas(pdf_file_path, pagesize=(page_size, page_size))

    # Try to register and use BebasNeue
    pdfmetrics.registerFont(TTFont('BebasNeue', 'BebasNeue-Regular.ttf'))
    try:
        c.setFont("BebasNeue", 16)
    except:
        c.setFont("Helvetica-Bold", 16)

    # 1. Visitor's full name at the top (centered)
    full_name = f"{first_name} {last_name}"
    c.drawCentredString(page_size/2, page_size - margin - 16, full_name)

    # 2. Purpose, Date, Meeting
    c.setFont("BebasNeue", 10)
    visit_date_str = datetime.now().strftime("%Y-%m-%d")
    info_lines = [
        f"Purpose: {purpose}",
        f"Date: {visit_date_str}",
        f"Meeting: {finding}"
    ]
    text_y = page_size - margin - 16 - 20
    for line in info_lines:
        c.drawCentredString(page_size/2, text_y, line)
        text_y -= 12

    # 3. Bottom area for images
    image_area_height = 25 * mm
    image_y = margin
    image_width = available_width / 2

    # Bottom-left: School logo
    try:
        logo = ImageReader(school_logo_path)
        c.drawImage(logo, margin, image_y, width=image_width, height=image_area_height,
                    preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print("Error loading school logo:", e)

    # Bottom-right: Visitor photo
    try:
        visitor_photo = ImageReader(visitor_photo_path)
        c.drawImage(visitor_photo, margin + image_width, image_y,
                    width=image_width, height=image_area_height,
                    preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print("Error loading visitor photo:", e)

    c.showPage()
    c.save()

def auto_print_label(first_name, last_name, purpose, finding, photo_path):
    """
    Creates a ~62mm label (732 px wide at 300 dpi),
    draws text at the top, then places the visitor's
    photo underneath the text, and prints via pyusb.
    """
    from PIL import Image, ImageDraw, ImageFont

    # Make the label taller so there's room for text + photo
    LABEL_WIDTH_PX = 732
    LABEL_HEIGHT_PX = 600
    background_color = "white"

    # Create the main label image
    label_img = Image.new('RGB', (LABEL_WIDTH_PX, LABEL_HEIGHT_PX), background_color)
    draw = ImageDraw.Draw(label_img)

    # Use a large font size so text is visible
    try:
        font = ImageFont.truetype("BebasNeue-Regular.ttf", 90)
    except:
        font = ImageFont.load_default()

    # Build label text
    visitor_name = f"{first_name} {last_name}"
    text = f"{visitor_name}\nPurpose: {purpose}\nMeeting: {finding}\nDate: {datetime.now().strftime('%Y-%m-%d')}"
    margin = 20
    x_text = margin
    y_text = margin

    # 1) Draw text line by line at the top
    for line in text.split("\n"):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_height = bbox[3] - bbox[1]
        draw.text((x_text, y_text), line, fill='black', font=font)
        y_text += line_height + 10

    # 2) Open and scale the visitor's photo
    try:
        photo = Image.open(photo_path)
        max_photo_size = (600, 600)  # Big, but we'll see if it fits
        photo.thumbnail(max_photo_size, Image.LANCZOS)
    except Exception as e:
        print("Error opening/resizing visitor photo:", e)
        photo = None

    # 3) Place the visitor photo below the text
    if photo:
        photo_x = (LABEL_WIDTH_PX - photo.width) // 2  # center it
        photo_y = y_text + 20  # place 20px below the last line of text
        label_img.paste(photo, (photo_x, photo_y))

    # Prepare instructions for QL-800
    model = 'QL-800'
    printer = 'usb://0x04f9:0x209b'  # Adjust if needed
    backend = 'pyusb'
    qlr = BrotherQLRaster(model)
    qlr.exception_on_warning = True

    instructions = convert(
        qlr=qlr,
        images=[label_img],
        label='62',  # 62 mm continuous tape
        red=True,
        threshold=70.0,
        dither=False,
        compress=False,
        dpi_600=False,
        hq=False,
        cut=True
    )

    send(
        instructions=instructions,
        printer_identifier=printer,
        backend_identifier=backend,
        blocking=False
    )
    print("✅ Label (text at top, photo below) sent to QL-800.")

@app.route('/submit', methods=['POST'])
def submit_visitor():
    """
    Expects a JSON payload with:
      - firstName
      - lastName
      - email
      - phone
      - purpose
      - finding
      - photo (Base64 encoded)
    """
    data = request.json
    required_fields = ['firstName', 'lastName', 'email', 'phone', 'purpose', 'finding', 'photo']
    if not all(field in data and data[field] for field in required_fields):
        return jsonify({"error": "Missing required fields."}), 400

    first_name = data['firstName'].strip()
    last_name = data['lastName'].strip()
    email = data['email'].strip()
    phone = data['phone'].strip()
    purpose = data['purpose'].strip()
    finding = data['finding'].strip()
    photo_b64 = data['photo']

    # 1) Save visitor photo
    visitor_photo_path = save_photo(photo_b64, phone)
    if not visitor_photo_path:
        return jsonify({"error": "Failed to save photo."}), 500

    # 2) Generate PDF (badge 62x62 mm)
    pdf_filename = f"visitor_{phone}_{int(datetime.utcnow().timestamp())}.pdf"
    pdf_path = os.path.join(PDF_DIR, pdf_filename)
    generate_pdf(pdf_path, first_name, last_name, purpose, finding, visitor_photo_path, "logo.png")

    # 3) Save DB record
    visitor = Visitor(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        purpose=purpose,
        finding=finding,
        photo_path=visitor_photo_path,
        pdf_path=pdf_path
    )
    db.session.add(visitor)
    db.session.commit()

    # 4) Auto-print the label (text on top, photo beneath)
    try:
        auto_print_label(first_name, last_name, purpose, finding, visitor_photo_path)
    except Exception as e:
        print("Error printing to Brother QL-800:", e)

    return jsonify({
        "success": True,
        "message": "Visitor registered successfully.",
        "pdfDownloadLink": f"/pdfs/{pdf_filename}",
        "photoDownloadLink": f"/photos/{os.path.basename(visitor_photo_path)}"
    })

@app.route('/pdfs/<filename>', methods=['GET'])
def download_pdf(filename):
    file_path = os.path.join(PDF_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "PDF not found."}), 404

@app.route('/photos/<filename>', methods=['GET'])
def download_photo(filename):
    file_path = os.path.join(PHOTO_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "Photo not found."}), 404

from flask import send_from_directory

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)


if __name__ == '__main__':
    app.run(debug=True)
