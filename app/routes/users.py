# app/routes/users.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.user import User, AuditLog, LoginHistory
from app.utils.decorators import admin_required

users_bp = Blueprint('users', __name__)


@users_bp.route('/')
@login_required
@admin_required
def index():
    users = User.query.order_by(User.full_name).all()
    return render_template('users/index.html', users=users)


@users_bp.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new():
    if request.method == 'POST':
        username = request.form['username'].strip().lower()
        email    = request.form['email'].strip().lower()
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return redirect(url_for('users.new'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('users.new'))
        u = User(username=username, email=email,
                 full_name=request.form['full_name'].strip(),
                 role=request.form.get('role','shopkeeper'),
                 phone=request.form.get('phone','').strip())
        u.set_password(request.form['password'])
        db.session.add(u)
        from app.utils.audit import log_action
        log_action('create_user', 'users', description=f'Created user {username}')
        db.session.commit()
        flash(f'User {u.full_name} created.', 'success')
        return redirect(url_for('users.index'))
    return render_template('users/form.html', user=None)


@users_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(user_id):
    u = db.get_or_404(User, user_id)
    if request.method == 'POST':
        u.full_name = request.form['full_name'].strip()
        u.role      = request.form.get('role', u.role)
        u.phone     = request.form.get('phone','').strip()
        u.is_active = bool(request.form.get('is_active'))
        if request.form.get('new_password'):
            u.set_password(request.form['new_password'])
        from app.utils.audit import log_action
        log_action('edit_user', 'users', u.id, f'Updated user {u.username}')
        db.session.commit()
        flash(f'User {u.username} updated.', 'success')
        return redirect(url_for('users.index'))
    return render_template('users/form.html', user=u)


@users_bp.route('/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle(user_id):
    u = db.get_or_404(User, user_id)
    if u.id == current_user.id:
        flash('Cannot deactivate yourself.', 'warning')
    else:
        u.is_active = not u.is_active
        from app.utils.audit import log_action
        log_action('toggle_user', 'users', u.id,
                   f'{"Activated" if u.is_active else "Deactivated"} {u.username}')
        db.session.commit()
        flash(f'User {"activated" if u.is_active else "deactivated"}.', 'info')
    return redirect(url_for('users.index'))


@users_bp.route('/audit-log')
@login_required
@admin_required
def audit_log():
    page = request.args.get('page', 1, type=int)
    module = request.args.get('module','')
    query = AuditLog.query
    if module:
        query = query.filter_by(module=module)
    logs = query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=50, error_out=False)
    return render_template('users/audit_log.html', logs=logs, module=module)


@users_bp.route('/login-history')
@login_required
@admin_required
def login_history():
    page = request.args.get('page', 1, type=int)
    logs = LoginHistory.query.order_by(LoginHistory.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False)
    return render_template('users/login_history.html', logs=logs)
