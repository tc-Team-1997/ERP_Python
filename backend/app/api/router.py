from fastapi import APIRouter

from backend.app.api.endpoints import (
    accounts, attendance, audit_logs, auth, bank, customers, documents, employees, expenses,
    financial_reports, fixed_assets, grns, invoices, items, journals,
    leads, leaves, opportunities, payroll, purchase_orders, purchase_requisitions,
    quotations, salary_structures, sales_orders, stock_movements, vendors, warehouses,
)

api_router = APIRouter()
# Core
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# HR / Payroll
api_router.include_router(employees.router, prefix="/employees", tags=["Employees"])
api_router.include_router(salary_structures.router, prefix="/salary-structures", tags=["Salary Structures"])
api_router.include_router(payroll.router, prefix="/payroll", tags=["Payroll"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
api_router.include_router(leaves.router, prefix="/leaves", tags=["Leave Requests"])
# Billing / AP-AR
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
api_router.include_router(expenses.router, prefix="/expenses", tags=["Expenses"])
# Sales & CRM
api_router.include_router(leads.router, prefix="/leads", tags=["Leads"])
api_router.include_router(opportunities.router, prefix="/opportunities", tags=["Opportunities"])
api_router.include_router(quotations.router, prefix="/quotations", tags=["Quotations"])
api_router.include_router(sales_orders.router, prefix="/sales-orders", tags=["Sales Orders"])
# Inventory
api_router.include_router(warehouses.router, prefix="/warehouses", tags=["Warehouses"])
api_router.include_router(items.router, prefix="/items", tags=["Items"])
api_router.include_router(stock_movements.router, prefix="/stock-movements", tags=["Stock Movements"])
# Procurement
api_router.include_router(vendors.router, prefix="/vendors", tags=["Vendors"])
api_router.include_router(purchase_requisitions.router, prefix="/prs", tags=["Purchase Requisitions"])
api_router.include_router(purchase_orders.router, prefix="/pos", tags=["Purchase Orders"])
api_router.include_router(grns.router, prefix="/grns", tags=["GRNs"])
# Finance & Accounting
api_router.include_router(accounts.router, prefix="/accounts", tags=["Chart of Accounts"])
api_router.include_router(journals.router, prefix="/journals", tags=["Journal Entries"])
api_router.include_router(fixed_assets.router, prefix="/fixed-assets", tags=["Fixed Assets"])
api_router.include_router(bank.router, prefix="/bank", tags=["Bank & Reconciliation"])
api_router.include_router(financial_reports.router, prefix="/financial-reports", tags=["Financial Reports"])
# DMS & Audit
api_router.include_router(documents.router, prefix="/documents", tags=["Documents / DMS"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Log"])
