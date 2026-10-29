# app/routes/accounting.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import func
from app import db
from app.models.accounting import Account, AccountTransaction, Expense
from app.models.sale import Sale
from app.models.purchase import Purchase

accounting_bp = Blueprint('accounting', __name__)


def parse_date(value, default=None):
    if not value or not str(value).strip():
        return default or date.today()
    val = str(value).strip()
    if isinstance(val, date):
        return val
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return default or date.today()


def get_account_balances():
    """
    Compute live balances for the main accounts from actual transaction data.
    The Account.balance column is NOT used — balances are always calculated live.
    """
    today      = date.today()
    month_start = today.replace(day=1)

    # ── Cash in Till (account 1001) ──────────────────────────────
    cash_sales = db.session.query(func.sum(Sale.amount_paid)).filter(
        Sale.payment_method == 'cash',
        Sale.is_voided == False
    ).scalar() or Decimal('0')

    cash_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.payment_method == 'cash'
    ).scalar() or Decimal('0')

    cash_purchases = db.session.query(func.sum(Purchase.amount_paid)).filter(
        Purchase.payment_status.in_(['paid','partial'])
    ).scalar() or Decimal('0')

    cash_balance = float(cash_sales) - float(cash_expenses) - float(cash_purchases)

    # ── Mobile Money (account 1002) ───────────────────────────────
    momo_sales = db.session.query(func.sum(Sale.amount_paid)).filter(
        Sale.payment_method == 'momo',
        Sale.is_voided == False
    ).scalar() or Decimal('0')

    momo_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.payment_method == 'momo'
    ).scalar() or Decimal('0')

    momo_balance = float(momo_sales) - float(momo_expenses)

    # ── Accounts Receivable (account 1010) ────────────────────────
    credit_total = db.session.query(func.sum(Sale.total_amount)).filter(
        Sale.payment_method == 'credit',
        Sale.payment_status != 'paid',
        Sale.is_voided == False
    ).scalar() or Decimal('0')

    credit_paid = db.session.query(func.sum(Sale.amount_paid)).filter(
        Sale.payment_method == 'credit',
        Sale.is_voided == False
    ).scalar() or Decimal('0')

    receivable_balance = float(credit_total) - float(credit_paid)

    # ── Sales Revenue (account 4001) ──────────────────────────────
    total_revenue = db.session.query(func.sum(Sale.total_amount)).filter(
        Sale.is_voided == False
    ).scalar() or Decimal('0')

    # ── Total Expenses (account 6xxx) ─────────────────────────────
    total_expenses = db.session.query(func.sum(Expense.amount)).scalar() or Decimal('0')

    # ── Month summaries ───────────────────────────────────────────
    month_sales = db.session.query(func.sum(Sale.total_amount)).filter(
        Sale.sale_date >= month_start,
        Sale.is_voided == False
    ).scalar() or Decimal('0')

    month_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.expense_date >= month_start
    ).scalar() or Decimal('0')

    month_profit = float(month_sales) - float(month_expenses)

    return {
        'cash_balance':       round(cash_balance, 2),
        'momo_balance':       round(momo_balance, 2),
        'receivable_balance': round(receivable_balance, 2),
        'total_revenue':      float(total_revenue),
        'total_expenses':     float(total_expenses),
        'month_sales':        float(month_sales),
        'month_expenses':     float(month_expenses),
        'month_profit':       round(month_profit, 2),
    }


@accounting_bp.route('/')
@login_required
def index():
    balances = get_account_balances()

    # Expenses by category for current month
    today = date.today()
    month_start = today.replace(day=1)
    exp_by_cat = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.expense_date >= month_start
    ).group_by(Expense.category).all()

    # Recent expenses
    recent_expenses = Expense.query.order_by(
        Expense.expense_date.desc(), Expense.created_at.desc()
    ).limit(10).all()

    # Credit sales outstanding
    from app.models.customer import Customer
    credit_sales = Sale.query.filter(
        Sale.payment_method == 'credit',
        Sale.payment_status != 'paid',
        Sale.is_voided == False
    ).order_by(Sale.sale_date.desc()).limit(10).all()

    return render_template('accounting/index.html',
        balances=balances,
        exp_by_cat=exp_by_cat,
        recent_expenses=recent_expenses,
        credit_sales=credit_sales,
    )


@accounting_bp.route('/expenses')
@login_required
def expenses():
    page      = request.args.get('page', 1, type=int)
    date_from = request.args.get('date_from', '')
    date_to   = request.args.get('date_to', '')
    category  = request.args.get('category', '')
    per_page  = current_app.config.get('ITEMS_PER_PAGE', 25)

    query = Expense.query
    if date_from:
        query = query.filter(Expense.expense_date >= parse_date(date_from))
    if date_to:
        query = query.filter(Expense.expense_date <= parse_date(date_to))
    if category:
        query = query.filter_by(category=category)

    expenses = query.order_by(Expense.expense_date.desc(), Expense.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)

    # Totals for filtered set
    total_filtered = sum(float(e.amount) for e in expenses.items)

    return render_template('accounting/expenses.html',
        expenses=expenses, date_from=date_from, date_to=date_to,
        category=category, total_filtered=total_filtered)


@accounting_bp.route('/expenses/new', methods=['GET', 'POST'])
@login_required
def new_expense():
    if request.method == 'POST':
        exp = Expense(
            description    = request.form['description'].strip(),
            category       = request.form['category'].strip(),
            amount         = request.form.get('amount', 0, type=float),
            payment_method = request.form.get('payment_method', 'cash'),
            reference      = request.form.get('reference', '').strip(),
            expense_date   = parse_date(request.form.get('expense_date')),
            notes          = request.form.get('notes', '').strip(),
            user_id        = current_user.id,
        )
        db.session.add(exp)
        db.session.commit()
        flash(f'Expense of GHS {exp.amount:,.2f} recorded successfully.', 'success')
        return redirect(url_for('accounting.expenses'))
    return render_template('accounting/expense_form.html',
        expense=None, today=date.today().isoformat())


@accounting_bp.route('/expenses/<int:expense_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    if not current_user.is_manager:
        flash('Permission denied.', 'danger')
        return redirect(url_for('accounting.expenses'))
    exp = db.get_or_404(Expense, expense_id)
    if request.method == 'POST':
        exp.description    = request.form['description'].strip()
        exp.category       = request.form['category'].strip()
        exp.amount         = request.form.get('amount', 0, type=float)
        exp.payment_method = request.form.get('payment_method', 'cash')
        exp.reference      = request.form.get('reference', '').strip()
        exp.expense_date   = parse_date(request.form.get('expense_date'))
        exp.notes          = request.form.get('notes', '').strip()
        db.session.commit()
        flash('Expense updated successfully.', 'success')
        return redirect(url_for('accounting.expenses'))
    return render_template('accounting/expense_form.html',
        expense=exp, today=date.today().isoformat())
