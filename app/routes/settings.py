# app/routes/settings.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/')
@login_required
def index():
    if not current_user.is_admin:
        flash('Admin access required.', 'danger')
        return redirect(url_for('dashboard.index'))
    return render_template('settings/index.html')


@settings_bp.route('/store', methods=['GET', 'POST'])
@login_required
def store_settings():
    if not current_user.is_admin:
        flash('Admin access required.', 'danger')
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        # In production, store settings in DB or config file
        flash('Store settings saved.', 'success')
        return redirect(url_for('settings.index'))
    return render_template('settings/store.html')
