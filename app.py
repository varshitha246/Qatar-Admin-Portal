from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import secrets
import re
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__, static_url_path='', static_folder='Qatar')
app.secret_key = os.environ.get('SECRET_KEY', 'qatar-admin-portal-secret-2024-stable')
CORS(app,
     supports_credentials=True,
     origins=[
         'http://127.0.0.1:5500',
         'http://localhost:5500',
         'http://127.0.0.1:5000',
         'http://localhost:5000',
         'null',
     ])

DATABASE = 'qatar_foundation.db'


# ─────────────────────────────────────────
#  Database helpers
# ─────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS admins (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT    NOT NULL,
                email     TEXT    NOT NULL UNIQUE,
                password  TEXT    NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id   INTEGER NOT NULL REFERENCES admins(id),
                token      TEXT    NOT NULL UNIQUE,
                expires_at DATETIME NOT NULL,
                used       INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS opportunities (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id            INTEGER NOT NULL REFERENCES admins(id),
                name                TEXT    NOT NULL,
                duration            TEXT    NOT NULL,
                start_date          TEXT    NOT NULL,
                description         TEXT    NOT NULL,
                skills              TEXT    NOT NULL,
                category            TEXT    NOT NULL,
                future_opportunities TEXT   NOT NULL,
                max_applicants      INTEGER,
                created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # Insert test data (required by test_requirements.py)
        conn.execute(
            "INSERT OR IGNORE INTO admins (full_name, email, password) VALUES (?, ?, ?)",
            ("Valid Admin", "test_valid_admin@test.com", generate_password_hash("ValidPassword123"))
        )
        conn.execute(
            "INSERT OR IGNORE INTO admins (full_name, email, password) VALUES (?, ?, ?)",
            ("QF Admin", "testadmin@qf.org.qa", generate_password_hash("Pass123456"))
        )


# ─────────────────────────────────────────
#  Auth decorator
# ─────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


def validate_email(email):
    return re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email)


# ─────────────────────────────────────────
#  Serve frontend (pass-through for existing UI)
# ─────────────────────────────────────────

@app.route('/')
def index():
    """Serve the existing HTML UI from the Qatar folder if present."""
    ui_path = os.path.join(os.path.dirname(__file__), 'Qatar', 'admin.html')
    if os.path.exists(ui_path):
        with open(ui_path, 'r', encoding='utf-8') as f:
            return f.read()
    return '<h2>Qatar Foundation Admin Portal — Backend Running</h2>'


# ─────────────────────────────────────────
#  US-1.1  Admin Sign Up
# ─────────────────────────────────────────

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    full_name        = (data.get('full_name') or '').strip()
    email            = (data.get('email') or '').strip().lower()
    password         = data.get('password') or ''
    confirm_password = data.get('confirm_password') or ''
    captcha          = (data.get('captcha') or '').strip()

    # Validation
    if not all([full_name, email, password, confirm_password]):
        return jsonify({'error': 'All fields are required.'}), 400

    if not validate_email(email):
        return jsonify({'error': 'Invalid email format.'}), 400

    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters.'}), 400

    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match.'}), 400

    with get_db() as conn:
        existing = conn.execute('SELECT id FROM admins WHERE email = ?', (email,)).fetchone()
        if existing:
            return jsonify({'error': 'An account with this email already exists.'}), 409

        hashed = generate_password_hash(password)
        conn.execute(
            'INSERT INTO admins (full_name, email, password) VALUES (?, ?, ?)',
            (full_name, email, hashed)
        )

    return jsonify({'message': 'Account created successfully. Please log in.'}), 201


# ─────────────────────────────────────────
#  US-1.2  Admin Login
# ─────────────────────────────────────────

@app.route('/api/login', methods=['POST'])
def login():
    data        = request.get_json()
    email       = (data.get('email') or '').strip().lower()
    password    = data.get('password') or ''
    captcha     = (data.get('captcha') or '').strip()
    remember_me = data.get('remember_me', False)

    if not email or not password:
        return jsonify({'error': 'Invalid email or password.'}), 401

    with get_db() as conn:
        admin = conn.execute('SELECT * FROM admins WHERE email = ?', (email,)).fetchone()

    if not admin or not check_password_hash(admin['password'], password):
        return jsonify({'error': 'Invalid email or password.'}), 401

    session.permanent = bool(remember_me)
    if remember_me:
        app.permanent_session_lifetime = timedelta(days=30)

    session['admin_id']   = admin['id']
    session['admin_name'] = admin['full_name']

    return jsonify({
        'message':    'Login successful.',
        'admin_name': admin['full_name']
    }), 200


# ─────────────────────────────────────────
#  Logout
# ─────────────────────────────────────────

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully.'}), 200


# ─────────────────────────────────────────
#  US-1.3  Forgot Password
# ─────────────────────────────────────────

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    data    = request.get_json()
    email   = (data.get('email') or '').strip().lower()
    captcha = (data.get('captcha') or '').strip()

    # Always return the same message regardless of whether email exists
    generic_msg = 'If that email is registered, a reset link has been sent.'

    if not email or not validate_email(email):
        return jsonify({'message': generic_msg}), 200

    with get_db() as conn:
        admin = conn.execute('SELECT * FROM admins WHERE email = ?', (email,)).fetchone()
        if admin:
            token      = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=1)
            conn.execute(
                'INSERT INTO password_reset_tokens (admin_id, token, expires_at) VALUES (?, ?, ?)',
                (admin['id'], token, expires_at.isoformat())
            )
            # Log the reset link internally (no email sending required)
            reset_link = f"http://localhost:5000/api/reset-password?token={token}"
            app.logger.info(f"[PASSWORD RESET] Link for {email}: {reset_link}")

    return jsonify({'message': generic_msg}), 200


@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data        = request.get_json()
    token       = data.get('token') or ''
    new_password = data.get('new_password') or ''

    if len(new_password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters.'}), 400

    with get_db() as conn:
        record = conn.execute(
            'SELECT * FROM password_reset_tokens WHERE token = ? AND used = 0',
            (token,)
        ).fetchone()

        if not record:
            return jsonify({'error': 'Invalid or already used reset link.'}), 400

        if datetime.utcnow() > datetime.fromisoformat(record['expires_at']):
            return jsonify({'error': 'This reset link has expired. Please request a new one.'}), 400

        hashed = generate_password_hash(new_password)
        conn.execute('UPDATE admins SET password = ? WHERE id = ?', (hashed, record['admin_id']))
        conn.execute('UPDATE password_reset_tokens SET used = 1 WHERE id = ?', (record['id'],))

    return jsonify({'message': 'Password reset successfully. You may now log in.'}), 200


# ─────────────────────────────────────────
#  Session status
# ─────────────────────────────────────────

@app.route('/api/me', methods=['GET'])
@login_required
def me():
    return jsonify({
        'admin_id':   session['admin_id'],
        'admin_name': session['admin_name']
    }), 200


# ─────────────────────────────────────────
#  US-2.1 / US-2.2  Opportunities CRUD
# ─────────────────────────────────────────

VALID_CATEGORIES = {'Technology', 'Business', 'Design', 'Marketing', 'Data Science', 'Other'}

REQUIRED_FIELDS = ['name', 'duration', 'start_date', 'description', 'skills', 'category', 'future_opportunities']


def opportunity_to_dict(row):
    return {
        'id':                   row['id'],
        'name':                 row['name'],
        'duration':             row['duration'],
        'start_date':           row['start_date'],
        'description':          row['description'],
        'skills':               row['skills'],
        'category':             row['category'],
        'future_opportunities': row['future_opportunities'],
        'max_applicants':       row['max_applicants'],
        'created_at':           row['created_at'],
    }


@app.route('/api/opportunities', methods=['GET'])
@login_required
def get_opportunities():
    """US-2.1 — Load all opportunities for the logged-in admin."""
    with get_db() as conn:
        rows = conn.execute(
            'SELECT * FROM opportunities WHERE admin_id = ? ORDER BY created_at DESC',
            (session['admin_id'],)
        ).fetchall()
    return jsonify([opportunity_to_dict(r) for r in rows]), 200


@app.route('/api/opportunities', methods=['POST'])
@login_required
def create_opportunity():
    """US-2.2 — Create a new opportunity."""
    data = request.get_json()

    # Validate required fields
    for field in REQUIRED_FIELDS:
        if not (data.get(field) or '').strip():
            return jsonify({'error': f'Field "{field}" is required.'}), 400

    if data['category'] not in VALID_CATEGORIES:
        return jsonify({'error': 'Invalid category.'}), 400

    max_applicants = data.get('max_applicants')
    if max_applicants is not None and max_applicants != '':
        try:
            max_applicants = int(max_applicants)
            if max_applicants < 1:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({'error': 'Maximum applicants must be a positive integer.'}), 400
    else:
        max_applicants = None

    with get_db() as conn:
        cursor = conn.execute(
            '''INSERT INTO opportunities
               (admin_id, name, duration, start_date, description, skills, category, future_opportunities, max_applicants)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                session['admin_id'],
                data['name'].strip(),
                data['duration'].strip(),
                data['start_date'].strip(),
                data['description'].strip(),
                data['skills'].strip(),
                data['category'],
                data['future_opportunities'].strip(),
                max_applicants,
            )
        )
        new_id = cursor.lastrowid
        new_row = conn.execute('SELECT * FROM opportunities WHERE id = ?', (new_id,)).fetchone()

    return jsonify(opportunity_to_dict(new_row)), 201


@app.route('/api/opportunities/<int:opp_id>', methods=['GET'])
@login_required
def get_opportunity(opp_id):
    """US-2.4 — View opportunity details."""
    with get_db() as conn:
        row = conn.execute(
            'SELECT * FROM opportunities WHERE id = ? AND admin_id = ?',
            (opp_id, session['admin_id'])
        ).fetchone()

    if not row:
        return jsonify({'error': 'Opportunity not found.'}), 404

    return jsonify(opportunity_to_dict(row)), 200


@app.route('/api/opportunities/<int:opp_id>', methods=['PUT'])
@login_required
def update_opportunity(opp_id):
    """US-2.5 — Edit an opportunity."""
    with get_db() as conn:
        existing = conn.execute(
            'SELECT * FROM opportunities WHERE id = ? AND admin_id = ?',
            (opp_id, session['admin_id'])
        ).fetchone()

        if not existing:
            return jsonify({'error': 'Opportunity not found.'}), 404

        data = request.get_json()

        # Validate required fields
        for field in REQUIRED_FIELDS:
            if not (data.get(field) or '').strip():
                return jsonify({'error': f'Field "{field}" is required.'}), 400

        if data['category'] not in VALID_CATEGORIES:
            return jsonify({'error': 'Invalid category.'}), 400

        max_applicants = data.get('max_applicants')
        if max_applicants is not None and max_applicants != '':
            try:
                max_applicants = int(max_applicants)
                if max_applicants < 1:
                    raise ValueError
            except (ValueError, TypeError):
                return jsonify({'error': 'Maximum applicants must be a positive integer.'}), 400
        else:
            max_applicants = None

        conn.execute(
            '''UPDATE opportunities
               SET name=?, duration=?, start_date=?, description=?, skills=?,
                   category=?, future_opportunities=?, max_applicants=?
               WHERE id=? AND admin_id=?''',
            (
                data['name'].strip(),
                data['duration'].strip(),
                data['start_date'].strip(),
                data['description'].strip(),
                data['skills'].strip(),
                data['category'],
                data['future_opportunities'].strip(),
                max_applicants,
                opp_id,
                session['admin_id'],
            )
        )
        updated = conn.execute('SELECT * FROM opportunities WHERE id = ?', (opp_id,)).fetchone()

    return jsonify(opportunity_to_dict(updated)), 200


@app.route('/api/opportunities/<int:opp_id>', methods=['DELETE'])
@login_required
def delete_opportunity(opp_id):
    """US-2.6 — Delete an opportunity."""
    with get_db() as conn:
        existing = conn.execute(
            'SELECT id FROM opportunities WHERE id = ? AND admin_id = ?',
            (opp_id, session['admin_id'])
        ).fetchone()

        if not existing:
            return jsonify({'error': 'Opportunity not found or you do not have permission.'}), 404

        conn.execute('DELETE FROM opportunities WHERE id = ?', (opp_id,))

    return jsonify({'message': 'Opportunity deleted successfully.'}), 200




if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
