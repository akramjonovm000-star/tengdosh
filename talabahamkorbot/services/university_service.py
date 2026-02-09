import json
import logging
import os
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class UniversityService:
    _data_cache: Optional[Dict] = None
    _code_map: Dict[str, Dict] = {} # prefix -> university_data
    
    DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uni_urls.json")

    @classmethod
    def _load_data(cls):
        if cls._data_cache is not None:
            return
            
        if not os.path.exists(cls.DATA_PATH):
            logger.error(f"University data file not found at {cls.DATA_PATH}")
            cls._data_cache = {"data": []}
            return

        try:
            with open(cls.DATA_PATH, "r", encoding="utf-8") as f:
                cls._data_cache = json.load(f)
                
            # Build fast lookup map
            for uni in cls._data_cache.get("data", []):
                code = uni.get("code")
                if code:
                    cls._code_map[str(code)] = uni
            
            logger.info(f"Loaded {len(cls._code_map)} universities from {cls.DATA_PATH}")
        except Exception as e:
            logger.error(f"Error loading university data: {e}")
            cls._data_cache = {"data": []}

    @classmethod
    def get_university_by_login(cls, login: str) -> Optional[Dict]:
        """
        Resolves university data based on the first 3 digits of the login.
        """
        cls._load_data()
        if not login or len(login) < 3:
            return None
            
        prefix = login[:3]
        return cls._code_map.get(prefix)

    @classmethod
    def get_api_url(cls, login: str) -> Optional[str]:
        """
        Returns the API URL for the university associated with the login prefix.
        Normalizes the URL by removing trailing slashes.
        """
        uni = cls.get_university_by_login(login)
        if uni:
            url = uni.get("api_url")
            if url and url.endswith("/"):
                url = url.rstrip("/")
            return url
        return None

    @classmethod
    def get_university_name(cls, login: str) -> Optional[str]:
        """
        Returns the university name associated with the login prefix.
        """
        uni = cls.get_university_by_login(login)
        if uni:
            return uni.get("name")
        return None
