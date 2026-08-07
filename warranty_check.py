"""
Checks for devices whose warranty expires within N days and creates
in-app notifications for all Admin/Super Admin users.

Run manually or schedule via cron:
    0 8 * * * cd /path/to/EDCRMS && venv/bin/python warranty_check.py
"""
from datetime import date, timedelta

from app.database.connection import SessionLocal
from app.models.device_model import Device
from app.models.user_model import User, Role
from app.services.notification_service import notify_user

DAYS_AHEAD = 30

db = SessionLocal()
try:
    cutoff = date.today() + timedelta(days=DAYS_AHEAD)
    expiring = db.query(Device).filter(
        Device.warranty_exp.isnot(None), Device.warranty_exp <= cutoff
    ).all()

    if not expiring:
        print("No devices with warranty expiring soon.")
    else:
        admins = db.query(User).join(Role).filter(Role.name.in_(["Admin", "Super Admin"])).all()

        for device in expiring:
            message = f"Device '{device.hostname}' warranty expires on {device.warranty_exp}."
            for admin in admins:
                notify_user(db, admin.id, message)

        print(f"Sent {len(expiring)} warranty alert(s) to {len(admins)} admin(s).")
finally:
    db.close()