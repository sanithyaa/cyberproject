"""
Audit logging helper – call log_action() anywhere to record an event.
"""
from flask import request
from extensions import db
from models.audit_log import AuditLog


def log_action(action: str, user_id: int = None, detail: str = None):
    """
    Insert an audit log entry.
    Silently swallows DB errors so a logging failure never breaks the app.
    """
    try:
        ip = request.remote_addr if request else None
        entry = AuditLog(
            user_id    = user_id,
            action     = action,
            detail     = detail,
            ip_address = ip,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:
        db.session.rollback()
