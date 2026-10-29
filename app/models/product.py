from datetime import datetime, timezone
from app import db

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    products = db.relationship('Product', backref='category', lazy='dynamic')

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    barcode = db.Column(db.String(100), unique=True, index=True)
    description = db.Column(db.Text)
    brand = db.Column(db.String(100))
    shelf_location = db.Column(db.String(50))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    unit = db.Column(db.String(30), default='piece')
    cost_price = db.Column(db.Numeric(12, 2), default=0.00)
    selling_price = db.Column(db.Numeric(12, 2), nullable=False)
    wholesale_price = db.Column(db.Numeric(12, 2))
    current_stock = db.Column(db.Integer, default=0)
    min_stock_level = db.Column(db.Integer, default=10)
    max_stock_level = db.Column(db.Integer, default=500)
    reorder_point = db.Column(db.Integer, default=15)
    is_active = db.Column(db.Boolean, default=True)
    is_taxable = db.Column(db.Boolean, default=True)
    image_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    sale_items = db.relationship('SaleItem', backref='product', lazy='dynamic')
    purchase_items = db.relationship('PurchaseItem', backref='product', lazy='dynamic')
    inventory_transactions = db.relationship('InventoryTransaction', backref='product', lazy='dynamic')

    @property
    def is_low_stock(self): return self.current_stock <= self.min_stock_level
    @property
    def stock_value(self): return float(self.cost_price) * self.current_stock
