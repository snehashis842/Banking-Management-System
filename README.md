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

## ⚙️ Setup Instructions

Follow these steps to get the project up and running on your local machine.

### 1️⃣ Clone the repository

```bash
git clone [https://github.com/snehashis842/Banking-Management-System.git](https://github.com/snehashis842/Banking-Management-System.git)
cd Banking-Management-System
2️⃣ Create a virtual environmentIt's highly recommended to use a virtual environment to manage dependencies.Bashpython -m venv venv
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
3️⃣ Install dependenciesInstall all required Python packages using pip.Bashpip install -r requirements.txt
4️⃣ Start MongoDBEnsure that your MongoDB server is running. The application is configured to connect to the default address:mongodb://localhost:27017/
5️⃣ Run the appExecute the main application file.Bashpython app.py
The application will now be running. You can access it in your web browser at:👉 http://localhost:5000✉️ Email Alerts SetupThe system uses SMTP for email notifications (login alerts, transaction summaries, admin reports).ConfigurationOpen utils.py and update the following variables with your credentials:PythonSMTP_EMAIL = "your_email@gmail.com"
SMTP_PASSWORD = "your_app_password"
Using Gmail SMTPIf you are using Gmail for the SMTP service, you must:Enable 2-Step Verification (2FA) on your Google account.Go to your Google Account Security settings and Create an App Password.Replace the SMTP_PASSWORD in utils.py with this generated App Password.📊 Transaction Chart ExampleThe Customer Module generates a financial chart upon request:Chart TypeDetailsDaily ActivityBar chart showing daily credit/debit transactions.Balance HistoryLine chart illustrating the balance over time.These charts are saved as a downloadable PNG file and automatically include:Total creditsTotal debitsNet changeCurrent balance📌 Future Improvements (Optional Roadmap)Auth Token: Implement JWT-based authentication for stateless API interactions.Frontend Upgrade: Migrate the frontend to a modern framework like React or Vue.Deployment: Add Docker support for easier deployment and containerization.Advanced Analytics: Develop an extensive Admin analytics panel with more diverse charts and metrics.Security Feature: Implement a comprehensive Password reset system.Scalability: Add support for a Multi-branch banking structure.📝 LicenseThis project is licensed under the MIT License. See the LICENSE file for details.🤝 ContributingWe welcome contributions!Feel free to submit Pull Requests for direct code contributions.Open an Issue for new features, desired improvements, or bug reports.👨‍💻 AuthorSnehashis DasGitHub: https://github.com/snehashis842Email: snehashisdas842@gmail.com
