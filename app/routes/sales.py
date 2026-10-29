# app/routes/sales.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timezone, date
from decimal import Decimal, InvalidOperation
from app import db
from app.models.sale import Sale, SaleItem
from app.models.product import Product
from app.models.customer import Customer
from app.models.inventory import InventoryTransaction

sales_bp = Blueprint('sales', __name__)


def safe_decimal(value, default='0'):
    """Convert any value to Decimal safely — never raises InvalidOperation."""
    try:
        s = str(value).strip()
        if not s or s.lower() in ('none', 'null', ''):
            return Decimal(default)
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return Decimal(default)


def generate_invoice_number():
    today = date.today()
    prefix = f"INV-{today.strftime('%Y%m%d')}"
    last = Sale.query.filter(Sale.invoice_number.like(f'{prefix}%')).order_by(
        Sale.invoice_number.desc()).first()
    seq = int(last.invoice_number.split('-')[-1]) + 1 if last else 1
    return f"{prefix}-{seq:04d}"


@sales_bp.route('/')
@login_required
def index():
    page           = request.args.get('page', 1, type=int)
    search         = request.args.get('search', '')
    date_from      = request.args.get('date_from', '')
    date_to        = request.args.get('date_to', '')
    payment_method = request.args.get('payment_method', '')
    per_page       = current_app.config.get('ITEMS_PER_PAGE', 25)

    query = Sale.query
    if search:
        query = query.filter(Sale.invoice_number.ilike(f'%{search}%'))
    if date_from:
        query = query.filter(Sale.sale_date >= date_from)
    if date_to:
        query = query.filter(Sale.sale_date <= date_to + ' 23:59:59')
    if payment_method:
        query = query.filter_by(payment_method=payment_method)

    sales = query.order_by(Sale.sale_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    return render_template('sales/index.html', sales=sales, search=search,
                           date_from=date_from, date_to=date_to,
                           payment_method=payment_method)


@sales_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    customers = Customer.query.filter_by(is_active=True).order_by(Customer.name).all()
    vat_rate  = current_app.config.get('VAT_RATE', 0.15)

    if request.method == 'POST':
        import json

        # ── Parse items ──────────────────────────────────────────
        try:
            items = json.loads(request.form.get('items_json', '[]'))
        except Exception:
            flash('Invalid cart data. Please try again.', 'danger')
            return redirect(url_for('sales.new'))

        if not items:
            flash('Cart is empty. Add products before completing a sale.', 'danger')
            return redirect(url_for('sales.new'))

        # ── Payment method & customer validation ─────────────────
        payment_method = request.form.get('payment_method', 'cash')
        customer_id    = request.form.get('customer_id', type=int)
        customer       = db.session.get(Customer, customer_id) if customer_id else None

        if payment_method == 'credit':
            if not customer:
                flash('A registered customer must be selected for credit sales. Walk-in customers cannot buy on credit.', 'danger')
                return redirect(url_for('sales.new'))
            # Check credit limit
            if customer.credit_limit > 0:
                available_credit = float(customer.credit_limit) - float(customer.outstanding_balance)
                # We will check after computing total below

        # ── Build sale items & subtotal ───────────────────────────
        subtotal   = Decimal('0')
        sale_items = []
        for item in items:
            product = db.session.get(Product, int(item['product_id']))
            if not product:
                flash(f'Product not found (id={item["product_id"]}).', 'danger')
                return redirect(url_for('sales.new'))
            qty = int(item['quantity'])
            if product.current_stock < qty:
                flash(f'Insufficient stock for {product.name}. Available: {product.current_stock}', 'danger')
                return redirect(url_for('sales.new'))
            price = safe_decimal(item['unit_price'])
            disc  = safe_decimal(item.get('discount', 0))
            line  = price * qty * (1 - disc / 100)
            subtotal += line
            sale_items.append((product, qty, price, disc, line))

        # ── Compute totals ────────────────────────────────────────
        apply_tax       = bool(request.form.get('apply_tax'))
        tax_amount      = subtotal * safe_decimal(vat_rate) if apply_tax else Decimal('0')
        discount_amount = safe_decimal(request.form.get('extra_discount'))
        total           = subtotal + tax_amount - discount_amount
        total           = max(total, Decimal('0'))

        # ── Amount paid handling ──────────────────────────────────
        if payment_method == 'credit':
            # For credit: amount paid is whatever deposit was entered (default 0)
            amount_paid = safe_decimal(request.form.get('amount_paid', '0'))
        else:
            # For cash/momo: default to full total if field left blank
            raw_paid = request.form.get('amount_paid', '').strip()
            amount_paid = safe_decimal(raw_paid) if raw_paid else total

        amount_paid = max(amount_paid, Decimal('0'))
        change      = amount_paid - total
        change      = max(change, Decimal('0'))

        # ── Credit limit check ────────────────────────────────────
        if payment_method == 'credit' and customer and customer.credit_limit > 0:
            available_credit = float(customer.credit_limit) - float(customer.outstanding_balance)
            new_balance = float(total) - float(amount_paid)
            if new_balance > available_credit:
                flash(
                    f'Credit limit exceeded. '
                    f'{customer.name} has GHS {available_credit:,.2f} available credit '
                    f'but this sale requires GHS {new_balance:,.2f}.',
                    'danger'
                )
                return redirect(url_for('sales.new'))

        # ── Determine payment status ──────────────────────────────
        if payment_method == 'credit':
            if amount_paid >= total:
                payment_status = 'paid'
            elif amount_paid > 0:
                payment_status = 'partial'
            else:
                payment_status = 'credit'
        else:
            payment_status = 'paid' if amount_paid >= total else 'partial'

        # ── Create Sale record ────────────────────────────────────
        sale = Sale(
            invoice_number  = generate_invoice_number(),
            customer_id     = customer_id,
            user_id         = current_user.id,
            subtotal        = subtotal,
            tax_amount      = tax_amount,
            discount_amount = discount_amount,
            total_amount    = total,
            amount_paid     = amount_paid,
            change_given    = change,
            payment_method  = payment_method,
            payment_status  = payment_status,
            notes           = request.form.get('notes', ''),
        )
        db.session.add(sale)
        db.session.flush()

        # ── Create SaleItems & adjust stock ──────────────────────
        for product, qty, price, disc, line in sale_items:
            si = SaleItem(
                sale_id    = sale.id,
                product_id = product.id,
                quantity   = qty,
                unit_price = price,
                cost_price = product.cost_price,
                discount   = disc,
                line_total = line,
            )
            db.session.add(si)
            product.current_stock -= qty
            txn = InventoryTransaction(
                product_id     = product.id,
                transaction_type = 'sale',
                quantity       = qty,
                reference_id   = sale.id,
                reference_type = 'sale',
                user_id        = current_user.id,
            )
            db.session.add(txn)

        # ── Update customer outstanding balance ───────────────────
        if customer and payment_method == 'credit':
            owed = total - amount_paid
            if owed > 0:
                customer.outstanding_balance = (
                    safe_decimal(customer.outstanding_balance) + owed
                )

        db.session.commit()

        # Audit log
        try:
            from app.utils.audit import log_action
            log_action('create_sale', 'sales', sale.id,
                       f'Sale {sale.invoice_number} GHS {float(total):.2f} [{payment_method}]')
            db.session.commit()
        except Exception:
            pass

        flash(f'Sale {sale.invoice_number} recorded successfully.', 'success')
        return redirect(url_for('sales.receipt', sale_id=sale.id))

    return render_template('sales/new.html', customers=customers, vat_rate=vat_rate)


@sales_bp.route('/<int:sale_id>')
@login_required
def detail(sale_id):
    sale = db.get_or_404(Sale, sale_id)
    return render_template('sales/detail.html', sale=sale)


@sales_bp.route('/<int:sale_id>/receipt')
@login_required
def receipt(sale_id):
    sale = db.get_or_404(Sale, sale_id)
    return render_template('sales/receipt.html', sale=sale)


@sales_bp.route('/<int:sale_id>/record-payment', methods=['GET', 'POST'])
@login_required
def record_payment(sale_id):
    """Record a payment against an outstanding credit sale."""
    sale = db.get_or_404(Sale, sale_id)

    if sale.payment_status == 'paid':
        flash('This sale is already fully paid.', 'info')
        return redirect(url_for('sales.detail', sale_id=sale_id))

    if sale.is_voided:
        flash('Cannot record payment on a voided sale.', 'danger')
        return redirect(url_for('sales.detail', sale_id=sale_id))

    outstanding = sale.total_amount - sale.amount_paid

    if request.method == 'POST':
        amount = safe_decimal(request.form.get('amount', '0'))
        if amount <= 0:
            flash('Please enter a valid payment amount.', 'danger')
            return redirect(url_for('sales.record_payment', sale_id=sale_id))

        # Calculate how much of this payment actually clears the balance
        # Allow overpayment — excess becomes change
        amount_to_apply = min(amount, outstanding)   # only apply up to outstanding
        change_back     = amount - amount_to_apply    # anything over = change to give back

        sale.amount_paid  += amount_to_apply
        sale.change_given  = change_back
        new_outstanding    = sale.total_amount - sale.amount_paid

        if new_outstanding <= Decimal('0.01'):
            sale.payment_status = 'paid'
        else:
            sale.payment_status = 'partial'

        # Reduce customer outstanding balance by exactly what was applied
        if sale.customer:
            sale.customer.outstanding_balance = max(
                safe_decimal(sale.customer.outstanding_balance) - amount_to_apply,
                Decimal('0')
            )
        
        # Store change info in notes for receipt reference
        if change_back > Decimal('0.005') and not sale.notes:
            sale.notes = f'Change given: GHS {float(change_back):.2f}'
        elif change_back > Decimal('0.005'):
            sale.notes = sale.notes + f' | Change: GHS {float(change_back):.2f}'

        try:
            from app.utils.audit import log_action
            log_action('record_payment', 'sales', sale.id,
                       f'Payment GHS {float(amount):.2f} on {sale.invoice_number}')
        except Exception:
            pass

        db.session.commit()
        if change_back > Decimal('0.005'):
            flash(f'Payment of GHS {float(amount):,.2f} recorded. Change given: GHS {float(change_back):,.2f}. Balance cleared for {sale.invoice_number}.', 'success')
        elif new_outstanding <= Decimal('0.01'):
            flash(f'Full payment of GHS {float(amount_to_apply):,.2f} recorded. {sale.invoice_number} is now fully paid.', 'success')
        else:
            flash(f'Partial payment of GHS {float(amount_to_apply):,.2f} recorded. Remaining balance: GHS {float(new_outstanding):,.2f}.', 'info')
        return redirect(url_for('sales.detail', sale_id=sale_id))

    return render_template('sales/record_payment.html', sale=sale, outstanding=outstanding)


@sales_bp.route('/<int:sale_id>/void', methods=['POST'])
@login_required
def void_sale(sale_id):
    if not current_user.is_manager:
        flash('Manager permission required to void a sale.', 'danger')
        return redirect(url_for('sales.detail', sale_id=sale_id))
    sale = db.get_or_404(Sale, sale_id)
    if not sale.is_voided:
        sale.is_voided = True
        # Reverse stock
        for item in sale.items:
            item.product.current_stock += item.quantity
            txn = InventoryTransaction(
                product_id     = item.product_id,
                transaction_type = 'return_in',
                quantity       = item.quantity,
                reference_id   = sale.id,
                reference_type = 'sale',
                notes          = f'Void of {sale.invoice_number}',
                user_id        = current_user.id,
            )
            db.session.add(txn)
        # Reverse customer balance if credit
        if sale.customer and sale.payment_method == 'credit':
            owed = sale.total_amount - safe_decimal(str(sale.amount_paid) if sale.amount_paid else '0')
            if owed > 0:
                sale.customer.outstanding_balance = max(
                    safe_decimal(sale.customer.outstanding_balance) - owed,
                    Decimal('0')
                )
        db.session.commit()
        flash(f'Sale {sale.invoice_number} has been voided.', 'warning')
    return redirect(url_for('sales.detail', sale_id=sale_id))
