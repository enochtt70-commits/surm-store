from datetime import datetime, timezone
from app import db

class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    purchase_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    expected_date = db.Column(db.Date)
    received_date = db.Column(db.Date)
    subtotal = db.Column(db.Numeric(12,2), default=0.00)
    tax_amount = db.Column(db.Numeric(12,2), default=0.00)
    total_amount = db.Column(db.Numeric(12,2), default=0.00)
    amount_paid = db.Column(db.Numeric(12,2), default=0.00)
    payment_status = db.Column(db.String(20), default='unpaid')
    status = db.Column(db.String(20), default='ordered')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    items = db.relationship('PurchaseItem', backref='purchase', lazy='dynamic', cascade='all, delete-orphan')
    supplier = db.relationship('Supplier', backref='purchases')
    ordered_by = db.relationship('User', backref='purchases', foreign_keys=[user_id])

class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_ordered = db.Column(db.Integer, nullable=False)
    quantity_received = db.Column(db.Integer, default=0)
    unit_cost = db.Column(db.Numeric(12,2), nullable=False)
    line_total = db.Column(db.Numeric(12,2), nullable=False)
