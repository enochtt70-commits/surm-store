# app/routes/settings.py
from decimal import Decimal

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models.accounting import Account, AccountTransaction, Expense
from app.models.customer import Customer
from app.models.inventory import InventoryTransaction
from app.models.product import Category, Product
from app.models.purchase import Purchase, PurchaseItem
from app.models.sale import Sale, SaleItem
from app.models.supplier import Supplier
from app.models.user import AuditLog, LoginHistory
from app.models.user import User

settings_bp = Blueprint('settings', __name__)

DATA_RECORD_TYPES = {
    'sales': (Sale, 'Sales'),
    'purchases': (Purchase, 'Purchases'),
    'expenses': (Expense, 'Expenses'),
    'products': (Product, 'Products'),
    'customers': (Customer, 'Customers'),
    'suppliers': (Supplier, 'Suppliers'),
    'categories': (Category, 'Categories'),
    'accounts': (Account, 'Accounts'),
    'account_transactions': (AccountTransaction, 'Account transactions'),
    'stock_history': (InventoryTransaction, 'Stock history'),
    'audit_history': (AuditLog, 'Audit history'),
    'login_history': (LoginHistory, 'Login history'),
}
DATA_RECORD_SINGULAR = {
    'sales': 'Sale',
    'purchases': 'Purchase',
    'expenses': 'Expense',
    'products': 'Product',
    'customers': 'Customer',
    'suppliers': 'Supplier',
    'categories': 'Category',
    'accounts': 'Account',
    'account_transactions': 'Account transaction',
    'stock_history': 'Stock history record',
    'audit_history': 'Audit history record',
    'login_history': 'Login history record',
}


def _require_super_admin():
    if not current_user.is_super_admin:
        flash('Super administrator access required.', 'danger')
        return redirect(url_for('dashboard.index'))
    return None


def _record_label(record_type, record):
    if record_type == 'sales':
        return f'{record.invoice_number} — GHS {record.total_amount:,.2f}'
    if record_type == 'purchases':
        return f'{record.po_number} — GHS {record.total_amount:,.2f}'
    if record_type == 'expenses':
        return f'{record.description} — GHS {record.amount:,.2f}'
    if record_type == 'products':
        return f'{record.name} ({record.sku})'
    if record_type in ('customers', 'suppliers', 'categories', 'accounts'):
        return record.name
    if record_type == 'account_transactions':
        return f'{record.transaction_type} — GHS {record.amount:,.2f} — {record.description or "No description"}'
    if record_type == 'stock_history':
        return f'{record.transaction_type} — product #{record.product_id} — quantity {record.quantity}'
    if record_type == 'audit_history':
        return f'{record.action} — {record.module or "system"} — {record.description or "No description"}'
    return f'{record.username or "Unknown user"} — {"successful" if record.success else "failed"} login'


def _delete_record(record_type, record):
    if record_type == 'sales':
        items = record.items.all()
        if not record.is_voided:
            for item in items:
                item.product.current_stock += item.quantity
        if record.customer and record.payment_method == 'credit':
            outstanding = max(
                Decimal(str(record.total_amount or 0)) - Decimal(str(record.amount_paid or 0)),
                Decimal('0'),
            )
            record.customer.outstanding_balance = max(
                Decimal(str(record.customer.outstanding_balance or 0)) - outstanding,
                Decimal('0'),
            )
        InventoryTransaction.query.filter_by(
            reference_type='sale', reference_id=record.id
        ).delete(synchronize_session=False)
    elif record_type == 'purchases':
        transactions = InventoryTransaction.query.filter_by(
            reference_type='purchase', reference_id=record.id
        ).all()
        received_by_product = {}
        for item in record.items.all():
            received_by_product[item.product_id] = (
                received_by_product.get(item.product_id, 0) + item.quantity_received
            )
        for product_id, quantity in received_by_product.items():
            product = db.session.get(Product, product_id)
            if product.current_stock < quantity:
                raise ValueError(
                    'This purchase cannot be deleted because some received stock has '
                    'since been sold or removed. Delete or adjust the related records first.'
                )
            product.current_stock -= quantity
        for transaction in transactions:
            db.session.delete(transaction)
    elif record_type == 'products':
        if record.sale_items.count() or record.purchase_items.count() or record.inventory_transactions.count():
            raise ValueError(
                'This product has sales, purchase, or stock history. Delete those related '
                'records first before deleting the product.'
            )
    elif record_type == 'customers' and record.sales:
        raise ValueError('This customer is linked to sales. Delete those sales first.')
    elif record_type == 'suppliers':
        if record.purchases:
            raise ValueError('This supplier is linked to purchases. Delete those purchases first.')
        Product.query.filter_by(supplier_id=record.id).update(
            {'supplier_id': None}, synchronize_session=False
        )
    elif record_type == 'categories' and record.products.count():
        raise ValueError('This category contains products. Delete those products first.')
    elif record_type == 'accounts':
        AccountTransaction.query.filter_by(account_id=record.id).delete(
            synchronize_session=False
        )
    db.session.delete(record)


@settings_bp.route('/data-management')
@login_required
def data_management():
    denied = _require_super_admin()
    if denied:
        return denied

    record_type = request.args.get('type', 'sales')
    if record_type not in DATA_RECORD_TYPES:
        record_type = 'sales'
    selected_model, selected_label = DATA_RECORD_TYPES[record_type]
    counts = [
        (key, label, model.query.count())
        for key, (model, label) in DATA_RECORD_TYPES.items()
    ]
    records = selected_model.query.order_by(selected_model.id.desc()).paginate(
        page=request.args.get('page', 1, type=int),
        per_page=25,
        error_out=False,
    )
    return render_template(
        'settings/data_management.html',
        counts=counts,
        records=records,
        record_type=record_type,
        selected_label=selected_label,
        record_label=_record_label,
    )


@settings_bp.route('/data-management/<record_type>/<int:record_id>/delete', methods=['POST'])
@login_required
def delete_record(record_type, record_id):
    denied = _require_super_admin()
    if denied:
        return denied
    if record_type not in DATA_RECORD_TYPES:
        flash('Unknown record type.', 'danger')
        return redirect(url_for('settings.data_management'))

    model, _ = DATA_RECORD_TYPES[record_type]
    record = db.session.get(model, record_id)
    if record is None:
        flash(f'{DATA_RECORD_SINGULAR[record_type]} not found.', 'warning')
        return redirect(url_for('settings.data_management', type=record_type))

    try:
        _delete_record(record_type, record)
        if record_type != 'audit_history':
            db.session.add(AuditLog(
                user_id=current_user.id,
                action='delete_record',
                module=record_type,
                record_id=record_id,
                description=f'{DATA_RECORD_SINGULAR[record_type]} deleted',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:255],
            ))
        db.session.commit()
    except ValueError as error:
        db.session.rollback()
        flash(str(error), 'danger')
        return redirect(url_for('settings.data_management', type=record_type))
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception('Failed to delete %s record %s', record_type, record_id)
        flash('The record could not be deleted. No changes were saved.', 'danger')
        return redirect(url_for('settings.data_management', type=record_type))

    flash(f'{DATA_RECORD_SINGULAR[record_type]} deleted.', 'success')
    return redirect(url_for('settings.data_management', type=record_type))


@settings_bp.route('/data-management/reset', methods=['POST'])
@login_required
def reset_all_data():
    denied = _require_super_admin()
    if denied:
        return denied
    if request.form.get('confirmation') != 'CLEAR ALL DATA':
        flash('Type CLEAR ALL DATA exactly to confirm the reset.', 'danger')
        return redirect(url_for('settings.data_management'))
    if not current_user.check_password(request.form.get('password', '')):
        flash('The current password is incorrect. No data was changed.', 'danger')
        return redirect(url_for('settings.data_management'))

    deletion_order = (
        AuditLog,
        LoginHistory,
        SaleItem,
        Sale,
        PurchaseItem,
        Purchase,
        InventoryTransaction,
        AccountTransaction,
        Expense,
        Product,
        Customer,
        Supplier,
        Category,
        Account,
    )
    try:
        for model in deletion_order:
            db.session.query(model).delete(synchronize_session=False)
        User.query.update({User.last_login: None}, synchronize_session=False)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception('Failed to reset business data')
        flash('The reset failed. No changes were saved.', 'danger')
        return redirect(url_for('settings.data_management'))

    flash('All business data and history were cleared. User accounts were kept.', 'success')
    return redirect(url_for('settings.data_management'))


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
