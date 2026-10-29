# app/routes/reports.py
from flask import Blueprint, render_template, request, make_response
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import date, timedelta
from app import db
from app.models.sale import Sale, SaleItem
from app.models.product import Product, Category
from app.models.accounting import Expense
from app.models.purchase import Purchase
from app.utils.decorators import accountant_required

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/')
@login_required
def index():
    if not current_user.can_view_reports:
        from flask import flash, redirect, url_for
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard.index'))
    return render_template('reports/index.html')


@reports_bp.route('/sales-summary')
@login_required
def sales_summary():
    if not current_user.can_view_reports:
        from flask import flash, redirect, url_for
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard.index'))
    date_from = request.args.get('date_from', str(date.today().replace(day=1)))
    date_to   = request.args.get('date_to',   str(date.today()))
    sales = Sale.query.filter(
        Sale.sale_date >= date_from,
        Sale.sale_date <= date_to + ' 23:59:59',
        Sale.is_voided == False
    ).order_by(Sale.sale_date.desc()).all()

    total_revenue  = sum(float(s.total_amount)    for s in sales)
    total_tax      = sum(float(s.tax_amount)      for s in sales)
    total_discount = sum(float(s.discount_amount) for s in sales)

    # Revenue by payment method
    by_payment = {}
    for s in sales:
        by_payment[s.payment_method] = by_payment.get(s.payment_method, 0) + float(s.total_amount)

    # COGS for gross profit
    cogs = db.session.query(func.sum(SaleItem.quantity * Product.cost_price))\
        .join(Product).join(Sale)\
        .filter(Sale.sale_date >= date_from,
                Sale.sale_date <= date_to + ' 23:59:59',
                Sale.is_voided == False).scalar() or 0
    gross_profit = total_revenue - float(cogs)

    return render_template('reports/sales_summary.html',
        sales=sales, total_revenue=total_revenue, total_tax=total_tax,
        total_discount=total_discount, by_payment=by_payment,
        gross_profit=gross_profit, cogs=float(cogs),
        date_from=date_from, date_to=date_to)


@reports_bp.route('/inventory-report')
@login_required
def inventory_report():
    if not current_user.can_view_reports:
        from flask import flash, redirect, url_for
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard.index'))
    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()
    total_value  = sum(p.stock_value for p in products)
    low_stock    = [p for p in products if 0 < p.current_stock <= p.min_stock_level]
    out_of_stock = [p for p in products if p.current_stock == 0]
    # Fast/slow movers (last 30 days)
    thirty_ago = date.today() - timedelta(days=30)
    top_movers = db.session.query(Product.name,
            func.sum(SaleItem.quantity).label('sold'))\
        .join(SaleItem).join(Sale)\
        .filter(Sale.sale_date >= thirty_ago, Sale.is_voided == False)\
        .group_by(Product.id).order_by(func.sum(SaleItem.quantity).desc()).limit(10).all()
    slow_movers = db.session.query(Product.name,
            func.sum(SaleItem.quantity).label('sold'))\
        .join(SaleItem).join(Sale)\
        .filter(Sale.sale_date >= thirty_ago, Sale.is_voided == False)\
        .group_by(Product.id).order_by(func.sum(SaleItem.quantity).asc()).limit(10).all()
    return render_template('reports/inventory_report.html',
        products=products, total_value=total_value,
        low_stock=low_stock, out_of_stock=out_of_stock,
        top_movers=top_movers, slow_movers=slow_movers)


@reports_bp.route('/profit-loss')
@login_required
def profit_loss():
    if not current_user.can_view_reports:
        from flask import flash, redirect, url_for
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard.index'))
    date_from = request.args.get('date_from', str(date.today().replace(day=1)))
    date_to   = request.args.get('date_to',   str(date.today()))

    sales = Sale.query.filter(
        Sale.sale_date >= date_from,
        Sale.sale_date <= date_to + ' 23:59:59',
        Sale.is_voided == False).all()
    total_revenue = sum(float(s.total_amount) for s in sales)

    cogs = float(db.session.query(func.sum(SaleItem.quantity * Product.cost_price))
        .join(Product).join(Sale)
        .filter(Sale.sale_date >= date_from,
                Sale.sale_date <= date_to + ' 23:59:59',
                Sale.is_voided == False).scalar() or 0)

    expenses_total = float(db.session.query(func.sum(Expense.amount))
        .filter(Expense.expense_date >= date_from,
                Expense.expense_date <= date_to).scalar() or 0)

    # Expenses by category
    exp_by_cat = db.session.query(Expense.category, func.sum(Expense.amount))\
        .filter(Expense.expense_date >= date_from, Expense.expense_date <= date_to)\
        .group_by(Expense.category).all()

    gross_profit = total_revenue - cogs
    net_profit   = gross_profit - expenses_total

    return render_template('reports/profit_loss.html',
        total_revenue=total_revenue, cogs=cogs,
        expenses_total=expenses_total, exp_by_cat=exp_by_cat,
        gross_profit=gross_profit, net_profit=net_profit,
        date_from=date_from, date_to=date_to,
        sale_count=len(sales))


@reports_bp.route('/purchases-report')
@login_required
def purchases_report():
    if not current_user.can_view_reports:
        from flask import flash, redirect, url_for
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard.index'))
    date_from = request.args.get('date_from', str(date.today().replace(day=1)))
    date_to   = request.args.get('date_to',   str(date.today()))
    purchases = Purchase.query.filter(
        Purchase.purchase_date >= date_from,
        Purchase.purchase_date <= date_to + ' 23:59:59'
    ).order_by(Purchase.purchase_date.desc()).all()
    total = sum(float(p.total_amount) for p in purchases)
    paid  = sum(float(p.amount_paid)  for p in purchases)
    return render_template('reports/purchases_report.html',
        purchases=purchases, total=total, paid=paid, outstanding=total-paid,
        date_from=date_from, date_to=date_to)


@reports_bp.route('/expenses-report')
@login_required
def expenses_report():
    if not current_user.can_view_reports:
        from flask import flash, redirect, url_for
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard.index'))
    date_from = request.args.get('date_from', str(date.today().replace(day=1)))
    date_to   = request.args.get('date_to',   str(date.today()))
    expenses = Expense.query.filter(
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to
    ).order_by(Expense.expense_date.desc()).all()
    total = sum(float(e.amount) for e in expenses)
    by_cat = {}
    for e in expenses:
        by_cat[e.category] = by_cat.get(e.category, 0) + float(e.amount)
    return render_template('reports/expenses_report.html',
        expenses=expenses, total=total, by_cat=by_cat,
        date_from=date_from, date_to=date_to)
