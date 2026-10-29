
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email         = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name     = db.Column(db.String(150), nullable=False)
    role          = db.Column(db.String(30), default='shopkeeper')
    is_active     = db.Column(db.Boolean, default=True)
    phone         = db.Column(db.String(20))
    last_login    = db.Column(db.DateTime)
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                               onupdate=lambda: datetime.now(timezone.utc))
    sales      = db.relationship('Sale', backref='cashier', lazy='dynamic', foreign_keys='Sale.user_id')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic', foreign_keys='AuditLog.user_id')

    def set_password(self, p): self.password_hash = generate_password_hash(p)
    def check_password(self, p): return check_password_hash(self.password_hash, p)

    @property
    def is_super_admin(self): return self.role == 'super_admin'
    @property
    def is_admin(self): return self.role in ('super_admin', 'owner')
    @property
    def is_manager(self): return self.role in ('super_admin', 'owner', 'manager')
    @property
    def is_accountant(self): return self.role in ('super_admin', 'owner', 'manager', 'accountant')
    @property
    def can_view_reports(self): return self.role in ('super_admin', 'owner', 'manager', 'accountant')
    @property
    def can_manage_products(self): return self.role in ('super_admin', 'owner', 'manager')
    @property
    def can_approve_adjustments(self): return self.role in ('super_admin', 'owner', 'manager')
    @property
    def role_display(self):
        return {'super_admin':'Super Administrator','owner':'Owner','manager':'Manager',
                'accountant':'Accountant / Auditor','shopkeeper':'Shopkeeper'}.get(self.role, self.role.title())
    def __repr__(self): return f'<User {self.username}>'

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    action      = db.Column(db.String(100), nullable=False)
    module      = db.Column(db.String(50))
    record_id   = db.Column(db.Integer)
    description = db.Column(db.Text)
    ip_address  = db.Column(db.String(45))
    user_agent  = db.Column(db.String(255))
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

class LoginHistory(db.Model):
    __tablename__ = 'login_history'
    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80), index=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    success    = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    login_user_rel = db.relationship('User', backref='login_history', foreign_keys=[user_id])

@login_manager.user_loader
def load_user(user_id): return db.session.get(User, int(user_id))
