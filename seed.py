"""
Run this once after the database and tables are created to seed initial
roles and a Super Admin user.

Usage:
    python seed.py
"""
from app.database.connection import SessionLocal, Base, engine
from app.models.user_model import User, Role
from app.core.security import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()

ROLES = ["Super Admin", "Admin", "Engineer", "Viewer"]

try:
    for role_name in ROLES:
        if not db.query(Role).filter(Role.name == role_name).first():
            db.add(Role(name=role_name, description=f"{role_name} role"))
    db.commit()

    super_admin_role = db.query(Role).filter(Role.name == "Super Admin").first()

    if not db.query(User).filter(User.username == "admin").first():
        admin = User(
            name="System Administrator",
            username="admin",
            password=hash_password("Admin@123"),
            status="active",
            role_id=super_admin_role.id,
        )
        db.add(admin)
        db.commit()
        print("Seed complete. Login with admin / Admin@123")
    else:
        print("Seed data already exists.")
finally:
    db.close()