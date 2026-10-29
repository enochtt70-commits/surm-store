
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()

def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.products import products_bp
    from app.routes.inventory import inventory_bp
    from app.routes.sales import sales_bp
    from app.routes.purchases import purchases_bp
    from app.routes.suppliers import suppliers_bp
    from app.routes.customers import customers_bp
    from app.routes.accounting import accounting_bp
    from app.routes.reports import reports_bp
    from app.routes.users import users_bp
    from app.routes.settings import settings_bp

    app.register_blueprint(auth_bp,       url_prefix="/auth")
    app.register_blueprint(dashboard_bp,  url_prefix="/")
    app.register_blueprint(products_bp,   url_prefix="/products")
    app.register_blueprint(inventory_bp,  url_prefix="/inventory")
    app.register_blueprint(sales_bp,      url_prefix="/sales")
    app.register_blueprint(purchases_bp,  url_prefix="/purchases")
    app.register_blueprint(suppliers_bp,  url_prefix="/suppliers")
    app.register_blueprint(customers_bp,  url_prefix="/customers")
    app.register_blueprint(accounting_bp, url_prefix="/accounting")
    app.register_blueprint(reports_bp,    url_prefix="/reports")
    app.register_blueprint(users_bp,      url_prefix="/users")
    app.register_blueprint(settings_bp,   url_prefix="/settings")

    from datetime import date as _date
    app.jinja_env.globals.update(
        current_year=lambda: _date.today().year,
        fmt_currency=lambda a: f"GHS {float(a or 0):,.2f}",
    )

    with app.app_context():
        db.create_all()
        _seed()
    return app

def _seed():
    from app.models.user import User
    from app.models.product import Category
    from app.models.accounting import Account
    if not User.query.first():
        for uname,email,fname,role,pwd in [
            ("admin","admin@surmstore.com","Super Admin","super_admin","Admin@123"),
            ("peterbrakoh","peter@surmstore.com","Mr. Peter Brakoh","owner","Peter@123"),
            ("victoria","victoria@surmstore.com","Miss Victoria Eshun","manager","Victoria@123"),
            ("enoch","enoch@surmstore.com","Mr. Enoch Delali Tetteh","accountant","Enoch@123"),
            ("michael","michael@surmstore.com","Mr. Michael Obeng","shopkeeper","Michael@123"),
        ]:
            u = User(username=uname,email=email,full_name=fname,role=role)
            u.set_password(pwd)
            db.session.add(u)
    if not Category.query.first():
        for c in ["Pipes","PVC Fittings","Valves","Water Closets (WC)","Wash Basins",
                  "Pumps","Water Tanks","Taps","Adhesives","Hardware","Accessories",
                  "T & G","Glues","Silicone","Bends","Stop Cocks","Other Plumbing Materials"]:
            db.session.add(Category(name=c))
    if not Account.query.first():
        for name,atype,num in [
            ("Cash in Till","asset","1001"),("Mobile Money (MoMo)","asset","1002"),
            ("Accounts Receivable","asset","1010"),("Inventory Asset","asset","1020"),
            ("Sales Revenue","income","4001"),("Cost of Goods Sold","expense","5001"),
            ("Salaries","expense","6001"),("Rent","expense","6002"),
            ("Utilities","expense","6003"),("Transport","expense","6004"),
            ("Miscellaneous","expense","6009"),
        ]:
            db.session.add(Account(name=name,account_type=atype,account_number=num))
    db.session.commit()
