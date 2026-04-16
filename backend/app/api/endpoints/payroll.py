from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, require_admin
from backend.app.db.session import get_db
from backend.app.models.payroll import PayrollRecord
from backend.app.models.tenant import Tenant
from backend.app.models.user import User
from backend.app.schemas.payroll import PayrollProcessRequest, PayrollRecordRead
from backend.app.services.payroll_service import process_monthly_payroll
from backend.app.services.pdf_service import build_payslip_pdf

router = APIRouter()


@router.post("/process")
def run_payroll_processing(
    payload: PayrollProcessRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    records, skipped = process_monthly_payroll(db, current_user.tenant_id, payload.month, payload.year)
    return {
        "message": "Payroll processed successfully",
        "processed_count": len(records),
        "skipped": skipped,
        "records": [PayrollRecordRead.model_validate(record).model_dump(mode="json") for record in records],
    }


@router.get("/history", response_model=list[PayrollRecordRead])
def list_payroll_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(PayrollRecord)
        .options(joinedload(PayrollRecord.employee))
        .filter(PayrollRecord.tenant_id == current_user.tenant_id)
        .order_by(PayrollRecord.year.desc(), PayrollRecord.month.desc(), PayrollRecord.processed_at.desc())
        .all()
    )


@router.get("/{record_id}", response_model=PayrollRecordRead)
def get_payroll_record(record_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = (
        db.query(PayrollRecord)
        .options(joinedload(PayrollRecord.employee))
        .filter(PayrollRecord.id == record_id, PayrollRecord.tenant_id == current_user.tenant_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payroll record not found")
    return record


@router.get("/{record_id}/payslip")
def download_payslip(record_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = (
        db.query(PayrollRecord)
        .options(joinedload(PayrollRecord.employee))
        .filter(PayrollRecord.id == record_id, PayrollRecord.tenant_id == current_user.tenant_id)
        .first()
    )
    if not record or not record.employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payroll record not found")

    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    pdf_buffer = build_payslip_pdf(
        company_name=tenant.name if tenant else "Business Automation SaaS",
        employee_name=record.employee.full_name,
        employee_code=record.employee.employee_code,
        payroll_record=record,
    )
    filename = f"payslip_{record.employee.employee_code}_{record.month:02d}_{record.year}.pdf"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)
