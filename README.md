# Qatar Foundation — Admin Portal Backend

Flask backend for the Qatar Foundation Admin Portal.

## Setup

```bash
# 1. Clone the repo and enter it
git clone https://github.com/Neerajvs32/Test1.git
cd Test1

# 2. Copy backend files into the repo root (alongside the Qatar/ folder)
#    app.py, requirements.txt, README.md → repo root

# 3. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the server
python app.py
```

The server starts at **http://localhost:5000**.

---

## How the frontend connects

The existing UI makes fetch/XHR calls. Point all API calls to `http://localhost:5000/api/...`
(or configure a proxy in your dev server). CORS is enabled for all origins with credentials.

---

## API Reference

### Auth

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| POST | `/api/signup` | `{full_name, email, password, confirm_password}` | US-1.1 Register |
| POST | `/api/login` | `{email, password, remember_me}` | US-1.2 Login |
| POST | `/api/logout` | — | Logout |
| GET  | `/api/me` | — | Current session info |
| POST | `/api/forgot-password` | `{email}` | US-1.3 Request reset link |
| POST | `/api/reset-password` | `{token, new_password}` | US-1.3 Perform reset |

### Opportunities (all require login)

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| GET    | `/api/opportunities` | — | US-2.1 List all (admin-scoped) |
| POST   | `/api/opportunities` | see below | US-2.2 Create |
| GET    | `/api/opportunities/<id>` | — | US-2.4 View details |
| PUT    | `/api/opportunities/<id>` | see below | US-2.5 Edit |
| DELETE | `/api/opportunities/<id>` | — | US-2.6 Delete |

**Opportunity body fields:**

| Field | Required | Notes |
|-------|----------|-------|
| `name` | ✅ | Opportunity name |
| `duration` | ✅ | e.g. "3 months" |
| `start_date` | ✅ | e.g. "2025-09-01" |
| `description` | ✅ | Short description |
| `skills` | ✅ | Comma-separated skills |
| `category` | ✅ | Technology / Business / Design / Marketing / Data Science / Other |
| `future_opportunities` | ✅ | Text describing future prospects |
| `max_applicants` | ❌ | Optional positive integer |

---

## Security notes

* Passwords are hashed with **Werkzeug PBKDF2-SHA256** — never stored in plain text.
* Sessions are server-side (Flask session cookie). `remember_me=true` sets a 30-day lifetime.
* Password reset tokens expire after **1 hour** and are single-use.
* Every opportunity endpoint is **scoped to the logged-in admin** — cross-admin access is impossible.
* Generic error messages are used for login failures and forgot-password (no user enumeration).

---

## Database

SQLite file `qatar_foundation.db` is auto-created on first run in the project root.

Tables:
- `admins` — registered admin accounts
- `password_reset_tokens` — one-hour expiry reset tokens
- `opportunities` — all created opportunities, linked to admin via `admin_id`
