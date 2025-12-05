import requests
from bs4 import BeautifulSoup
import logging
import time
import random

logger = logging.getLogger(__name__)

def parse_category(url):
    """Парсинг категорий с Kaspi"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        logger.info(f"Парсинг категории: {url}")
        
        response = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, "lxml")
        categories = []
        
        for a in soup.select("a[href]"):
            link = a.get("href")
            if "/shop/c/" in link:
                categories.append(link)
        
        time.sleep(1)
        
        unique_categories = list(set(categories))
        logger.info(f"Найдено {len(unique_categories)} уникальных категорий")
        
        return unique_categories
        
    except Exception as e:
        logger.error(f"Ошибка парсинга {url}: {e}")
        return []