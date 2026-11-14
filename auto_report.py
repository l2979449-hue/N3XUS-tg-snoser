import asyncio
import os
import random
import requests
import threading
from pyrogram import Client
from pyrogram.raw import functions, types as raw_types

SESSIONS_DIR = os.path.abspath("sessions")
active_proxies = []
proxy_lock = threading.Lock()

def check_proxy(ip):
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
                        if len(active_proxies) >= 10:
                            break
                    is_alive = await asyncio.to_thread(check_proxy, ip)
                    if is_alive:
                        with proxy_lock:
                            if ip not in active_proxies:
                                active_proxies.append(ip)
                                print(f"[+] Найден прокси: {ip}")
        except Exception:
            pass
        await asyncio.sleep(2)

async def report_single_session(session_path, target_bot):
    session_name = os.path.basename(session_path).replace(".session", "")
    
    with proxy_lock:
        if not active_proxies:
            print(f"[{session_name}] ❌ Нет прокси.")
            return False
        proxy_ip = random.choice(active_proxies)
    
    print(f"[{session_name}] Через {proxy_ip} заходим в @{target_bot}...")
    
    host = proxy_ip.split(":")[0]
    port = int(proxy_ip.split(":")[1]) if ":" in proxy_ip else 80
    
    try:
        # ВОТ ГЛАВНЫЙ ФИКС: Мы не указываем api_id и api_hash!
        # Pyrogram сам достанет их из файла .session
        app = Client(
            name=session_name, 
            workdir=SESSIONS_DIR, 
            no_updates=True,
            proxy=dict(scheme="http", hostname=host, port=port)
        )
        
        await app.start()
        await app.send_message(target_bot, "/start")
        await asyncio.sleep(3)
        
        found_msg_id = None
        async for msg in app.get_chat_history(target_bot, limit=5):
            if msg.from_user and msg.from_user.is_bot:
                found_msg_id = msg.id
                break
                
        if not found_msg_id:
            print(f"[{session_name}] ❌ Бот не ответил.")
            return False
            
        peer = await app.resolve_peer(target_bot)
        await app.invoke(
            functions.messages.Report(
                peer=peer, id=[found_msg_id],
                reason=raw_types.InputReportReasonIllegalDrugs(),
                message="Данный бот рекламирует и продает наркотики. Прошу проверить и заблокировать."
            )
        )
        print(f"[{session_name}] ✅ Жалоба отправлена!")
        return True
        
    except Exception as e:
        print(f"[{session_name}] ❌ Ошибка: {str(e)[:50]}")
        with proxy_lock:
            if proxy_ip in active_proxies:
                active_proxies.remove(proxy_ip)
        return False
    finally:
        try: await app.stop()
        except: pass

async def main():
    bots_input = os.environ.get("BOTS_LIST", "")
    if not bots_input: return
        
    targets = [b.strip().lstrip('@') for b in bots_input.split(',') if b.strip()]
    
    sessions = [os.path.join(SESSIONS_DIR, f) for f in os.listdir(SESSIONS_DIR) if f.endswith(".session")]
    if not sessions: 
        print("Нет сессий!")
        return

    print("⏳ Ищем прокси...")
    for _ in range(5):
        asyncio.create_task(proxy_scanner())

    while len(active_proxies) < 3:
        print(f"   Ждем: {len(active_proxies)}/3")
        await asyncio.sleep(3)
        
    print(f"✅ Прокси готовы ({len(active_proxies)}). Начинаем...")

    for target in targets:
        print(f"\n=== Обработка @{target} ===")
        # Ограничиваем до 2 сессий одновременно
        sem = asyncio.Semaphore(2)
        
        async def guarded(sess):
            async with sem:
                await asyncio.sleep(random.uniform(2, 5))
                await report_single_session(sess, target)
                
        await asyncio.gather(*(guarded(s) for s in sessions))
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
