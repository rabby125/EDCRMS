from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.connection import Base, engine

# Import all models so SQLAlchemy metadata knows about them before create_all
from app.models import user_model, infrastructure_model, device_model, asset_model, cable_model, log_model  # noqa

from app.api import (
    auth, user, role,
    company, datacenter, building, floor, room,
    rack, device, device_type, vendor, manufacturer, model,
    asset, cable, report, audit, dashboard, notification,
)

app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

ALLOWED_ORIGINS = [
    "https://yourdomain.com",  # TODO: replace with your real production domain(s)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static assets (css/js/images)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# ---- Register API Routers ----
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(role.router)
app.include_router(company.router)
app.include_router(datacenter.router)
app.include_router(building.router)
app.include_router(floor.router)
app.include_router(room.router)
app.include_router(rack.router)
app.include_router(device.router)
app.include_router(device_type.router)
app.include_router(vendor.router)
app.include_router(manufacturer.router)
app.include_router(model.router)
app.include_router(asset.router)
app.include_router(asset.cat_router)
app.include_router(cable.router)
app.include_router(cable.type_router)
app.include_router(report.router)
app.include_router(audit.router)
app.include_router(dashboard.router)
app.include_router(notification.router)


# ---- Frontend Page Routes (server-rendered shell; data loads via AJAX) ----
@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@app.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard/index.html", {"request": request})


@app.get("/racks")
def racks_page(request: Request):
    return templates.TemplateResponse("rack/index.html", {"request": request})


@app.get("/devices")
def devices_page(request: Request):
    return templates.TemplateResponse("device/index.html", {"request": request})


@app.get("/companies")
def companies_page(request: Request):
    return templates.TemplateResponse("company/index.html", {"request": request})


@app.get("/datacenters")
def datacenters_page(request: Request):
    return templates.TemplateResponse("datacenter/index.html", {"request": request})


@app.get("/buildings")
def buildings_page(request: Request):
    return templates.TemplateResponse("building/index.html", {"request": request})


@app.get("/floors")
def floors_page(request: Request):
    return templates.TemplateResponse("floor/index.html", {"request": request})


@app.get("/rooms")
def rooms_page(request: Request):
    return templates.TemplateResponse("room/index.html", {"request": request})


@app.get("/vendors")
def vendors_page(request: Request):
    return templates.TemplateResponse("vendor/index.html", {"request": request})


@app.get("/manufacturers")
def manufacturers_page(request: Request):
    return templates.TemplateResponse("manufacturer/index.html", {"request": request})


@app.get("/assets")
def assets_page(request: Request):
    return templates.TemplateResponse("asset/index.html", {"request": request})


@app.get("/reports")
def reports_page(request: Request):
    return templates.TemplateResponse("report/index.html", {"request": request})


@app.get("/users")
def users_page(request: Request):
    return templates.TemplateResponse("user/index.html", {"request": request})


@app.on_event("startup")
def on_startup():
    # For quick local dev only. In production, use Alembic migrations instead.
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)