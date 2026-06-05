# 🛡️ BugHunter - AI-Powered Vulnerability Scanner

An intelligent web vulnerability scanner with AI-powered risk assessment.

---

## 👥 Team Information

| Role | Name | Student ID | Responsibility |
|------|------|------------|----------------|
| **Person 1** | [Your Name] | [Student ID] | Scanner Engineer |
| **Person 2** | [Name] | [Student ID] | ML Engineer |
| **Person 3** | [Name] | [Student ID] | Backend Developer |
| **Person 4** | [Name] | [Student ID] | Frontend Developer |

---

## ✅ Project Status

**All components are complete and integrated!**

- ✅ **Scanner API** - Fully functional
- ✅ **ML Risk Scorer** - Complete
- ✅ **Backend API** - Complete
- ✅ **Frontend** - Complete
- ✅ **Docker Integration** - Complete
- ✅ **Documentation** - Complete

---

## 🏗️ Project Structure
```
BUGHUNTER/
├── vulnerability-scanner/    # Person 1 - Scanner API (Complete ✅)
│   ├── scanners/            # 7 vulnerability scanners
│   ├── payloads/            # Attack payloads
│   ├── app.py               # Main API
│   ├── Dockerfile           # Docker configuration
│   └── README.md            # Scanner documentation
├── ml-risk-scorer/          # Person 2 - ML API (Complete ✅)
├── backend-api/             # Person 3 - Backend API (Complete ✅)
├── frontend/                # Person 4 - Frontend (Complete ✅)
├── tests/                   # Integration & E2E tests
│   ├── integration_test.sh  # Service health checks
│   ├── e2e_test.py          # End-to-end flow tests
│   └── load_test.py         # Performance tests
├── docker-compose.yml       # Docker orchestration
├── .env                     # Environment variables (DO NOT COMMIT!)
├── .env.example             # Environment template
└── README.md                # This file
```

---

## 🚀 Quick Start

### Prerequisites

Install these first:
- **Docker Desktop** ([Download](https://www.docker.com/products/docker-desktop))
- **Git**

### Installation Steps

#### 1. Clone Repository
```bash
git clone <repository-url>
cd BUGHUNTER
```

#### 2. Create Environment File
```bash
cp .env.example .env
```

Edit `.env` with your configuration (LINE token, JWT secret, etc.)

#### 3. Build & Run with Docker
```bash
docker-compose up -d
```

#### 4. Verify All Services
```bash
docker-compose ps
```

**Expected output:**
```
NAME           STATUS
scanner_api    Up (healthy)
ml_api         Up (healthy)
backend_api    Up (healthy)
frontend_app   Up
vuln_db        Up (healthy)
```

#### 5. Test APIs

**Scanner API:**
```bash
curl http://localhost:5001/health
```

**ML API:**
```bash
curl http://localhost:5000/health
```

**Backend API:**
```bash
curl http://localhost:8000/health
```

**Frontend:**
Open browser: `http://localhost`

---

## 🧪 Testing

### Run Integration Tests
```bash
./tests/integration_test.sh
```

### Run End-to-End Tests
```bash
python tests/e2e_test.py
```

### Run Load Tests
```bash
python tests/load_test.py
```

---

## 🔧 Development

### For Individual Services

Each service can run independently for development:

**Scanner (Person 1):**
```bash
cd vulnerability-scanner
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

**ML (Person 2):**
```bash
cd ml-risk-scorer
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

**Backend (Person 3):**
```bash
cd backend-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend (Person 4):**
```bash
cd frontend
npm install
npm run dev
```

---

## 🐳 Docker Commands

**Start services:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f
```

**Check status:**
```bash
docker-compose ps
```

**Stop services:**
```bash
docker-compose down
```

**Rebuild images:**
```bash
docker-compose up -d --build
```

---

## 📊 Architecture
```
User → Frontend (React) 
       ↓
       Backend API (FastAPI)
       ↓
       ├─→ Scanner API (Flask) - 7 vulnerability types
       ├─→ ML API (Flask) - Risk assessment
       └─→ PostgreSQL - Data storage
```

### Technology Stack

**Frontend:**
- React + Vite
- Tailwind CSS
- Recharts + D3.js

**Backend:**
- FastAPI
- PostgreSQL
- SQLAlchemy

**Scanner:**
- Python + Flask
- Beautiful Soup
- Requests

**ML:**
- Scikit-learn
- SHAP
- Pandas

---

## 🔑 Environment Variables

Important variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | Database username | scanuser |
| `POSTGRES_PASSWORD` | Database password | scanpass123 |
| `POSTGRES_DB` | Database name | vulnerability_scanner |
| `JWT_SECRET` | JWT secret key | **MUST CHANGE!** |
| `LINE_NOTIFY_TOKEN` | LINE notification token | (optional) |

---

## 🐛 Troubleshooting

### Service not starting?
```bash
# View logs
docker-compose logs [service-name]

# Example
docker-compose logs scanner
```

### Port already in use?
```bash
# Find process using port
lsof -i :5001

# Kill process
kill -9 <PID>
```

### Database connection failed?
```bash
# Restart PostgreSQL
docker-compose restart postgres
```

---

## 📝 Additional Documentation

- Scanner API: `vulnerability-scanner/README.md`
- ML API: `ml-risk-scorer/README.md`
- Backend API: `backend-api/README.md`
- Frontend: `frontend/README.md`

---

## 🎯 Features

- ✅ **7 Vulnerability Scanners:**
  - SQL Injection
  - Cross-Site Scripting (XSS)
  - Cross-Site Request Forgery (CSRF)
  - Security Headers
  - SSL/TLS Configuration
  - Directory Traversal
  - Command Injection

- ✅ **AI-Powered Risk Assessment:**
  - Machine learning risk scoring
  - SHAP explainability
  - Prioritized vulnerability ranking

- ✅ **Real-time Notifications:**
  - LINE Notify integration
  - Email alerts (optional)

- ✅ **Comprehensive Reports:**
  - PDF generation
  - Detailed remediation guidance
  - Code examples

---

## 📞 Contact

For issues or questions, contact the team:

| Member | Email |
|--------|-------|
| Person 1 | [email] |
| Person 2 | [email] |
| Person 3 | [email] |
| Person 4 | [email] |

---

## 📜 License

MIT License

---

## ⚠️ Disclaimer

This tool is for **educational purposes and authorized security testing only**. Do not use it to scan websites without permission.

---

**Built with ❤️ by Team BugHunter**

**Course:** [Course Name]  
**University:** King Mongkut's University of Technology Thonburi (KMUTT)  
**Year:** 2025