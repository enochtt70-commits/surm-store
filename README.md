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

## Default Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Super Administrator | `admin` | `Admin@123` |
| Owner | `peterbrakoh` | `Peter@123` |
| Manager | `victoria` | `Victoria@123` |
| Accountant | `enoch` | `Enoch@123` |
| Shopkeeper | `michael` | `Michael@123` |

> **Change all passwords immediately after first login.**

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
