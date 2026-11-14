import asyncio
import os
import random
import requests
import threading
from pyrogram import Client
from pyrogram.raw import functions, types as raw_types
import config

SESSIONS_DIR = "sessions"
active_proxies = []
proxy_lock = threading.Lock()

def check_proxy(ip):
    # Пробуем подключиться к Telegram через прокси
    proxy_url = f"http://{ip}"
    try:
        res = requests.get("https://api.telegram.org", proxies={"http": proxy_url, "https": proxy_url}, timeout=3)
        if res.status_code in (200, 302, 404):
            return ip
    except:
        pass
    return None

async def proxy_scanner():
    api_url = "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=2000&country=all&ssl=yes"
    while True:
        try:
            res = await asyncio.to_thread(requests.get, api_url, timeout=5)
            if res.status_code == 200:
                ips = [line.strip() for line in res.text.splitlines() if line.strip()]
                random.shuffle(ips)
                for ip in ips:
                    with proxy_lock:
                        if len(active_proxies) >= 10: # Держим в пуле 10 штук
                            break
                    # Проверяем прокси в отдельном потоке, чтобы не блокировать
                    is_alive = await asyncio.to_thread(check_proxy, ip)
                    if is_alive:
                        with proxy_lock:
                            if ip not in active_proxies:
                                active_proxies.append(ip)
                                print(f"[+] Найден живой прокси: {ip}")
        except Exception as e:
            pass
        await asyncio.sleep(2)

async def report_single_session(session_path, target_bot, api_id, api_hash):
    session_name = os.path.basename(session_path).replace(".session", "")
    
    # Берем случайный прокси
    with proxy_lock:
        if not active_proxies:
            print(f"[{session_name}] ❌ Нет прокси, ждем...")
            return False
        proxy_ip = random.choice(active_proxies)
    
    print(f"[{session_name}] Подключаемся через {proxy_ip} к @{target_bot}...")
    
    # Парсим IP и порт
    host = proxy_ip.split(":")[0]
    port = int(proxy_ip.split(":")[1]) if ":" in proxy_ip else 80
    
    app = Client(
        name=session_name, 
        api_id=api_id, 
        api_hash=api_hash, 
        workdir=SESSIONS_DIR, 
        no_updates=True,
        proxy=dict(scheme="http", hostname=host, port=port)
    )
    
    try:
        await app.start()
        
        # 1. Отправляем /start
        await app.send_message(target_bot, "/start")
        await asyncio.sleep(3) # Ждем капчу
        
        # 2. Ищем сообщение
        found_msg_id = None
        async for msg in app.get_chat_history(target_bot, limit=5):
            if msg.from_user and msg.from_user.is_bot:
                found_msg_id = msg.id
                break
                
        if not found_msg_id:
            print(f"[{session_name}] ❌ Бот не прислал сообщение.")
            return False
            
        # 3. Жалуемся на наркотики
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
        print(f"[{session_name}] ❌ Ошибка через {proxy_ip}: {str(e)[:50]}...")
        # Если прокси сдох, удаляем его из пула
        with proxy_lock:
            if proxy_ip in active_proxies:
                active_proxies.remove(proxy_ip)
        return False
    finally:
        try:
            await app.stop()
        except:
            pass

async def main():
    bots_input = os.environ.get("BOTS_LIST", "")
    if not bots_input:
        print("❌ Список ботов пуст.")
        return
        
    targets = [b.strip().lstrip('@') for b in bots_input.split(',') if b.strip()]
    
    raw_api = random.choice(config.apis)
    api_id, api_hash = raw_api.split(" ")
    api_id = int(api_id)
    
    sessions = [os.path.join(SESSIONS_DIR, f) for f in os.listdir(SESSIONS_DIR) if f.endswith(".session")]
    if not sessions:
        print("❌ Нет сессий в папке sessions!")
        return

    print("⏳ Запускаем поиск бесплатных прокси...")
    for _ in range(5):
        asyncio.create_task(proxy_scanner())

    # Ждем, пока наберется хотя бы 3 прокси
    while len(active_proxies) < 3:
        print(f"   [~] Ждем прокси: {len(active_proxies)}/3...")
        await asyncio.sleep(3)
        
    print(f"✅ Найдено {len(active_proxies)} прокси. Начинаем...")

    for target in targets:
        print(f"\n=== Обработка @{target} ===")
        # Запускаем по 2 сессии одновременно (чтобы не спалить все сразу)
        sem = asyncio.Semaphore(2) 
        
        async def guarded(sess):
            async with sem:
                await asyncio.sleep(random.uniform(2, 5))
                await report_single_session(sess, target, api_id, api_hash)
                
        await asyncio.gather(*(guarded(s) for s in sessions))
        await asyncio.sleep(5) # Пауза перед следующим ботом

if __name__ == "__main__":
    asyncio.run(main())
