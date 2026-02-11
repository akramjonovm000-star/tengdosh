import os
import requests
import json
import logging
import subprocess
from collections import defaultdict
import time

# API Config
API_URL = "https://student.jmcu.uz/rest/v1/data/student-list"
API_TOKEN = "LXjqwQE0Xemgq3E7LeB0tn2yMQWY0zXW"
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

# DB Config
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "Mukhammadali2623")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "talabahamkorbot_db")

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_all_students():
    """Fetches all students from JMCU API with pagination."""
    all_students = []
    page = 1
    limit = 200
    
    while True:
        logger.info(f"Fetching page {page}...")
        try:
            resp = requests.get(API_URL, params={"limit": limit, "page": page}, headers=HEADERS, verify=False, timeout=30)
            data = resp.json()
            
            if not data.get("success"):
                logger.error(f"API Error: {data}")
                break
            
            items = data.get("data", {}).get("items", [])
            if not items:
                break
            
            all_students.extend(items)
            
            total = data.get("data", {}).get("pagination", {}).get("totalCount", 0)
            logger.info(f"Fetched {len(items)} items. Total fetched: {len(all_students)}/{total}")
            
            if len(all_students) >= total:
                break
            
            page += 1
            time.sleep(0.1) # Be nice to API
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            break
            
    return all_students

def get_registered_ids_from_psql():
    """Execute psql command to get registered logins."""
    query_reg = "SELECT hemis_login FROM students WHERE hemis_login LIKE '395%';"
    query_act = "SELECT s.hemis_login FROM students s JOIN tg_accounts t ON s.id = t.student_id WHERE s.hemis_login LIKE '395%';"
    
    try:
        env = os.environ.copy()
        env['PGPASSWORD'] = DB_PASSWORD
        
        # Registered
        cmd_reg = ["psql", "-h", DB_HOST, "-U", DB_USER, "-d", DB_NAME, "-t", "-A", "-c", query_reg]
        out_reg = subprocess.check_output(cmd_reg, env=env, text=True)
        registered = set(out_reg.strip().split('\n')) if out_reg.strip() else set()
        
        # Active
        cmd_act = ["psql", "-h", DB_HOST, "-U", DB_USER, "-d", DB_NAME, "-t", "-A", "-c", query_act]
        out_act = subprocess.check_output(cmd_act, env=env, text=True)
        active = set(out_act.strip().split('\n')) if out_act.strip() else set()
        
        # Filter empty strings
        registered = {x for x in registered if x}
        active = {x for x in active if x}
        
        return registered, active
    except subprocess.CalledProcessError as e:
        logger.error(f"PSQL Error: {e}")
        return set(), set()

def get_tutor_map_from_psql():
    """Execute psql command to get group -> tutor name mapping."""
    query = "SELECT tg.group_number, s.full_name FROM tutor_groups tg JOIN staff s ON tg.tutor_id = s.id;"
    
    try:
        env = os.environ.copy()
        env['PGPASSWORD'] = DB_PASSWORD
        
        cmd = ["psql", "-h", DB_HOST, "-U", DB_USER, "-d", DB_NAME, "-t", "-A", "-F", "|", "-c", query]
        out = subprocess.check_output(cmd, env=env, text=True)
        
        tutor_map = {}
        if out.strip():
            for line in out.strip().split('\n'):
                parts = line.split('|')
                if len(parts) >= 2:
                    group_num = parts[0].strip()
                    tutor_name = parts[1].strip()
                    tutor_map[group_num] = tutor_name
        
        return tutor_map
    except subprocess.CalledProcessError as e:
        logger.error(f"PSQL Error: {e}")
        return {}

def generate_report():
    logger.info("Starting analytics generation...")
    
    # 1. Fetch Data
    api_students = fetch_all_students()
    registered_ids, active_ids = get_registered_ids_from_psql()
    tutor_map = get_tutor_map_from_psql()
    
    logger.info(f"Total API Students: {len(api_students)}")
    logger.info(f"Total Registered DB: {len(registered_ids)}")
    logger.info(f"Total Active (Telegram): {len(active_ids)}")
    
    # 2. Aggregation
    
    stats = {
        "total": len(api_students),
        "registered": 0,
        "active": 0,
        "faculties": defaultdict(lambda: {
            "total": 0, "registered": 0, "active": 0,
            "specialties": defaultdict(lambda: {
                "total": 0, "registered": 0, "active": 0,
                "groups": defaultdict(lambda: {"total": 0, "registered": 0, "active": 0})
            })
        })
    }
    
    for s in api_students:
        login = s.get("student_id_number")
        fac_name = s.get("department", {}).get("name", "Noma'lum Fakultet")
        spec_name = s.get("specialty", {}).get("name", "Noma'lum Yo'nalish")
        group_name = s.get("group", {}).get("name", "Noma'lum Guruh")
        
        is_reg = login in registered_ids
        is_act = login in active_ids
        
        # Global
        if is_reg: stats["registered"] += 1
        if is_act: stats["active"] += 1
        
        # Hierarchy: Faculty -> Specialty -> Group
        fac = stats["faculties"][fac_name]
        fac["total"] += 1
        if is_reg: fac["registered"] += 1
        if is_act: fac["active"] += 1
        
        spec = fac["specialties"][spec_name]
        spec["total"] += 1
        if is_reg: spec["registered"] += 1
        if is_act: spec["active"] += 1
        
        grp = spec["groups"][group_name]
        grp["total"] += 1
        if is_reg: grp["registered"] += 1
        if is_act: grp["active"] += 1

    # 3. Output Markdown (Clean Hierarchy Only)
    report_lines = []
    report_lines.append("# 📊 JMCU Talabalar Analytics Hisoboti")
    report_lines.append(f"**Jami Talabalar (HEMIS):** {stats['total']}")
    report_lines.append(f"**Ro'yxatdan o'tgan (DB):** {stats['registered']} ({stats['registered']/stats['total']*100:.1f}%)")
    report_lines.append(f"**Faol (Telegram ulangan):** {stats['active']} ({stats['active']/stats['total']*100:.1f}%)")
    report_lines.append("\n---")
    
    sorted_facs = sorted(stats["faculties"].items(), key=lambda x: x[1]['total'], reverse=True)
    
    for fac_name, fac_data in sorted_facs:
        report_lines.append(f"\n## 🏫 {fac_name}")
        report_lines.append(f"**Jami:** {fac_data['total']} | **Active:** {fac_data['active']} ({fac_data['active']/fac_data['total']*100:.1f}%)")
        
        sorted_specs = sorted(fac_data["specialties"].items(), key=lambda x: x[1]['total'], reverse=True)
        
        for spec_name, spec_data in sorted_specs:
            report_lines.append(f"\n### 🎓 {spec_name}")
            report_lines.append(f"**Jami:** {spec_data['total']} | **Active:** {spec_data['active']} ({spec_data['active']/spec_data['total']*100:.1f}%)")
            
            report_lines.append("\n| Guruh | Tyutor | Jami | Active | % |")
            report_lines.append("|---|---|---|---|---|")
            
            sorted_grps = sorted(spec_data["groups"].items(), key=lambda x: x[0])
            
            for grp_name, grp_data in sorted_grps:
                pct = (grp_data['active'] / grp_data['total'] * 100) if grp_data['total'] > 0 else 0
                
                # Match group name (Full) with Tutor Map (Short codes)
                t_name = "-"
                
                # Direct lookup
                if grp_name in tutor_map:
                    t_name = tutor_map[grp_name]
                else:
                    # Prefix lookup: Check if any key in tutor_map is a prefix of grp_name
                    # Optimization: Extract the code (first word) from grp_name
                    parts = grp_name.split(' ')
                    if parts:
                        code = parts[0]
                        if code in tutor_map:
                            t_name = tutor_map[code]
                
                report_lines.append(f"| {grp_name} | {t_name} | {grp_data['total']} | {grp_data['active']} | {pct:.1f}% |")
    
    with open("jmcu_analytics_report.md", "w") as f:
        f.write("\n".join(report_lines))
    
    logger.info("Report generated: jmcu_analytics_report.md")

if __name__ == "__main__":
    generate_report()
