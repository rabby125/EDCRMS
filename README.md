# Enterprise Data Center Rack Management System (EDCRMS)

FastAPI + SQLAlchemy + MySQL + JWT দিয়ে বানানো একটা Data Center Rack Management সিস্টেমের ফাউন্ডেশন। Company → Data Center → Building → Floor → Room → Rack → Device পুরো hierarchy, RBAC, Rack Layout visualization, Asset/Cable tracking, Audit Log, Dashboard, এবং CSV Reports — সব কাজ করছে।

## ⚠️ যা জানা দরকার

এটা একটা ২০-ফেজের বিশাল এন্টারপ্রাইজ প্রজেক্ট। আমি একটা **প্রোডাকশন-গ্রেড, চলমান ফাউন্ডেশন** বানিয়ে দিয়েছি (Phase 1–16 মূলত কভার করা, বাকিগুলো — PDF/Excel export, email notification, backup/restore, Docker — বেসিক স্ট্রাকচার আছে, পুরোপুরি বিল্ড-আউট করা নাই)। নিচে ঠিক কী আছে আর কী নাই তার লিস্ট দিলাম।

### ✅ যা সম্পূর্ণভাবে কাজ করছে
- **Authentication**: JWT login/logout, bcrypt password hashing
- **RBAC**: Super Admin > Admin > Engineer > Viewer — প্রতিটা API endpoint role দিয়ে protected
- **Infrastructure CRUD**: Company, Data Center, Building, Floor, Room, Rack — সব cascading filter সহ
- **Rack Layout Engine**: 42U/45U/48U visual rack view, free space হিসাব, U-space overlap validation
- **Device Management**: Add/Edit/Move device, IP duplicate check, warranty tracking
- **Asset Management**: Tagging, category, history log
- **Cable Management**: Port-to-port tracing, cable type/color
- **Audit Log**: প্রতিটা create/update/delete/login/logout ট্র্যাক হয়
- **Dashboard**: ১১টা summary card + device status chart + recent activity feed
- **CSV Reports**: Devices, Racks, Warranty
- **Frontend**: Bootstrap 5 login, dashboard, rack layout, device list পেজ (কাজ করা, কিন্তু বেসিক ডিজাইন — তুমি চাইলে আরো সুন্দর করে দিতে পারি)

### 🚧 যা স্ট্রাকচার আছে কিন্তু এক্সটেন্ড করা দরকার
- PDF/Excel export (এখন শুধু CSV আছে — `app/api/report.py`)
- Email/SMTP notification system (Phase 18-19 — `notifications` টেবিল আছে, sender logic নাই)
- Vendor/Manufacturer/Model UI পেজ (API আছে, HTML পেজ নাই)
- Company/DataCenter/Building/Floor/Room এর জন্য আলাদা HTML পেজ (API আছে, শুধু Rack ও Device পেজ বানানো আছে — বাকিগুলো একই প্যাটার্নে কপি করে বানানো যাবে)
- Docker Compose ফাইল

## 📁 Folder Structure
প্রজেক্ট রুটে গিয়ে `tree` করলে পুরো স্ট্রাকচার দেখতে পাবা — `app/api` (routes), `app/models` (DB tables), `app/schemas` (validation), `app/templates` (HTML), `app/static` (css/js)।

## 🚀 Setup — ধাপে ধাপে

### ১. MySQL Database বানাও
```sql
CREATE DATABASE edcrms CHARACTER SET utf8mb4;
```

### ২. `.env` ফাইল এডিট করো
প্রজেক্ট রুটে `.env` ফাইল আছে, তোমার MySQL এর user/password/host দিয়ে আপডেট করো:
```
DATABASE_URL=mysql+pymysql://YOUR_USER:YOUR_PASSWORD@localhost:3306/edcrms
SECRET_KEY=একটা-র‍্যান্ডম-লম্বা-সিক্রেট-কী-বসাও
```

### ৩. Virtual environment + install
```bash
cd EDCRMS
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### ৪. Database টেবিল তৈরি + seed data
সহজ উপায় (dev-এর জন্য, app চালু হলে অটো টেবিল বানায়):
```bash
python seed.py
```
এটা সব roles বানাবে আর একটা Super Admin ইউজার তৈরি করবে:
- **Email:** admin@edcrms.com
- **Password:** Admin@123

(প্রোডাকশনে Alembic দিয়ে migration চালানো ভালো — নিচে দেখো)

### ৫. অ্যাপ চালাও
```bash
uvicorn main:app --reload
```
ব্রাউজারে যাও: **http://localhost:8000**
API Docs (Swagger): **http://localhost:8000/docs**

## 🗄️ Alembic Migration (Production Recommended)
```bash
alembic revision --autogenerate -m "initial tables"
alembic upgrade head
```
`alembic.ini` আর `alembic/env.py` আগে থেকেই কনফিগার করা আছে — শুধু `.env` এর DATABASE_URL ঠিক করলেই কাজ করবে।

## 🔑 কীভাবে API ব্যবহার করবা (উদাহরণ)
```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@edcrms.com","password":"Admin@123"}'

# Response থেকে access_token নিয়ে পরের সব request-এ ব্যবহার করো:
curl http://localhost:8000/api/companies/ \
  -H "Authorization: Bearer <token>"
```

## 🏗️ নতুন মডিউল যোগ করার প্যাটার্ন
যদি নতুন কিছু (যেমন vendor বা room-এর জন্য HTML পেজ) বানাতে চাও, এই প্যাটার্ন ফলো করো:
1. `app/models/` এ SQLAlchemy model থাকলে দেখো (আগে থেকেই আছে সবগুলা)
2. `app/schemas/` এ Pydantic schema আছে কিনা চেক করো
3. `app/api/xxx.py` এ CRUD router বানাও (existing `company.py` বা `rack.py` কপি করে টেমপ্লেট হিসেবে ইউজ করো)
4. `main.py` তে `app.include_router(xxx.router)` যোগ করো
5. HTML পেজ চাইলে `app/templates/xxx/index.html` বানাও (`rack/index.html` কপি করে শুরু করো), `main.py` তে page route যোগ করো

## 📌 পরবর্তী ধাপ (Recommended Priority)
1. প্রথমে MySQL কানেক্ট করে `seed.py` চালিয়ে লগইন টেস্ট করো
2. Swagger UI (`/docs`) দিয়ে company → datacenter → building → floor → room → rack → device — এই ক্রমে কিছু টেস্ট ডেটা ঢুকাও
3. `/racks` পেজে গিয়ে rack layout visual দেখো
4. এরপর আমাকে বলো কোন specific মডিউল (PDF report, email alert, Docker, বাকি HTML পেজ) আগে দরকার — আমি সেটা এক্সটেন্ড করে দিব

---
প্রশ্ন থাকলে বা কোনো ফিচার এক্সটেন্ড করতে চাইলে জানিও — আমি ঠিক ওই মডিউলটা নিয়ে কাজ করব।
