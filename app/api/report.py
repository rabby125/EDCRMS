import csv
import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from app.database.connection import get_db
from app.models.device_model import Device
from app.models.infrastructure_model import Rack
from app.models.user_model import User
from app.core.permissions import require_role

router = APIRouter(prefix="/api/reports", tags=["Reports"])


def _csv_response(rows, headers, filename):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _excel_response(rows, headers, filename, sheet_title="Report"):
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title

    header_fill = PatternFill(start_color="1E2A38", end_color="1E2A38", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)

    ws.append(headers)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font

    for row in rows:
        ws.append([str(v) if v is not None else "" for v in row])

    for col in ws.columns:
        max_len = max((len(str(c.value)) for c in col if c.value is not None), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/devices/csv")
def export_devices_csv(db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    devices = db.query(Device).all()
    rows = [
        [d.id, d.hostname, d.ip_address, d.rack_id, d.start_u, d.height_u, d.status, d.warranty_exp]
        for d in devices
    ]
    headers = ["ID", "Hostname", "IP Address", "Rack ID", "Start U", "Height U", "Status", "Warranty Expiry"]
    return _csv_response(rows, headers, "devices_report.csv")


@router.get("/devices/excel")
def export_devices_excel(db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    devices = db.query(Device).all()
    rows = [
        [d.id, d.hostname, d.ip_address, d.rack_id, d.start_u, d.height_u, d.status, d.warranty_exp]
        for d in devices
    ]
    headers = ["ID", "Hostname", "IP Address", "Rack ID", "Start U", "Height U", "Status", "Warranty Expiry"]
    return _excel_response(rows, headers, "devices_report.xlsx", "Devices")


@router.get("/racks/csv")
def export_racks_csv(db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    racks = db.query(Rack).all()
    rows = [[r.id, r.rack_name, r.rack_code, r.height_u, r.used_u(), r.free_u(), r.status] for r in racks]
    headers = ["ID", "Rack Name", "Rack Code", "Total U", "Used U", "Free U", "Status"]
    return _csv_response(rows, headers, "racks_report.csv")


@router.get("/racks/excel")
def export_racks_excel(db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    racks = db.query(Rack).all()
    rows = [[r.id, r.rack_name, r.rack_code, r.height_u, r.used_u(), r.free_u(), r.status] for r in racks]
    headers = ["ID", "Rack Name", "Rack Code", "Total U", "Used U", "Free U", "Status"]
    return _excel_response(rows, headers, "racks_report.xlsx", "Racks")


@router.get("/warranty/csv")
def export_warranty_csv(db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    devices = db.query(Device).filter(Device.warranty_exp.isnot(None)).order_by(Device.warranty_exp).all()
    rows = [[d.id, d.hostname, d.serial, d.warranty_exp] for d in devices]
    headers = ["ID", "Hostname", "Serial", "Warranty Expiry"]
    return _csv_response(rows, headers, "warranty_report.csv")


@router.get("/warranty/excel")
def export_warranty_excel(db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    devices = db.query(Device).filter(Device.warranty_exp.isnot(None)).order_by(Device.warranty_exp).all()
    rows = [[d.id, d.hostname, d.serial, d.warranty_exp] for d in devices]
    headers = ["ID", "Hostname", "Serial", "Warranty Expiry"]
    return _excel_response(rows, headers, "warranty_report.xlsx", "Warranty")
