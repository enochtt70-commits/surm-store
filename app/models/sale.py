from datetime import datetime, timezone
from app import db

class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sale_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    subtotal = db.Column(db.Numeric(12,2), default=0.00)
    tax_amount = db.Column(db.Numeric(12,2), default=0.00)
    discount_amount = db.Column(db.Numeric(12,2), default=0.00)
    total_amount = db.Column(db.Numeric(12,2), default=0.00)
    amount_paid = db.Column(db.Numeric(12,2), default=0.00)
    change_given = db.Column(db.Numeric(12,2), default=0.00)
    payment_method = db.Column(db.String(30), default='cash')
    payment_status = db.Column(db.String(20), default='paid')
    notes = db.Column(db.Text)
    is_voided = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    items = db.relationship('SaleItem', backref='sale', lazy='dynamic', cascade='all, delete-orphan')
    customer = db.relationship('Customer', backref='sales')

class SaleItem(db.Model):
    __tablename__ = 'sale_items'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(12,2), nullable=False)
    cost_price = db.Column(db.Numeric(12,2), default=0.00)
    discount = db.Column(db.Numeric(5,2), default=0.00)
    line_total = db.Column(db.Numeric(12,2), nullable=False)
