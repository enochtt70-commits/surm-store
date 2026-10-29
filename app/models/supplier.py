from datetime import datetime, timezone
from app import db

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    city = db.Column(db.String(80))
    region = db.Column(db.String(80))
    tin_number = db.Column(db.String(50))
    payment_terms = db.Column(db.Integer, default=30)
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    products = db.relationship('Product', backref='supplier', lazy='dynamic', foreign_keys='Product.supplier_id')
