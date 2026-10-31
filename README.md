# Surm Store Management System

A modern, secure, web-based store management system for **Surm Store** — a plumbing and hardware store located in **Bogoso, Western Region, Ghana**.

Built with Python Flask, SQLAlchemy, and SQLite.

---

## Features

- **Point of Sale (POS)** — fast product search, cart, VAT, discounts, change calculation
- **Sales Management** — cash, mobile money (MoMo), and credit/invoice sales
- **Credit Sales** — customer balance tracking, payment recording, change calculation
- **Inventory Management** — stock tracking, adjustments, low stock alerts
- **Purchase Orders** — supplier POs, goods received, stock auto-update
- **Accounting** — live cash/MoMo balances, expenses, profit & loss
- **Reports** — sales summary, inventory valuation, P&L, expenses
- **User Management** — role-based access (Super Admin, Owner, Manager, Accountant, Shopkeeper)
- **Audit Logs** — every user action recorded for theft prevention
- **Receipts** — thermal receipt and A4 invoice printing

---

## Local Development Login

The development database is seeded with sample users when it is empty. Their credentials are configured in `app/__init__.py` and are for local testing only. Production uses a separately configured administrator account; never use development credentials online.

## Deployment

The app can run on Render with PostgreSQL. Connect the GitHub repository to a Render web service, use `pip install -r requirements.txt` as the build command, and use `gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120` as the start command. Set:

- `FLASK_ENV` to `production`
- `SECRET_KEY` to a unique secret value
- `DATABASE_URL` to a persistent PostgreSQL connection string
- `INITIAL_ADMIN_USERNAME`, `INITIAL_ADMIN_EMAIL`, and `INITIAL_ADMIN_PASSWORD` to the first administrator's credentials

Set a unique `SECRET_KEY` of at least 32 characters and set the initial administrator password (at least 12 characters) as a secret in the hosting dashboard, not in Git or this file. The app creates only this administrator on a new production database; development sample accounts are not created in production. After the first administrator exists, the initial-credential variables are not used to replace or reset users.

Use persistent PostgreSQL storage for store records. The production configuration rejects SQLite, requires a valid `SECRET_KEY`, and enables secure session cookies.

---

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/enochtt70-commits/surm-store.git
cd surm-store
```

### 2. Create a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
# Copy the example file
cp .env.example .env

# Edit .env and set your SECRET_KEY
```

### 5. Run the application
```bash
python run.py
```

Open your browser at: **http://127.0.0.1:5000**

---

## Project Structure

```
surm-store/
├── app/
│   ├── models/          # Database models (User, Product, Sale, etc.)
│   ├── routes/          # Flask blueprints (auth, sales, inventory, etc.)
│   ├── static/
│   │   ├── css/         # Stylesheets
│   │   └── js/          # JavaScript (POS system)
│   ├── templates/       # Jinja2 HTML templates
│   └── utils/           # Helpers (audit, decorators)
├── config.py            # App configuration
├── run.py               # Entry point
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variable template
```

---

## Tech Stack

- **Backend:** Python 3, Flask 3
- **Database:** SQLite (via SQLAlchemy)
- **Frontend:** HTML5, CSS3, JavaScript (vanilla)
- **Auth:** Flask-Login with bcrypt password hashing
- **Security:** CSRF protection, role-based access control, audit logging

---

## Store Info

**Surm Store** | Bogoso, Western Region, Ghana
