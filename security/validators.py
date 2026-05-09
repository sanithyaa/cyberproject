"""
Input validation helpers.
All user-supplied data must pass through these before touching the DB.
"""
import re
import html
from markupsafe import escape


# ── Password policy ────────────────────────────────────────────────────────────
PASSWORD_MIN_LEN = 8
PASSWORD_REGEX   = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&_\-#])[A-Za-z\d@$!%*?&_\-#]{8,}$'
)

def validate_password(password: str) -> tuple[bool, str]:
    """
    Returns (True, '') on success or (False, error_message) on failure.
    Policy: min 8 chars, uppercase, lowercase, digit, special char.
    """
    if len(password) < PASSWORD_MIN_LEN:
        return False, f'Password must be at least {PASSWORD_MIN_LEN} characters.'
    if not PASSWORD_REGEX.match(password):
        return False, ('Password must contain uppercase, lowercase, '
                       'a digit, and a special character (@$!%*?&_-#).')
    return True, ''


# ── Username policy ────────────────────────────────────────────────────────────
USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_]{3,30}$')

def validate_username(username: str) -> tuple[bool, str]:
    if not USERNAME_REGEX.match(username):
        return False, 'Username must be 3–30 characters: letters, digits, underscores only.'
    return True, ''


# ── Email ──────────────────────────────────────────────────────────────────────
EMAIL_REGEX = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

def validate_email(email: str) -> tuple[bool, str]:
    if not EMAIL_REGEX.match(email):
        return False, 'Invalid email address.'
    return True, ''


# ── XSS sanitisation ──────────────────────────────────────────────────────────
def sanitize_input(value: str) -> str:
    """Escape HTML special characters to prevent XSS."""
    return str(escape(value)).strip()


# ── File upload ────────────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename: str) -> bool:
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )

def secure_filename_ext(filename: str) -> str:
    """Return only the extension, lower-cased."""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
