"""
AI сервис для GigaChat API (по официальной документации)
https://developers.sber.ru/docs/ru/gigachat/quickstart/ind-using-api
"""

import json
import asyncio
import aiohttp
import uuid
import time
from typing import List, Dict, Any, Optional
from config import GIGACHAT_AUTH_KEY, DEBUG, AI_TIMEOUT

class AIService:
    def __init__(self):
        self.access_token = None
        self.token_expires_at = 0
    
    async def analyze_food_text(self, text: str) -> Optional[List[Dict[str, Any]]]:
        """
        Основной метод: анализирует текст с едой через GigaChat API
        """
        if DEBUG:
            print(f"🤖 Анализируем: '{text}'")
        
        try:
            # Получаем токен
            token = await self._get_access_token()
            
            # Отправляем запрос к GigaChat
            dishes = await self._call_gigachat_api(token, text)
            
            if dishes and len(dishes) > 0:
                if DEBUG:
                    print(f"✅ Получено {len(dishes)} блюд")
                return dishes
            else:
                if DEBUG:
                    print("⚠️  Пустой ответ от AI, использую заглушку")
                return self._get_fallback_response(text)
                
        except Exception as e:
            print(f"❌ Ошибка AI: {e}")
            return self._get_fallback_response(text)
    
    async def _get_access_token(self) -> str:
        """
        Получаем access token по документации:
        POST https://ngw.devices.sberbank.ru:9443/api/v2/oauth
        Authorization: Basic {authorization_key}
        scope: GIGACHAT_API_PERS
        """
        # Если токен ещё действителен (30 минут - 5 минут запаса)
        if self.access_token and time.time() < self.token_expires_at - 300:
            return self.access_token
        
        if not GIGACHAT_AUTH_KEY:
            raise ValueError("GIGACHAT_AUTH_KEY не установлен в .env")
        
        # Создаем уникальный RqUID
        rquid = str(uuid.uuid4())
        
        # Заголовки как в документации
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': rquid,
            'Authorization': f'Basic {GIGACHAT_AUTH_KEY}'
        }
        
        # Данные формы
        data = {'scope': 'GIGACHAT_API_PERS'}
        
        if DEBUG:
            print(f"🔑 Запрашиваю токен...")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    'https://ngw.devices.sberbank.ru:9443/api/v2/oauth',
                    headers=headers,
                    data=data,
                    ssl=False,
                    timeout=AI_TIMEOUT
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ошибка получения токена: {response.status} - {error_text}")
                    
                    result = await response.json()
                    
                    # Сохраняем токен
                    self.access_token = result['access_token']
                    # expires_at в миллисекундах, переводим в секунды
                    self.token_expires_at = result.get('expires_at', 0) / 1000
                    
                    if DEBUG:
                        print(f"✅ Токен получен, действителен до: {time.ctime(self.token_expires_at)}")
                    
                    return self.access_token
                    
            except Exception as e:
                print(f"❌ Ошибка при получении токена: {e}")
                raise
    
    async def _call_gigachat_api(self, access_token: str, text: str) -> Optional[List[Dict[str, Any]]]:
        """
        Отправляем запрос к GigaChat API для анализа текста
        """
        # Загружаем промпт
        prompt = await self._load_prompt()
        
        # Формируем полный промпт
        full_prompt = f"{prompt}\n\nТекст пользователя: {text}"
        
        # Заголовки для API запроса
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Тело запроса как в документации
        payload = {
            "model": "GigaChat",
            "messages": [
                {
                    "role": "system",
                    "content": "Ты помощник для подсчёта КБЖУ. Всегда отвечай только в формате JSON."
                },
                {
                    "role": "user",
                    "content": full_prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 1000,
            "stream": False
        }
        
        if DEBUG:
            print(f"📤 Отправляю запрос к GigaChat API...")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    'https://gigachat.devices.sberbank.ru/api/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    ssl=False,
                    timeout=AI_TIMEOUT
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ошибка API: {response.status} - {error_text}")
                    
                    result = await response.json()
                    
                    if DEBUG:
                        print(f"📥 Ответ получен, парсим...")
                    
                    # Извлекаем текст ответа
                    response_text = result['choices'][0]['message']['content']
                    
                    # Парсим JSON
                    return self._parse_ai_response(response_text)
                    
            except Exception as e:
                print(f"❌ Ошибка при вызове GigaChat API: {e}")
                raise
    
    async def _load_prompt(self) -> str:
        """Загружаем промпт из файла"""
        try:
            with open('prompts/kbju_prompt.txt', 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Минимальный промпт по умолчанию
            return """Проанализируй текст с описанием еды и верни JSON со списком блюд и их КБЖУ.
Формат: {"dishes": [{"name": "название", "calories": число, "protein": число, "fat": число, "carbs": число}]}
Всегда отвечай только в этом формате."""
    
    def _parse_ai_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Парсим ответ AI в список блюд
        """
        try:
            # Очищаем ответ от возможного markdown
            import re
            
            # Убираем ```json и ```
            clean_text = re.sub(r'```json|```', '', response_text).strip()
            
            # Ищем JSON объект
            json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if not json_match:
                if DEBUG:
                    print(f"❌ JSON не найден в ответе: {response_text[:200]}")
                return []
            
            json_str = json_match.group()
            data = json.loads(json_str)
            
            dishes = data.get('dishes', [])
            
            # Валидируем и нормализуем данные
            valid_dishes = []
            for dish in dishes:
                if not isinstance(dish, dict):
                    continue
                
                name = dish.get('name', '').strip()
                if not name:
                    continue
                
                # Округляем значения
                calories = round(float(dish.get('calories', 300)))
                protein = round(float(dish.get('protein', 10)))
                fat = round(float(dish.get('fat', 10)))
                carbs = round(float(dish.get('carbs', 40)))
                
                # Ограничиваем разумные пределы
                calories = max(0, min(calories, 2000))
                protein = max(0, min(protein, 100))
                fat = max(0, min(fat, 100))
                carbs = max(0, min(carbs, 200))
                
                valid_dishes.append({
                    'name': name,
                    'calories': calories,
                    'protein': protein,
                    'fat': fat,
                    'carbs': carbs
                })
            
            if DEBUG:
                print(f"✅ Распарсено {len(valid_dishes)} блюд")
            
            return valid_dishes
            
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка декодирования JSON: {e}")
            print(f"Текст ответа: {response_text[:200]}...")
            return []
        except Exception as e:
            print(f"❌ Ошибка парсинга ответа: {e}")
            return []
    
    def _get_fallback_response(self, text: str) -> List[Dict[str, Any]]:
        """
        Запасной вариант на случай ошибки AI
        """
        if DEBUG:
            print(f"🔄 Использую запасной вариант для: {text}")
        
        # Простая логика разделения
        parts = []
        if ' и ' in text:
            parts = text.split(' и ')
        elif ', ' in text:
            parts = text.split(', ')
        else:
            parts = [text]
        
        dishes = []
        for part in parts:
            part = part.strip()
            if part:
                # Простые значения по умолчанию
                dishes.append({
                    'name': part,
                    'calories': 300,
                    'protein': 12,
                    'fat': 8,
                    'carbs': 40
                })
        
        return dishes