# app/routes/products.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.product import Product, Category
from app.models.supplier import Supplier

products_bp = Blueprint('products', __name__)


@products_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    status = request.args.get('status', 'active')
    per_page = current_app.config.get('ITEMS_PER_PAGE', 25)

    query = Product.query
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    if search:
        query = query.filter(
            db.or_(Product.name.ilike(f'%{search}%'),
                   Product.sku.ilike(f'%{search}%'),
                   Product.barcode.ilike(f'%{search}%'))
        )
    if category_id:
        query = query.filter_by(category_id=category_id)

    products = query.order_by(Product.name).paginate(page=page, per_page=per_page, error_out=False)
    categories = Category.query.order_by(Category.name).all()
    return render_template('products/index.html', products=products, categories=categories,
                           search=search, category_id=category_id, status=status)


@products_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if not current_user.is_manager:
        flash('Permission denied.', 'danger')
        return redirect(url_for('products.index'))
    categories = Category.query.order_by(Category.name).all()
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    if request.method == 'POST':
        product = Product(
            name=request.form['name'].strip(),
            sku=request.form['sku'].strip().upper(),
            barcode=request.form.get('barcode', '').strip() or None,
            description=request.form.get('description', '').strip(),
            category_id=request.form.get('category_id', type=int),
            unit=request.form.get('unit', 'piece'),
            cost_price=request.form.get('cost_price', 0, type=float),
            selling_price=request.form['selling_price'],
            wholesale_price=request.form.get('wholesale_price', type=float),
            min_stock_level=request.form.get('min_stock_level', 10, type=int),
            max_stock_level=request.form.get('max_stock_level', 500, type=int),
            reorder_point=request.form.get('reorder_point', 15, type=int),
            is_taxable=bool(request.form.get('is_taxable')),
            supplier_id=request.form.get('supplier_id', type=int),
        )
        db.session.add(product)
        db.session.commit()
        flash(f'Product "{product.name}" created successfully.', 'success')
        return redirect(url_for('products.index'))
    return render_template('products/form.html', product=None, categories=categories, suppliers=suppliers)


@products_bp.route('/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(product_id):
    if not current_user.is_manager:
        flash('Permission denied.', 'danger')
        return redirect(url_for('products.index'))
    product = db.get_or_404(Product, product_id)
    categories = Category.query.order_by(Category.name).all()
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    if request.method == 'POST':
        product.name = request.form['name'].strip()
        product.sku = request.form['sku'].strip().upper()
        product.barcode = request.form.get('barcode', '').strip() or None
        product.description = request.form.get('description', '').strip()
        product.category_id = request.form.get('category_id', type=int)
        product.unit = request.form.get('unit', 'piece')
        product.cost_price = request.form.get('cost_price', 0, type=float)
        product.selling_price = request.form['selling_price']
        product.wholesale_price = request.form.get('wholesale_price', type=float)
        product.min_stock_level = request.form.get('min_stock_level', 10, type=int)
        product.max_stock_level = request.form.get('max_stock_level', 500, type=int)
        product.reorder_point = request.form.get('reorder_point', 15, type=int)
        product.is_taxable = bool(request.form.get('is_taxable'))
        product.supplier_id = request.form.get('supplier_id', type=int)
        db.session.commit()
        flash(f'Product "{product.name}" updated.', 'success')
        return redirect(url_for('products.index'))
    return render_template('products/form.html', product=product, categories=categories, suppliers=suppliers)


@products_bp.route('/<int:product_id>')
@login_required
def detail(product_id):
    product = db.get_or_404(Product, product_id)
    return render_template('products/detail.html', product=product)


@products_bp.route('/<int:product_id>/toggle', methods=['POST'])
@login_required
def toggle(product_id):
    if not current_user.is_manager:
        return jsonify({'error': 'Permission denied'}), 403
    product = db.get_or_404(Product, product_id)
    product.is_active = not product.is_active
    db.session.commit()
    return jsonify({'active': product.is_active})


@products_bp.route('/categories')
@login_required
def categories():
    cats = Category.query.order_by(Category.name).all()
    return render_template('products/categories.html', categories=cats)


@products_bp.route('/categories/new', methods=['POST'])
@login_required
def new_category():
    if not current_user.is_manager:
        flash('Permission denied.', 'danger')
        return redirect(url_for('products.categories'))
    name = request.form.get('name', '').strip()
    if name:
        cat = Category(name=name, description=request.form.get('description', ''))
        db.session.add(cat)
        db.session.commit()
        flash(f'Category "{name}" created.', 'success')
    return redirect(url_for('products.categories'))


@products_bp.route('/search-json')
def search_json():
    # Return JSON 401 instead of redirecting – needed for AJAX fetch from POS page
    from flask_login import current_user as cu
    if not cu.is_authenticated:
        return jsonify({'error': 'Not authenticated'}), 401
    q = request.args.get('q', '').strip()
    products = Product.query.filter(
        Product.is_active == True,
        db.or_(Product.name.ilike(f'%{q}%'), Product.sku.ilike(f'%{q}%'),
               Product.barcode.ilike(f'%{q}%'))
    ).order_by(Product.name).limit(20).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'sku': p.sku,
        'price': float(p.selling_price),
        'stock': p.current_stock,
        'unit': p.unit
    } for p in products])
