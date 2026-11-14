import requests
import random
import string
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from colorama import Fore, Style, init

init()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def generate_random_phone():
    return f"+79{ ''.join( random.choice( '0123456789' ) for _ in range ( 9 ) ) }"

def generate_random_email():
    domains = [ "gmail.com", "mail.ru", "rambler.ru", "ya.ru" ]
    name_length = random.randint( 5, 20 )
    letters = "abcdefghijklmnopqrstuvwxyz1234567890"
    email_name = ''.join( random.choice( letters ) for _ in range (name_length ) )
    return f"{ email_name }@{random.choice( domains ) }"

complaint_types = {
    "Наркотики": [
        "Данный бот распространяет и продаёт наркотические вещества. В описании и сообщениях бота есть прямые предложения о покупке, цены и контакты. Также бот вербует работников: предлагает распространение и сбыт за деньги. Прошу проверить и заблокировать бота. ID: {user_id}",
        "Жалоба на продажу наркотиков. Пользователь {user} с ID: {user_id} занимается незаконным оборотом запрещенных веществ и вербует людей. Прошу заблокировать.",
        "Обнаружен канал по продаже наркотиков. ID: {user_id}. В сообщениях указаны цены и предложения о работе курьером. Прошу заблокировать.",
        "This bot distributes and sells illegal drugs. ID: {user_id}. Please block it immediately."
    ],
    "Спам": [
        "Пользователь {user} ID: {user_id} использует чат для рассылки рекламы и спама, что нарушает правила сообщества. Прошу удалить его сессию и заблокировать возможность отправки нежелательных сообщений.",
        "Здравствуйте, хочу пожаловаться на {user} ID: {user_id}, он использует спам для продвижения своего канала из-за чего невозможно общаться в группе, прошу принять меры по удалению аккаунта. Спасибо",
        "Доброго времени суток, прошу принять меры по рассылке спама. ID: {user_id} пользователя.",
        "Жалоба на рассылку рекламы. Пользователь {user} с ID: {user_id} спамит по группам, прошу принять меры",
        "Hello, I want to complain about ID: {user_id}, he uses spam to promote his channel, which makes it impossible to communicate in the group, please take steps to delete the account. Thank you",
        "Good day, I ask you to take measures to send spam. ID: {user_id} of the user.",
        "Complaint about sending advertisements. User with ID: {user_id} is spamming groups, please take action"
    ],
    "Порнография": [
        "Добрый день, прошу заблокировать доступ к порнографическому контенту. Акаунту {user} с  ID: {user_id}. Проблема в том что он занимается продажей детской порнографией",
        "Здравствуйте, хочу подать жалобу на порнографию.  Пользиватель {user} с  ID: {user_id} продает детскую порнографию, прошу принять меры по удалению акаунта. Спасибо",
        "Данный пользиватель {user} с ID: {user_id} растространяет запрешеный детский контент (дп,цп) прошу вас удалить данный акаунт. Спасибо",
        "Пользователь {user_id} распространяет порнографические материалы. Прошу заблокировать его аккаунт за нарушение правил платформы. Ссылка на материалы: {id}",
        "Good afternoon, please block access to pornographic content. Account with ID: {user_id}. The problem is that it sells child pornography"
    ],
    "Фишинг": [
        "Здравствуйте, сообщаю о подозрительной попытке фишинга. Акк: {user} ID: {user_id}.",
        "Добрый день, прошу обратить внимание на пользивателя {user} с ID: {user_id} он создает фишинг сылки, прошу принять меры по удалению данного акаунта",
        "Жалоба на фишинг. Пожалуйста, примите меры. {user} с ID: {user_id} использует фишинг для получения личных данных других пользывателей, прошу принять меры по удалению акаунта. Спасибо"
    ],
    "Дианон": [
        "Здравствуйте уважаемая поддержка телеграмм,хочу пожаловаться на пользователя {user} с ID:{user_id} дело в том что он нарушает правила телеграмм, он продает услули деанона, занимается терроризмом , а еще хочу сообщить что он оскорбляет чужие личности! ",
        "Здравствуйте уважаемая поддержка. Пользователь {user} вашей платформы Telegram с ID: {user_id}, угрожает дean0минuзациеё и свaтuнг0м. Требую удалить его аккаунт для безопасности других пользователей."
    ],
    "Мошенничество": [
        "Уважаемая служба поддержки!Хочу сообщить о случае мошенничества. Пользователь {user} с ID: {user_id} пишет людям и предлагает услугу по выводу Notcoin на карту. После перевода Notcoin пользователь добавляет в черный список и отказывается переводить Notcoin. Прошу принять меры по удалению аккаунта. Спасибо!",
        "Добрый день!Прошу рассмотреть жалобу на мошенничество. Пользователь {user} с ID: {user_id} занимается мошенничеством, прошу принять меры по блокировке аккаунта."
    ],
    "Домогательство": [
        "I ask you to delete user ID: {user_id}, he writes to my friends and asks them to send their intimate photos, please take action",
        "I ask you to delete user ID: {user_id}, he writes to my friend who is 15 years old and asks for intimate photos, I ask you to take punitive measures.  Thank you"
    ],
    "Канал": [
        "Hello, Telegram support! I want to file a complaint against the Telegram channel link: {id}, this channel distributes methods of doxing, hacking, and swatting. Please remove this channel. Thank you.",
        "Good afternoon, I want to complain about the telegram channel link: {id}, this channel publishes personal information of users, please take measures to delete the channel. Thanks."
    ],
    "Группа": [
        "Hello, Telegram Support, I want to file a complaint against the group with ID: {id} for the reason: distribution of prohibited content. Please take action to block the group!",
        "Good day, I ask you to take action on my complaint. Group ID: {id} is used to distribute illegal materials, please block the group. Thanks!"
    ],
    "Сессия": [
        "Здраствуйте,меня взломали и выкинули с аккаунта {user}. Теперь Я не могу зайти на аккаунт так как мгновенно выкидывают меня с аккаунта. Прошу помогите, удалите аккаунт или обнулите сессии, там было очень много важной информации. Вот мой ID: {user_id}",
        "Здраствуйте, я попался на фишинг ссылку и меня как то взломали, на моем аккаунте {user} было очень много важных вещей, поэтому прошу вас обнулите пожалуйста сессию или же удалите аккаунт.Вот мой айди: {user_id}"
    ]
}       

def get_user_input():
    clear_screen()
    user_id = input(Fore.CYAN + "   Введите ID (если нет, оставьте пустым): " + Style.RESET_ALL)
    
    print(Fore.CYAN + "\n   Введите @username'ы (через запятую или с новой строки):" + Style.RESET_ALL)
    user_input = input("   > ")
    # Разбиваем по запятым и пробелам, очищаем от пустых строк
    users = [u.strip().lstrip('@') for u in user_input.replace('\n', ',').split(',') if u.strip()]
    
    id_link = input(Fore.CYAN + "\n   Введите ссылку на нарушение (если есть, иначе Enter): " + Style.RESET_ALL)
    total_per_user = int(input(Fore.CYAN + "   Сколько жалоб отправить НА КАЖДОГО? (например, 10): " + Style.RESET_ALL))
    
    print(Fore.CYAN + "   Выберите тип жалобы:" + Style.RESET_ALL)
    for i, complaint_type in enumerate(complaint_types.keys()):
        print(f"   {i+1}. {complaint_type}")
    choice = int(input(Fore.CYAN + "   Выберите номер типа жалобы: " + Style.RESET_ALL)) - 1 
    chosen_complaint_type = list(complaint_types.keys())[choice]
    
    return user_id, users, id_link, total_per_user, chosen_complaint_type 

active_proxies = []
proxy_lock = threading.Lock()
is_running = True

def check_single_proxy(ip):
    proxy = {"http": f"http://{ip}", "https": f"http://{ip}"}
    try:
        test = requests.get("https://telegram.org", proxies=proxy, timeout=1.5)
        if test.status_code == 200:
            return proxy
    except:
        pass
    return None

def single_scanner_worker():
    global is_running, active_proxies
    api_url = "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=2000&country=all&ssl=yes"
    
    while is_running:
        try:
            res = requests.get(api_url, timeout=4)
            if res.status_code == 200:
                proxies_list = [line.strip() for line in res.text.splitlines() if line.strip()]
                random.shuffle(proxies_list)
                
                for ip in proxies_list:
                    if not is_running:
                        break
                    
                    proxy = check_single_proxy(ip)
                    if proxy:
                        with proxy_lock:
                            if proxy not in active_proxies and len(active_proxies) < 50: # Увеличили пул до 50
                                active_proxies.append(proxy)
        except:
            pass
        time.sleep(1)

def worker_task(user_id, user, id_link, chosen_type, sites_pool):
    global active_proxies
    
    while is_running:
        with proxy_lock:
            if active_proxies:
                proxy = random.choice(active_proxies)
                break
        time.sleep(0.2)

    if not is_running:
        return False

    random_site = random.choice(sites_pool)
    data = random_site['data'].copy()

    formatted_text = random.choice(complaint_types[chosen_type]).format(user_id=user_id, user=user, id=id_link)

    if 'tg_feedback_appeal' in data:
        data['tg_feedback_appeal'] = formatted_text
        data['tg_feedback_email'] = generate_random_email()
        data['tg_feedback_phone'] = generate_random_phone()
    else:
        data['name'] = user
        data['email'] = f"{user_id}@example.com"
        data['message'] = formatted_text

    headers = {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
        ])
    }

    session = requests.Session()
    try:
        response = session.post(random_site['url'], headers=headers, data=data, proxies=proxy, timeout=3)
        response.raise_for_status()
        return True
    except Exception:
        with proxy_lock:
            if proxy in active_proxies:
                active_proxies.remove(proxy)
        return False

def main():
    global is_running
    user_id, users, id_link, total_per_user, chosen_complaint_type = get_user_input()

    sites = [
        {'url': 'https://telegram.org/support?setln=ru', 'data': {'tg_feedback_appeal': '...', 'tg_feedback_email': '...', 'tg_feedback_phone': '...'}},
        {'url': 'https://telegram.org/support', 'data': {'name': '...', 'email': '...', 'message': '...'}}
    ]

    print(Fore.CYAN + f"\n[i] Запускаем сканеры прокси. Целей: {len(users)}. По {total_per_user} жалоб на каждого..." + Style.RESET_ALL)

    for _ in range(30): # Увеличили количество потоков сканера
        t = threading.Thread(target=single_scanner_worker, daemon=True)
        t.start()

    while len(active_proxies) < 20 and is_running:
        print(f"   {Fore.YELLOW}[!] Накопление прокси: {len(active_proxies)}/20{Style.RESET_ALL}", end="\r")
        time.sleep(0.5)

    print(Fore.GREEN + f"\n[✓] Прокси готовы! Начинаем рассылку на {len(users)} целей...\n" + Style.RESET_ALL)

    for target_user in users:
        if not is_running: break
        print(Fore.MAGENTA + f"\n=== Обработка цели: @{target_user} ===" + Style.RESET_ALL)
        
        sent_count = 0
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(worker_task, user_id, target_user, id_link, chosen_complaint_type, sites) for _ in range(total_per_user)]
            
            for future in as_completed(futures):
                if future.result():
                    sent_count += 1
                with proxy_lock:
                    pool_size = len(active_proxies)
                print(f"[{Fore.YELLOW}* Успешно: {sent_count}/{total_per_user} | Прокси в пуле: {pool_size} {Style.RESET_ALL}", end="\r")
        
        print(f"\n{Fore.GREEN}[+] Завершено для @{target_user}. Отправлено: {sent_count}{Style.RESET_ALL}")
        time.sleep(random.randint(3, 7)) # Пауза между разными ботами

    is_running = False
    print(f"\n\n{Fore.GREEN}Все задачи выполнены!{Style.RESET_ALL}")
    input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main()
