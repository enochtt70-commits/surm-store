# app/routes/inventory.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import date
from app import db
from app.models.product import Product
from app.models.inventory import InventoryTransaction

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    filter_type = request.args.get('filter', 'low_stock')

    query = Product.query.filter_by(is_active=True)
    if filter_type == 'low_stock':
        query = query.filter(Product.current_stock <= Product.min_stock_level)
    elif filter_type == 'out_of_stock':
        query = query.filter_by(current_stock=0)
    elif filter_type == 'over_stock':
        query = query.filter(Product.current_stock >= Product.max_stock_level)
    if search:
        query = query.filter(
            db.or_(Product.name.ilike(f'%{search}%'), Product.sku.ilike(f'%{search}%'))
        )

    products = query.order_by(Product.current_stock.asc()).paginate(page=page, per_page=25, error_out=False)
    return render_template('inventory/index.html', products=products, search=search, filter_type=filter_type)


@inventory_bp.route('/adjust', methods=['GET', 'POST'])
@login_required
def adjust():
    if not current_user.is_manager:
        flash('Permission denied.', 'danger')
        return redirect(url_for('inventory.index'))
    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()
    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        adj_type = request.form.get('adjustment_type')
        quantity = request.form.get('quantity', 0, type=int)
        notes = request.form.get('notes', '')
        product = db.get_or_404(Product, product_id)
        if adj_type == 'add':
            product.current_stock += quantity
            txn_type = 'adjustment_in'
        elif adj_type == 'remove':
            if product.current_stock < quantity:
                flash('Insufficient stock for removal.', 'danger')
                return redirect(url_for('inventory.adjust'))
            product.current_stock -= quantity
            txn_type = 'adjustment_out'
        elif adj_type == 'set':
            diff = quantity - product.current_stock
            txn_type = 'adjustment_in' if diff >= 0 else 'adjustment_out'
            quantity = abs(diff)
            product.current_stock = int(request.form.get('quantity', type=int))
        txn = InventoryTransaction(
            product_id=product.id,
            transaction_type=txn_type,
            quantity=quantity,
            notes=notes,
            user_id=current_user.id
        )
        db.session.add(txn)
        db.session.commit()
        flash(f'Stock adjusted for {product.name}.', 'success')
        return redirect(url_for('inventory.index'))
    return render_template('inventory/adjust.html', products=products)


@inventory_bp.route('/transactions')
@login_required
def transactions():
    page = request.args.get('page', 1, type=int)
    product_id = request.args.get('product_id', type=int)
    txn_type = request.args.get('type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    query = InventoryTransaction.query
    if product_id:
        query = query.filter_by(product_id=product_id)
    if txn_type:
        query = query.filter_by(transaction_type=txn_type)
    if date_from:
        query = query.filter(InventoryTransaction.created_at >= date_from)
    if date_to:
        query = query.filter(InventoryTransaction.created_at <= date_to + ' 23:59:59')

    transactions = query.order_by(InventoryTransaction.created_at.desc()).paginate(
        page=page, per_page=25, error_out=False)
    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()
    return render_template('inventory/transactions.html', transactions=transactions,
                           products=products, product_id=product_id, txn_type=txn_type)
