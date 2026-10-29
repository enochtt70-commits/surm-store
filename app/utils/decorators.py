
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def manager_required(f):
    @wraps(f)
    def d(*a, **kw):
        if not current_user.is_manager:
            flash("Manager or above access required.", "danger")
            return redirect(url_for("dashboard.index"))
        return f(*a, **kw)
    return d

def admin_required(f):
    @wraps(f)
    def d(*a, **kw):
        if not current_user.is_admin:
            flash("Administrator access required.", "danger")
            return redirect(url_for("dashboard.index"))
        return f(*a, **kw)
    return d

def accountant_required(f):
    @wraps(f)
    def d(*a, **kw):
        if not current_user.is_accountant:
            flash("Accountant or above access required.", "danger")
            return redirect(url_for("dashboard.index"))
        return f(*a, **kw)
    return d
