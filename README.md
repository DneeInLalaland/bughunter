# 🛡️ BugHunter

**AI-Powered Web Vulnerability Scanner**

An automated web vulnerability scanning system with Machine Learning-based risk prioritization.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)

---

## ✨ Features

- 🔍 **7 Vulnerability Types** - SQL Injection, XSS, CSRF, Auth Flaws, Outdated Dependencies, Port Scan, SSL Check
- 🤖 **AI Risk Scoring** - Machine Learning prioritizes vulnerabilities (93.42% Accuracy)
- 📊 **Beautiful Dashboard** - Real-time visualization with interactive charts
- 📄 **PDF Reports** - Auto-generated security reports
- 🔔 **LINE Notifications** - Instant alerts for critical vulnerabilities
- 🐳 **Docker Ready** - Easy deployment with Docker Compose

---

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│  Scanner    │
│   (React)   │     │  (FastAPI)  │     │   (Flask)   │
│  Port 5173  │     │  Port 8000  │     │  Port 5001  │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
                          ▼
                   ┌─────────────┐     ┌─────────────┐
                   │  ML Model   │     │ PostgreSQL  │
                   │   (Flask)   │     │  Database   │
                   │  Port 5000  │     │  Port 5432  │
                   └─────────────┘     └─────────────┘
```

---

## 🚀 Quick Start

### With Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/DneeInLalaland/bughunter.git
cd bughunter

# Start all services
docker-compose up -d

# Open in browser
open http://localhost:5173
```

### Manual Setup

```bash
# 1. Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2. Scanner
cd scanner
pip install -r requirements.txt
python app.py

# 3. ML Model
cd ml-model
pip install -r requirements.txt
python app.py

# 4. Frontend
cd frontend
npm install
npm run dev
```

---

## 📁 Project Structure

```
bughunter/
├── frontend/          # React Frontend
├── backend/           # FastAPI Backend
├── scanner/           # Vulnerability Scanner API
├── ml-model/          # Machine Learning API
├── docker-compose.yml # Docker Configuration
└── README.md
```

---

## 🔍 Vulnerability Types

| Type | Description | Severity |
|------|-------------|----------|
| SQL Injection | Detects SQL command injection | 🔴 Critical |
| XSS | Cross-Site Scripting attacks | 🟠 High |
| CSRF | Cross-Site Request Forgery | 🟡 Medium |
| Auth Flaws | Authentication vulnerabilities | 🟠 High |
| Outdated Deps | Outdated libraries & frameworks | 🟡 Medium |
| Open Ports | Exposed network ports | 🟡 Medium |
| SSL Issues | SSL/TLS misconfigurations | 🔴 Critical |

---

## 📊 ML Model Performance

| Metric | Value |
|--------|-------|
| Accuracy | 93.42% |
| Model | Random Forest Classifier |
| Features | 13 features from CVE data |
| Training Data | 150,000+ vulnerabilities from NVD |

### User Study Results

- **65% faster** critical vulnerability resolution
- **26% reduction** in assessment time
- **8.7/10** user satisfaction score

---

## 🛠️ Tech Stack

**Frontend:**
- React 18 + Vite
- Tailwind CSS
- Recharts / D3.js
- Axios

**Backend:**
- FastAPI
- SQLAlchemy
- PostgreSQL
- ReportLab (PDF)

**Scanner:**
- Flask
- BeautifulSoup
- Requests
- Python-nmap

**ML:**
- Scikit-learn
- Pandas
- SHAP (Explainable AI)

---

## 🔧 Configuration

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/bughunter

# Scanner API
SCANNER_API_URL=http://localhost:5001

# ML API
ML_API_URL=http://localhost:5000

# LINE Notify (Optional)
LINE_NOTIFY_TOKEN=your_token_here
```

---

## 👥 Team

| Role | Responsibility |
|------|----------------|
| Scanner Engineer | 7 vulnerability type scanners |
| ML Engineer | AI risk scoring system |
| Backend Developer | API & database integration |
| Frontend Developer | Dashboard UI/UX |

---

## ⚠️ Disclaimer

**For educational and authorized testing purposes only.**

Scanning websites without permission may be illegal. Only use this tool on websites you own or have explicit authorization to test.

---

## 📝 License

MIT License - Free to use and modify.

---

## 🙏 Acknowledgments

- [OWASP](https://owasp.org/) - Security best practices
- [NVD](https://nvd.nist.gov/) - Vulnerability database
- [Acunetix Vulnweb](http://testphp.vulnweb.com/) - Testing environment

---

Made with ❤️ by KMUTT Students
