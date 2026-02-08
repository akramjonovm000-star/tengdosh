import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import StudentCache



logger = logging.getLogger(__name__)

class HemisService:
    # Point to IPv4 IP directly due to local IPv6 issues
    # BASE_URL = "https://195.158.26.100/rest/v1"
    BASE_URL = "https://student.jmcu.uz/rest/v1"
    HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    
    # Shared Client Singletons
    _client: httpx.AsyncClient = None
    _auth_cache: Dict[str, Dict[str, Any]] = {} # {token: {"status": str, "expiry": datetime}}

    @staticmethod
    async def fetch_with_retry(client: httpx.AsyncClient, method: str, url: str, **kwargs):
        """
        Robust fetch with retries for network errors.
        """
        tries = 3
        last_exception = None
        for i in range(tries):
            try:
                response = await client.request(method, url, **kwargs)
                return response
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                last_exception = e
                logger.warning(f"Network error {e}, retrying {i+1}/{tries} for {url}")
                import asyncio
                await asyncio.sleep(1.0 * (i + 1))
            except Exception as e:
                # Other errors (SSL, Protocol) might not be recoverable instantly
                logger.error(f"Unrecoverable Request Error: {e}")
                raise e
        
        logger.error(f"Max retries reached for {url}")
        if last_exception:
            raise last_exception
        raise Exception("Request failed after retries")

    @classmethod
    async def get_client(cls):
        if cls._client is None or cls._client.is_closed:
            # Optimized restrictions for faster connection setup
            # Increased limits to avoid bottlenecks under load
            limits = httpx.Limits(max_keepalive_connections=50, max_connections=200)
            timeout = httpx.Timeout(30.0, connect=10.0) # Increased to 30s
            cls._client = httpx.AsyncClient(
                verify=False,
                limits=limits,
                timeout=timeout,
                headers=cls.HEADERS
            )
        return cls._client

    @classmethod
    async def close_client(cls):
        if cls._client and not cls._client.is_closed:
            await cls._client.aclose()
            cls._client = None

    @staticmethod
    def get_headers(token: str = None):
        # We don't use class HEADERS here because we set default headers in Client
        # But for specific requests we might need Authorization
        h = {} 
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    @staticmethod
    async def check_auth_status(token: str) -> str:
        # Check Cache
        now = datetime.utcnow()
        if token in HemisService._auth_cache:
            cache = HemisService._auth_cache[token]
            if cache["expiry"] > now:
                return cache["status"]
                
        client = await HemisService.get_client()
        try:
            url = f"{HemisService.BASE_URL}/account/me"
            response = await client.get(url, headers=HemisService.get_headers(token))
            
            status = "NETWORK_ERROR"
            if response.status_code == 200:
                status = "OK"
            elif response.status_code in [401, 403]:
                status = "AUTH_ERROR"
            
            # Cache for 2 minutes to reduce latency
            HemisService._auth_cache[token] = {
                "status": status,
                "expiry": now + timedelta(minutes=2)
            }
            return status
        except Exception as e:
            logger.error(f"Auth Check error: {e}")
            return "NETWORK_ERROR"

    @staticmethod
    async def get_subject_tasks(token: str, semester_id: str = None):
        client = await HemisService.get_client()
        url = f"{HemisService.BASE_URL}/data/subject-task-student-list"
        params = {}
        if semester_id:
            params['semester'] = semester_id
        
        try:
            response = await HemisService.fetch_with_retry(client, "GET", url, headers=HemisService.get_headers(token), params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("items", []) or data.get("data", [])
            return []
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return []

    @staticmethod
    async def authenticate(login: str, password: str):
        client = await HemisService.get_client()
        # --- TEST CREDENTIALS ---
        if login == "test_tutor" and password == "123":
            return "test_token_tutor", None
        # ------------------------

        url = f"{HemisService.BASE_URL}/auth/login"
        try:
            safe_login = int(str(login))
        except:
            safe_login = login 
            
        json_payload = {"login": safe_login, "password": password}

        try:
            # We don't overwrite headers, just use defaults + json content type is automatic with json=
            # LOGGING ADDED FOR DEBUGGING
            logger.info(f"Authenticating User: {safe_login}...")
            
            response = await HemisService.fetch_with_retry(
                client, "POST", url, json=json_payload
            )
            
            logger.info(f"Auth Response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") is False:
                    return None, data.get("error", "Login yoki parol noto'g'ri")
                        
                token = data.get("data", {}).get("token") or data.get("token")
                return token, None
            elif response.status_code == 401:
                    try:
                        data = response.json()
                        logger.warning(f"Auth Failed 401: {data}")
                        return None, data.get("error", "Login yoki parol noto'g'ri")
                    except:
                        return None, "Login yoki parol noto'g'ri"
            elif response.status_code == 404:
                    return None, "Bunday foydalanuvchi topilmadi"
            else:
                    logger.error(f"Auth Server Error: {response.status_code} - {response.text}")
                    return None, f"Server xatosi: {response.status_code}"
        except Exception as e:
            logger.error(f"Auth Network Exception: {e}")
            return None, f"Tarmoq xatosi: {str(e)[:50]}"

    @staticmethod
    def generate_auth_url(state: str = "mobile", role: str = "student"):
        from config import (
            HEMIS_CLIENT_ID, HEMIS_REDIRECT_URL, HEMIS_AUTH_URL,
            HEMIS_STAFF_CLIENT_ID, HEMIS_STAFF_REDIRECT_URL
        )
        
        domain = HEMIS_AUTH_URL
        client_id = HEMIS_CLIENT_ID
        redirect_uri = HEMIS_REDIRECT_URL

        if role == "staff":
            client_id = HEMIS_STAFF_CLIENT_ID
            redirect_uri = HEMIS_STAFF_REDIRECT_URL
            if "student.jmcu.uz" in domain:
                domain = domain.replace("student.jmcu.uz", "hemis.jmcu.uz")
        else: # student
            if "hemis.jmcu.uz" in domain:
                domain = domain.replace("hemis.jmcu.uz", "student.jmcu.uz")
            
        return f"{domain}?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&state={state}"

    @staticmethod
    def generate_oauth_url(state: str = "mobile"):
        return HemisService.generate_auth_url(state)

    @staticmethod
    async def exchange_code(code: str, base_url: Optional[str] = None):
        # OAuth usually requires fresh client context or we can use shared
        # Keeping shared is fine
        client = await HemisService.get_client()
        from config import (
            HEMIS_CLIENT_ID, HEMIS_CLIENT_SECRET, HEMIS_REDIRECT_URL, HEMIS_TOKEN_URL,
            HEMIS_STAFF_CLIENT_ID, HEMIS_STAFF_CLIENT_SECRET, HEMIS_STAFF_REDIRECT_URL
        )
        
        # Determine credentials based on base_url
        is_staff = base_url and "hemis.jmcu.uz" in base_url
        
        c_id = HEMIS_STAFF_CLIENT_ID if is_staff else HEMIS_CLIENT_ID
        c_secret = HEMIS_STAFF_CLIENT_SECRET if is_staff else HEMIS_CLIENT_SECRET
        r_uri = HEMIS_STAFF_REDIRECT_URL if is_staff else HEMIS_REDIRECT_URL

        # Determine token URL
        token_url = HEMIS_TOKEN_URL
        if base_url:
            domain = base_url
            if domain.endswith("/rest/v1"): domain = domain.replace("/rest/v1", "")
            token_url = f"{domain}/oauth/access-token"

        try:
            # Basic Auth + Body params (No credentials in body, as per test bot standard)
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": r_uri,
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            logger.info(f"Token Exchange (Basic Auth) on {token_url}: client_id={c_id}, redirect_uri={r_uri}")
            
            response = await client.post(token_url, data=data, headers=headers, auth=(c_id, c_secret))
            
            if response.status_code == 200:
                return response.json(), None
            
            logger.error(f"Token Exchange Failed: {response.status_code} - {response.text}")
            return None, f"Token exchange failed: {response.status_code} Body: {response.text}"
        except Exception as e:
            logger.error(f"Token Exchange Exception: {e}")
            return None, str(e)

    @staticmethod
    async def exchange_code_for_token(code: str):
        data, error = await HemisService.exchange_code(code)
        if data:
            return data.get("access_token"), None
        return None, error

    @staticmethod
    async def get_me(token: str, base_url: Optional[str] = None):
        from config import HEMIS_PROFILE_URL
        
        # Determine URLs
        domain = base_url or "https://student.jmcu.uz"
        if domain.endswith("/rest/v1"): domain = domain.replace("/rest/v1", "")
        
        rest_url = f"{domain}/rest/v1/account/me"
        oauth_profile_url = f"{domain}/oauth/api/user?fields=id,uuid,type,login,firstname,surname,patronymic,picture,email,phone,birth_date,roles"

        client = await HemisService.get_client()
        try:
            # 1. Try REST API Endpoint
            response = await HemisService.fetch_with_retry(client, "GET", rest_url, headers=HemisService.get_headers(token))
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    return data["data"]
                return data
            
            if response.status_code in [401, 403]:
                return None

            # 2. Fallback to OAuth Endpoint
            logger.warning(f"REST Profile failed ({response.status_code}). Trying OAuth Profile on {oauth_profile_url}...")
            response = await HemisService.fetch_with_retry(client, "GET", oauth_profile_url, headers=HemisService.get_headers(token))
            if response.status_code == 200:
                return response.json()

            return None
        except Exception as e:
            logger.error(f"Me Error: {e}")
            return None

    @staticmethod
    async def get_student_absence(token: str, semester_code: str = None, student_id: int = None, force_refresh: bool = False):
        key = f"attendance_{semester_code}" if semester_code else "attendance_all"
        
        def calculate_totals(data):
            total, excused, unexcused = 0, 0, 0
            for item in data:
                hour = item.get("hour", 2)
                total += hour
                is_explicable = item.get("explicable", False)
                if is_explicable:
                    excused += hour
                else:
                    status = item.get("absent_status", {})
                    code = str(status.get("code", "12"))
                    name = status.get("name", "").lower()
                    if code in ["11", "13"] or any(x in name for x in ["sababli", "kasallik", "ruxsat", "xizmat"]): 
                         excused += hour
                    else:
                         unexcused += hour
            return total, excused, unexcused

        stale_data = None
        # Check Cache if not forcing refresh
        if student_id and not force_refresh:
            try:
                async with AsyncSessionLocal() as session:
                    cache = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                    if cache: 
                        # Cache validity: 30 minutes for attendance (it changes often)
                        age = (datetime.utcnow() - cache.updated_at).total_seconds()
                        if age < 30 * 60:
                            t, e, u = calculate_totals(cache.data)
                            return t, e, u, cache.data
                        stale_data = cache.data
            except Exception as e: 
                logger.error(f"Cache Read Error: {e}")

        client = await HemisService.get_client()
        try:
            params = {"semester": semester_code} if semester_code else {}
            response = await HemisService.fetch_with_retry(
                client, "GET", 
                f"{HemisService.BASE_URL}/education/attendance",
                headers=HemisService.get_headers(token), params=params
            )
            
            if response.status_code == 200:
                data = response.json().get("data", [])
                
                # Update Cache ONLY if data is present
                if student_id and data:
                     try:
                         async with AsyncSessionLocal() as session:
                             c = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                             if c: 
                                 c.data = data
                                 c.updated_at = datetime.utcnow()
                             else:
                                 session.add(StudentCache(student_id=student_id, key=key, data=data))
                             await session.commit()
                     except Exception as e:
                         logger.error(f"Cache Write Error: {e}")
                         
                t, e, u = calculate_totals(data)
                return t, e, u, data
            
            if stale_data:
                t, e, u = calculate_totals(stale_data)
                return t, e, u, stale_data
            
            return 0, 0, 0, []
        except Exception as e:
            if stale_data:
                t, e, u = calculate_totals(stale_data)
                return t, e, u, stale_data
            # Raise error if no cache and network failed
            logger.error(f"Absence Error: {e}")
            raise e

    @staticmethod
    async def get_semester_list(token: str, student_id: int = None, force_refresh: bool = False):
        key = "semesters_list"
        
        # Check Cache
        if student_id and not force_refresh:
            try:
                async with AsyncSessionLocal() as session:
                    cache = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                    # Cache validity: 24 hours for semesters (they rarely change)
                    if cache and (datetime.utcnow() - cache.updated_at).total_seconds() < 86400:
                        return cache.data
            except Exception as e: 
                logger.error(f"Semester Cache Read Error: {e}")

        client = await HemisService.get_client()
        try:
            url = f"{HemisService.BASE_URL}/education/semesters"
            response = await HemisService.fetch_with_retry(client, "GET", url, headers=HemisService.get_headers(token))
            
            if response.status_code == 200:
                data = response.json().get("data", [])
                
                # Update Cache
                if student_id and data:
                    try:
                        async with AsyncSessionLocal() as session:
                            c = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                            if c: 
                                c.data = data
                                c.updated_at = datetime.utcnow()
                            else:
                                session.add(StudentCache(student_id=student_id, key=key, data=data))
                            await session.commit()
                    except Exception as e:
                        logger.error(f"Semester Cache Write Error: {e}")

                def get_code(x):
                    try: return int(str(x.get("code") or x.get("id")))
                    except: return 0
                data.sort(key=get_code, reverse=True)
                return data
            return []
        except Exception as e:
            logger.error(f"Semester List Error: {e}")
            return []

    @staticmethod
    async def get_student_subject_list(token: str, semester_code: str = None, student_id: int = None, force_refresh: bool = False):
        key = f"subjects_{semester_code}" if semester_code else "subjects_all"
        
        # Check Cache
        if student_id and not force_refresh:
            try:
                async with AsyncSessionLocal() as session:
                    cache = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                    # Cache validity: 1 hour for subjects/grades
                    if cache and (datetime.utcnow() - cache.updated_at).total_seconds() < 3600:
                        return cache.data
            except Exception as e: 
                pass

        client = await HemisService.get_client()
        try:
            params = {"semester": semester_code} if semester_code else {}
            response = await HemisService.fetch_with_retry(
                client, "GET", 
                f"{HemisService.BASE_URL}/education/subject-list",
                headers=HemisService.get_headers(token), params=params
            )
            if response.status_code == 200:
                data = response.json().get("data", [])
                # Update Cache ONLY if data is present
                if student_id and data:
                     try:
                         async with AsyncSessionLocal() as session:
                             c = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                             if c: 
                                 c.data = data
                                 c.updated_at = datetime.utcnow()
                             else:
                                 session.add(StudentCache(student_id=student_id, key=key, data=data))
                             await session.commit()
                     except Exception as e:
                         logger.error(f"Cache Write Error: {e}")
                return data
            return []
        except Exception as e:
            logger.error(f"Subject List Error: {e}")
            return []

    @staticmethod
    async def get_student_schedule_cached(token: str, semester_code: str = None, student_id: int = None, force_refresh: bool = False):
        key = f"schedule_{semester_code}" if semester_code else "schedule_all"
        
        # Check Cache
        if student_id and not force_refresh:
            try:
                async with AsyncSessionLocal() as session:
                    cache = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                    # Cache validity: 1 day for schedule (it basically never changes mid-semester)
                    if cache and (datetime.utcnow() - cache.updated_at).total_seconds() < 86400:
                            return cache.data
            except Exception as e: 
                pass # Removed logger.error(f"Cache Read Error: {e}")

        client = await HemisService.get_client()
        try:
            params = {"semester": semester_code} if semester_code else {}
            response = await HemisService.fetch_with_retry(
                client, "GET", 
                f"{HemisService.BASE_URL}/education/schedule",
                headers=HemisService.get_headers(token), params=params
            )
            if response.status_code == 200:
                data = response.json().get("data", [])
                # Update Cache ONLY if data is present
                if student_id and data:
                     try:
                         async with AsyncSessionLocal() as session:
                             c = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                             if c: 
                                 c.data = data
                                 c.updated_at = datetime.utcnow()
                             else:
                                 session.add(StudentCache(student_id=student_id, key=key, data=data))
                             await session.commit()
                     except Exception as e:
                         logger.error(f"Cache Write Error: {e}")
                return data
            return []
        except Exception as e:
            logger.error(f"Schedule Error: {e}")
            return []

    @staticmethod
    async def get_curriculum_topics(token: str, subject_id: str = None, semester_code: str = None, training_type_code: str = None, student_id: int = None):
        key = f"curriculum_topics_{subject_id}_{semester_code}_{training_type_code}"
        if student_id:
            try:
                async with AsyncSessionLocal() as session:
                    cache = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                    # Cache validity: 3 days for curriculum
                    if cache and (datetime.utcnow() - cache.updated_at).total_seconds() < 3 * 86400:
                            return cache.data
            except: pass

        client = await HemisService.get_client()
        try:
            params = {
                "limit": 200,
                "_subject": subject_id,
                "_semester": semester_code,
                "_training_type": training_type_code
            }
            params = {k: v for k, v in params.items() if v is not None}
            
            url = f"{HemisService.BASE_URL}/data/curriculum-subject-topic-list"
            response = await client.get(url, headers=HemisService.get_headers(token), params=params)
            
            if response.status_code == 200:
                data = response.json().get("data", {}).get("items", [])
                # Only cache if data exists
                if student_id and data:
                    async with AsyncSessionLocal() as session:
                        c = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                        if c:
                            c.data = data
                            c.updated_at = datetime.utcnow()
                        else:
                            session.add(StudentCache(student_id=student_id, key=key, data=data))
                        await session.commit()
                return data
            return []
        except: return []

    @staticmethod
    async def get_student_schedule(token: str, week_start: str, week_end: str):
        client = await HemisService.get_client()
        try:
            params = {"week_start": week_start, "week_end": week_end}
            response = await client.get(
                f"{HemisService.BASE_URL}/education/schedule",
                headers=HemisService.get_headers(token),
                params=params
            )
            if response.status_code == 200:
                return response.json().get("data", [])
            return []
        except: return []

    @staticmethod
    async def get_student_performance(token: str, student_id: int = None, semester_code: str = None):
        try:
            # Reuses get_student_subject_list which is cached
            subjects = await HemisService.get_student_subject_list(token, semester_code=semester_code, student_id=student_id)
            if not subjects: return 0.0
            from services.gpa_calculator import GPACalculator
            result = GPACalculator.calculate_gpa(subjects)
            return result.gpa
        except Exception as e:
            logger.error(f"GPA Calculation Error: {e}")
            return 0.0

    @staticmethod
    def parse_grades_detailed(subject_data: dict) -> dict:
        exams = subject_data.get("gradesByExam", []) or []
        def to_5_scale(val, max_val):
            if val is None: val = 0
            if max_val == 0: return 0 
            if max_val <= 5: return round(val)
            return round((val / max_val) * 5)
            
        # Default Structure
        results = {
            "JN": {"val_5": 0, "raw": 0, "max": 0},
            "ON": {"val_5": 0, "raw": 0, "max": 0},
            "YN": {"val_5": 0, "raw": 0, "max": 0},
            "total": {"val_5": 0, "raw": 0, "max": 0},
            "raw_total": 0
        }
        
        raw_total = 0
        for ex in exams:
            code = str(ex.get("examType", {}).get("code"))
            name = ex.get("examType", {}).get("name", "Noma'lum")
            val = ex.get("grade", 0)
            max_b = ex.get("max_ball", 0)
            
            raw_total += val
            
            # 11/15: JN, 12: ON, 13: YN
            type_map = {'11': 'JN', '15': 'JN', '12': 'ON', '13': 'YN'}
            if code in type_map:
                t = type_map[code]
                results[t] = {
                    "type": t,
                    "name": name,
                    "val_5": to_5_scale(val, max_b),
                    "raw": val,
                    "max": max_b
                }
        
        results["raw_total"] = raw_total
        return results

    @staticmethod
    async def get_student_resources(token: str, subject_id: str, semester_code: str = None):
        client = await HemisService.get_client()
        try:
            url = f"{HemisService.BASE_URL}/education/resources?subject={subject_id}"
            if semester_code:
                url += f"&semester={semester_code}"
            
            response = await client.get(url, headers=HemisService.get_headers(token))
            if response.status_code == 200:
                return response.json().get("data", [])
            return []
        except: return []

    @staticmethod
    async def download_resource_file(token: str, url: str):
        # For heavy downloads, maybe use a fresh client or streaming?
        # But shared client is fine usually.
        client = await HemisService.get_client()
        try:
            if not url.startswith("http"):
               base = "https://student.jmcu.uz" # Reverted IP hardcode here too
               if not url.startswith("/"): url = "/" + url
               url = base + url

            # Long timeout for downloads
            response = await client.get(url, headers=HemisService.get_headers(token)) # Timeout is global 20s
            if response.status_code == 200:
                filename = "document"
                cd = response.headers.get("content-disposition")
                if cd:
                    import re
                    fname = re.findall('filename="?([^"]+)"?', cd)
                    if fname: filename = fname[0]
                return response.content, filename
            return None, None
        except: return None, None

    @staticmethod
    async def get_semester_teachers(token: str, semester_code: str = None):
        schedule_data = await HemisService.get_student_schedule_cached(token, semester_code)
        if not schedule_data: return []
            
        teachers = {}
        for item in schedule_data:
            emp = item.get("employee", {})
            if emp and emp.get("id"):
                tid = emp.get("id")
                if tid not in teachers:
                    teachers[tid] = {
                        "id": tid, 
                        "name": emp.get("name"),
                        "subjects": set()
                    }
                subj = item.get("subject", {}).get("name")
                if subj: teachers[tid]["subjects"].add(subj)
        
        result = []
        for t in teachers.values():
            t["subjects"] = list(t["subjects"])
            t["subjects"].sort()
            result.append(t)
        return result

    # --- Surveys (So'rovnomalar) ---
    
    @staticmethod
    async def get_student_surveys(token: str):
        """GET /v1/student/survey"""
        client = await HemisService.get_client()
        try:
            url = f"{HemisService.BASE_URL}/student/survey"
            response = await client.get(url, headers=HemisService.get_headers(token))
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error fetching surveys: {e}")
            return None

    @staticmethod
    async def start_student_survey(token: str, survey_id: int):
        """POST /v1/student/survey-start"""
        client = await HemisService.get_client()
        try:
            url = f"{HemisService.BASE_URL}/student/survey-start"
            payload = {"id": survey_id, "lang": "UZ"}
            response = await client.post(url, headers=HemisService.get_headers(token), json=payload)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error starting survey: {e}")
            return None

    @staticmethod
    async def submit_survey_answer(token: str, question_id: int, button_type: str, answer: Any):
        """POST /v1/student/survey-answer"""
        client = await HemisService.get_client()
        try:
            url = f"{HemisService.BASE_URL}/student/survey-answer"
            payload = {
                "question_id": question_id,
                "button_type": button_type,
                "answer": answer
            }
            response = await client.post(url, headers=HemisService.get_headers(token), json=payload)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error submitting survey answer: {e}")
            return None

    @staticmethod
    async def finish_student_survey(token: str, quiz_rule_id: int):
        """POST /v1/student/survey-finish"""
        client = await HemisService.get_client()
        try:
            url = f"{HemisService.BASE_URL}/student/survey-finish"
            payload = {"quiz_rule_id": quiz_rule_id}
            response = await client.post(url, headers=HemisService.get_headers(token), json=payload)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error finishing survey: {e}")
            return None

# Force update

    @staticmethod
    async def prefetch_data(token: str, student_id: int):
        """
        Eagerly loads critical data into cache to prevent 'First Load' delay.
        Should be called as a background task upon login.
        """
        logger.info(f"Prefetching data for student {student_id}...")
        try:
            # 0. Warm Me Cache
            await HemisService.get_me(token)

            # 1. Semesters (Fast)
            semesters = await HemisService.get_semester_list(token, student_id=student_id)
            
            # Resolve ID
            sem_code = None
            # Try to get from Me first if possible, but get_me isn't cached here. 
            # Let's assume most recent semester from list is current or close enough for cache warming.
            if semesters:
                 # Find 'current' flag
                 for s in semesters:
                     if s.get("current") is True:
                         sem_code = str(s.get("code") or s.get("id"))
                         break
                 if not sem_code and semesters:
                     sem_code = str(semesters[0].get("code") or semesters[0].get("id"))

            if not sem_code: sem_code = "11" # Fallback

            # 2. Parallel Fetch of Critical Modules
            import asyncio
            await asyncio.gather(
                # Grades / Subjects
                HemisService.get_student_subject_list(token, semester_code=sem_code, student_id=student_id),
                # Attendance
                HemisService.get_student_absence(token, semester_code=sem_code, student_id=student_id),
                # Schedule
                HemisService.get_student_schedule_cached(token, semester_code=sem_code, student_id=student_id)
            )
            logger.info(f"Prefetch complete for student {student_id}")
        except Exception as e:
            logger.error(f"Prefetch error: {e}")

    @staticmethod
    async def get_total_student_count(token: str) -> int:
        """
        Fetches the total number of students visible to the staff member.
        Used for Management Dashboard.
        Attempts /data/student-count-by-shift (User Priority) then fallbacks.
        """
        client = await HemisService.get_client()
        
        # Priority 1: /data/student-count-by-shift (Specific User Request)
        # This endpoint returns aggregated data including "total": 5000
        url_shift = f"{HemisService.BASE_URL}/data/student-count-by-shift"
        try:
             response = await client.get(url_shift, headers=HemisService.get_headers(token))
             if response.status_code == 200:
                 data = response.json()
                 # Structure: { "success": true, "data": { "total": 5000, ... } }
                 if "data" in data and isinstance(data["data"], dict):
                     total = data["data"].get("total")
                     if total is not None:
                         return int(total)
        except Exception as e:
             logger.warning(f"Failed to fetch student count from {url_shift}: {e}")

        # Priority 2: education/student-list (standard), then data/student-list
        endpoints = [
            f"{HemisService.BASE_URL}/education/student-list",
            f"{HemisService.BASE_URL}/data/student-list"
        ]
        
        for url in endpoints:
            try:
                # Fetch only 1 item to get metadata count
                response = await client.get(url, headers=HemisService.get_headers(token), params={"limit": 1, "page": 1})
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Structure 1: { "success": true, "data": { "items": [...], "_meta": { "totalCount": 123 } } }
                    if "data" in data and isinstance(data["data"], dict):
                        meta = data["data"].get("_meta")
                        if meta and "totalCount" in meta:
                            return int(meta["totalCount"])
                            
                    # Structure 2: { "data": { "pagination": { "totalCount": 123 } } }
                    if "data" in data and isinstance(data["data"], dict) and "pagination" in data["data"]:
                         return int(data["data"]["pagination"].get("totalCount", 0))

            except Exception as e:
                logger.warning(f"Failed to fetch student count from {url}: {e}")
                
        return 0
