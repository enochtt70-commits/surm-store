from datetime import datetime, timezone
from app import db

class InventoryTransaction(db.Model):
    __tablename__ = 'inventory_transactions'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    transaction_type = db.Column(db.String(30), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_cost = db.Column(db.Numeric(12,2))
    reference_id = db.Column(db.Integer)
    reference_type = db.Column(db.String(20))
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    user = db.relationship('User', backref='inventory_transactions')
