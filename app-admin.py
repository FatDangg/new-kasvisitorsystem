#!/usr/bin/env python
import os
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = "goddam"  # Replace with a secure secret key
CORS(app, resources={r"/*": {"origins": "*"}})

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///visitors.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# For demo purposes, hardcode admin credentials
ADMIN_USERNAME = "danielchen"
ADMIN_PASSWORD = "password"

# Visitor model
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

# --------- Authentication Routes --------- #
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # Simple login page
        return """
        <!DOCTYPE html>
<html>
<head>
  <title>Admin Login</title>
  <style>
    /* Ensure padding doesn't expand elements beyond their declared width */
    * {
      box-sizing: border-box;
    }

    body {
      font-family: Arial, sans-serif;
      background: #f5f5f5;
      margin: 0; /* remove default margin for consistency */
      padding: 0;
    }

    .login-container {
      width: 400px;         /* fixed width on larger screens */
      max-width: 90%;       /* allow it to shrink on smaller screens */
      margin: 100px auto;   /* centers horizontally */
      padding: 1rem;
      background: #fff;
      border: 1px solid #ccc;
      border-radius: 4px;
    }

    .login-container h2 {
      margin-bottom: 1rem;  /* add some spacing below heading */
    }

    input {
      width: 100%;          /* fill container width */
      padding: 0.5rem;
      margin-bottom: 1rem;
      border: 1px solid #ccc;
      border-radius: 4px;
    }

    button {
      width: 100%;          /* make the button match input width for consistency */
      padding: 0.5rem;
      background: #00573d;
      color: #fff;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }

    button:hover {
      background: #007f57;
    }
  </style>
</head>
<body>
  <div class="login-container">
    <h2>Admin Login</h2>
    <form method="POST" action="/login">
      <input type="text" name="username" placeholder="Username" required>
      <input type="password" name="password" placeholder="Password" required>
      <button type="submit">Login</button>
    </form>
  </div>
</body>
</html>
        """
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            return "Invalid credentials. <a href='/login'>Try again</a>"

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# --------- Admin Panel Routes --------- #
@app.route('/admin')
def admin_panel():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    # Serve the admin.html file from the current folder
    return send_from_directory(app.static_folder, "admin.html")

@app.route('/api/visitors', methods=['GET'])
def get_visitors():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    visitors = Visitor.query.order_by(Visitor.created_at.desc()).all()
    data = []
    for v in visitors:
        data.append({
            "full_name": f"{v.first_name} {v.last_name}",
            "purpose": v.purpose,
            "created_at": v.created_at.isoformat(),
            "finding": v.finding,
            "email": v.email,      # Added email
            "phone": v.phone,      # Added phone number
            "photo_download": f"/photos/{os.path.basename(v.photo_path)}",
            "pdf_download": f"/pdfs/{os.path.basename(v.pdf_path)}"
        })
    return jsonify(data)

@app.route('/photos/<filename>', methods=['GET'])
def download_photo(filename):
    file_path = os.path.join("photos", filename)
    if os.path.exists(file_path):
        return send_from_directory("photos", filename)
    return jsonify({"error": "Photo not found"}), 404

@app.route('/pdfs/<filename>', methods=['GET'])
def download_pdf(filename):
    file_path = os.path.join("pdfs", filename)
    
    if os.path.exists(file_path):
        return send_from_directory("pdfs", filename)
    return jsonify({"error": "PDF not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
