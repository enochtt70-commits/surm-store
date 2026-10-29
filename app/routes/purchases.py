# app/routes/purchases.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import date
from decimal import Decimal
from app import db
from app.models.purchase import Purchase, PurchaseItem
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.inventory import InventoryTransaction
import json

purchases_bp = Blueprint('purchases', __name__)


def generate_po_number():
    today = date.today()
    prefix = f"PO-{today.strftime('%Y%m%d')}"
    last = Purchase.query.filter(Purchase.po_number.like(f'{prefix}%')).order_by(
        Purchase.po_number.desc()).first()
    seq = int(last.po_number.split('-')[-1]) + 1 if last else 1
    return f"{prefix}-{seq:04d}"


@purchases_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    supplier_id = request.args.get('supplier_id', type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 25)

    query = Purchase.query
    if search:
        query = query.filter(Purchase.po_number.ilike(f'%{search}%'))
    if status:
        query = query.filter_by(status=status)
    if supplier_id:
        query = query.filter_by(supplier_id=supplier_id)

    purchases = query.order_by(Purchase.purchase_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    return render_template('purchases/index.html', purchases=purchases, suppliers=suppliers,
                           search=search, status=status, supplier_id=supplier_id)


@purchases_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if not current_user.is_manager:
        flash('Permission denied.', 'danger')
        return redirect(url_for('purchases.index'))
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()
    if request.method == 'POST':
        items_json = request.form.get('items_json', '[]')
        try:
            items = json.loads(items_json)
        except Exception:
            flash('Invalid items data.', 'danger')
            return redirect(url_for('purchases.new'))

        subtotal = Decimal('0')
        po_items = []
        for item in items:
            product = db.session.get(Product, int(item['product_id']))
            qty = int(item['quantity'])
            cost = Decimal(str(item['unit_cost']))
            line = qty * cost
            subtotal += line
            po_items.append((product, qty, cost, line))

        tax_amount = Decimal(str(request.form.get('tax_amount', 0)))
        total = subtotal + tax_amount

        purchase = Purchase(
            po_number=generate_po_number(),
            supplier_id=request.form.get('supplier_id', type=int),
            user_id=current_user.id,
            expected_date=request.form.get('expected_date') or None,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total,
            notes=request.form.get('notes', ''),
        )
        db.session.add(purchase)
        db.session.flush()

        for product, qty, cost, line in po_items:
            pi = PurchaseItem(purchase_id=purchase.id, product_id=product.id,
                              quantity_ordered=qty, unit_cost=cost, line_total=line)
            db.session.add(pi)

        db.session.commit()
        flash(f'Purchase Order {purchase.po_number} created.', 'success')
        return redirect(url_for('purchases.detail', purchase_id=purchase.id))

    return render_template('purchases/new.html', suppliers=suppliers, products=products)


@purchases_bp.route('/<int:purchase_id>')
@login_required
def detail(purchase_id):
    purchase = db.get_or_404(Purchase, purchase_id)
    return render_template('purchases/detail.html', purchase=purchase)


@purchases_bp.route('/<int:purchase_id>/receive', methods=['POST'])
@login_required
def receive(purchase_id):
    if not current_user.is_manager:
        flash('Permission denied.', 'danger')
        return redirect(url_for('purchases.detail', purchase_id=purchase_id))
    purchase = db.get_or_404(Purchase, purchase_id)
    if purchase.status in ('received', 'cancelled'):
        flash('Purchase already completed or cancelled.', 'warning')
        return redirect(url_for('purchases.detail', purchase_id=purchase_id))

    all_received = True
    for item in purchase.items:
        qty_key = f'qty_{item.id}'
        qty = request.form.get(qty_key, 0, type=int)
        if qty > 0:
            item.quantity_received += qty
            item.product.current_stock += qty
            txn = InventoryTransaction(
                product_id=item.product_id, transaction_type='purchase',
                quantity=qty, unit_cost=item.unit_cost,
                reference_id=purchase.id, reference_type='purchase',
                user_id=current_user.id
            )
            db.session.add(txn)
        if item.quantity_received < item.quantity_ordered:
            all_received = False

    purchase.status = 'received' if all_received else 'partial'
    purchase.received_date = date.today()
    db.session.commit()
    flash(f'Items received for {purchase.po_number}.', 'success')
    return redirect(url_for('purchases.detail', purchase_id=purchase_id))
