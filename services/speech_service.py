"""
Сервис для работы с SaluteSpeech API (распознавание речи).
Документация: https://developers.sber.ru/docs/ru/salutespeech/api/main
"""

import os
import asyncio
import aiohttp
import uuid
import time
from typing import Optional
from config import SALUTEspeech_API_KEY, DEBUG, AI_TIMEOUT


class SpeechService:
    """Сервис для распознавания речи через SaluteSpeech API"""
    
    def __init__(self):
        self.access_token = None
        self.token_expires_at = 0
    
    async def recognize_speech(self, audio_file_path: str) -> Optional[str]:
        """
        Распознает речь из аудиофайла.
        
        Args:
            audio_file_path: Путь к аудиофайлу
            
        Returns:
            Распознанный текст или None в случае ошибки
        """
        print(f"🎤 Начинаю распознавание речи из файла: {audio_file_path}")
        import sys
        sys.stdout.flush()
        
        try:
            # Получаем токен доступа
            token = await self._get_access_token()
            
            # Отправляем запрос на распознавание
            text = await self._call_recognition_api(token, audio_file_path)
            
            if text:
                print(f"✅ Распознан текст: '{text}'")
                sys.stdout.flush()
                return text
            else:
                print("⚠️  Пустой ответ от API распознавания")
                sys.stdout.flush()
                return None
                
        except Exception as e:
            print(f"❌ Ошибка распознавания речи: {e}")
            import traceback
            print(f"📋 Трассировка:\n{traceback.format_exc()}")
            sys.stdout.flush()
            return None
    
    async def _get_access_token(self) -> str:
        """
        Получаем access token для SaluteSpeech API.
        POST https://ngw.devices.sberbank.ru:9443/api/v2/oauth
        Authorization: Basic {authorization_key}
        scope: SALUTE_SPEECH_PERS
        """
        # Если токен ещё действителен (30 минут - 5 минут запаса)
        if self.access_token and time.time() < self.token_expires_at - 300:
            return self.access_token
        
        if not SALUTEspeech_API_KEY:
            raise ValueError("SALUTEspeech_API_KEY не установлен в .env")
        
        # Создаем уникальный RqUID
        rquid = str(uuid.uuid4())
        
        # Заголовки как в документации
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': rquid,
            'Authorization': f'Basic {SALUTEspeech_API_KEY}'
        }
        
        # Данные формы - правильный scope для SaluteSpeech
        data = {'scope': 'SALUTE_SPEECH_PERS'}
        
        print(f"🔑 Запрашиваю токен SaluteSpeech...")
        print(f"📋 Scope: SALUTE_SPEECH_PERS")
        import sys
        sys.stdout.flush()
        
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
                    
                    print(f"✅ Токен SaluteSpeech получен, действителен до: {time.ctime(self.token_expires_at)}")
                    import sys
                    sys.stdout.flush()
                    return self.access_token
                    
            except Exception as e:
                print(f"❌ Ошибка при получении токена SaluteSpeech: {e}")
                import sys
                sys.stdout.flush()
                raise
    
    async def _call_recognition_api(self, access_token: str, audio_file_path: str) -> Optional[str]:
        """
        Отправляет аудиофайл на распознавание речи.
        POST https://smartspeech.sber.ru/rest/v1/speech:recognize
        
        Согласно документации SaluteSpeech API, поддерживаются форматы:
        - OGG Opus (Telegram использует этот формат)
        - WAV
        - MP3
        """
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Аудиофайл не найден: {audio_file_path}")
        
        # Получаем размер файла
        file_size = os.path.getsize(audio_file_path)
        print(f"📊 Размер аудиофайла: {file_size} байт ({file_size / 1024:.2f} КБ)")
        
        # Читаем аудиофайл
        with open(audio_file_path, 'rb') as audio_file:
            audio_data = audio_file.read()
        
        # Определяем формат файла по расширению
        file_ext = os.path.splitext(audio_file_path)[1].lower()
        if file_ext == '.ogg':
            format_param = 'opus'
        elif file_ext == '.wav':
            format_param = 'wav'
        elif file_ext == '.mp3':
            format_param = 'mp3'
        else:
            # По умолчанию считаем OGG Opus (формат Telegram)
            format_param = 'opus'
        
        # Заголовки для API запроса
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        
        # Параметры запроса
        params = {
            'format': format_param,
            'lang': 'ru-RU',
        }
        
        # Используем raw body с правильным Content-Type (более надежный вариант для SaluteSpeech)
        file_ext = os.path.splitext(audio_file_path)[1].lower()
        if file_ext == '.ogg':
            content_type = 'audio/ogg;codecs=opus'
        elif file_ext == '.wav':
            content_type = 'audio/wav'
        elif file_ext == '.mp3':
            content_type = 'audio/mpeg'
        else:
            content_type = 'audio/ogg;codecs=opus'
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': content_type,
        }
        
        print(f"📤 Отправляю аудио на распознавание (размер: {len(audio_data)} байт, формат: {format_param})...")
        print(f"🔗 URL: https://smartspeech.sber.ru/rest/v1/speech:recognize")
        print(f"📋 Параметры: {params}")
        print(f"📋 Content-Type: {content_type}")
        import sys
        sys.stdout.flush()
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    'https://smartspeech.sber.ru/rest/v1/speech:recognize',
                    headers=headers,
                    params=params,
                    data=audio_data,
                    ssl=False,
                    timeout=AI_TIMEOUT * 2  # Распознавание может занять больше времени
                ) as response:
                    
                    response_text = await response.text()
                    print(f"📥 Статус ответа: {response.status}")
                    print(f"📋 Тело ответа (первые 500 символов): {response_text[:500]}")
                    
                    if response.status != 200:
                        print(f"❌ Ошибка API распознавания: {response.status}")
                        print(f"📋 Полный ответ: {response_text}")
                        raise Exception(f"Ошибка API распознавания: {response.status} - {response_text}")
                    
                    try:
                        result = await response.json()
                    except Exception as json_error:
                        print(f"❌ Ошибка парсинга JSON: {json_error}")
                        print(f"📋 Ответ был: {response_text}")
                        raise
                    
                    print(f"📥 Ответ получен, извлекаю текст...")
                    print(f"📋 Полный ответ API: {result}")
                    
                    # Извлекаем распознанный текст
                    # Формат ответа может быть разным, проверяем несколько вариантов
                    if 'result' in result:
                        if isinstance(result['result'], str):
                            print(f"✅ Найден текст в result (str): '{result['result']}'")
                            return result['result']
                        elif isinstance(result['result'], list) and len(result['result']) > 0:
                            # Если результат - массив, берем первый элемент
                            first_result = result['result'][0]
                            if isinstance(first_result, dict) and 'alternatives' in first_result:
                                alternatives = first_result['alternatives']
                                if len(alternatives) > 0:
                                    text = alternatives[0].get('text', '')
                                    print(f"✅ Найден текст в result[0].alternatives[0].text: '{text}'")
                                    return text
                            elif isinstance(first_result, str):
                                print(f"✅ Найден текст в result[0] (str): '{first_result}'")
                                return first_result
                        elif isinstance(result['result'], dict):
                            # Если результат - объект с полем text
                            if 'text' in result['result']:
                                text = result['result']['text']
                                print(f"✅ Найден текст в result.text: '{text}'")
                                return text
                            elif 'alternatives' in result['result']:
                                alternatives = result['result']['alternatives']
                                if len(alternatives) > 0:
                                    text = alternatives[0].get('text', '')
                                    print(f"✅ Найден текст в result.alternatives[0].text: '{text}'")
                                    return text
                    
                    # Альтернативный формат ответа
                    if 'text' in result:
                        text = result['text']
                        print(f"✅ Найден текст в text: '{text}'")
                        return text
                    
                    # Еще один вариант - может быть массив результатов напрямую
                    if isinstance(result, list) and len(result) > 0:
                        first_item = result[0]
                        if isinstance(first_item, dict) and 'text' in first_item:
                            text = first_item['text']
                            print(f"✅ Найден текст в [0].text: '{text}'")
                            return text
                        elif isinstance(first_item, str):
                            print(f"✅ Найден текст в [0] (str): '{first_item}'")
                            return first_item
                    
                    print(f"⚠️  Неожиданный формат ответа: {result}")
                    print(f"⚠️  Тип результата: {type(result)}")
                    if isinstance(result, dict):
                        print(f"⚠️  Ключи в результате: {list(result.keys())}")
                    import sys
                    sys.stdout.flush()
                    return None
                    
            except Exception as e:
                print(f"❌ Ошибка при вызове API распознавания: {e}")
                import traceback
                print(f"📋 Трассировка ошибки:\n{traceback.format_exc()}")
                import sys
                sys.stdout.flush()
                raise
    
