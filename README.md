# Secure Online Voting System

A full-stack cybersecurity-focused online voting platform built with Python FLASK

## Security Features

| Feature | Implementation |
|---|---|
| Password Hashing | bcrypt via Flask-Bcrypt |
| CSRF Protection | Flask-WTF on every form |
| SQL Injection Prevention | SQLAlchemy ORM (parameterised queries) |
| XSS Prevention | Jinja2 auto-escaping + input sanitisation |
| Role-Based Access Control | Admin / Voter roles with decorators |
| Two-Factor Authentication | TOTP-based OTP (pyotp) |
| Brute-Force Protection | Flask-Limiter (10 login attempts/min) |
| Session Security | HttpOnly cookies, 30-min timeout |
| Secure HTTP Headers | CSP, X-Frame-Options, X-XSS-Protection |
| Audit Trail | Immutable AuditLog table |
| Secure File Upload | Extension whitelist + UUID rename |

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Create default candidate image
```bash
python create_default_image.py
```

### 3. Run the app
```bash
python app.py
```

Visit: http://localhost:5000

### Default Admin Credentials
- **Username:** `admin`
- **Password:** `Admin@1234`
- **OTP:** shown in the flash message (demo mode)

> Change the admin password immediately after first login.

## Project Structure

```
secure-online-voting-system/
├── app.py                  # Application factory + entry point
├── config.py               # Configuration (dev/prod)
├── extensions.py           # Flask extension instances
├── requirements.txt
├── .env                    # Environment variables (not committed)
├── models/
│   ├── user.py             # User model (bcrypt hashing)
│   ├── candidate.py        # Candidate model
│   ├── vote.py             # Vote model (unique constraint)
│   ├── election.py         # Election state model
│   └── audit_log.py        # Immutable audit trail
├── routes/
│   ├── auth.py             # Register, login, OTP, logout
│   ├── voter.py            # Dashboard, vote, results
│   ├── admin.py            # Admin panel routes
│   └── public.py           # Home, about
├── security/
│   ├── validators.py       # Input validation + sanitisation
│   └── decorators.py       # admin_required, voter_required
├── utils/
│   ├── audit.py            # Audit logging helper
│   └── mail_helper.py      # OTP email helper
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── verify_otp.html
│   ├── dashboard.html
│   ├── vote.html
│   ├── vote_confirmation.html
│   ├── results.html
│   ├── about.html
│   ├── admin/
│   │   ├── base_admin.html
│   │   ├── dashboard.html
│   │   ├── candidates.html
│   │   ├── add_candidate.html
│   │   ├── edit_candidate.html
│   │   ├── election.html
│   │   ├── users.html
│   │   ├── results.html
│   │   └── audit_logs.html
│   └── errors/
│       ├── 403.html
│       ├── 404.html
│       ├── 429.html
│       └── 500.html
└── static/
    ├── css/style.css
    ├── css/admin.css
    ├── js/main.js
    ├── js/validation.js
    ├── images/
    └── uploads/
```

## Database Schema

### users
| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| username | String(80) | Unique |
| email | String(120) | Unique |
| password_hash | String(256) | bcrypt hash |
| role | String(20) | 'admin' or 'voter' |
| has_voted | Boolean | Duplicate vote prevention |
| is_active | Boolean | Admin can disable accounts |
| otp_secret | String(32) | TOTP secret |

### candidates
| Column | Type |
|---|---|
| id | Integer PK |
| name | String(120) |
| party | String(120) |
| photo | String(256) |
| bio | Text |

### votes
| Column | Type | Notes |
|---|---|---|
| id | Integer PK | |
| voter_id | FK → users | Unique constraint |
| candidate_id | FK → candidates | |
| timestamp | DateTime | |

### elections
| Column | Type |
|---|---|
| id | Integer PK |
| title | String(200) |
| is_active | Boolean |
| start_time | DateTime |
| end_time | DateTime |

### audit_logs
| Column | Type |
|---|---|
| id | Integer PK |
| user_id | FK → users (nullable) |
| action | String(100) |
| detail | Text |
| ip_address | String(45) |
| timestamp | DateTime |

## Security Testing

### SQL Injection Test
Try entering in the login username field:
```
' OR '1'='1
```
**Expected:** Login fails. SQLAlchemy ORM uses parameterised queries.

### XSS Test
Try entering in any text field:
```html
<script>alert('XSS')</script>
```
**Expected:** Input is HTML-escaped and displayed as plain text.

### CSRF Test
Try submitting a form without the CSRF token.
**Expected:** 400 Bad Request.

### Authorization Test
Try accessing `/admin/` as a voter.
**Expected:** 403 Forbidden.

### Duplicate Vote Test
Vote once, then try to vote again.
**Expected:** Redirected with "already voted" message.

### Brute Force Test
Make more than 10 login attempts per minute.
**Expected:** 429 Too Many Requests.

## Deployment (Render / Railway)

1. Push to GitHub
2. Connect repo to Render
3. Set environment variables:
   - `SECRET_KEY` = long random string
   - `FLASK_ENV` = production
4. Render auto-detects `render.yaml`
5. HTTPS is provided automatically

##Points 

- **bcrypt**: adaptive hashing algorithm; cost factor makes brute-force expensive
- **CSRF tokens**: unique per-session token in every form; server validates before processing
- **Parameterised queries**: user input is never concatenated into SQL strings
- **Jinja2 escaping**: `{{ variable }}` auto-escapes HTML; prevents XSS
- **Role-based access**: `@admin_required` decorator checks `current_user.role` before every admin route
- **OTP**: TOTP algorithm (RFC 6238); 5-minute window; secret stored per user
- **Audit logs**: INSERT-only table; records every login, vote, and admin action with IP and timestamp
