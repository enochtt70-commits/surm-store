# app/routes/customers.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.customer import Customer

customers_bp = Blueprint('customers', __name__)


@customers_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    ctype = request.args.get('type', '')
    per_page = current_app.config.get('ITEMS_PER_PAGE', 25)
    query = Customer.query.filter_by(is_active=True)
    if search:
        query = query.filter(
            db.or_(Customer.name.ilike(f'%{search}%'), Customer.phone.ilike(f'%{search}%'))
        )
    if ctype:
        query = query.filter_by(customer_type=ctype)
    customers = query.order_by(Customer.name).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('customers/index.html', customers=customers, search=search, ctype=ctype)


@customers_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        c = Customer(
            name=request.form['name'].strip(),
            phone=request.form.get('phone', '').strip(),
            email=request.form.get('email', '').strip(),
            address=request.form.get('address', '').strip(),
            city=request.form.get('city', '').strip(),
            customer_type=request.form.get('customer_type', 'retail'),
            credit_limit=request.form.get('credit_limit', 0, type=float),
            notes=request.form.get('notes', '').strip(),
        )
        db.session.add(c)
        db.session.commit()
        flash(f'Customer "{c.name}" added.', 'success')
        return redirect(url_for('customers.index'))
    return render_template('customers/form.html', customer=None)


@customers_bp.route('/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(customer_id):
    c = db.get_or_404(Customer, customer_id)
    if request.method == 'POST':
        c.name = request.form['name'].strip()
        c.phone = request.form.get('phone', '').strip()
        c.email = request.form.get('email', '').strip()
        c.address = request.form.get('address', '').strip()
        c.city = request.form.get('city', '').strip()
        c.customer_type = request.form.get('customer_type', 'retail')
        c.credit_limit = request.form.get('credit_limit', 0, type=float)
        c.notes = request.form.get('notes', '').strip()
        db.session.commit()
        flash(f'Customer "{c.name}" updated.', 'success')
        return redirect(url_for('customers.index'))
    return render_template('customers/form.html', customer=c)


@customers_bp.route('/<int:customer_id>')
@login_required
def detail(customer_id):
    c = db.get_or_404(Customer, customer_id)
    return render_template('customers/detail.html', customer=c)
