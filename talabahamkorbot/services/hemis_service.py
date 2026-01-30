import httpx
import logging
from typing import Dict, Any
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

    @classmethod
    async def get_client(cls):
        if cls._client is None or cls._client.is_closed:
            # Optimized restrictions for faster connection setup
            limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
            timeout = httpx.Timeout(20.0, connect=10.0)
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
            response = await client.get(url, headers=HemisService.get_headers(token), params=params)
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
            response = await client.post(
                url,
                json=json_payload
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
        return HemisService.generate_auth_url(state)

    @staticmethod
    async def exchange_code(code: str):
        # OAuth usually requires fresh client context or we can use shared
        # Keeping shared is fine
        client = await HemisService.get_client()
        from config import HEMIS_CLIENT_ID, HEMIS_CLIENT_SECRET, HEMIS_REDIRECT_URL, HEMIS_TOKEN_URL
        try:
            data = {
                "client_id": HEMIS_CLIENT_ID,
                "client_secret": HEMIS_CLIENT_SECRET,
                "redirect_uri": HEMIS_REDIRECT_URL,
                "grant_type": "authorization_code",
                "code": code
            }
            response = await client.post(HEMIS_TOKEN_URL, data=data)
            if response.status_code == 200:
                return response.json(), None
            return None, f"Token exchange failed: {response.status_code}"
        except Exception as e:
            return None, str(e)

    @staticmethod
    async def exchange_code_for_token(code: str):
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
                "login": "test_tutor",
                "firstname": "Test",
                "lastname": "Tyutor",
                "roles": [{"code": "tutor", "name": "Tyutor"}]
            }
        # ------------------------

        client = await HemisService.get_client()
        try:
            # 1. Try REST API Endpoint
            url = f"{HemisService.BASE_URL}/account/me"
            response = await client.get(url, headers=HemisService.get_headers(token))
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    return data["data"]
                return data
            
            if response.status_code in [401, 403]:
                return None

            # 2. Fallback to OAuth Endpoint
            url_oauth = f"{HEMIS_PROFILE_URL}?fields=id,uuid,type,login,firstname,surname,patronymic,picture,email,phone,birth_date"
            response = await client.get(url_oauth, headers=HemisService.get_headers(token))
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
        # DISABLED StudentCache: Force live data
        # if student_id and not force_refresh:
        #     try:
        #         async with AsyncSessionLocal() as session:
        #             cache = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
        #             if cache: 
        #                 age = (datetime.utcnow() - cache.updated_at).total_seconds()
        #                 if age < 4 * 3600:
        #                     t, e, u = calculate_totals(cache.data)
        #                     return t, e, u, cache.data
        #                 stale_data = cache.data
        #     except: pass

        client = await HemisService.get_client()
        try:
            params = {"semester": semester_code} if semester_code else {}
            response = await client.get(
                f"{HemisService.BASE_URL}/education/attendance",
                headers=HemisService.get_headers(token), params=params
            )
            
            if response.status_code == 200:
                data = response.json().get("data", [])
                
                # DISABLED StudentCache: No update
                # if student_id:
                #      async with AsyncSessionLocal() as session:
                #          c = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                #          if c: 
                #              c.data = data
                #              c.updated_at = datetime.utcnow()
                #          else:
                #              session.add(StudentCache(student_id=student_id, key=key, data=data))
                #          await session.commit()
                         
                t, e, u = calculate_totals(data)
                return t, e, u, data
            
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
    async def get_semester_list(token: str, force_refresh: bool = False):
        client = await HemisService.get_client()
        try:
            url = f"{HemisService.BASE_URL}/education/semesters"
            response = await client.get(url, headers=HemisService.get_headers(token))
            
            if response.status_code == 200:
                data = response.json().get("data", [])
                def get_code(x):
                    try: return int(str(x.get("code") or x.get("id")))
                    except: return 0
                data.sort(key=get_code, reverse=True)
                return data
            return []
        except Exception as e:
            return []

    @staticmethod
    async def get_student_subject_list(token: str, semester_code: str = None, student_id: int = None, force_refresh: bool = False):
        key = f"subjects_{semester_code}" if semester_code else "subjects_all"
        # DISABLED StudentCache
        # if student_id and not force_refresh:
        #     try:
        #         async with AsyncSessionLocal() as session:
        #             cache = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
        #             if cache and (datetime.utcnow() - cache.updated_at).total_seconds() < 1800:
        #                 return cache.data
        #     except: pass

        client = await HemisService.get_client()
        try:
            params = {"semester": semester_code} if semester_code else {}
            response = await client.get(
                f"{HemisService.BASE_URL}/education/subject-list",
                headers=HemisService.get_headers(token), params=params
            )
            if response.status_code == 200:
                data = response.json().get("data", [])
                # DISABLED StudentCache
                # if student_id:
                #      async with AsyncSessionLocal() as session:
                #          c = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                #          if c: 
                #              c.data = data
                #              c.updated_at = datetime.utcnow()
                #          else:
                #              session.add(StudentCache(student_id=student_id, key=key, data=data))
                #          await session.commit()
                return data
            return []
        except: return []

    @staticmethod
    async def get_student_schedule_cached(token: str, semester_code: str = None, student_id: int = None, force_refresh: bool = False):
        key = f"schedule_{semester_code}" if semester_code else "schedule_all"
        # DISABLED StudentCache
        # if student_id and not force_refresh:
        #     try:
        #         async with AsyncSessionLocal() as session:
        #             cache = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
        #             if cache and (datetime.utcnow() - cache.updated_at).total_seconds() < 1800:
        #                     return cache.data
        #     except: pass

        client = await HemisService.get_client()
        try:
            params = {"semester": semester_code} if semester_code else {}
            response = await client.get(
                f"{HemisService.BASE_URL}/education/schedule",
                headers=HemisService.get_headers(token), params=params
            )
            if response.status_code == 200:
                data = response.json().get("data", [])
                # DISABLED StudentCache
                # if student_id:
                #      async with AsyncSessionLocal() as session:
                #          c = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                #          if c: 
                #              c.data = data
                #              c.updated_at = datetime.utcnow()
                #          else:
                #              session.add(StudentCache(student_id=student_id, key=key, data=data))
                #          await session.commit()
                return data
            return []
        except: return []

    @staticmethod
    async def get_curriculum_topics(token: str, subject_id: str = None, semester_code: str = None, training_type_code: str = None, student_id: int = None):
        key = f"curriculum_topics_{subject_id}_{semester_code}_{training_type_code}"
        if student_id:
            try:
                async with AsyncSessionLocal() as session:
                    cache = await session.scalar(select(StudentCache).where(StudentCache.student_id == student_id, StudentCache.key == key))
                    if cache and (datetime.utcnow() - cache.updated_at).total_seconds() < 24 * 3600:
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
    async def get_student_performance(token: str, semester_code: str = None):
        try:
            subjects = await HemisService.get_student_subject_list(token, semester_code)
            if not subjects: return 0.0
            from services.gpa_calculator import GPACalculator
            result = GPACalculator.calculate_gpa(subjects)
            return result.gpa
        except: return 0.0

    @staticmethod
    def parse_grades_detailed(subject_data: dict) -> list:
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
            
            # 11/15: JN, 12: ON, 13: YN
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
