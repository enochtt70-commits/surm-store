# app/routes/suppliers.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.supplier import Supplier

suppliers_bp = Blueprint('suppliers', __name__)


@suppliers_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    per_page = current_app.config.get('ITEMS_PER_PAGE', 25)
    query = Supplier.query
    if search:
        query = query.filter(
            db.or_(Supplier.name.ilike(f'%{search}%'), Supplier.phone.ilike(f'%{search}%'))
        )
    suppliers = query.filter_by(is_active=True).order_by(Supplier.name).paginate(
        page=page, per_page=per_page, error_out=False)
    return render_template('suppliers/index.html', suppliers=suppliers, search=search)


@suppliers_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if not current_user.is_manager:
        flash('Permission denied.', 'danger')
        return redirect(url_for('suppliers.index'))
    if request.method == 'POST':
        s = Supplier(
            name=request.form['name'].strip(),
            contact_person=request.form.get('contact_person', '').strip(),
            phone=request.form.get('phone', '').strip(),
            email=request.form.get('email', '').strip(),
            address=request.form.get('address', '').strip(),
            city=request.form.get('city', '').strip(),
            region=request.form.get('region', '').strip(),
            tin_number=request.form.get('tin_number', '').strip(),
            payment_terms=request.form.get('payment_terms', 30, type=int),
            notes=request.form.get('notes', '').strip(),
        )
        db.session.add(s)
        db.session.commit()
        flash(f'Supplier "{s.name}" added.', 'success')
        return redirect(url_for('suppliers.index'))
    return render_template('suppliers/form.html', supplier=None)


@suppliers_bp.route('/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(supplier_id):
    if not current_user.is_manager:
        flash('Permission denied.', 'danger')
        return redirect(url_for('suppliers.index'))
    s = db.get_or_404(Supplier, supplier_id)
    if request.method == 'POST':
        s.name = request.form['name'].strip()
        s.contact_person = request.form.get('contact_person', '').strip()
        s.phone = request.form.get('phone', '').strip()
        s.email = request.form.get('email', '').strip()
        s.address = request.form.get('address', '').strip()
        s.city = request.form.get('city', '').strip()
        s.region = request.form.get('region', '').strip()
        s.tin_number = request.form.get('tin_number', '').strip()
        s.payment_terms = request.form.get('payment_terms', 30, type=int)
        s.notes = request.form.get('notes', '').strip()
        db.session.commit()
        flash(f'Supplier "{s.name}" updated.', 'success')
        return redirect(url_for('suppliers.index'))
    return render_template('suppliers/form.html', supplier=s)


@suppliers_bp.route('/<int:supplier_id>')
@login_required
def detail(supplier_id):
    s = db.get_or_404(Supplier, supplier_id)
    return render_template('suppliers/detail.html', supplier=s)
