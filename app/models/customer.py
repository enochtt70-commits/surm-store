from datetime import datetime, timezone
from decimal import Decimal
from app import db

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30), index=True)
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    city = db.Column(db.String(80))
    customer_type = db.Column(db.String(20), default='retail')
    credit_limit = db.Column(db.Numeric(12,2), default=0.00)
    outstanding_balance = db.Column(db.Numeric(12,2), default=0.00)
    loyalty_points = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    @property
    def total_purchases(self): return sum(float(s.total_amount) for s in self.sales if not s.is_voided)
