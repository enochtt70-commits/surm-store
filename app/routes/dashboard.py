# app/routes/dashboard.py
from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta, timezone, date
import json
from app import db
from app.models.sale import Sale, SaleItem
from app.models.product import Product
from app.models.purchase import Purchase
from app.models.customer import Customer
from app.models.supplier import Supplier
from app.models.accounting import Expense
from app.models.user import User

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    today = date.today()
    month_start = today.replace(day=1)

    today_sales = db.session.query(func.sum(Sale.total_amount)).filter(
        func.date(Sale.sale_date) == today, Sale.is_voided == False).scalar() or 0
    month_sales = db.session.query(func.sum(Sale.total_amount)).filter(
        Sale.sale_date >= month_start, Sale.is_voided == False).scalar() or 0
    today_transactions = Sale.query.filter(
        func.date(Sale.sale_date) == today, Sale.is_voided == False).count()

    # Profit calculation (revenue - COGS)
    today_cogs = db.session.query(func.sum(SaleItem.quantity * Product.cost_price))\
        .join(Product).join(Sale)\
        .filter(func.date(Sale.sale_date) == today, Sale.is_voided == False).scalar() or 0
    month_cogs = db.session.query(func.sum(SaleItem.quantity * Product.cost_price))\
        .join(Product).join(Sale)\
        .filter(Sale.sale_date >= month_start, Sale.is_voided == False).scalar() or 0
    today_profit  = float(today_sales) - float(today_cogs)
    month_profit  = float(month_sales) - float(month_cogs)

    low_stock_products = Product.query.filter(
        Product.current_stock <= Product.min_stock_level, Product.is_active == True
    ).order_by(Product.current_stock.asc()).limit(15).all()
    out_of_stock = Product.query.filter_by(current_stock=0, is_active=True).count()
    reorder_needed = Product.query.filter(
        Product.current_stock <= Product.reorder_point, Product.is_active == True).count()
    recent_sales = Sale.query.filter_by(is_voided=False).order_by(Sale.sale_date.desc()).limit(10).all()
    pending_purchases = Purchase.query.filter(Purchase.status.in_(['ordered','partial'])).count()
    month_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.expense_date >= month_start).scalar() or 0
    total_customers = Customer.query.filter_by(is_active=True).count()
    total_products = Product.query.filter_by(is_active=True).count()
    logged_in_count = 1  # current user at minimum

    # Weekly chart data (last 7 days)
    weekly_labels, weekly_sales_data, weekly_profit_data = [], [], []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        amt = float(db.session.query(func.sum(Sale.total_amount)).filter(
            func.date(Sale.sale_date) == day, Sale.is_voided == False).scalar() or 0)
        cgs = float(db.session.query(func.sum(SaleItem.quantity * Product.cost_price))
            .join(Product).join(Sale)
            .filter(func.date(Sale.sale_date) == day, Sale.is_voided == False).scalar() or 0)
        weekly_labels.append(day.strftime('%a'))
        weekly_sales_data.append(round(amt, 2))
        weekly_profit_data.append(round(amt - cgs, 2))

    # Monthly sales last 6 months
    monthly_labels, monthly_sales_data = [], []
    for i in range(5, -1, -1):
        # go back i months
        yr = today.year
        mo = today.month - i
        while mo <= 0:
            mo += 12; yr -= 1
        ms = date(yr, mo, 1)
        me = date(yr, mo+1, 1) if mo < 12 else date(yr+1, 1, 1)
        amt = float(db.session.query(func.sum(Sale.total_amount)).filter(
            Sale.sale_date >= ms, Sale.sale_date < me, Sale.is_voided == False).scalar() or 0)
        monthly_labels.append(ms.strftime('%b %Y'))
        monthly_sales_data.append(round(amt, 2))

    return render_template('dashboard/index.html',
        today_sales=today_sales, month_sales=month_sales,
        today_profit=today_profit, month_profit=month_profit,
        today_transactions=today_transactions,
        low_stock_products=low_stock_products,
        out_of_stock=out_of_stock, reorder_needed=reorder_needed,
        recent_sales=recent_sales, pending_purchases=pending_purchases,
        month_expenses=month_expenses, total_customers=total_customers,
        total_products=total_products, logged_in_count=logged_in_count,
        weekly_labels=json.dumps(weekly_labels),
        weekly_sales_data=json.dumps(weekly_sales_data),
        weekly_profit_data=json.dumps(weekly_profit_data),
        monthly_labels=json.dumps(monthly_labels),
        monthly_sales_data=json.dumps(monthly_sales_data),
    )
