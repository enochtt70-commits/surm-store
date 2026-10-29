
from flask import request as flask_request
from flask_login import current_user
from app import db
from app.models.user import AuditLog

def log_action(action, module="", record_id=None, description=""):
    try:
        uid = current_user.id if current_user and current_user.is_authenticated else None
        db.session.add(AuditLog(user_id=uid, action=action, module=module,
            record_id=record_id, description=description,
            ip_address=flask_request.remote_addr,
            user_agent=flask_request.headers.get("User-Agent","")[:255]))
    except Exception:
        pass
