# Banking Management System (Flask + MongoDB)

A **secure, role-based banking management system** built with **Flask**, **MongoDB**, and **REST APIs**. It supports Admin, Employee, and Customer roles and includes authentication, session management, auto-generated User IDs, transactions, dashboards, email notifications and simple transaction analytics using Matplotlib.

---

## 🚀 Features

### 🔐 Authentication & Security

* Login system with hashed passwords
* Session-based authentication
* Role-based access control (Admin / Employee / Customer)
* Login history tracking (timestamps)

### 🧑‍💼 Admin Module

* Create users with auto-generated User IDs
* View all users and activity status
* Manage roles and account status
* Monthly login statistics
* Automated monthly email reports to Super Admin (configurable)
* System-wide dashboards

### 👨‍🔧 Employee Module

* View customer transactions
* Read-only access to user details

### 👤 Customer Module

* Credit / debit transactions
* Real-time balance updates
* Download a 6-month transaction chart (PNG)
* Email notifications for logins and transactions
* View monthly transaction counts

### 📈 Analytics & Reporting

* Login history aggregation
* Transaction history aggregation
* Matplotlib chart generation
* Admin dashboard metrics

---

## 🛠️ Tech Stack

**Backend**

* Python
* Flask
* Flask-Caching (optional)
* REST APIs
* Session-based authentication

**Database**

* MongoDB (pymongo)
* Indexing for optimized queries
* Connection pooling

**Other Tools**

* Matplotlib (charting)
* SMTP for email notifications
* UUID for transaction IDs
* Datetime / Timedelta for date operations

---

## 📁 Project Structure

```
Banking-Management-System/
├─ app.py            # Main Flask application
├─ utils.py          # Helpers: DB, email, charts, validation
├─ requirements.txt
├─ templates/        # HTML templates
└─ static/           # CSS, JS, generated charts
```

---

## ⚙️ Setup Instructions

Follow these steps to get the project running on your machine.

### Prerequisites

* Python 3.10+ installed
* MongoDB running locally (or a cloud URI)
* (Optional) SMTP account for email features

### 1) Clone the repository

```bash
git clone https://github.com/snehashis842/Banking-Management-System.git
cd Banking-Management-System
```

### 2) Create and activate a virtual environment

**macOS / Linux**

```bash
python -m venv venv
source venv/bin/activate
```

**Windows (PowerShell)**

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**Windows (cmd.exe)**

```cmd
python -m venv venv
venv\Scripts\activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Configure environment (optional but recommended)

Create a `.env` file or set environment variables for sensitive configuration. Example variables:

```
MONGO_URI=mongodb://localhost:27017/
DB_NAME=banking_system
FLASK_SECRET=change-me-secret-key
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

> **Using Gmail SMTP:**
>
> * Enable 2-Step Verification on your Google account.
> * Create an App Password and use it as `SMTP_PASSWORD`.

### 5) Start MongoDB

Make sure your MongoDB server is running. If you installed MongoDB locally, start the service or run `mongod` as per your OS instructions.

### 6) Run the app

```bash
python app.py
```

Open your browser at: `http://localhost:5000`

On first run the app creates a default admin if none exists: `admin@local` (password `admin123`). Change this password immediately.

---

## 📊 Transaction Chart Example

The Customer module generates a chart (PNG) with:

* Daily credits vs debits
* Balance history over the selected period

Charts are saved in `static/charts/` and include summary values such as total credits, total debits, net change and current balance.

---

## 🔐 Security & Production Notes

* This project is a demo/example. Before deploying to production:

  * Replace the default secret key and admin password
  * Use HTTPS and secure cookie settings
  * Store secrets (DB URIs, SMTP creds) in a secured secrets manager or environment variables
  * Add rate-limiting and input validation
  * Use proper authentication libraries (Flask-Login, OAuth, or JWT) if required

---

## 📌 Future Improvements (optional roadmap)

* JWT-based authentication for stateless APIs
* Frontend upgrade (React, Vue, or modern static client)
* Docker support for containerized deployment
* Extended admin analytics panel with more charts
* Password-reset and email verification workflows
* Multi-branch banking support

---

## 🤝 Contributing

We welcome contributions!

* Submit pull requests for code changes
* Open issues for bug reports or feature requests

---

## 📝 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## 👨‍💻 Author

**Snehashis Das**
GitHub: [https://github.com/snehashis842](https://github.com/snehashis842)
Email: [snehashisdas842@gmail.com](mailto:snehashisdas842@gmail.com)
