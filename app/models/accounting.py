from datetime import datetime, timezone
from app import db

class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(30), nullable=False)
    account_number = db.Column(db.String(20), unique=True)
    balance = db.Column(db.Numeric(14,2), default=0.00)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    transactions = db.relationship('AccountTransaction', backref='account', lazy='dynamic')

class AccountTransaction(db.Model):
    __tablename__ = 'account_transactions'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False, index=True)
    transaction_type = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Numeric(12,2), nullable=False)
    description = db.Column(db.String(255))
    reference = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    transaction_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    user = db.relationship('User', backref='account_transactions')

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Numeric(12,2), nullable=False)
    payment_method = db.Column(db.String(30), default='cash')
    reference = db.Column(db.String(80))
    receipt_filename = db.Column(db.String(255))
    expense_date = db.Column(db.Date, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', backref='expenses')
