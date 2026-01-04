"""
Тестовый скрипт для проверки GigaChat API
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_gigachat():
    """Тестируем подключение к GigaChat API"""
    print("🧪 Тестируем GigaChat API...")
    
    # Проверяем наличие ключа
    from dotenv import load_dotenv
    load_dotenv()
    
    auth_key = os.getenv('GIGACHAT_AUTH_KEY')
    if not auth_key:
        print("❌ GIGACHAT_AUTH_KEY не найден в .env")
        print("   Получите ключ в кабинете GigaChat API")
        return
    
    print(f"✅ Ключ найден (первые 20 символов): {auth_key[:20]}...")
    
    # Тест получения токена
    import aiohttp
    import uuid
    
    rquid = str(uuid.uuid4())
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': rquid,
        'Authorization': f'Basic {auth_key}'
    }
    data = {'scope': 'GIGACHAT_API_PERS'}
    
    print("🔑 Пробуем получить токен...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://ngw.devices.sberbank.ru:9443/api/v2/oauth',
                headers=headers,
                data=data,
                ssl=False,
                timeout=30
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Токен получен успешно!")
                    print(f"   Access token: {result['access_token'][:50]}...")
                    print(f"   Expires at: {result['expires_at']}")
                    
                    # Тест запроса к API
                    print("\n🤖 Пробуем запрос к API...")
                    
                    api_headers = {
                        'Authorization': f'Bearer {result["access_token"]}',
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                    
                    payload = {
                        "model": "GigaChat",
                        "messages": [
                            {
                                "role": "user",
                                "content": "Привет! Как дела?"
                            }
                        ],
                        "temperature": 0.3,
                        "max_tokens": 100
                    }
                    
                    async with session.post(
                        'https://gigachat.devices.sberbank.ru/api/v1/chat/completions',
                        headers=api_headers,
                        json=payload,
                        ssl=False,
                        timeout=30
                    ) as api_response:
                        
                        if api_response.status == 200:
                            api_result = await api_response.json()
                            print(f"✅ API запрос успешен!")
                            print(f"   Ответ: {api_result['choices'][0]['message']['content'][:100]}...")
                        else:
                            error_text = await api_response.text()
                            print(f"❌ Ошибка API запроса: {api_response.status}")
                            print(f"   Ответ: {error_text}")
                            
                elif response.status == 401:
                    print("❌ Ошибка 401: Неавторизован")
                    print("   Проверьте правильность Authorization Key")
                    print("   Убедитесь, что ключ действителен и не истёк")
                else:
                    error_text = await response.text()
                    print(f"❌ Ошибка: {response.status}")
                    print(f"   Ответ: {error_text}")
                    
    except Exception as e:
        print(f"❌ Исключение: {e}")

if __name__ == "__main__":
    asyncio.run(test_gigachat())