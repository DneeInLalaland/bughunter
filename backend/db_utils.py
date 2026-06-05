# db_utils.py - REAL PostgreSQL Implementation
import psycopg2 
from psycopg2 import sql
from fastapi import HTTPException
from datetime import datetime

# =======================================================
# *** ส่วนที่ 1: การตั้งค่าการเชื่อมต่อ (DB_CONFIG) ***
# =======================================================

DB_CONFIG = {
    "dbname": "vulnerability_scanner",
    "user": "scanuser",
    "password": "scanpass123",
    "host": "postgres",
    "port": "5432"
}


# ----------------- 2. การเชื่อมต่อ DB -----------------
def get_db_connection():
    """สร้างและคืนค่าการเชื่อมต่อฐานข้อมูล"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed. Check DB_CONFIG and PostgreSQL Service.")

# =======================================================
# *** ส่วนที่ 2: ฟังก์ชันสำหรับ CRUD (CREATE, READ, UPDATE) ***
# =======================================================

def start_new_scan_in_db(target_url: str):
    """บันทึกการสแกนใหม่ลงในตาราง scans และคืนค่า scan_id"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO scans (target_url, status, start_time) VALUES (%s, %s, %s) RETURNING scan_id;",
                (target_url, 'running', datetime.now())
            )
            scan_id = cur.fetchone()[0]
            conn.commit()
            print(f"[DB REAL] Started scan with ID: {scan_id}")
            return scan_id
    except Exception as e:
        print(f"Error starting new scan: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def save_vulnerability(scan_id: int, vuln_data: dict):
    """บันทึกช่องโหว่และคะแนน AI ลงในตาราง vulnerabilities"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO vulnerabilities (scan_id, type, severity, ai_risk_score, description, affected_url, discovered_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    scan_id, 
                    vuln_data.get('type'), 
                    vuln_data.get('severity'), 
                    vuln_data.get('ai_risk_score', 0.0),
                    vuln_data.get('description', 'No description provided.'), 
                    vuln_data.get('affected_url', None),
                    datetime.now()
                )
            )
            conn.commit()
            print(f"[DB REAL] Saved vuln '{vuln_data.get('type')}' for scan ID {scan_id}")
    except Exception as e:
        print(f"Error saving vulnerability: {e}")
        conn.rollback()
    finally:
        conn.close()


def update_scan_status(scan_id: int, status: str):
    """อัพเดตสถานะการสแกนในตาราง scans (พร้อมบันทึก end_time และนับ severity counts)"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if status in ('completed', 'failed'):
                # นับจำนวน vulnerabilities ทั้งหมด
                cur.execute(
                    "SELECT COUNT(*) FROM vulnerabilities WHERE scan_id = %s;",
                    (scan_id,)
                )
                vuln_count = cur.fetchone()[0]
                
                # 🔥 FIX: นับแยกตาม severity
                cur.execute("""
                    SELECT 
                        COALESCE(SUM(CASE WHEN LOWER(severity) = 'critical' THEN 1 ELSE 0 END), 0) as critical_count,
                        COALESCE(SUM(CASE WHEN LOWER(severity) = 'high' THEN 1 ELSE 0 END), 0) as high_count,
                        COALESCE(SUM(CASE WHEN LOWER(severity) = 'medium' THEN 1 ELSE 0 END), 0) as medium_count,
                        COALESCE(SUM(CASE WHEN LOWER(severity) = 'low' THEN 1 ELSE 0 END), 0) as low_count
                    FROM vulnerabilities 
                    WHERE scan_id = %s;
                """, (scan_id,))
                
                counts = cur.fetchone()
                critical_count = counts[0]
                high_count = counts[1]
                medium_count = counts[2]
                low_count = counts[3]
                
                print(f"[DB REAL] Severity counts - Critical: {critical_count}, High: {high_count}, Medium: {medium_count}, Low: {low_count}")
                
                # 🔥 FIX: อัพเดตพร้อม severity counts
                cur.execute("""
                    UPDATE scans 
                    SET status = %s, 
                        end_time = %s, 
                        total_vulnerabilities = %s,
                        critical_count = %s,
                        high_count = %s,
                        medium_count = %s,
                        low_count = %s
                    WHERE scan_id = %s;
                """, (status, datetime.now(), vuln_count, critical_count, high_count, medium_count, low_count, scan_id))
                
                print(f"[DB REAL] Scan ID {scan_id} status updated to '{status}' with {vuln_count} vulnerabilities")
            else:
                cur.execute(
                    "UPDATE scans SET status = %s WHERE scan_id = %s;",
                    (status, scan_id)
                )
                print(f"[DB REAL] Scan ID {scan_id} status updated to '{status}'")
            conn.commit()
    except Exception as e:
        print(f"Error updating status: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_results_from_db(scan_id: int):
    """ดึงผลลัพธ์การสแกนและช่องโหว่ทั้งหมดจากฐานข้อมูล"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # ดึงข้อมูลการสแกนหลัก
            cur.execute("SELECT target_url, status, start_time, end_time FROM scans WHERE scan_id = %s;", (scan_id,))
            scan_data = cur.fetchone()
            if not scan_data:
                return None

            scan_keys = ['target_url', 'status', 'start_time', 'end_time']
            result = dict(zip(scan_keys, scan_data))
            result['scan_id'] = scan_id

            # ดึงข้อมูลช่องโหว่ทั้งหมด
            cur.execute(
                "SELECT type, severity, ai_risk_score, description, affected_url FROM vulnerabilities WHERE scan_id = %s ORDER BY ai_risk_score DESC;",
                (scan_id,)
            )
            vulns = cur.fetchall()
            vuln_keys = ['type', 'severity', 'ai_risk_score', 'description', 'affected_url']
            
            result['vulnerabilities'] = [dict(zip(vuln_keys, v)) for v in vulns]
            result['total_vulnerabilities'] = len(result['vulnerabilities'])
            
            return result

    except Exception as e:
        print(f"Error retrieving results: {e}")
        return None
    finally:
        conn.close()

def update_scan_progress(scan_id: int, progress: int, status_message: str = ""):
    """อัปเดต progress ของ scan (0-100%)"""
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
            UPDATE scans 
            SET progress = %s, status_message = %s 
            WHERE scan_id = %s
        """, (progress, status_message, scan_id))
        conn.commit()
        cur.close()
        conn.close()
        print(f"[DB] Progress: {progress}% - {status_message}")
    except Exception as e:
        print(f"[DB] Error updating progress: {e}")