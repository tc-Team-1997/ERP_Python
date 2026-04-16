from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session, joinedload

from backend.app.models.employee import Employee
from backend.app.models.payroll import PayrollRecord

TWO_PLACES = Decimal("0.01")


def to_decimal(value: float | Decimal | None) -> Decimal:
    return Decimal(str(value or 0)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def process_monthly_payroll(db: Session, tenant_id: int, month: int, year: int):
    employees = (
        db.query(Employee)
        .options(joinedload(Employee.salary_structure))
        .filter(Employee.tenant_id == tenant_id, Employee.is_active.is_(True))
        .all()
    )

    processed_records = []
    skipped = []

    for employee in employees:
        structure = employee.salary_structure
        if structure is None:
            skipped.append({"employee_id": employee.id, "employee_name": employee.full_name, "reason": "Salary structure missing"})
            continue

        basic = to_decimal(structure.basic)
        hra = to_decimal(structure.hra)
        allowances = to_decimal(structure.allowances)
        manual_deductions = to_decimal(structure.deductions)
        gross_salary = basic + hra + allowances
        tax_amount = (gross_salary * to_decimal(structure.tax_percent) / Decimal("100")).quantize(TWO_PLACES)
        total_deductions = manual_deductions + tax_amount
        net_salary = gross_salary - total_deductions

        record = (
            db.query(PayrollRecord)
            .filter(
                PayrollRecord.tenant_id == tenant_id,
                PayrollRecord.employee_id == employee.id,
                PayrollRecord.month == month,
                PayrollRecord.year == year,
            )
            .first()
        )

        if record is None:
            record = PayrollRecord(
                tenant_id=tenant_id,
                employee_id=employee.id,
                month=month,
                year=year,
            )

        record.basic = basic
        record.hra = hra
        record.allowances = allowances
        record.gross_salary = gross_salary
        record.deductions = total_deductions
        record.tax_amount = tax_amount
        record.net_salary = net_salary
        record.status = "processed"

        db.add(record)
        processed_records.append(record)

    db.commit()

    for record in processed_records:
        db.refresh(record)

    return processed_records, skipped
