# main.py
import os
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests 
import time 
# Import สำหรับ Email Alert
import smtplib
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

# ตั้งค่า Service URL 
SCANNER_API_URL = os.getenv("SCANNER_API_URL", "http://scanner:5001") + "/scan/all"
ML_API_URL = os.getenv("ML_API_URL", "http://ml:5000") + "/predict"


from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import สำหรับ DB (Task 3.1)
from db_utils import start_new_scan_in_db, save_vulnerability, update_scan_status, get_results_from_db 

# -------------------- ส่วนที่ 1: CONFIGURATION --------------------

# --- A. Port Configuration (Task 3.3) ---
SCANNER_API_URL = os.getenv("SCANNER_API_URL", "http://scanner:5001") + "/scan/all"
ML_API_URL = os.getenv("ML_API_URL", "http://ml:5000") + "/predict"   

# *** B. Email Configuration (Task 3.4) ***
EMAIL_SENDER = "projectfinal.i02bug@gmail.com"        # <-- **** อีเมลผู้ส่ง ****
EMAIL_PASSWORD = "uuyx ixmk gnya zlpg"        # <-- **** รหัสผ่านสำหรับแอป 16 หลัก ****
EMAIL_RECEIVER = "dnee5515@gmail.com" # <-- อีเมลผู้รับแจ้งเตือน
SMTP_SERVER = "smtp.gmail.com"              
SMTP_PORT = 587                             

app = FastAPI(title="AI-Powered Vulnerability Scanner Backend (P3)")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------- ส่วนที่ 2: FUNTIONS --------------------
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def call_scanner_api(url: str):
    """เรียกใช้ Scanner API (Person 1) พร้อม Retry 3 ครั้ง"""
    try:
        print(f"[SCANNER] Calling Scanner API: {SCANNER_API_URL}")
        response = requests.post(
            SCANNER_API_URL,
            json={"url": url}, 
            timeout=60 
        ) 
        response.raise_for_status()
        result = response.json()
        print(f"[SCANNER] Response received: {result.keys() if isinstance(result, dict) else type(result)}")
        return result
    except Exception as e:
        print(f"[SCANNER] ERROR: {e}")
        return {"vulnerabilities": []}

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def call_ml_api(vuln_data: dict):
    """เรียกใช้ ML API (Person 2) พร้อม Retry 3 ครั้ง"""
    # NOTE: vuln_data อาจถูกแปลงให้มีแต่ features ที่ ML ต้องการ
    response = requests.post(
        ML_API_URL, 
        json=vuln_data,
        timeout=30
    )
    
    response.raise_for_status() 
    return response.json()
# --- Task 3.4: Email Alert Function ---
def send_email_notification(subject: str, body: str):
    """
    ส่งอีเมลแจ้งเตือนผ่าน SMTP (Gmail ต้องใช้ App Password)
    """
    SENDER_DISPLAY_NAME = "Bughunter" 
    
    msg = MIMEMultipart()
    msg['From'] = f"{SENDER_DISPLAY_NAME} <{EMAIL_SENDER}>"
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() 
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, text)
        server.quit()
        print(f"[ALERT SUCCESS] Email notification sent: {subject[:50]}...")
    except Exception as e:
        print(f"[ALERT ERROR] Failed to send email notification: {e}")
        pass

def save_vulnerability(scan_id: int, vuln: dict):
    """Save vulnerability to database"""
    import psycopg2
    
    try:
        conn = psycopg2.connect(
            dbname="vulnerability_scanner",
            user="scanuser",
            password="scanpass123",
            host="postgres",
            port="5432"
        )
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO vulnerabilities 
            (scan_id, type, severity, cvss_score, ai_risk_score, description, affected_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            scan_id,
            vuln.get('type', 'Unknown'),
            vuln.get('severity', 'Low'),
            vuln.get('cvss_score', 0.0),
            vuln.get('ai_risk_score', 0.0),
            vuln.get('description', ''),
            vuln.get('url', '')
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"[DB] Saved vulnerability: {vuln.get('type')}")
        
    except Exception as e:
        print(f"[DB] Error saving vulnerability: {e}")

def run_full_scan(scan_id: int, url: str, client_email: str = ""):
    """
    ฟังก์ชันหลักที่รันใน Background เพื่อประสานงาน Scanner และ ML Model (P1 & P2)
    """
    try:
        print(f"[ORCHESTRATOR] Starting scan for ID: {scan_id}, URL: {url}")
        
        # 1. CALL Scanner API (P1) - Integration
        scanner_results = call_scanner_api(url) 
        # Extract vulnerabilities from nested structure
        all_vulns = []
        results = scanner_results.get('results', {})
        for scan_type, data in results.items():
            vulns = data.get('vulnerabilities', data.get('issues', []))
            for v in vulns:
                v['scan_type'] = scan_type
                all_vulns.append(v)

        vulnerabilities = all_vulns

        # 2. LOOP และ CALL ML API (P2)
        for vuln in vulnerabilities:
            # 2.1 เรียก ML API
            ai_result = call_ml_api(vuln) 
            
            # 2.2 นำคะแนน AI มาเพิ่ม
            vuln['ai_risk_score'] = ai_result.get('risk_level', 0.0)
            
            # 3. Save to Database (Task 3.1)
            save_vulnerability(scan_id, vuln)
            
            # 4. Task 3.4: Critical Alert Logic
            if vuln.get('ai_risk_score', 0.0) >= 0.9: 
                alert_subject = f"🚨 CRITICAL VULN: {vuln.get('type')}"
                alert_body = f"พบช่องโหว่ Critical ที่ URL: {url}\nAI Risk Score: {vuln.get('ai_risk_score')}"
                send_email_notification(alert_subject, alert_body) # ส่งหา Admin


        # --- ขั้นตอนสุดท้ายหลังสแกนเสร็จ ---
        update_scan_status(scan_id, 'completed') # บันทึกสถานะสำเร็จ
        print(f"[ORCHESTRATOR] Scan ID {scan_id} COMPLETED and Report ready for {client_email}.")
    except Exception as e:
        print(f"[ORCHESTRATOR] EXCEPTION: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

        # 6. Task 4.1: Error Handling (เมื่อ Retry ล้มเหลวครบ 3 ครั้ง)
        print(f"[ORCHESTRATOR] FATAL ERROR for Scan ID {scan_id}: {e}")
        update_scan_status(scan_id, 'failed') 
        
        error_subject = f"❌ SCAN FAILED: ID {scan_id} - {url}"
        error_body = f"Scan failed due to API connection issue or other error: {e}"
        send_email_notification(error_subject, error_body) # แจ้ง Admin
# -------------------- ส่วนที่ 3: ENDPOINTS API --------------------

@app.post("/scan")
# API version with /api prefix
@app.post("/api/scan")

class ScanRequest(BaseModel):
    target_url: str

@app.post("/api/scans")
async def start_scan_api_json(
    request: ScanRequest,
    background_tasks: BackgroundTasks
):
    return await start_scan_api(request.target_url, background_tasks)
async def start_scan_api(
    url: str = Query(..., description="The URL to scan"), 
    background_tasks: BackgroundTasks = None
):
    """🚀 Start a new vulnerability scan (API version)"""
    return await start_scan(url, background_tasks)

async def start_scan(
    url: str = Query(..., description="The URL to scan"), 
    background_tasks: BackgroundTasks = None
):
    """
    🚀 Start a new vulnerability scan.
    """
    scan_id = start_new_scan_in_db(url)
    
    if scan_id is None:
        raise HTTPException(status_code=500, detail="Failed to initialize scan (Database error).")
        
    background_tasks.add_task(run_full_scan, scan_id, url)
    
    return {
        "scan_id": scan_id,
        "message": "Scan initiated. Check status_url for results.",
        "status_url": f"/scan/{scan_id}"
    }

@app.get("/scan/{scan_id}")
async def get_scan_results(scan_id: int):
    """
    📊 Retrieve the results or current status of a specific scan ID.
    """
    results = get_results_from_db(scan_id) 
    
    if results is None:
        raise HTTPException(status_code=404, detail=f"Scan ID {scan_id} not found.")
        
    return results
# เพิ่ม Health Check Endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "scanner_api": SCANNER_API_URL,
        "ml_api": ML_API_URL
    }

# เพิ่ม Get All Scans (สำหรับ Frontend)
@app.get("/api/scans")
async def get_all_scans(skip: int = 0, limit: int = 10):
    """Get list of all scans"""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    try:
        conn = psycopg2.connect(
            dbname="vulnerability_scanner",
            user="scanuser",
            password="scanpass123",
            host="postgres",
            port="5432"
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM scans ORDER BY scan_date DESC LIMIT %s OFFSET %s", (limit, skip))
        scans = cur.fetchall()
        cur.close()
        conn.close()
        return scans
    except Exception as e:
        print(f"Error fetching scans: {e}")
        return []
@app.get("/api/scans/{scan_id}")
async def get_scan_by_id(scan_id: int):
    """Get scan details by ID"""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    try:
        conn = psycopg2.connect(
            dbname="vulnerability_scanner",
            user="scanuser",
            password="scanpass123",
            host="postgres",
            port="5432"
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM scans WHERE scan_id = %s", (scan_id,))
        scan = cur.fetchone()
        
        if scan:
            # ดึง vulnerabilities ด้วย
            cur.execute("SELECT * FROM vulnerabilities WHERE scan_id = %s", (scan_id,))
            vulnerabilities = cur.fetchall()
            scan['vulnerabilities'] = vulnerabilities
        
        cur.close()
        conn.close()
        
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        return scan
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "BugHunter API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
