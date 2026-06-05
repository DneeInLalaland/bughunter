# main.py
import os
import textwrap
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests 
import time 
import smtplib
from tenacity import retry, stop_after_attempt, wait_fixed

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from db_utils import start_new_scan_in_db, update_scan_status, get_results_from_db, update_scan_progress 

# -------------------- CONFIGURATION --------------------

SCANNER_API_URL = os.getenv("SCANNER_API_URL", "http://scanner:5001") + "/scan/all"
ML_API_URL = os.getenv("ML_API_URL", "http://ml:5000") + "/predict"   

EMAIL_SENDER = "projectfinal.i02bug@gmail.com"
EMAIL_PASSWORD = "uuyx ixmk gnya zlpg"
EMAIL_RECEIVER = "dnee5515@gmail.com"
SMTP_SERVER = "smtp.gmail.com"              
SMTP_PORT = 587                             

app = FastAPI(title="AI-Powered Vulnerability Scanner Backend (P3)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- VULNERABILITY KNOWLEDGE BASE --------------------
# Enhanced descriptions with CVSS scores and remediation info

VULN_KNOWLEDGE = {
    "SQL Injection": {
        "cvss": 9.8,
        "severity": "Critical",
        "description": "SQL Injection allows attackers to execute malicious SQL commands in your database. This can lead to data theft, data manipulation, or complete system compromise.",
        "remediation": "Use parameterized queries (prepared statements) instead of string concatenation. Example: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))"
    },
    "Cross-Site Scripting (XSS)": {
        "cvss": 7.5,
        "severity": "High",
        "description": "XSS vulnerability allows attackers to inject malicious scripts into web pages viewed by other users. This can steal session cookies, redirect users, or deface websites.",
        "remediation": "Sanitize and escape all user input before rendering. Use Content Security Policy (CSP) headers. Example: Use DOMPurify.sanitize() or template auto-escaping."
    },
    "Cross-Site Request Forgery (CSRF)": {
        "cvss": 6.5,
        "severity": "Medium",
        "description": "CSRF allows attackers to trick authenticated users into performing unwanted actions. Attackers can change passwords, transfer funds, or modify account settings.",
        "remediation": "Implement CSRF tokens in all forms. Verify Origin/Referer headers. Use SameSite cookie attribute."
    },
    "Weak Password Policy": {
        "cvss": 5.0,
        "severity": "Medium",
        "description": "Weak password policy allows users to set easily guessable passwords, making brute-force attacks more likely to succeed.",
        "remediation": "Enforce minimum 8 characters with uppercase, lowercase, numbers, and symbols. Implement account lockout after failed attempts."
    },
    "Session Management Weakness": {
        "cvss": 5.5,
        "severity": "Medium",
        "description": "Session management issues can allow attackers to hijack user sessions through session fixation or prediction attacks.",
        "remediation": "Regenerate session ID after login. Set secure and httpOnly flags on session cookies. Implement session timeout."
    },
    "Account Enumeration": {
        "cvss": 3.5,
        "severity": "Low",
        "description": "Account enumeration allows attackers to determine valid usernames through different error messages, enabling targeted attacks.",
        "remediation": "Use generic error messages like 'Invalid credentials' instead of 'Username not found' or 'Wrong password'."
    },
    "Outdated Server Software": {
        "cvss": 6.0,
        "severity": "Medium",
        "description": "Running outdated server software exposes known vulnerabilities that have public exploits available.",
        "remediation": "Update to the latest stable version. Enable automatic security updates. Monitor CVE databases for your software versions."
    },
    "Outdated PHP Version": {
        "cvss": 7.0,
        "severity": "High",
        "description": "Outdated PHP versions contain known security vulnerabilities including remote code execution and information disclosure.",
        "remediation": "Upgrade to PHP 8.x. PHP 5.x and 7.x are end-of-life and no longer receive security updates."
    },
    "Outdated JavaScript Library": {
        "cvss": 5.5,
        "severity": "Medium",
        "description": "Outdated JavaScript libraries may contain XSS vulnerabilities or other security flaws with public exploits.",
        "remediation": "Update to the latest version using npm update or yarn upgrade. Use tools like npm audit to find vulnerable packages."
    },
    "Outdated Dependency": {
        "cvss": 3.5,
        "severity": "Low",
        "description": "Using outdated dependencies may expose your application to known vulnerabilities. While not immediately critical, these should be updated as part of regular maintenance.",
        "remediation": "Run 'pip install --upgrade package-name' or 'npm update package-name'. Use Dependabot or Snyk for automated updates."
    },
    "Dangerous Port Open": {
        "cvss": 7.5,
        "severity": "High",
        "description": "Dangerous ports like FTP (21), Telnet (23), or RDP (3389) are open and accessible. These services are frequent attack targets.",
        "remediation": "Close unnecessary ports using firewall rules. If services are needed, restrict access to specific IP addresses. Use SSH instead of Telnet."
    },
    "Open Port": {
        "cvss": 2.0,
        "severity": "Low",
        "description": "Standard service ports are open. This is informational - ensure only necessary services are exposed.",
        "remediation": "Review if all open ports are necessary. Use firewall to restrict access to trusted IPs only."
    },
    "Open Ports Information": {
        "cvss": 2.0,
        "severity": "Low",
        "description": "Multiple ports were found open during the scan. Review each service to ensure it's necessary and properly secured.",
        "remediation": "Audit all running services. Close unused ports. Implement network segmentation and firewall rules."
    },
    "Expired SSL Certificate": {
        "cvss": 8.0,
        "severity": "High",
        "description": "SSL certificate has expired, causing browsers to show security warnings and potentially exposing traffic to interception.",
        "remediation": "Renew the SSL certificate immediately. Consider using Let's Encrypt for free auto-renewing certificates."
    },
    "SSL Certificate Expiring Soon": {
        "cvss": 4.0,
        "severity": "Medium",
        "description": "SSL certificate will expire soon. Plan renewal to avoid service disruption and security warnings.",
        "remediation": "Renew the certificate before expiration. Set up automated renewal with certbot or similar tools."
    },
    "Weak TLS Version": {
        "cvss": 6.5,
        "severity": "Medium",
        "description": "Server supports outdated TLS versions (1.0 or 1.1) which have known vulnerabilities like BEAST and POODLE attacks.",
        "remediation": "Disable TLS 1.0 and 1.1. Configure server to use only TLS 1.2 and 1.3. Update ssl_protocols in nginx/apache config."
    },
    "Weak Cipher Suite": {
        "cvss": 5.0,
        "severity": "Medium",
        "description": "Server uses weak cipher suites (DES, RC4, MD5) that can be broken by modern attacks.",
        "remediation": "Configure strong cipher suites only. Use Mozilla SSL Configuration Generator for recommended settings."
    },
    "SSL/TLS Configuration Error": {
        "cvss": 7.0,
        "severity": "High",
        "description": "SSL/TLS connection could not be established properly, indicating misconfiguration or certificate issues.",
        "remediation": "Check certificate chain is complete. Verify certificate matches domain. Use SSL Labs to test configuration."
    }
}

def get_enhanced_vuln_info(vuln_type, original_description="", severity="Medium"):
    """Get enhanced vulnerability information from knowledge base"""
    
    vuln_type_lower = vuln_type.lower()
    
    # Mapping keywords to knowledge base keys
    keyword_mapping = {
        "sql": "SQL Injection",
        "injection": "SQL Injection",
        "xss": "Cross-Site Scripting (XSS)",
        "cross-site scripting": "Cross-Site Scripting (XSS)",
        "csrf": "Cross-Site Request Forgery (CSRF)",
        "request forgery": "Cross-Site Request Forgery (CSRF)",
        "password": "Weak Password Policy",
        "session": "Session Management Weakness",
        "enumeration": "Account Enumeration",
        "outdated": "Outdated Dependency",
        "dependency": "Outdated Dependency",
        "port": "Open Port",
        "ftp": "Dangerous Port Open",
        "telnet": "Dangerous Port Open",
        "rdp": "Dangerous Port Open",
        "ssl": "SSL/TLS Configuration Error",
        "tls": "Weak TLS Version",
        "certificate": "SSL Certificate Expiring Soon",
        "expired": "Expired SSL Certificate",
        "cipher": "Weak Cipher Suite",
        "https": "Missing HTTPS",
        "php": "Outdated PHP Version",
        "javascript": "Outdated JavaScript Library",
        "server": "Outdated Server Software",
        "insecure": "Dangerous Port Open",
    }
    
    # Add Missing HTTPS to knowledge base dynamically
    VULN_KNOWLEDGE["Missing HTTPS"] = {
        "cvss": 7.0,
        "severity": "High",
        "description": "Website does not use HTTPS encryption. All data transmitted between users and the server can be intercepted by attackers (man-in-the-middle attacks).",
        "remediation": "Enable HTTPS by obtaining an SSL certificate (free from Let's Encrypt). Configure your web server to redirect all HTTP traffic to HTTPS."
    }
    
    VULN_KNOWLEDGE["Insecure Port Open"] = {
        "cvss": 6.5,
        "severity": "Medium",
        "description": "An insecure service port is open. Services like FTP, Telnet transmit data in plain text and should be replaced with secure alternatives.",
        "remediation": "Close unnecessary ports. Replace FTP with SFTP, Telnet with SSH. Use firewall rules to restrict access."
    }
    
    # Try exact match first
    if vuln_type in VULN_KNOWLEDGE:
        info = VULN_KNOWLEDGE[vuln_type]
        return {
            "cvss": info["cvss"],
            "severity": info["severity"],
            "description": info['description'],
            "remediation": info["remediation"]
        }
    
    # Try keyword matching
    matched_key = None
    for keyword, kb_key in keyword_mapping.items():
        if keyword in vuln_type_lower:
            matched_key = kb_key
            break
    
    if matched_key and matched_key in VULN_KNOWLEDGE:
        info = VULN_KNOWLEDGE[matched_key]
        return {
            "cvss": info["cvss"],
            "severity": info["severity"],
            "description": info['description'],
            "remediation": info["remediation"]
        }
    
    # Try partial match on knowledge base keys
    for key, info in VULN_KNOWLEDGE.items():
        key_lower = key.lower()
        if key_lower in vuln_type_lower or vuln_type_lower in key_lower:
            return {
                "cvss": info["cvss"],
                "severity": info["severity"],
                "description": info['description'],
                "remediation": info["remediation"]
            }
    
    # Default based on severity - ALWAYS provide a CVSS score
    cvss_defaults = {"Critical": 9.5, "High": 7.5, "Medium": 5.5, "Low": 3.5, "Info": 2.0}
    default_descriptions = {
        "Critical": f"Critical security vulnerability detected: {vuln_type}. This requires immediate attention as it poses severe risk to your system.",
        "High": f"High severity security issue: {vuln_type}. This vulnerability should be addressed promptly to prevent potential exploitation.",
        "Medium": f"Medium severity finding: {vuln_type}. While not immediately critical, this issue should be remediated as part of your security maintenance.",
        "Low": f"Low severity observation: {vuln_type}. Consider addressing this as part of regular security improvements.",
        "Info": f"Informational finding: {vuln_type}. Review for potential security implications."
    }
    
    return {
        "cvss": cvss_defaults.get(severity, 5.0),
        "severity": severity,
        "description": default_descriptions.get(severity, f"Security issue detected: {vuln_type}"),
        "remediation": f"Review and address this {severity.lower()} severity issue according to security best practices for {vuln_type}."
    }

# -------------------- FUNCTIONS --------------------

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def call_scanner_api(url: str):
    """Call Scanner API with retry"""
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
    """Call ML API with retry"""
    response = requests.post(
        ML_API_URL, 
        json=vuln_data,
        timeout=30
    )
    response.raise_for_status() 
    return response.json()

def send_email_notification(subject: str, body: str):
    """Send email notification via SMTP"""
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


def generate_pdf_report(scan_id: int, results: dict):
    """Generate PDF report with enhanced vulnerability details"""
    report_dir = "reports"
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    
    report_filename = os.path.join(report_dir, f"report_scan_{scan_id}.pdf")
    
    c = canvas.Canvas(report_filename, pagesize=letter)
    width, height = letter
    
    # === 1. Title Section ===
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height - 50, "AI-Powered Vulnerability Scan Report")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - 75, "BugHunter Security Scanner")
    
    # === 2. Scan Details ===
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, height - 120, "Scan Information")
    c.line(72, height - 125, 540, height - 125)
    
    c.setFont("Helvetica", 11)
    y = height - 145
    
    target_url = results.get('target_url', 'N/A')
    status = results.get('status', 'unknown')
    vulnerabilities = results.get('vulnerabilities', [])
    total_vulns = len(vulnerabilities)
    
    start_time_obj = results.get('start_time')
    end_time_obj = results.get('end_time')
    
    if isinstance(start_time_obj, datetime):
        start_time_str = start_time_obj.strftime("%Y-%m-%d %H:%M:%S")
    elif start_time_obj:
        start_time_str = str(start_time_obj)
    else:
        start_time_str = 'N/A'
    
    if isinstance(end_time_obj, datetime):
        end_time_str = end_time_obj.strftime("%Y-%m-%d %H:%M:%S")
    elif end_time_obj:
        end_time_str = str(end_time_obj)
    else:
        end_time_str = 'N/A'
    
    c.drawString(72, y, f"Scan ID: {scan_id}")
    y -= 18
    c.drawString(72, y, f"Target URL: {target_url}")
    y -= 18
    c.drawString(72, y, f"Status: {status.upper()}")
    y -= 18
    c.drawString(72, y, f"Start Time: {start_time_str}")
    y -= 18
    c.drawString(72, y, f"End Time: {end_time_str}")
    y -= 35
    
    # === 3. Summary Statistics ===
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Vulnerability Summary")
    c.line(72, y - 5, 540, y - 5)
    y -= 25
    
    critical_count = sum(1 for v in vulnerabilities if v.get('severity', '').lower() == 'critical')
    high_count = sum(1 for v in vulnerabilities if v.get('severity', '').lower() == 'high')
    medium_count = sum(1 for v in vulnerabilities if v.get('severity', '').lower() == 'medium')
    low_count = sum(1 for v in vulnerabilities if v.get('severity', '').lower() == 'low')
    
    c.setFont("Helvetica", 11)
    c.drawString(72, y, f"Total Vulnerabilities Found: {total_vulns}")
    y -= 18
    
    c.setFillColorRGB(0.8, 0, 0)
    c.drawString(72, y, f"Critical: {critical_count}")
    
    c.setFillColorRGB(1, 0.5, 0)
    c.drawString(172, y, f"High: {high_count}")
    
    c.setFillColorRGB(0.8, 0.6, 0)
    c.drawString(272, y, f"Medium: {medium_count}")
    
    c.setFillColorRGB(0, 0.6, 0)
    c.drawString(372, y, f"Low: {low_count}")
    
    c.setFillColorRGB(0, 0, 0)
    y -= 40
    
    # === 4. Detailed Vulnerabilities ===
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Detailed Findings")
    c.line(72, y - 5, 540, y - 5)
    y -= 25
    
    c.setFont("Helvetica", 10)
    
    severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
    sorted_vulns = sorted(
        vulnerabilities, 
        key=lambda v: severity_order.get(v.get('severity', 'low').lower(), 4)
    )
    
    for i, vuln in enumerate(sorted_vulns[:15], 1):
        if y < 120:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 50
        
        vuln_type = vuln.get('type', 'Unknown')
        severity = vuln.get('severity', 'Medium')
        cvss = vuln.get('cvss_score')
        ai_score = vuln.get('ai_risk_score')
        affected_url = vuln.get('url', vuln.get('affected_url', 'N/A'))
        description = vuln.get('description', 'No description')
        remediation = vuln.get('remediation', '')
        
        # CVSS fallback based on severity if not provided
        cvss_fallback = {"Critical": 9.5, "High": 7.5, "Medium": 5.5, "Low": 3.5, "Info": 2.0}
        if cvss is None or cvss == 0 or cvss == 'N/A':
            cvss = cvss_fallback.get(severity, 5.0)
        
        # Format CVSS - always show a number now
        try:
            cvss_str = f"{float(cvss):.1f}"
        except:
            cvss_str = f"{cvss_fallback.get(severity, 5.0):.1f}"
        
        # AI Risk fallback
        ai_fallback = {"Critical": 9.0, "High": 7.0, "Medium": 5.0, "Low": 3.0, "Info": 1.5}
        if ai_score is None or ai_score == 0 or ai_score == 'N/A':
            ai_score = ai_fallback.get(severity, 5.0)
        
        # Format AI Risk
        try:
            ai_str = f"{float(ai_score):.2f}"
        except:
            ai_str = f"{ai_fallback.get(severity, 5.0):.2f}"
        
        # Severity color
        if severity.lower() == 'critical':
            c.setFillColorRGB(0.8, 0, 0)
        elif severity.lower() == 'high':
            c.setFillColorRGB(1, 0.5, 0)
        elif severity.lower() == 'medium':
            c.setFillColorRGB(0.8, 0.6, 0)
        else:
            c.setFillColorRGB(0, 0.5, 0)
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(72, y, f"{i}. [{severity.upper()}] {vuln_type}")
        c.setFillColorRGB(0, 0, 0)
        
        y -= 14
        c.setFont("Helvetica", 8)
        # Shorter URL to fit
        url_short = str(affected_url)[:30] if len(str(affected_url)) > 30 else str(affected_url)
        c.drawString(90, y, f"CVSS: {cvss_str} | AI Risk: {ai_str} | URL: {url_short}")
        
        y -= 11
        # Use textwrap for proper line wrapping (width=60 chars)
        wrapped_desc = textwrap.wrap(f"Issue: {description}", width=60)
        for line in wrapped_desc[:2]:  # Max 2 lines
            c.drawString(90, y, line)
            y -= 10
        
        # Show remediation if available
        if remediation:
            c.setFillColorRGB(0, 0.4, 0)
            wrapped_rem = textwrap.wrap(f"Fix: {remediation}", width=60)
            for line in wrapped_rem[:1]:  # Max 1 line
                c.drawString(90, y, line)
                y -= 10
            c.setFillColorRGB(0, 0, 0)
        
        y -= 8
    
    if len(vulnerabilities) > 15:
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(72, y, f"... and {len(vulnerabilities) - 15} more vulnerabilities")
        y -= 25
    
    # === 5. Footer ===
    c.setFont("Helvetica", 8)
    c.drawString(72, 40, f"Report generated by BugHunter on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(72, 28, "AI-Powered Vulnerability Scanner - KMUTT Project")
    
    c.save()
    print(f"[REPORT] PDF Report generated: {report_filename}")
    
    return report_filename


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
    """Main scan orchestration function"""
    scan_start_time = datetime.now()
    
    try:
        print(f"[ORCHESTRATOR] Starting scan for ID: {scan_id}, URL: {url}")
        
        # 1. Call Scanner API
        update_scan_progress(scan_id, 15, "Scanning target website...")
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

        # 2. Process each vulnerability
        total_vulns = len(vulnerabilities)
        update_scan_progress(scan_id, 40, f"Found {total_vulns} vulnerabilities, analyzing...")
        
        for idx, vuln in enumerate(vulnerabilities):
            if total_vulns > 0:
                progress_per_vuln = 45.0 / total_vulns
                current_progress = 40 + int((idx + 1) * progress_per_vuln)
                update_scan_progress(scan_id, current_progress, f"Analyzing vulnerability {idx + 1}/{total_vulns}...")
            
            print(f"[DEBUG] Processing vulnerability: {vuln.get('type', 'Unknown')}")
            
            # Get enhanced info from knowledge base
            original_desc = vuln.get('description', '')
            original_severity = vuln.get('severity', 'Medium')
            enhanced_info = get_enhanced_vuln_info(vuln.get('type', 'Unknown'), original_desc, original_severity)
            
            # ALWAYS set CVSS from knowledge base (never N/A)
            vuln['cvss_score'] = enhanced_info['cvss']
            
            # Use enhanced description from knowledge base
            vuln['description'] = enhanced_info['description']
            vuln['remediation'] = enhanced_info['remediation']
            
            # Use severity from knowledge base if scanner didn't provide one
            if not vuln.get('severity') or vuln.get('severity') == 'Unknown':
                vuln['severity'] = enhanced_info['severity']
            
            print(f"[ENHANCED] Type: {vuln.get('type')} | CVSS: {vuln['cvss_score']} | Severity: {vuln.get('severity')}")
            
            # Helper functions for ML encoding
            def encode_severity(severity):
                mapping = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
                return mapping.get(severity, 1)
            
            def encode_attack_vector(vector):
                mapping = {"Network": 1, "Adjacent": 2, "Local": 3, "Physical": 4}
                return mapping.get(vector, 1)
            
            def encode_privileges(priv):
                mapping = {"None": 2, "Low": 1, "High": 0}
                return mapping.get(priv, 1)
            
            cvss_score = float(vuln.get("cvss_score", 5.0))
            severity = vuln.get("severity", "Medium")
            
            # Build ML input
            ml_input = {
                "cvss_base_score": cvss_score,
                "exploitability_score": float(vuln.get("exploitability_score", cvss_score * 0.4)),
                "impact_score": float(vuln.get("impact_score", cvss_score * 0.6)),
                "cvss_severity_encoded": encode_severity(severity),
                "attack_vector_encoded": encode_attack_vector(vuln.get("attack_vector", "Network")),
                "attack_complexity_encoded": 0 if vuln.get("attack_complexity", "Low") == "Low" else 1,
                "privileges_required_encoded": encode_privileges(vuln.get("privileges_required", "None")),
                "user_interaction_encoded": 0 if vuln.get("user_interaction", "None") == "None" else 1,
                "cvss_combined": cvss_score,
                "attack_ease_score": float(vuln.get("exploitability_score", cvss_score * 0.4)) * 0.7,
                "public_exposure": 1 if vuln.get("has_public_exploit", False) else 0,
                "age_factor": 0.5,
                "severity_score": encode_severity(severity)
            }
            
            print(f"[ML INPUT] Sending to ML: {ml_input}")
            
            # Call ML API
            try:
                ai_result = call_ml_api(ml_input)
                print(f"[ML RESULT] Got result: {ai_result}")
                
                # Calculate AI Risk Score
                confidence = ai_result.get('confidence', 0.8)
                base_risk = {"Critical": 9.0, "High": 7.0, "Medium": 5.0, "Low": 3.0, "Info": 1.5}
                vuln['ai_risk_score'] = round(base_risk.get(severity, 5.0) + (confidence * 1.0), 2)
            except Exception as ml_error:
                print(f"[ML ERROR] {ml_error}")
                base_risk = {"Critical": 9.5, "High": 7.5, "Medium": 5.5, "Low": 3.5, "Info": 1.5}
                vuln['ai_risk_score'] = base_risk.get(severity, 5.5)
            
            # Save to Database
            save_vulnerability(scan_id, vuln)
            
            # Critical Alert
            if vuln.get('ai_risk_score', 0.0) >= 9.0:
                alert_subject = f"🚨 CRITICAL VULN: {vuln.get('type')}"
                alert_body = f"Critical vulnerability found at URL: {url}\nType: {vuln.get('type')}\nAI Risk Score: {vuln.get('ai_risk_score')}\nDescription: {vuln.get('description', '')[:200]}"
                send_email_notification(alert_subject, alert_body)

        # Generate PDF Report
        scan_end_time = datetime.now()
        results_for_report = {
            'target_url': url,
            'status': 'completed',
            'start_time': scan_start_time,
            'end_time': scan_end_time,
            'vulnerabilities': vulnerabilities
        }
        update_scan_progress(scan_id, 90, "Generating PDF report...")
        generate_pdf_report(scan_id, results_for_report)

        # Complete
        update_scan_progress(scan_id, 100, "Scan completed!")
        update_scan_status(scan_id, 'completed')
        print(f"[ORCHESTRATOR] Scan ID {scan_id} COMPLETED!")
        
    except Exception as e:
        print(f"[ORCHESTRATOR] EXCEPTION: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

        print(f"[ORCHESTRATOR] FATAL ERROR for Scan ID {scan_id}: {e}")
        update_scan_status(scan_id, 'failed')
        
        error_subject = f"❌ SCAN FAILED: ID {scan_id} - {url}"
        error_body = f"Scan failed with error: {str(e)}"
        send_email_notification(error_subject, error_body)


# -------------------- API ENDPOINTS --------------------

class ScanRequest(BaseModel):
    target_url: str

@app.post("/scan")
async def start_scan(
    url: str = Query(..., description="The URL to scan"), 
    background_tasks: BackgroundTasks = None
):
    """Start a new vulnerability scan"""
    scan_id = start_new_scan_in_db(url)
    
    if scan_id is None:
        raise HTTPException(status_code=500, detail="Failed to initialize scan (Database error).")
        
    background_tasks.add_task(run_full_scan, scan_id, url)
    
    return {
        "id": scan_id,
        "message": "Scan initiated. Check status_url for results.",
        "status_url": f"/scan/{scan_id}"
    }

@app.post("/api/scan")
async def start_scan_api(
    url: str = Query(..., description="The URL to scan"), 
    background_tasks: BackgroundTasks = None
):
    """Start a new vulnerability scan (API version)"""
    return await start_scan(url, background_tasks)

@app.post("/api/scans")
async def start_scan_api_json(
    request: ScanRequest,
    background_tasks: BackgroundTasks
):
    """Start a new vulnerability scan (JSON body version)"""
    scan_id = start_new_scan_in_db(request.target_url)
    
    if scan_id is None:
        raise HTTPException(status_code=500, detail="Failed to initialize scan (Database error).")
        
    background_tasks.add_task(run_full_scan, scan_id, request.target_url)
    
    return {
        "id": scan_id,
        "message": "Scan initiated. Check status_url for results.",
        "status_url": f"/scan/{scan_id}"
    }

@app.get("/scan/{scan_id}")
async def get_scan_results(scan_id: int):
    """Get scan results by ID"""
    results = get_results_from_db(scan_id) 
    
    if results is None:
        raise HTTPException(status_code=404, detail=f"Scan ID {scan_id} not found.")
        
    return results

@app.get("/api/reports/{scan_id}")
async def get_report(scan_id: int):
    """Download PDF report for a scan"""
    results = get_results_from_db(scan_id)
    
    if results is None:
        raise HTTPException(status_code=404, detail=f"Scan ID {scan_id} not found")
    
    report_path = generate_pdf_report(scan_id, results)
    
    return FileResponse(
        path=report_path,
        filename=f"vulnerability_report_scan_{scan_id}.pdf",
        media_type="application/pdf"
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "scanner_api": SCANNER_API_URL,
        "ml_api": ML_API_URL
    }

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
        for scan in scans:
            scan["id"] = scan["scan_id"]
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
            cur.execute("SELECT * FROM vulnerabilities WHERE scan_id = %s", (scan_id,))
            vulnerabilities = cur.fetchall()
            scan["vulnerabilities"] = vulnerabilities
            scan["id"] = scan["scan_id"]
            scan["progress"] = scan.get("progress", 0)
            scan["status_message"] = scan.get("status_message", "")
        
        cur.close()
        conn.close()
        
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        return scan
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "BugHunter API",
        "docs": "/docs",
        "health": "/health",
        "reports": "/api/reports/{scan_id}",
        "explain": "/api/explain/{vuln_id}"
    }

@app.get("/api/explain/{vuln_id}")
async def explain_vulnerability(vuln_id: int):
    """
    Get SHAP-like explanation for why a vulnerability has its risk level.
    Returns top contributing factors.
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    try:
        # Get vulnerability from database
        conn = psycopg2.connect(
            dbname="vulnerability_scanner",
            user="scanuser",
            password="scanpass123",
            host="postgres",
            port="5432"
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM vulnerabilities WHERE id = %s", (vuln_id,))
        vuln = cur.fetchone()
        cur.close()
        conn.close()
        
        if not vuln:
            raise HTTPException(status_code=404, detail="Vulnerability not found")
        
        # Prepare features for ML API
        severity = vuln.get('severity', 'Medium')
        cvss_score = float(vuln.get('cvss_score') or 5.0)
        
        def encode_severity(sev):
            mapping = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
            return mapping.get(sev, 1)
        
        ml_input = {
            "cvss_base_score": cvss_score,
            "exploitability_score": cvss_score * 0.4,
            "impact_score": cvss_score * 0.6,
            "cvss_severity_encoded": encode_severity(severity),
            "attack_vector_encoded": 1,  # Network
            "attack_complexity_encoded": 0,  # Low
            "privileges_required_encoded": 2,  # None
            "user_interaction_encoded": 0,  # None
            "cvss_combined": cvss_score,
            "attack_ease_score": cvss_score * 0.3,
            "public_exposure": 1,
            "age_factor": 0.5,
            "severity_score": encode_severity(severity)
        }
        
        # Call ML API explain endpoint
        try:
            ml_response = requests.post(
                ML_API_URL.replace("/predict", "/explain"),
                json=ml_input,
                timeout=10
            )
            ml_response.raise_for_status()
            explanation = ml_response.json()
            
            return {
                "vulnerability_id": vuln_id,
                "vulnerability_type": vuln.get('type', 'Unknown'),
                "severity": severity,
                "risk_level": explanation.get('risk_level', severity),
                "confidence": explanation.get('confidence', 0.8),
                "explanation": explanation.get('explanation', ''),
                "top_factors": explanation.get('top_factors', []),
            }
        except Exception as ml_error:
            print(f"[EXPLAIN] ML API error: {ml_error}")
            # Fallback explanation based on severity
            fallback_factors = generate_fallback_explanation(vuln)
            return {
                "vulnerability_id": vuln_id,
                "vulnerability_type": vuln.get('type', 'Unknown'),
                "severity": severity,
                "risk_level": severity,
                "confidence": 0.75,
                "explanation": f"This vulnerability is rated {severity} because:",
                "top_factors": fallback_factors,
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[EXPLAIN ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))


def generate_fallback_explanation(vuln):
    """Generate fallback explanation when ML API is unavailable"""
    severity = vuln.get('severity', 'Medium')
    vuln_type = vuln.get('type', 'Unknown')
    cvss = float(vuln.get('cvss_score') or 5.0)
    
    factors = []
    
    # Factor 1: CVSS Score
    if cvss >= 7.0:
        factors.append({
            "feature_name": "CVSS Base Score",
            "value": cvss,
            "contribution": 2.5,
            "direction": "increased"
        })
    elif cvss >= 4.0:
        factors.append({
            "feature_name": "CVSS Base Score",
            "value": cvss,
            "contribution": 1.5,
            "direction": "increased"
        })
    else:
        factors.append({
            "feature_name": "CVSS Base Score",
            "value": cvss,
            "contribution": 0.5,
            "direction": "decreased"
        })
    
    # Factor 2: Vulnerability Type
    high_risk_types = ['SQL Injection', 'Remote Code Execution', 'Authentication Bypass']
    medium_risk_types = ['XSS', 'CSRF', 'Missing HTTPS']
    
    if any(t.lower() in vuln_type.lower() for t in high_risk_types):
        factors.append({
            "feature_name": "Vulnerability Type",
            "value": vuln_type,
            "contribution": 2.0,
            "direction": "increased"
        })
    elif any(t.lower() in vuln_type.lower() for t in medium_risk_types):
        factors.append({
            "feature_name": "Vulnerability Type", 
            "value": vuln_type,
            "contribution": 1.2,
            "direction": "increased"
        })
    else:
        factors.append({
            "feature_name": "Vulnerability Type",
            "value": vuln_type,
            "contribution": 0.5,
            "direction": "neutral"
        })
    
    # Factor 3: Network Exposure
    factors.append({
        "feature_name": "Network Exposure",
        "value": "Internet-facing",
        "contribution": 1.5,
        "direction": "increased"
    })
    
    # Factor 4: Authentication
    if severity in ['Critical', 'High']:
        factors.append({
            "feature_name": "Authentication Required",
            "value": "None",
            "contribution": 1.0,
            "direction": "increased"
        })
    else:
        factors.append({
            "feature_name": "Authentication Required",
            "value": "Required",
            "contribution": -0.5,
            "direction": "decreased"
        })
    
    # Factor 5: Exploit Availability
    if severity == 'Critical':
        factors.append({
            "feature_name": "Public Exploit",
            "value": "Available",
            "contribution": 1.8,
            "direction": "increased"
        })
    else:
        factors.append({
            "feature_name": "Public Exploit",
            "value": "Unknown",
            "contribution": 0.3,
            "direction": "neutral"
        })
    
    return factors[:5]  # Return top 5


@app.delete("/api/reset")
def reset_all_data():
    """Reset all scan data (for demo purposes)"""
    try:
        from db_utils import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM vulnerabilities")
        cursor.execute("DELETE FROM scans")
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print("[RESET] All data deleted successfully!")
        return {"message": "All scan data has been reset successfully", "status": "success"}
    except Exception as e:
        print(f"[RESET ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)