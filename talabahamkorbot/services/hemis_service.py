import httpx
import logging
from datetime import datetime
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import StudentCache


logger = logging.getLogger(__name__)

class HemisService:
    # Point to IPv4 IP directly due to local IPv6 issues
    # BASE_URL = "https://195.158.26.100/rest/v1"
    BASE_URL = "https://student.jmcu.uz/rest/v1"
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    @staticmethod
    def get_headers(token: str = None):
        h = HemisService.HEADERS.copy()
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    @staticmethod
    async def check_auth_status(token: str) -> str:
        """
        Checks if token is valid.
        Returns: 'OK', 'AUTH_ERROR', or 'NETWORK_ERROR'
        """
        async with httpx.AsyncClient(verify=False) as client:
            try:
                # Use account/me as lightweight check
                url = f"{HemisService.BASE_URL}/account/me"
                headers = HemisService.get_headers(token)
                response = await client.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    return "OK"
                if response.status_code in [401, 403]:
                    return "AUTH_ERROR"
                
                # Try OAuth endpoint if REST failed with 404/500 but not 401?
                # Actually, strictly for password check, if account/me gives 401, it's 401.
                return "NETWORK_ERROR"
            except:
                return "NETWORK_ERROR"

    @staticmethod
    async def get_subject_tasks(token: str, semester_id: str = None):
        """Fetch subject tasks to calculate JN"""
        async with httpx.AsyncClient(verify=False) as client:
            url = f"{HemisService.BASE_URL}/data/subject-task-student-list"
            params = {}
            if semester_id:
                params['semester'] = semester_id
            
            try:
                response = await client.get(url, headers=HemisService.get_headers(token), params=params, timeout=20)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", {}).get("items", []) or data.get("data", [])
                return []
            except Exception as e:
                logger.error(f"Error fetching tasks: {e}")
                return []

    # ... authenticate is skipped in replacement content if I target chunks.
    # Wait, replace_file_content requires contiguous block.
    # Lines 7 to 152 covers get_headers, get_subject_tasks, authenticate, get_me.
    # This is fine. I will provide the content for all.
    
    @staticmethod
    async def authenticate(login: str, password: str):
        async with httpx.AsyncClient(verify=False) as client:
            # --- TEST CREDENTIALS ---
            if login == "test_tutor" and password == "123":
                return "test_token_tutor", None
            # ------------------------

            # Use BASE_URL instead of hardcoded IP
            url = f"{HemisService.BASE_URL}/auth/login"

            # Prepare payload - send as INT if digit (Based on Swagger)
            # FORCE INT CASTING to avoid firewall blocks on string logins
            try:
                safe_login = int(str(login))
            except:
                safe_login = login # Fallback if not digits
                
            json_payload = {"login": safe_login, "password": password}

            try:
                response = await client.post(
                    url,
                    json=json_payload,
                    headers=HemisService.get_headers(),
                    timeout=20
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") is False:
                        return None, data.get("error", "Login yoki parol noto'g'ri")
                         
                    token = data.get("data", {}).get("token") or data.get("token")
                    return token, None
                elif response.status_code == 401:
                     try:
                         data = response.json()
                         return None, data.get("error", "Login yoki parol noto'g'ri")
                     except:
                         return None, "Login yoki parol noto'g'ri"
                elif response.status_code == 404:
                     return None, "Bunday foydalanuvchi topilmadi"
                else:
                     return None, f"Server xatosi: {response.status_code}"
            except Exception as e:
                return None, f"Tarmoq xatosi: {str(e)[:50]}"

    @staticmethod
    def generate_auth_url(state: str = "mobile"):
        from config import HEMIS_CLIENT_ID, HEMIS_REDIRECT_URL, HEMIS_AUTH_URL
        return f"{HEMIS_AUTH_URL}?client_id={HEMIS_CLIENT_ID}&redirect_uri={HEMIS_REDIRECT_URL}&response_type=code&state={state}"

    @staticmethod
    def generate_oauth_url(state: str = "mobile"):
        """Alias for generate_auth_url used in some parts of the code."""
        return HemisService.generate_auth_url(state)

    @staticmethod
    async def exchange_code(code: str):
        from config import HEMIS_CLIENT_ID, HEMIS_CLIENT_SECRET, HEMIS_REDIRECT_URL, HEMIS_TOKEN_URL
        async with httpx.AsyncClient(verify=False) as client:
            try:
                data = {
                    "client_id": HEMIS_CLIENT_ID,
                    "client_secret": HEMIS_CLIENT_SECRET,
                    "redirect_uri": HEMIS_REDIRECT_URL,
                    "grant_type": "authorization_code",
                    "code": code
                }
                response = await client.post(HEMIS_TOKEN_URL, data=data, timeout=15)
                if response.status_code == 200:
                    return response.json(), None
                return None, f"Token exchange failed: {response.status_code}"
            except Exception as e:
                return None, str(e)

    @staticmethod
    async def exchange_code_for_token(code: str):
        """Standardizes response for callback handlers."""
        data, error = await HemisService.exchange_code(code)
        if data:
            return data.get("access_token"), None
        return None, error

    @staticmethod
    async def get_me(token: str):
        from config import HEMIS_PROFILE_URL
        
        # --- TEST CREDENTIALS ---
        if token == "test_token_tutor":
            return {
                "id": 99999,
                "uuid": "test-tutor-uuid",
                "type": "employee",
                "login": "test_tutor",
                "firstname": "Test",
                "lastname": "Tyutor",
                "fathername": "Admin",
                "image": "https://ui-avatars.com/api/?name=Test+Tyutor",
                "roles": [{"code": "tutor", "name": "Tyutor"}]
            }
        # ------------------------

        async with httpx.AsyncClient(verify=False) as client:
            try:
                # 1. Try REST API Endpoint (Preferred for Direct Login)
                url = f"{HemisService.BASE_URL}/account/me"
                headers = HemisService.get_headers(token)
                
                response = await client.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    # REST API returns wrapped in "data"
                    if "data" in data:
                        return data["data"]
                    return data
                
                if response.status_code in [401, 403]:
                    return None

                # 2. Fallback to OAuth Endpoint (If token is OAuth)
                url_oauth = f"{HEMIS_PROFILE_URL}?fields=id,uuid,type,login,firstname,surname,patronymic,picture,email,phone,birth_date"
                # For proper IPv4 routing if needed, but here we used hostname in config
                # url_oauth = url_oauth.replace("student.jmcu.uz", "195.158.26.100") 
                
                response = await client.get(url_oauth, headers=headers, timeout=15)
                if response.status_code == 200:
                    return response.json()

                # If both fail
                logger.error(f"Me Error ({response.status_code}): {response.text[:200]}")
                return None
            except Exception as e:
                logger.error(f"Me Error: {e}")
                return None

    @staticmethod
    async def get_student_absence(token: str, semester_code: str = None, student_id: int = None):
        # Simplified Cache Logic
        key = f"attendance_{semester_code}" if semester_code else "attendance_all"
        
        def calculate_totals(data):
            total, excused, unexcused = 0, 0, 0
            for item in data:
                hour = item.get("hour", 2)
                total += hour
                
                # Check status
                # New Logic based on logs: 'explicable': True
                is_explicable = item.get("explicable", False)
                
                # Check absent_on vs absent_off
                # absent_on -> excused hours?
                # absent_off -> unexcused hours?
                
                if is_explicable:
                    excused += hour
                else:
                    # Fallback to old logic just in case
                    status = item.get("absent_status", {})
                    code = str(status.get("code", "12"))
                    name = status.get("name", "").lower()
                    
                    if code in ["11", "13"] or any(x in name for x in ["sababli", "kasallik", "ruxsat", "xizmat"]): 
                         excused += hour
                    else:
                         unexcused += hour
            return total, excused, unexcused

        if student_id:
            try:
                async with AsyncSessionLocal() as session:
                    cache = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                    if cache: 
                        # Check freshness (4h TTL)
                        age = (datetime.utcnow() - cache.updated_at).total_seconds()
                        if age < 4 * 3600:
                            t, e, u = calculate_totals(cache.data)
                            return t, e, u, cache.data
                        # If stale, we keep it for fallback
                        stale_data = cache.data
                    else:
                        stale_data = None
            except: stale_data = None
        else:
            stale_data = None

        async with httpx.AsyncClient(verify=False) as client:
            try:
                params = {"semester": semester_code} if semester_code else {}
                
                response = await client.get(
                    f"{HemisService.BASE_URL}/education/attendance",
                    headers=HemisService.get_headers(token), params=params, timeout=12
                )
                
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    
                    # Update Cache
                    if student_id:
                         async with AsyncSessionLocal() as session:
                             c = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                             if c: 
                                 c.data = data
                                 c.updated_at = datetime.utcnow()
                             else:
                                 session.add(StudentCache(student_id=student_id, key=key, data=data))
                             await session.commit()
                             
                    t, e, u = calculate_totals(data)
                    return t, e, u, data
                
                # Fallback to stale if available
                if stale_data:
                    t, e, u = calculate_totals(stale_data)
                    return t, e, u, stale_data
                
                return 0, 0, 0, []
            except:
                if stale_data:
                    t, e, u = calculate_totals(stale_data)
                    return t, e, u, stale_data
                return 0, 0, 0, []

    @staticmethod
    async def get_semester_list(token: str):
        """Fetch all available semesters"""
        async with httpx.AsyncClient(verify=False) as client:
            try:
                # Standard HEMIS endpoint for semesters
                url = f"{HemisService.BASE_URL}/education/semesters"
                response = await client.get(url, headers=HemisService.get_headers(token), timeout=10)
                
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    # Sort by code descending (latest first) using INT comparison
                    def get_code(x):
                        try:
                            val = x.get("code") or x.get("id")
                            return int(str(val))
                        except:
                            return 0
                            
                    data.sort(key=get_code, reverse=True)
                    return data
                return []
            except Exception as e:
                logger.error(f"Semester List Error: {e}")
                return []

    @staticmethod
    async def get_student_subject_list(token: str, semester_code: str = None, student_id: int = None):
        key = f"subjects_{semester_code}" if semester_code else "subjects_all"
        if student_id:
            try:
                async with AsyncSessionLocal() as session:
                    cache = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                    if cache:
                        age = (datetime.utcnow() - cache.updated_at).total_seconds()
                        if age < 4 * 3600:
                            return cache.data
                        stale_data = cache.data
                    else:
                        stale_data = None
            except: stale_data = None
        else:
            stale_data = None

        async with httpx.AsyncClient(verify=False) as client:
            try:
                params = {"semester": semester_code} if semester_code else {}
                
                response = await client.get(
                    f"{HemisService.BASE_URL}/education/subject-list",
                    headers=HemisService.get_headers(token), params=params, timeout=12
                )
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    
                    # Update Cache
                    if student_id:
                         async with AsyncSessionLocal() as session:
                             c = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                             if c: 
                                 c.data = data
                                 c.updated_at = datetime.utcnow()
                             else:
                                 session.add(StudentCache(student_id=student_id, key=key, data=data))
                             await session.commit()
                             
                    return data
                
                if stale_data: return stale_data
                return []
            except: 
                if stale_data: return stale_data
                return []

    # Keeping other methods minimal or omitting if not critical for Login/Home

    @staticmethod
    async def get_student_schedule_cached(token: str, semester_code: str = None, student_id: int = None):
        key = f"schedule_{semester_code}" if semester_code else "schedule_all"
        if student_id:
            try:
                async with AsyncSessionLocal() as session:
                    cache = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                    if cache:
                        # Add 4 hour TTL
                        age = (datetime.utcnow() - cache.updated_at).total_seconds()
                        if age < 4 * 3600:
                            return cache.data
                        stale_data = cache.data
                    else:
                        stale_data = None
            except: stale_data = None
        else:
            stale_data = None

        async with httpx.AsyncClient(verify=False) as client:
            try:
                params = {"semester": semester_code} if semester_code else {}
                
                response = await client.get(
                    f"{HemisService.BASE_URL}/education/schedule",
                    headers=HemisService.get_headers(token), params=params, timeout=12
                )
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    
                    # Update Cache
                    if student_id:
                         async with AsyncSessionLocal() as session:
                             c = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                             if c: 
                                 c.data = data
                                 c.updated_at = datetime.utcnow()
                             else:
                                 session.add(StudentCache(student_id=student_id, key=key, data=data))
                             await session.commit()
                             
                    return data
                
                if stale_data: return stale_data
                return []
            except: 
                if stale_data: return stale_data
                return []

    @staticmethod
    async def get_student_schedule(token: str, week_start: str, week_end: str):
        """
        Fetch schedule for specific date range.
        Format: YYYY-MM-DD
        """
        async with httpx.AsyncClient(verify=False) as client:
            try:
                params = {
                    "week_start": week_start,
                    "week_end": week_end
                }
                
                response = await client.get(
                    f"{HemisService.BASE_URL}/education/schedule",
                    headers=HemisService.get_headers(token),
                    params=params, 
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    return data
                
                # For now just return empty list to avoid crashing
                return []
            except Exception as e:
                logger.error(f"Schedule Fetch Error: {e}")
                return []

    @staticmethod
    async def get_student_performance(token: str, semester_code: str = None):
        """
        Calculates average GPA using GPACalculator (Weighted Average).
        """
        try:
            subjects = await HemisService.get_student_subject_list(token, semester_code)
            if not subjects:
                return 0.0
            
            from services.gpa_calculator import GPACalculator
            
            # Use the robust calculator
            result = GPACalculator.calculate_gpa(subjects)
            return result.gpa
            
        except Exception as e:
            logger.error(f"Performance Error: {e}")
            return 0.0

    @staticmethod
    def parse_grades_detailed(subject_data: dict) -> list:
        """
        Parses detailed ON/YN grades.
        Returns list of { "name": label, "val_5": x, "raw": y, "type": "JN"|"ON"|"YN"}
        """
        exams = subject_data.get("gradesByExam", []) or []
        
        def to_5_scale(val, max_val):
            if val is None: val = 0
            if max_val == 0: return 0 
            if max_val <= 5: return round(val)
            return round((val / max_val) * 5)
            
        results = []
        for ex in exams:
            code = str(ex.get("examType", {}).get("code"))
            name = ex.get("examType", {}).get("name", "Noma'lum")
            val = ex.get("grade", 0)
            max_b = ex.get("max_ball", 0)
            
            # 11/15: JN, 12: Oraliq, 13: Yakuniy
            type_map = {'11': 'JN', '15': 'JN', '12': 'ON', '13': 'YN'}
            if code in type_map:
                res = {
                    "type": type_map[code],
                    "name": name,
                    "val_5": to_5_scale(val, max_b),
                    "raw": val,
                    "max": max_b
                }
                results.append(res)
        
        return results

    @staticmethod
    async def get_student_resources(token: str, subject_id: str, semester_code: str = None):
        async with httpx.AsyncClient(verify=False) as client:
            try:
                
                url = f"{HemisService.BASE_URL}/education/resources?subject={subject_id}"
                if semester_code:
                    url += f"&semester={semester_code}"
                
                # logger.info(f"Fetching Resources URL: {url}")
                response = await client.get(url, headers=HemisService.get_headers(token), timeout=15)
                # logger.info(f"Resources Response ({response.status_code}): {response.text[:500]}")
                
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    return data
                return []
            except Exception as e:
                logger.error(f"Resources Error: {e}")
                return []

    @staticmethod
    async def download_resource_file(token: str, url: str):
        async with httpx.AsyncClient(verify=False) as client:
            try:
                # Handle relative URLs
                if not url.startswith("http"):
                   # Use IP specifically to avoid IPv6 issues
                   base = "https://195.158.26.100"
                   if not url.startswith("/"):
                       url = "/" + url
                   url = base + url

                response = await client.get(url, headers=HemisService.get_headers(token), timeout=60)
                if response.status_code == 200:
                    filename = "document" # default
                    cd = response.headers.get("content-disposition")
                    if cd:
                        import re
                        fname = re.findall('filename="?([^"]+)"?', cd)
                        if fname: filename = fname[0]
                        
                    return response.content, filename
                return None, None
            except Exception as e:
                logger.error(f"Download Error: {e}")
                return None, None

    @staticmethod
    async def get_semester_teachers(token: str, semester_code: str = None):
        """
        Extracts unique teachers from the student's schedule.
        Returns list of dict: { "id": 123, "name": "...", "subjects": ["Math", "Physics"] }
        """
        # We use schedule because it's the most reliable source of "My Teachers"
        schedule_data = await HemisService.get_student_schedule_cached(token, semester_code)
        if not schedule_data:
            return []
            
        teachers = {}
        for item in schedule_data:
            emp = item.get("employee", {})
            if emp and emp.get("id"):
                tid = emp.get("id")
                if tid not in teachers:
                    teachers[tid] = {
                        "id": tid, # Hemis ID
                        "name": emp.get("name"),
                        "subjects": set()
                    }
                
                # Add subject name context
                subj = item.get("subject", {}).get("name")
                if subj:
                    teachers[tid]["subjects"].add(subj)
        
        # Format for return
        result = []
        for t in teachers.values():
            t["subjects"] = list(t["subjects"])
            result.append(t)
            
        return result
