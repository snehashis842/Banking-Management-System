# Banking Management System (Flask + MongoDB)

A **secure, role-based banking management system** built with **Flask** and **MongoDB**. Supports Admin, Employee, and Customer roles, with self-signup, session-based authentication, hashed passwords, transactions, dashboards, email notifications, and transaction analytics via Matplotlib.

---

## 🚀 Features

### 🔐 Authentication & Security

- Self-signup for new customers, plus admin-created accounts for any role
- Passwords hashed with Werkzeug's `generate_password_hash` (no plaintext or reversible encoding stored)
- Default password format `Test@DDMMYYYY` (based on DOB), emailed to the user on account creation
- Session-based authentication with a configurable session lifetime
- Role-based access control (Super_Admin / Admin / Employee / Customer)
- Login history tracking

### 🧑‍💼 Admin Module

- Create users of any role, with auto-generated User IDs
- View all users and their activity status
- Monthly login statistics and reports emailed to Super_Admin
- System-wide dashboards

### 👨‍🔧 Employee Module

- View customer transactions (read-only)

### 👤 Customer Module

- Self-service signup
- Credit / debit transactions with real-time balance updates
- Downloadable 6-month transaction chart (PNG)
- Email notifications on login and transactions

### 📈 Analytics & Reporting

- Login history aggregation
- Transaction history aggregation
- Matplotlib chart generation
- Admin dashboard metrics

---

## 🛠️ Tech Stack

**Backend:** Python, Flask (application factory + blueprints), Flask-Caching, session-based auth
**Database:** MongoDB (pymongo), indexed collections, connection pooling
**Other:** Matplotlib (charts), SMTP for email, Werkzeug for password hashing, `python-dotenv` for config

---

## 📁 Project Structure

```
banking_management_system/
├─ run.py                     # Entry point
├─ requirements.txt
├─ .env.example                # Copy to .env and fill in real values
├─ .gitignore
├─ reset_password.py           # One-off: fix a single legacy-password account
├─ migrate_passwords.py        # Bulk-fix all legacy-password accounts
├─ app/
│  ├─ __init__.py              # create_app() application factory
│  ├─ config.py                # All environment-based configuration
│  ├─ extensions.py            # Shared Flask-Caching instance
│  ├─ db.py                    # MongoDB connection, collections, indexes, ID generation
│  ├─ security.py              # Password hashing / verification / generation
│  ├─ validators.py            # Request payload validation
│  ├─ auth.py                  # Auth/role decorators (require_admin, etc.)
│  ├─ reference.py             # Role/status name lookups
│  ├─ locations.py             # Indian states/cities reference data
│  ├─ email_utils.py           # Welcome emails, login alerts, monthly reports
│  ├─ charts.py                # Matplotlib transaction chart generation
│  └─ routes/
│     ├─ auth_routes.py        # /, /login, /signup, /logout
│     ├─ user_routes.py        # /add_user, /get_users, roles/states/cities
│     ├─ dashboard_routes.py   # /dashboard, stats, monthly report
│     └─ transaction_routes.py # Transactions, chart download
├─ templates/                  # Jinja2 templates
└─ static/
   ├─ css/style.css
   └─ js/common.js
```

---

## ⚙️ Setup Instructions

### Prerequisites

- Python 3.12 (3.13+ is not currently supported by this stack — some dependencies rely on `pkgutil.get_loader`, removed in 3.13)
- MongoDB running locally, or a cloud URI (e.g. MongoDB Atlas)
- An SMTP account for email features (e.g. Gmail with an App Password)

### 1) Clone the repository

```bash
git clone https://github.com/snehashis842/Banking-Management-System.git
cd Banking-Management-System
```

### 2) Create a virtual environment (kept outside the repo, or `.gitignore`d if inside it)

**macOS / Linux**
```bash
python3.12 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell)**
```powershell
py -3.12 -m venv venv
venv\Scripts\Activate.ps1
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Configure environment variables

```bash
cp .env.example .env   # Windows: copy .env.example .env
```

Edit `.env` with real values:

```
MONGO_URI=mongodb://localhost:27017/
DB_NAME=project
FLASK_SECRET=<generate with the command below>
FLASK_ENV=development
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
ADMIN_EMAILS=admin1@example.com,admin2@example.com
```

Generate a real secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

> **Using Gmail SMTP:** enable 2-Step Verification on your Google account, then create an App Password and use it as `SMTP_PASSWORD`.

### 5) Start MongoDB

Make sure your MongoDB server is running (local `mongod`, a Docker container, or an Atlas cluster referenced in `MONGO_URI`).

### 6) Run the app

```bash
python run.py
```

Open your browser at `http://localhost:5000`.

### 7) Creating your first account

- **New customers**: use the **Sign Up** link on the login page. The default password is `Test@DDMMYYYY` based on your date of birth, and is also emailed to you.
- **Admin/Employee/Super_Admin accounts**: must be created by an existing admin via the "Add User" page — there is no self-signup path for these roles.
- **Bootstrapping the very first admin**: since there's no self-signup for admin roles, insert one directly into MongoDB, or ask an existing project maintainer to create one for you via `/add_user`.

---

## 🔧 Utility Scripts

- `python reset_password.py <UserId> <NewPassword>` — resets one user's password (properly hashed).
- `python migrate_passwords.py` — bulk-fixes any accounts still on a legacy (non-hashed) password format, resetting them to the DOB-derived default.

---

## 📊 Transaction Chart

The Customer module generates a chart (PNG) showing daily credits vs. debits and balance history over the last 6 months, downloadable from the dashboard.

---

## 🔐 Security & Production Notes

- Passwords are hashed with Werkzeug (`pbkdf2`/`scrypt`) — never stored in plaintext or reversible encoding.
- All secrets (DB URI, SMTP credentials, session secret) are read from environment variables via `.env` — nothing is hardcoded in source.
- Before deploying to production:
  - Set a real, stable `FLASK_SECRET` (a random one is generated per-restart if unset, which breaks sessions across restarts/multi-worker deployments).
  - Turn off debug mode (`FLASK_ENV=production`).
  - Use HTTPS and secure cookie settings.
  - Enable MongoDB authentication.
  - Add rate-limiting to `/login` and `/signup`.
  - Run behind a production WSGI server (e.g. `gunicorn "app:create_app()"`), not Flask's built-in dev server.

---

## 📌 Future Improvements

- Rate limiting on login/signup
- User-initiated password change flow
- JWT-based authentication for stateless APIs
- Docker support for containerized deployment
- Automated tests, especially around transactions and auth
- Multi-branch banking support

---

## 🤝 Contributing

Pull requests and issue reports are welcome.

---

## 👨‍💻 Author

**Snehashis Das**
GitHub: [https://github.com/snehashis842](https://github.com/snehashis842)
Email: [snehashisdas842@gmail.com](mailto:snehashisdas842@gmail.com)
