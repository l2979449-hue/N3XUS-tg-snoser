import asyncio
import os
import random
from urllib.parse import urlparse
from pyrogram import Client
from pyrogram.raw import functions, types as raw_types

# ================= НАСТРОЙКИ =================
API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"

# Папка, где лежат твои Pyrogram-сессии (например, "sessions" или ".")
SESSIONS_DIR = "."

# ТВОИ МОБИЛЬНЫЕ SOCKS5 ПРОКСИ
MY_PROXIES = [
    "socks5://1r7jkt5u6u5:15n8bb9nofl@190.2.147.59:1080",
    "socks5://2417przaex3:2ahqfyg0elh@190.2.147.59:1080",
    "socks5://uw4omtgdm1:1kjadmf6q4b@190.2.147.59:1080",
    "socks5://akg176d23l:179lyn4n3yn@190.2.147.59:1080",
]

def get_random_proxy_cfg():
    """Парсит строку прокси и возвращает словарь для Pyrogram."""
    proxy_str = random.choice(MY_PROXIES)
    parsed = urlparse(proxy_str)
    return dict(
        scheme="socks5", 
        hostname=parsed.hostname, 
        port=parsed.port,
        username=parsed.username, 
        password=parsed.password
    )

# ================= ОСНОВНАЯ ЛОГИКА =================
async def report_single_session(session_name, target_bot):
    proxy_cfg = get_random_proxy_cfg()
    
    print(f"[{session_name}] 🚀 Заходим в @{target_bot} через {proxy_cfg['hostname']}...")
    
    app = Client(
        name=session_name, 
        api_id=API_ID,        # <--- Вставили твои ключи
        api_hash=API_HASH,    # <--- Вставили твои ключи
        workdir=SESSIONS_DIR, 
        no_updates=True,
        proxy=proxy_cfg       # <--- Используем SOCKS5
    )
    
    try:
        await app.start()
        await app.send_message(target_bot, "/start")
        await asyncio.sleep(3) # Ждем ответа от бота
        
        found_msg_id = None
        async for msg in app.get_chat_history(target_bot, limit=5):
            if msg.from_user and msg.from_user.is_bot:
                found_msg_id = msg.id
                break
                
        if not found_msg_id:
            print(f"[{session_name}] ❌ Бот не ответил.")
            return False
            
        # Жалуемся на сообщение (на меню с наркотиками)
        peer = await app.resolve_peer(target_bot)
        await app.invoke(
            functions.messages.Report(
                peer=peer, id=[found_msg_id],
                reason=raw_types.InputReportReasonIllegalDrugs(),
                message="Данный бот рекламирует и продает наркотики. Прошу проверить и заблокировать."
            )
        )
        print(f"[{session_name}] ✅ Жалоба на @{target_bot} отправлена!")
        return True
        
    except Exception as e:
        print(f"[{session_name}] ❌ Ошибка: {str(e)[:60]}")
        return False
    finally:
        try: 
            await app.stop()
        except: 
            pass

async def main():
    # Читаем список ботов из файла
    if not os.path.exists("targets.txt"):
        print("❌ Файл targets.txt не найден! Создай его и впиши ботов.")
        return
        
    with open("targets.txt", "r", encoding="utf-8") as f:
        targets = [t.strip().lstrip('@') for t in f.read().replace(',', '\n').split('\n') if t.strip()]

    # Ищем сессии Pyrogram
    sessions = [f.replace(".session", "") for f in os.listdir(SESSIONS_DIR) 
                if f.endswith(".session") and "_telethon" not in f]
    
    if not sessions: 
        print("❌ Нет Pyrogram сессий в папке!")
        return

    print(f"=====================================")
    print(f"📱 Сессий: {len(sessions)}. 🎯 Целей: {len(targets)}.")
    print(f"🌐 Прокси: {len(MY_PROXIES)} мобильных SOCKS5.")
    print(f"=====================================")
    
    for target in targets:
        print(f"\n=== Обработка @{target} ===")
        
        # Ставим ограничение в 3 потока, чтобы прокси не зависли
        sem = asyncio.Semaphore(3)
        
        async def guarded(sess):
            async with sem:
                await asyncio.sleep(random.uniform(1, 3))
                await report_single_session(sess, target)
                
        await asyncio.gather(*(guarded(s) for s in sessions))
        await asyncio.sleep(3) # Пауза перед следующим ботом

if __name__ == "__main__":
    asyncio.run(main())
