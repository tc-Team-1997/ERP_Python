# Business Automation SaaS (Phase 1)

A modern, cloud-ready, **multi-tenant business automation platform** built with **FastAPI + PostgreSQL + Streamlit**.

This starter implementation focuses on **Phase 1: Payroll Management** and is structured for future expansion into **Billing/Invoicing** and **Expense Management**.

## ✅ Phase 1 Features

- Multi-tenant tenant onboarding (`business -> users -> isolated payroll data`)
- JWT-based authentication
- Role-based access (`admin`, `user`)
- Employee management (CRUD)
- Salary structure setup
- Monthly payroll processing
- Payslip PDF download
- Payroll history storage
- Docker-ready deployment structure

---

## 🏗️ Architecture

- **Backend:** FastAPI (REST APIs)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Auth:** JWT Bearer tokens
- **Frontend:** Streamlit (simple browser UI)
- **Multi-tenancy strategy:** shared database + `tenant_id` isolation
- **Cloud readiness:** environment-based config, Docker support, modular folders

---

## 📁 Project Structure

```text
business-automation-saas/
├── backend/
│   ├── Dockerfile
│   └── app/
│       ├── api/
│       │   ├── deps.py
│       │   ├── router.py
│       │   └── endpoints/
│       ├── core/
│       ├── db/
│       ├── models/
│       ├── schemas/
│       └── services/
├── frontend/
│   └── app.py
├── tests/
│   └── test_smoke.py
├── .env.example
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🚀 Run Locally in VS Code

### 1) Open the folder
Open `C:\Users\Amit\business-automation-saas` in Visual Studio Code.

### 2) Create and activate a virtual environment
**PowerShell:**

```powershell
cd C:\Users\Amit\business-automation-saas
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3) Install dependencies

```powershell
pip install -r requirements.txt
```

### 4) Start PostgreSQL
Option A: Use Docker

```powershell
docker compose up -d db
```

Option B: Use your local PostgreSQL instance and update `.env`.

### 5) Start the FastAPI backend

```powershell
uvicorn backend.app.main:app --reload
```

API docs: `http://127.0.0.1:8000/docs`

### 6) Start the Streamlit frontend
Open a new terminal:

```powershell
streamlit run frontend/app.py
```

Frontend URL: `http://localhost:8501`

---

## 🐳 Run Everything with Docker

```powershell
docker compose up --build
```

Services:
- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:8501`
- PostgreSQL: `localhost:5432`

---

## 🔐 Key API Endpoints

### Authentication
- `POST /api/v1/auth/register-tenant`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Employees
- `POST /api/v1/employees/`
- `GET /api/v1/employees/`
- `GET /api/v1/employees/{employee_id}`
- `PUT /api/v1/employees/{employee_id}`
- `DELETE /api/v1/employees/{employee_id}`

### Salary Structures
- `POST /api/v1/salary-structures/`
- `GET /api/v1/salary-structures/`
- `GET /api/v1/salary-structures/{employee_id}`
- `PUT /api/v1/salary-structures/{employee_id}`

### Payroll
- `POST /api/v1/payroll/process`
- `GET /api/v1/payroll/history`
- `GET /api/v1/payroll/{record_id}`
- `GET /api/v1/payroll/{record_id}/payslip`

---

## 🧱 Database Design (Multi-Tenant)

Core tables:
- `tenants`
- `users`
- `employees`
- `salary_structures`
- `payroll_records`

Each tenant-scoped table includes a **`tenant_id`** column to enforce logical data isolation.

---

## 🔭 Planned Future Phases

### Phase 2: Billing / Invoicing
- Invoice CRUD
- GST/tax logic
- Customer management
- PDF/Excel export

### Phase 3: Expense Management
- Expense CRUD
- Categories
- Reports
- Bill / receipt uploads

---

## 💡 Next Recommended Improvements

1. Add Alembic migrations
2. Add refresh tokens and password reset
3. Add audit logs and activity tracking
4. Add React frontend for richer UX
5. Add tenant-aware middleware and row-level security
6. Deploy to AWS/GCP/Azure using managed PostgreSQL + container hosting
