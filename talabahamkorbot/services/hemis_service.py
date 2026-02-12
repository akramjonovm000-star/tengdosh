import httpx
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import StudentCache
from config import HEMIS_ADMIN_TOKEN



logger = logging.getLogger(__name__)

class HemisService:
    # Point to IPv4 IP directly due to local IPv6 issues
    # BASE_URL = "https://195.158.26.100/rest/v1"
    BASE_URL = "https://student.jmcu.uz/rest/v1"
    HEADERS = {
        "Accept": "application/json"
    }
    
    
    # Shared Client Singletons
    _client: httpx.AsyncClient = None
    _auth_cache: Dict[str, Dict[str, Any]] = {} # {token: {"status": str, "expiry": datetime}}

    @staticmethod
    async def fetch_with_retry(client: httpx.AsyncClient, method: str, url: str, **kwargs):
        """
        Robust fetch with retries for network errors.
        [FIX] Remap hemis.jmcu.uz to student.jmcu.uz for internal network reachability.
        """
        if "hemis.jmcu.uz" in url:
            url = url.replace("hemis.jmcu.uz", "student.jmcu.uz")
            logger.info(f"INTERNAL REMAP: {url}")

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
            # Optimized restrictions to avoid IP Blocking
            # Reduced limits to stay under University Firewall radar
            limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
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
    async def check_auth_status(token: str, base_url: Optional[str] = None) -> str:
        # Check Cache
        now = datetime.utcnow()
        cache_key = f"{token}-{base_url or 'default'}"
        if cache_key in HemisService._auth_cache:
            cache = HemisService._auth_cache[cache_key]
            if cache["expiry"] > now:
                return cache["status"]
                
        client = await HemisService.get_client()
        final_base = base_url or HemisService.BASE_URL
        try:
            url = f"{final_base}/account/me"
            response = await client.get(url, headers=HemisService.get_headers(token))
            
            status = "NETWORK_ERROR"
            if response.status_code == 200:
                status = "OK"
            elif response.status_code in [401, 403]:
                status = "AUTH_ERROR"
            
            # Cache for 2 minutes ONLY IF OK (Don't cache errors)
            if status == "OK":
                HemisService._auth_cache[cache_key] = {
                    "status": status,
                    "expiry": now + timedelta(minutes=2)
                }
            else:
                 # If error, remove from cache so we retry immediately next time
                 if cache_key in HemisService._auth_cache:
                     del HemisService._auth_cache[cache_key]
            return status
        except Exception as e:
            logger.error(f"Auth Check error: {e}")
            return "NETWORK_ERROR"

    @staticmethod
    async def get_subject_tasks(token: str, semester_id: str = None, base_url: Optional[str] = None):
        client = await HemisService.get_client()
        final_base = base_url or HemisService.BASE_URL
        try:
            params = {}
            if semester_id: params["semester"] = str(semester_id)
            
            response = await HemisService.fetch_with_retry(client, "GET", f"{final_base}/education/tasks", headers=HemisService.get_headers(token), params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("items", []) or data.get("data", [])
            return []
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return []

    @staticmethod
    async def authenticate(login: str, password: str, base_url: Optional[str] = None):
        client = await HemisService.get_client()
        
        # Determine URL
        final_base = base_url or HemisService.BASE_URL
        url = f"{final_base}/auth/login"
        
        # --- TEST CREDENTIALS ---
        if login == "test_tutor" and password == "123":
            return "test_token_tutor", None
        # ------------------------

        # [MODIFIED] Ensure login is string for TSUE compatibility
        safe_login = str(login)
        json_payload = {"login": safe_login, "password": password}

        try:
            # We don't overwrite headers, just use defaults + json content type is automatic with json=
            # LOGGING ADDED FOR DEBUGGING
            logger.info(f"Authenticating User: {safe_login}...")
            
            response = await HemisService.fetch_with_retry(
                client, "POST", url, data=json_payload
            )
            
            # [DEBUG] Log Headers to verify if IP is being forwarded
            if hasattr(response.request, 'headers'):
                 logger.info(f"DEBUG OUTGOING HEADERS: {response.request.headers}")
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
            # [FIX] Remap hemis.jmcu.uz to student.jmcu.uz for internal network reachability
            # This is required because hemis.jmcu.uz is not resolvable/reachable from inside the container
            if "hemis.jmcu.uz" in domain:
                 domain = domain.replace("hemis.jmcu.uz", "student.jmcu.uz")
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
    async def exchange_code_for_token(code: str, base_url: Optional[str] = None):
        data, error = await HemisService.exchange_code(code, base_url=base_url)
        if data:
            return data.get("access_token"), None
        return None, error

    @staticmethod
    async def get_me(token: str, base_url: Optional[str] = None, use_oauth_endpoint: bool = False):
        from config import HEMIS_PROFILE_URL
        
        # Determine URLs
        domain = base_url or "https://student.jmcu.uz"
        if domain.endswith("/rest/v1"): domain = domain.replace("/rest/v1", "")
        
        # Ensure rest_url uses the correct base
        rest_base = base_url or HemisService.BASE_URL
        # [FIX] Internal Remap for Profile
        if rest_base and "hemis.jmcu.uz" in rest_base:
             rest_base = rest_base.replace("hemis.jmcu.uz", "student.jmcu.uz")
             domain = domain.replace("hemis.jmcu.uz", "student.jmcu.uz")
             
        rest_url = f"{rest_base}/account/me"
        # Updated fields per user suggestion and GitHub Guide
        oauth_profile_url = f"{domain}/oauth/api/user?fields=id,uuid,type,roles,name,login,picture,email,university_id,phone,employee_id_number,firstname,surname,patronymic,birth_date"

        # [FIX] Header Injection for VHost Routing
        # If we remapped to student.jmcu.uz, we MUST send the original Host header
        # so Nginx knows we want the HEMIS (Staff) vhost, not Student.
        headers = HemisService.get_headers(token)
        if "student.jmcu.uz" in domain and "hemis.jmcu.uz" in (base_url or ""):
             headers["Host"] = "hemis.jmcu.uz"
             logger.info("Injecting 'Host: hemis.jmcu.uz' header for staff request via student.jmcu.uz")

        client = await HemisService.get_client()
        try:
            # 1. If forced or preferred, use OAuth Endpoint directly
            if use_oauth_endpoint:
                logger.info(f"Fetching OAuth Profile directly from {oauth_profile_url}")
                response = await HemisService.fetch_with_retry(client, "GET", oauth_profile_url, headers=headers)
                if response and response.status_code == 200:
                    return response.json()
                logger.warning(f"OAuth Profile failed: {response.status_code if response else 'No Response'}")
                return None

            # 2. Try REST API Endpoint (Standard Flow)
            logger.info(f"DEBUG: Fetching REST Profile from {rest_url}")
            response = await HemisService.fetch_with_retry(client, "GET", rest_url, headers=headers)
            
            if response:
                logger.info(f"DEBUG: REST Response: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    if "data" in data:
                        return data["data"]
                    return data
                
                if response.status_code in [401, 403, 404, 500]:
                     logger.warning(f"REST Profile failed ({response.status_code}). Proceeding to OAuth fallback...")

            # 3. Fallback to OAuth Endpoint
            logger.warning(f"Trying OAuth Profile on {oauth_profile_url}...")
            response = await HemisService.fetch_with_retry(client, "GET", oauth_profile_url, headers=headers)
            
            if response:
                 logger.info(f"DEBUG: OAuth Response: {response.status_code}")
                 if response.status_code == 200:
                     return response.json()
            
            logger.error(f"OAuth Profile Failed: {response.status_code if response else 'No Response'} - {response.text if response else ''}")
            return None
        except Exception as e:
            logger.error(f"Me Error: {e}")
            return None

    @staticmethod
    async def get_student_absence(token: str, semester_code: str = None, student_id: int = None, force_refresh: bool = False, base_url: Optional[str] = None):
        key = f"attendance_{semester_code}" if semester_code else "attendance_all"
        
        final_base = base_url or HemisService.BASE_URL
        
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
                f"{final_base}/education/attendance",
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
    async def get_semester_list(token: str, student_id: int = None, force_refresh: bool = False, base_url: Optional[str] = None):
        key = "semesters_list"
        final_base = base_url or HemisService.BASE_URL
        
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
            url = f"{final_base}/education/semesters"
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
    async def get_student_subject_list(token: str, semester_code: str = None, student_id: int = None, force_refresh: bool = False, base_url: Optional[str] = None):
        key = f"subjects_{semester_code}" if semester_code else "subjects_all"
        final_base = base_url or HemisService.BASE_URL
        
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
                f"{final_base}/education/subject-list",
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
    async def get_student_schedule_cached(token: str, semester_code: str = None, student_id: int = None, force_refresh: bool = False, base_url: Optional[str] = None):
        key = f"schedule_{semester_code}" if semester_code else "schedule_all"
        final_base = base_url or HemisService.BASE_URL
        
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
                f"{final_base}/education/schedule",
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
    async def get_curriculum_topics(token: str, subject_id: str = None, semester_code: str = None, training_type_code: str = None, student_id: int = None, base_url: Optional[str] = None):
        key = f"curriculum_topics_{subject_id}_{semester_code}_{training_type_code}"
        final_base = base_url or HemisService.BASE_URL
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
            
            url = f"{final_base}/data/curriculum-subject-topic-list"
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
    async def get_student_schedule(token: str, week_start: str, week_end: str, base_url: Optional[str] = None):
        client = await HemisService.get_client()
        final_base = base_url or HemisService.BASE_URL
        try:
            params = {"week_start": week_start, "week_end": week_end}
            response = await client.get(
                f"{final_base}/education/schedule",
                headers=HemisService.get_headers(token),
                params=params
            )
            if response.status_code == 200:
                return response.json().get("data", [])
            return []
        except: return []

    @staticmethod
    async def get_student_performance(token: str, student_id: int = None, semester_code: str = None, base_url: Optional[str] = None):
        try:
            # Reuses get_student_subject_list which is cached
            subjects = await HemisService.get_student_subject_list(token, semester_code=semester_code, student_id=student_id, base_url=base_url)
            if not subjects: return 0.0
            from services.gpa_calculator import GPACalculator
            result = GPACalculator.calculate_gpa(subjects)
            return result.gpa
        except Exception as e:
            logger.error(f"GPA Calculation Error: {e}")
            return 0.0

    @staticmethod
    def parse_grades_detailed(subject_data: dict, skip_conversion: bool = False) -> dict:
        exams = subject_data.get("gradesByExam", []) or []
        def to_5_scale(val, max_val):
            if val is None: val = 0
            if max_val == 0: return 0 
            if max_val <= 5: return round(val)
            if skip_conversion: return val # Skip conversion for non-JMCU
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
    def _normalize_name(name: str) -> str:
        if not name: return ""
        # Handle Uzbek characters variations (o', g', o, g)
        n = name.lower().strip()
        n = n.replace("‘", "'").replace("’", "'").replace("`", "'").replace("'", "")
        n = n.replace("o'", "o").replace("g'", "g").replace("h", "x") # Loose match x/h
        n = n.replace(" ", "").replace("-", "").replace(".", "")
        return n

    @staticmethod
    async def resolve_specialty_id(specialty_name: str, education_type: str = None, faculty_id: int = None, education_form: str = None) -> Optional[int]:
        """Find the best matching specialty ID, checking counts for duplicates."""
        if not HEMIS_ADMIN_TOKEN or not specialty_name: return None
        
        if not HEMIS_ADMIN_TOKEN or not specialty_name: return None
        
        # 1. Check persistent cache (memory only for now)
        # keys now include context
        cache_key = f"{specialty_name}:{education_type}:{faculty_id}:{education_form}"
        if not hasattr(HemisService, "_resolved_specialty_ids"):
             HemisService._resolved_specialty_ids = {}
        if cache_key in HemisService._resolved_specialty_ids:
             return HemisService._resolved_specialty_ids[cache_key]

        all_specs = await HemisService.get_specialty_list()
        req_norm = HemisService._normalize_name(specialty_name)
        
        # 2. Collect candidates
        candidates = []
        for s in all_specs:
            s_name = s.get("name", "")
            s_norm = HemisService._normalize_name(s_name)
            if req_norm == s_norm or req_norm in s_norm or s_norm in req_norm:
                candidates.append(s)
        
        if not candidates: return None

        # 3. Narrow by Education Type (60... Bakalavr, 70... Magistr)
        if education_type:
            is_bach = "Bakalavr" in education_type or str(education_type) == "11"
            is_mag = "Magistr" in education_type or str(education_type) == "12"
            type_prefix = "6" if is_bach else "7" if is_mag else None
            if type_prefix:
                typed = [c for c in candidates if str(c.get("code", "")).startswith(type_prefix)]
                if typed:
                    candidates = typed
        
        # 4. Narrow by Exact Normalized Name if multiple exist
        exact = [c for c in candidates if req_norm == HemisService._normalize_name(c.get("name", ""))]
        if exact:
            candidates = exact

        # 5. Narrow by Context (Specialized departments or Faculty)
        context_candidates = []
        
        # A. Sirtqi/Magistr Context (Specialized departments)
        is_sirtqi = education_form and ("Sirtqi" in education_form or str(education_form) == "13")
        is_mag = education_type and ("Magistr" in education_type or str(education_type) == "12")
        
        if is_sirtqi:
            sirtqi_matches = [c for c in candidates if c.get("department", {}).get("id") == 35]
            if sirtqi_matches:
                context_candidates = sirtqi_matches
        elif is_mag:
            mag_matches = [c for c in candidates if c.get("department", {}).get("id") == 16]
            if mag_matches:
                context_candidates = mag_matches
        
        # B. Faculty Context (Prioritize Selected Faculty)
        if not context_candidates and faculty_id:
            faculty_matches = [c for c in candidates if c.get("department", {}).get("id") == faculty_id]
            if faculty_matches:
                context_candidates = faculty_matches
                
        if context_candidates:
            candidates = context_candidates

        # 6. Resolve among remaining clones by checking real student counts
        resolved_id = None
        if len(candidates) > 1:
            try:
                client = await HemisService.get_client()
                tasks = []
                # Limit to first 5 candidates to avoid overwhelming
                for c in candidates[:5]:
                    sid = c.get("id")
                    url = f"{HemisService.BASE_URL}/data/student-list"
                    tasks.append(client.get(url, 
                        headers={"Authorization": f"Bearer {HEMIS_ADMIN_TOKEN}"},
                        params={"limit": 1, "_specialty": sid}
                    ))
                
                responses = await asyncio.gather(*tasks)
                max_count = -1
                for i, r in enumerate(responses):
                    if r.status_code == 200:
                        count = r.json().get("data", {}).get("pagination", {}).get("totalCount", 0)
                        if count > max_count:
                            max_count = count
                            resolved_id = candidates[i].get("id")
            except Exception as e:
                logger.error(f"Error resolving specialty count: {e}")
                # Fallback to highest ID if count check fails
                candidates.sort(key=lambda x: x.get("id"), reverse=True)
                resolved_id = candidates[0].get("id")
        elif candidates:
            resolved_id = candidates[0].get("id")

        if resolved_id:
            HemisService._resolved_specialty_ids[cache_key] = resolved_id
        return resolved_id

    # [NEW] Admin API Methods for accurate search
    @staticmethod
    async def get_group_list(
        faculty_id: int = None, 
        specialty_id: int = None, 
        education_type: str = None, 
        education_form: str = None,
        level_name: str = None,
        token: str = None
    ):
        """Fetch list of groups from Admin API with optional filtering"""
        """Fetch list of groups from Admin API with optional filtering"""
        auth_token = token or HEMIS_ADMIN_TOKEN
        if not auth_token: return []
        
        # Cache key based on filters
        cache_key = (faculty_id, specialty_id, education_type, education_form, level_name)
        if not hasattr(HemisService, "_cached_groups_map"):
            HemisService._cached_groups_map = {}
            
        if cache_key in HemisService._cached_groups_map:
            return HemisService._cached_groups_map[cache_key]
            
        # Normalization for Admin API
        norm_level = level_name
        if level_name and "-kurs" in level_name:
            norm_level = level_name.replace("-kurs", "")
            
        norm_type = education_type
        if education_type:
            if "Bakalavr" in education_type:
                norm_type = "11"
            elif "Magistr" in education_type:
                norm_type = "12"

        norm_form = education_form
        if education_form:
            if "Kunduzgi" in education_form:
                norm_form = "11"
            elif "Kechki" in education_form:
                norm_form = "12"
            elif "Sirtqi" in education_form:
                norm_form = "13"
            elif "Masofaviy" in education_form:
                norm_form = "16"

        # [FIX] Sirtqi Logic: If Sirtqi is selected, we must look into Dept 35 (Sirtqi bo'limi)
        # But we must filter by the original Faculty's specialties later (Smart Filter).
        # However, for the raw group list fetch, we just need to target Dept 35 if form is Sirtqi.
        target_dept = faculty_id
        if education_form and ("Sirtqi" in education_form or str(education_form) == "13"):
             target_dept = 35

        client = await HemisService.get_client()
        try:
            url = f"{HemisService.BASE_URL}/data/group-list"
            # Default limit 200 (server max seems to be 200)
            base_params = {
                "limit": 200,
                "_department": target_dept,
                "_specialty": specialty_id,
                "_education_type": norm_type,
                "_education_form": norm_form,
                "_level": norm_level
            }
            # Remove None values
            base_params = {k: v for k, v in base_params.items() if v is not None}
            
            all_items = []
            page = 1
            
            while True:
                base_params["page"] = page
                # Use standard client.get to handle pagination manually
                response = await client.get(url, headers={"Authorization": f"Bearer {auth_token}"}, params=base_params, timeout=20)
                
                if response.status_code == 200:
                    data_json = response.json()
                    data = data_json.get("data", {})
                    items = data.get("items", []) if isinstance(data, dict) else []
                    
                    if items:
                        all_items.extend(items)
                    
                    # Check pagination
                    pagination = data.get("pagination", {}) if isinstance(data, dict) else {}
                    page_count = pagination.get("pageCount", 1)
                    current_page = pagination.get("page", 1)
                    
                    if current_page >= page_count:
                        break
                    
                    page += 1
                else:
                    logger.warning(f"Group list fetch page {page} failed: {response.status_code}")
                    break
            
            HemisService._cached_groups_map[cache_key] = all_items
            # Also populate the legacy all-groups cache if no filters
            if not any([faculty_id, specialty_id, education_type, education_form, level_name]):
                HemisService._cached_groups = all_items
            return all_items

        except Exception as e:
            logger.error(f"Group list fetch failed: {e}")
            return []

    @staticmethod
    async def resolve_group_id(group_name: str, token: str = None, faculty_id: int = None) -> Optional[int]:
        """Find the matching group ID from the group list."""
        auth_token = token or HEMIS_ADMIN_TOKEN
        if not auth_token or not group_name: return None
        
        # Cache resolution
        if not hasattr(HemisService, "_resolved_group_ids"):
             HemisService._resolved_group_ids = {}
        if group_name in HemisService._resolved_group_ids:
             return HemisService._resolved_group_ids[group_name]
        
        # Pass faculty_id if provided
        all_groups = await HemisService.get_group_list(token=auth_token, faculty_id=faculty_id)
        req_norm = HemisService._normalize_name(group_name)
        
        # 1. Try exact or substantial substring match
        for g in all_groups:
            g_original = g.get("name", "")
            g_norm = HemisService._normalize_name(g_original)
            if req_norm == g_norm or req_norm in g_norm or g_norm in req_norm:
                gid = g.get("id")
                HemisService._resolved_group_ids[group_name] = gid
                return gid
        
        # 2. Try matching by group prefix code (e.g. "25-23")
        import re
        # Match standard pattern: 2 digits - 2 digits (e.g. 25-23)
        match = re.search(r'(\d{2}-\d{2})', group_name)
        if match:
            group_prefix = match.group(1)
            # Filter candidates by prefix first
            candidates = [g for g in all_groups if group_prefix in g.get("name", "")]
            
            # If we have candidates, try to match the rest of the name
            # Normalize and remove the prefix and common words
            def clean_name(n):
                n = HemisService._normalize_name(n)
                return n.replace(group_prefix.replace("-", ""), "").replace("kunduzgi", "").replace("kechki", "").replace("sirtqi", "")

            req_clean = clean_name(group_name)
            
            for g in candidates:
                g_name = g.get("name", "")
                g_clean = clean_name(g_name)
                
                # Loose match: if one contains the other
                if req_clean in g_clean or g_clean in req_clean:
                     gid = g.get("id")
                     HemisService._resolved_group_ids[group_name] = gid
                     return gid
            
            # Fallback: if only 1 candidate with that prefix, use it? 
            # Risk: 25-23 Gr1 vs 25-23 Gr2. Better to be safe.
            # But usually prefix + Specialty name is enough.
            
        # 3. Try matching by ignoring parenthesis content
        # "25-23 AXBOROT ... (KUNDUZGI)" -> "25-23 AXBOROT ..."
        base_name = re.sub(r'\(.*?\)', '', group_name).strip()
        if base_name != group_name:
             base_norm = HemisService._normalize_name(base_name)
             for g in all_groups:
                g_norm = HemisService._normalize_name(g.get("name", ""))
                if base_norm in g_norm:
                    gid = g.get("id")
                    HemisService._resolved_group_ids[group_name] = gid
                    return gid
                    
        return None

    @staticmethod
    async def get_specialty_list(faculty_id: int = None, education_type: str = None):
        """Fetch list of specialties from Admin API with optional faculty and type filters"""
        if not HEMIS_ADMIN_TOKEN: return []
        
        # Cache key based on faculty and type
        cache_key = (faculty_id, education_type)
        if not hasattr(HemisService, "_cached_specialties_map"):
            HemisService._cached_specialties_map = {}
            
        if cache_key in HemisService._cached_specialties_map:
            return HemisService._cached_specialties_map[cache_key]
            
        # Normalize type for local-filter-fallback if needed, 
        # but primarily we use it for potential API param if they start supporting it.
        norm_type = education_type
        if education_type:
            if "Bakalavr" in education_type:
                norm_type = "11"
            elif "Magistr" in education_type:
                norm_type = "12"

        client = await HemisService.get_client()
        try:
            url = f"{HemisService.BASE_URL}/data/specialty-list"
            params = {"limit": 300}
            if faculty_id:
                params["_department"] = faculty_id
            
            # Note: _education_type is often NOT supported for specialty-list in Admin API.
            # We will fetch by department then filter by code locally if type is provided.
            response = await HemisService.fetch_with_retry(
                client, "GET", url, 
                params=params,
                headers={"Authorization": f"Bearer {HEMIS_ADMIN_TOKEN}"}
            )
            if response.status_code == 200:
                data = response.json().get("data", {})
                items = data if isinstance(data, list) else data.get("items", [])
                
                # Local filtering by Education Type prefix (6... for Bakalavr, 7... for Magistr)
                # We use the raw education_type for string matching check or norm_type
                if education_type:
                    type_prefix = "6" if "11" == norm_type or "Bakalavr" in education_type else "7" if "12" == norm_type or "Magistr" in education_type else None
                    if type_prefix:
                        items = [s for s in items if str(s.get("code", "")).startswith(type_prefix)]
                
                HemisService._cached_specialties_map[cache_key] = items
                # Populate legacy cache if no filters
                if not faculty_id and not education_type:
                    HemisService._cached_specialties = items
                return items
        except Exception as e:
            logger.error(f"Error fetching specialty list: {e}")
        return []

    @staticmethod
    async def get_admin_student_list(filters: Dict[str, Any], page: int = 1, limit: int = 20):
        if not HEMIS_ADMIN_TOKEN: return [], 0
        
        client = await HemisService.get_client()
        try:
            url = f"{HemisService.BASE_URL}/data/student-list"
            params = {
                "limit": limit,
                "page": page,
                **filters
            }
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            response = await HemisService.fetch_with_retry(
                client, "GET", url, 
                headers={"Authorization": f"Bearer {HEMIS_ADMIN_TOKEN}"},
                params=params
            )
            
            if response.status_code == 200:
                data = response.json().get("data", {})
                items = data.get("items", [])
                total = data.get("pagination", {}).get("totalCount", 0)
                return items, total
            return [], 0
        except Exception as e:
            logger.error(f"Admin Student List Error: {e}")
            return [], 0

    @staticmethod
    async def get_student_resources(token: str, subject_id: str, semester_code: str = None, base_url: Optional[str] = None):
        client = await HemisService.get_client()
        final_base = base_url or HemisService.BASE_URL
        try:
            params = {"subject": subject_id}
            if semester_code: params["semester"] = semester_code
            
            response = await client.get(f"{final_base}/education/resources", headers=HemisService.get_headers(token), params=params)
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
    async def get_semester_teachers(token: str, semester_code: str = None, base_url: Optional[str] = None):
        client = await HemisService.get_client()
        final_base = base_url or HemisService.BASE_URL
        try:
            url = f"{final_base}/education/teachers"
            response = await client.get(url, headers=HemisService.get_headers(token))
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error fetching teachers: {e}") # Changed error message to reflect new functionality
            return None

    # --- Surveys (So'rovnomalar) ---
    
    @staticmethod
    async def get_student_surveys(token: str, base_url: Optional[str] = None):
        """GET /v1/student/survey"""
        client = await HemisService.get_client()
        final_base = base_url or HemisService.BASE_URL
        try:
            url = f"{final_base}/student/survey"
            response = await client.get(url, headers=HemisService.get_headers(token))
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error fetching surveys: {e}")
            return None

    @staticmethod
    async def start_student_survey(token: str, survey_id: int, base_url: Optional[str] = None):
        """POST /v1/student/survey-start"""
        client = await HemisService.get_client()
        final_base = base_url or HemisService.BASE_URL
        try:
            url = f"{final_base}/student/survey-start"
            payload = {"id": survey_id, "lang": "UZ"}
            response = await client.post(url, headers=HemisService.get_headers(token), json=payload)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error starting survey: {e}")
            return None

    @staticmethod
    async def submit_survey_answer(token: str, question_id: int, button_type: str, answer: Any, base_url: Optional[str] = None):
        """POST /v1/student/survey-answer"""
        client = await HemisService.get_client()
        final_base = base_url or HemisService.BASE_URL
        try:
            url = f"{final_base}/student/survey-answer"
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
    async def finish_student_survey(token: str, quiz_rule_id: int, base_url: Optional[str] = None):
        """POST /v1/student/survey-finish"""
        client = await HemisService.get_client()
        final_base = base_url or HemisService.BASE_URL
        try:
            url = f"{final_base}/student/survey-finish"
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
    async def prefetch_data(token: str, student_id: int, base_url: Optional[str] = None):
        """
        Eagerly loads critical data into cache to prevent 'First Load' delay.
        Should be called as a background task upon login.
        """
        logger.info(f"Prefetching data for student {student_id} (URL: {base_url})...")
        try:
            # 0. Warm Me Cache
            await HemisService.get_me(token, base_url=base_url)

            # 1. Semesters (Fast)
            semesters = await HemisService.get_semester_list(token, student_id=student_id, base_url=base_url)
            
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
                HemisService.get_student_subject_list(token, semester_code=sem_code, student_id=student_id, base_url=base_url),
                # Attendance
                HemisService.get_student_absence(token, semester_code=sem_code, student_id=student_id, base_url=base_url),
                # Schedule
                HemisService.get_student_schedule_cached(token, semester_code=sem_code, student_id=student_id, base_url=base_url)
            )
            logger.info(f"Prefetch complete for student {student_id}")
        except Exception as e:
            logger.error(f"Prefetch error: {e}")

    @staticmethod
    async def get_public_stats() -> Dict[str, Any]:
        """
        Fetches the full public statistics JSON.
        """
        client = await HemisService.get_client()
        url = f"{HemisService.BASE_URL}/public/stat-student"
        try:
            response = await client.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return data.get("data", {})
        except Exception as e:
            logger.warning(f"Public stats fetch failed: {e}")
        return {}

    @staticmethod
    async def get_public_student_total() -> int:
        """
        Fetches total student count from public statistics API.
        No token required.
        """
        stats = await HemisService.get_public_stats()
        if not stats:
            return 0
        try:
            # Aggregate from 'education_type' -> 'Jami'
            jami = stats.get("education_type", {}).get("Jami", {})
            total = jami.get("Erkak", 0) + jami.get("Ayol", 0)
            if total > 0:
                return total
        except Exception:
            pass
        return 0

    @staticmethod
    async def get_public_employee_count() -> int:
        """
        Fetches total employee count from public statistics API.
        No token required.
        """
        client = await HemisService.get_client()
        url = f"{HemisService.BASE_URL}/public/stat-employee"
        try:
            response = await client.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    stats = data.get("data", {})
                    # Aggregate from 'employment_form' (shows total unique contracts/people usually)
                    # "Asosiy ish joy", "O‘rindoshlik", etc.
                    # Or 'gender' -> 'Jami'? 
                    # Let's check 'gender' -> 'Jami' which is usually the simplest total.
                    # In sample: gender: { Erkak: 56, Ayol: 139, Jami: 195 }
                    
                    gender_stats = stats.get("gender", {})
                    if "Jami" in gender_stats:
                        return int(gender_stats["Jami"])
                    
                    # Fallback: Sum of employment forms if Jami is missing
                    emp_form = stats.get("employment_form", {})
                    return sum(emp_form.values()) if emp_form else 0
        except Exception as e:
            logger.warning(f"Public employee stats fetch failed: {e}")
        return 0


    @staticmethod
    async def get_admin_student_count(filters: Dict[str, Any], token: str = None) -> int:
        """
        Fetches total student count using HEMIS_ADMIN_TOKEN and /data/student-list.
        Allows filtering by any parameter (e.g., _department, _specialty, _group, _education_type).
        """
        auth_token = token or HEMIS_ADMIN_TOKEN
        if not auth_token:
            return 0
            
        client = await HemisService.get_client()
        url = f"{HemisService.BASE_URL}/data/student-list"
        
        # Prepare params
        params = {"limit": 1} # We only need the totalCount
        params.update(filters)
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        try:
            response = await client.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Check pagination or _meta
                if "data" in data:
                    inner = data["data"]
                    if "pagination" in inner:
                        return int(inner["pagination"].get("totalCount", 0))
                    elif "_meta" in inner:
                        return int(inner["_meta"].get("totalCount", 0))
        except Exception as e:
            logger.warning(f"Admin student count fetch failed: {e}")
        return 0

    @staticmethod
    async def get_total_students_for_groups(group_numbers: list[str], token: str) -> int:
        """
        Calculates total students in the given list of group names using the provided token.
        """
        counts = await HemisService.get_group_student_counts(group_numbers, token)
        return sum(counts.values())

    @staticmethod
    async def get_group_student_counts(group_numbers: list[str], token: str) -> dict[str, int]:
        """
        Returns a dictionary mapping group_number -> student_count.
        """
        if not token or not group_numbers:
            return {}
            
        counts = {}
        # We need to resolve each group name to an ID to query student count
        for group_name in group_numbers:
            # 1. Resolve Group ID
            group_id = await HemisService.resolve_group_id(group_name, token=token)
            if group_id:
                # 2. Get Count for this Group
                # Optimization: get_admin_student_count is cached? No, but lightweight.
                count = await HemisService.get_admin_student_count(
                    {"_group": group_id}, 
                    token=token
                )
                counts[group_name] = count
            else:
                counts[group_name] = 0
                
        return counts

    @staticmethod
    async def get_students_for_groups(group_numbers: list[str], token: str) -> tuple[list[dict], int]:
        """
        Fetches full student list for the given group names.
        Returns (list_of_students, total_count).
        """
        if not token or not group_numbers:
            return [], 0
            
        all_students = []
        true_total_count = 0
        
        try:
            client = await HemisService.get_client()
            tasks = []
            group_map = {} 
            
            # [FIX] Rate Limiting: Use Semaphore to prevent server blocking
            sem = asyncio.Semaphore(3) # Limit to 3 concurrent requests
            
            async def fetch_group(idx, g_name):
                async with sem:
                    # Resolve ID
                    g_id = await HemisService.resolve_group_id(g_name, token=token)
                    if not g_id:
                        logger.warning(f"Could not resolve group ID for: {g_name}")
                        return None
                    
                    # Fetch Data
                    url = f"{HemisService.BASE_URL}/data/student-list"
                    try:
                        resp = await client.get(
                             url, 
                             headers={"Authorization": f"Bearer {token}"},
                             params={"_group": g_id, "limit": 200},
                             timeout=15
                        )
                        # Small sleep to be nice to server
                        await asyncio.sleep(0.1)
                        return (idx, g_name, resp)
                    except Exception as e:
                        logger.error(f"Request failed for {g_name}: {e}")
                        return None

            # Create tasks
            for idx, group_name in enumerate(group_numbers):
                tasks.append(fetch_group(idx, group_name))
            
            if not tasks: return [], 0
            
            # Run with Semaphore
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for res in results:
                if not res or isinstance(res, Exception):
                    continue
                    
                idx, g_name, r = res
                
                if r.status_code == 200:
                    data = r.json()
                    items = data.get("data", {}).get("items", [])
                    all_students.extend(items)
                    
                    pagination = data.get("data", {}).get("pagination", {})
                    p_total = pagination.get("totalCount", 0)
                    if p_total > 0:
                        true_total_count += p_total
                    else:
                        true_total_count += len(items)
                        
                    logger.info(f"Fetched {len(items)} (Total: {p_total}) students for group {g_name}")
                else:
                    logger.warning(f"Group fetch failed for {g_name} with status {r.status_code}: {r.text}")
            
            final_count = max(true_total_count, len(all_students))
            return all_students, final_count
            
        except Exception as e:
            logger.error(f"Error fetching students for groups: {e}")
            return [], 0

    @staticmethod
    async def get_faculties(token: str = None) -> list:
        """
        Fetches list of faculties (structureType="Fakultet") from /data/department-list.
        Requires Admin Token or a user token with access.
        """
        auth_token = token or HEMIS_ADMIN_TOKEN
        if not auth_token:
            return []
            
        client = await HemisService.get_client()
        url = f"{HemisService.BASE_URL}/data/department-list"
        params = {"limit": 200}
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        try:
            response = await client.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", {}).get("items", [])
                
                faculties = []
                for item in items:
                    stype = item.get("structureType", {}).get("name")
                    if stype == "Fakultet":
                        faculties.append({
                            "id": item.get("id"),
                            "name": item.get("name"),
                            "code": item.get("code")
                        })
                return faculties
        except Exception as e:
            logger.warning(f"Faculties fetch failed: {e}")
        return []

    @staticmethod
    async def get_total_student_count(token: Optional[str] = None) -> int:
        """
        Fetches the total number of students.
        Attempts Public API first, then falls back to shift-based or list-based counts with token.
        """
        # Try Public API first (most accurate general stat)
        try:
            public_total = await HemisService.get_public_student_total()
            if public_total > 0:
                return public_total
        except Exception:
            pass

        if not token:
            return 0

        client = await HemisService.get_client()
        
        # Fallback 1: /data/student-count-by-shift
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        params = {
            "start_date": start_of_week.strftime("%Y-%m-%d"),
            "end_date": end_of_week.strftime("%Y-%m-%d")
        }

        url_shift = f"{HemisService.BASE_URL}/data/student-count-by-shift"
        try:
             response = await client.get(url_shift, headers=HemisService.get_headers(token), params=params)
             if response.status_code == 200:
                 data = response.json()
                 if "data" in data and isinstance(data["data"], dict):
                     total = data["data"].get("total")
                     if total is not None:
                         return int(total)
        except Exception:
             pass

        # Fallback 2: student-list counters
        endpoints = [
            f"{HemisService.BASE_URL}/education/student-list",
            f"{HemisService.BASE_URL}/data/student-list"
        ]
        
        for url in endpoints:
            try:
                response = await client.get(url, headers=HemisService.get_headers(token), params={"limit": 1, "page": 1})
                if response.status_code == 200:
                    data = response.json()
                    if "data" in data and isinstance(data["data"], dict):
                        meta = data["data"].get("_meta")
                        if meta and "totalCount" in meta:
                            return int(meta["totalCount"])
                        if "pagination" in data["data"]:
                             return int(data["data"]["pagination"].get("totalCount", 0))
            except Exception:
                pass
                
        return 0
