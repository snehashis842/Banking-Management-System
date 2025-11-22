# **Banking Management System (Flask + MongoDB)**

A **secure, role-based banking management system** built using **Flask**, **MongoDB**, and **REST APIs**, featuring Admin, Employee, and Customer modules.  
It includes **authentication**, **session management**, **auto-generated User IDs**, **transactions**, **dashboards**, **email notifications**, and **transaction analytics** with Matplotlib.

---

## 🚀 **Features**

### 🔐 Authentication & Security
- Login system with encoded passwords  
- Session-based authentication  
- Role-based access control (Admin / Employee / Customer)  
- Login tracking with timestamp history  

### 🧑‍💼 Admin Module
- Add new users with auto-generated User IDs  
- View all users with activity status  
- Manage roles and account status  
- Monthly login statistics  
- Automated monthly email reports to Super Admin  
- System-wide dashboards

### 👨‍🔧 Employee Module
- View all customer transactions  
- Access user details (read-only)

### 👤 Customer Module
- Credit / debit transactions  
- Real-time balance updates  
- Download 6-month transaction chart  
- Email login notifications with transaction summary  
- View monthly transaction count  

### 📈 Analytics & Reporting
- Login history tracking  
- Transaction history aggregation  
- Matplotlib chart generation  
- Admin dashboard metrics  

---

## 🛠️ **Tech Stack**

### **Backend**
- Python  
- Flask  
- Flask-Caching  
- REST APIs  
- Session authentication

### **Database**
- MongoDB  
- Mongoose-like validation  
- Indexing for optimized queries  
- Connection pooling  

### **Other Tools**
- Matplotlib (charting)  
- SMTP (email notifications)  
- UUID (transaction IDs)  
- Datetime / Timedelta  

---

## 📁 **Project Structure**

│── app.py # Main Flask application
│── utils.py # Helpers: DB, email, charts, validation
│── templates/ # HTML templates (placeholder versions)
│── static/ # CSS, JS, images (placeholder folders)
│── requirements.txt
└── README.md


---

## ⚙️ **Setup Instructions**

### **1️⃣ Clone the repository**
```bash
git clone https://github.com/snehashis842/Banking-Management-System.git
cd Banking-Management-System
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
