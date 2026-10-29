# app/routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timezone
from app import db
from app.models.user import User, LoginHistory

auth_bp = Blueprint('auth', __name__)


def _record_login(username, user_id, success):
    try:
        e = LoginHistory(username=username, user_id=user_id, success=success,
                         ip_address=request.remote_addr,
                         user_agent=request.headers.get('User-Agent','')[:255])
        db.session.add(e)
        db.session.commit()
    except Exception:
        pass


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember)
            user.last_login = datetime.now(timezone.utc)
            _record_login(username, user.id, True)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(next_page or url_for('dashboard.index'))
        _record_login(username, getattr(user,'id',None), False)
        if user and not user.is_active:
            flash('Your account has been deactivated. Contact the administrator.', 'danger')
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    from app.utils.audit import log_action
    log_action('logout', 'auth', description=f'{current_user.username} logged out')
    db.session.commit()
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        cur = request.form.get('current_password', '')
        new = request.form.get('new_password', '')
        con = request.form.get('confirm_password', '')
        if not current_user.check_password(cur):
            flash('Current password is incorrect.', 'danger')
        elif new != con:
            flash('New passwords do not match.', 'danger')
        elif len(new) < 8:
            flash('Password must be at least 8 characters.', 'danger')
        else:
            current_user.set_password(new)
            from app.utils.audit import log_action
            log_action('change_password', 'auth', current_user.id)
            db.session.commit()
            flash('Password changed successfully.', 'success')
            return redirect(url_for('dashboard.index'))
    return render_template('auth/change_password.html')
