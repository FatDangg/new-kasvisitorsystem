#!/usr/bin/env python
import os
import base64
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from flask_cors import CORS
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

# Database Model for Visitor
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
    Decode the base64 photo and save it to the PHOTO_DIR.
    Uses the identifier (e.g., phone) for naming.
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
      2. Purpose of visit, date of visit (YYYY-MM-DD), and who they are meeting
      3. Visitor's photo (bottom right)
      4. School logo (bottom left)
    Tries to use a cool font (BebasNeue) and falls back to Helvetica-Bold.
    """
    # Set page dimensions: 62mm x 62mm
    page_size = 62 * mm
    margin = 3 * mm
    available_width = page_size - 2 * margin

    c = canvas.Canvas(pdf_file_path, pagesize=(page_size, page_size))

    # Try to use BebasNeue; fallback to Helvetica-Bold if not available
    pdfmetrics.registerFont(TTFont('BebasNeue', 'BebasNeue-Regular.ttf'))
    try:
        c.setFont("BebasNeue", 16)
        print("I got the font")
    except Exception as e:
        c.setFont("Helvetica-Bold", 16)

    # 1. Draw visitor's full name (centered at the top)
    full_name = f"{first_name} {last_name}"
    c.drawCentredString(page_size/2, page_size - margin - 16, full_name)

    # 2. Draw additional info: purpose, date, and meeting person
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

    # 3. Reserve bottom area for images (approx. 25mm height)
    image_area_height = 25 * mm
    image_y = margin  # bottom margin
    image_width = available_width / 2  # left for logo, right for photo

    # Draw school logo on bottom left
    try:
        logo = ImageReader(school_logo_path)
        c.drawImage(logo, margin, image_y, width=image_width, height=image_area_height,
                    preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print("Error loading school logo:", e)

    # Draw visitor photo on bottom right
    try:
        visitor_photo = ImageReader(visitor_photo_path)
        c.drawImage(visitor_photo, margin + image_width, image_y, width=image_width, height=image_area_height,
                    preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print("Error loading visitor photo:", e)

    c.showPage()
    c.save()

@app.route('/submit', methods=['POST'])
def submit_visitor():
    """
    Expects a JSON payload with:
      - firstName
      - lastName
      - email
      - phone
      - purpose
      - finding (Who are they visiting)
      - photo (Base64 encoded image)
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

    # Save visitor photo
    visitor_photo_path = save_photo(photo_b64, phone)
    if not visitor_photo_path:
        return jsonify({"error": "Failed to save photo."}), 500

    # Generate PDF badge
    pdf_filename = f"visitor_{phone}_{int(datetime.utcnow().timestamp())}.pdf"
    pdf_path = os.path.join(PDF_DIR, pdf_filename)
    generate_pdf(pdf_path, first_name, last_name, purpose, finding, visitor_photo_path, "logo.png")

    # Save visitor record to database
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

if __name__ == '__main__':
    app.run(debug=True)
