import asyncio
import json, os, time, aiocron, psutil, sys, subprocess, platform, datetime

from scripts.tapswap    import TapSwap
from scripts.hamster    import HamsterCombat
from scripts.cexio      import Cex_IO
from scripts.logger     import setup_custom_logger
from scripts.cache_data import SimpleCache
from scripts.tg_client  import create_client, reload_sessions, reload_rabbit_url

executor = ThreadPoolExecutor(15)

with open('config.json') as f:
    data             = json.load(f)
    api_id           = data['api_id']
    api_hash         = data['api_hash']
    admin            = data['admin']
    bot_token        = data['bot_token']
    auto_upgrade     = data['auto_upgrade']
    max_tap_level    = data['max_tap_level']
    max_charge_level = data['max_charge_level']
    max_energy_level = data['max_energy_level']
    max_days_for_return = data['max_days_for_return']
    
    cexio_clicker    = data['cexio_clicker']
    tapswap_clicker  = data['tapswap_clicker']
    hamster_clicker  = data['hamster_clicker']
        
    cexio_ref_code   = data['cexio_ref_code']
    blum_ref_code    = data['blum_ref_code']
    

if not os.path.exists('sessions'):
    os.mkdir('sessions')


m = """
Welcome to the Multi Session version of the All in One Clicker script! 🎉

GitHub Repository: https://github.com/Poryaei/All-In-One

Please choose:

1. Add account (session / clicker)
2. Run the bots
3. Reload Sessions ( For New Bots )
"""

print(m)

while True:
    choice = input("Please enter your choice: ")
    
    if choice == "1":
        create_client(api_id, api_hash, admin, cexio_ref_code)
    elif choice == "2":
        break
    elif choice == "3":
        reload_sessions()
    else:
        print("Invalid choice. Please try again.")
    
    print(m)
    
if not os.path.exists('sessions'):
    os.mkdir('sessions')

client = TelegramClient('sessions/robot', api_id, api_hash)
client.start(bot_token=bot_token)

print("Client is ready")

if os.path.exists('start.txt'):
    os.unlink('start.txt')

db = {
    'click': 'on',
    'start': False,
    'rabbit_update': 0
}
clickers = {}
url_files = [f for f in os.listdir('cache') if f.endswith('.json')]
VERSION    = "1.2"
START_TIME = time.time()

def convert_time(uptime):
    hours   = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)

    return (hours if hours > 0 else 0), minutes

def hamster_do_tasks():
    def task(file):
        client_id = file.split('.json')[0]
        cache_db = SimpleCache(client_id)
        hamster_url = cache_db.get('hamster_url')
        try:
            hamster_client = HamsterCombat(hamster_url, max_days_for_return, client_id)
            hamster_client.do_tasks()
            return f"User: {client_id} | Tasks done"
        except Exception as e:
            logger.warning(f"User: {client_id} | Error in Hamster Tasks: " + str(e))
            return f"User: {client_id} | Error: {str(e)}"
    
    with concurrent.futures.ThreadPoolExecutor(10) as executor:
        results = list(executor.map(task, url_files))
    return results

def daily_cipher(cipher: str):
    def task(file):
        client_id = file.split('.json')[0]
        cache_db = SimpleCache(client_id)
        hamster_url = cache_db.get('hamster_url')
        try:
            hamster_client = HamsterCombat(hamster_url, max_days_for_return, client_id)
            hamster_client.claim_daily_cipher(cipher)
            return f"User: {client_id} | Daily cipher claimed"
        except Exception as e:
            logger.warning(f"User: {client_id} | Error in Hamster Daily Cipher: " + str(e))
            return f"User: {client_id} | Error: {str(e)}"
    
    with concurrent.futures.ThreadPoolExecutor(10) as executor:
        results = list(executor.map(task, url_files))
    return results

def daily_combo():
    def task(file):
        client_id = file.split('.json')[0]
        cache_db = SimpleCache(client_id)
        hamster_url = cache_db.get('hamster_url')
        try:
            hamster_client = HamsterCombat(hamster_url, max_days_for_return, client_id)
            hamster_client.claim_daily_combo()
            return f"User: {client_id} | Daily combo claimed"
        except Exception as e:
            logger.warning(f"User: {client_id} | Error in Hamster Daily Combo: " + str(e))
            return f"User: {client_id} | Error: {str(e)}"
    
    with concurrent.futures.ThreadPoolExecutor(10) as executor:
        results = list(executor.map(task, url_files))
            
    return results

def buy_card(item: str):
    def task(file):
        client_id = file.split('.json')[0]
        cache_db = SimpleCache(client_id)
        hamster_url = cache_db.get('hamster_url')
        try:
            hamster_client = HamsterCombat(hamster_url, max_days_for_return, client_id)
            r = hamster_client.upgrade_item(item)
            return f"User: {client_id} | Card bought: {r}"
        except Exception as e:
            logger.warning(f"User: {client_id} | Error in Hamster buy card: " + str(e))
            return f"User: {client_id} | Error: {str(e)}"
    
    with concurrent.futures.ThreadPoolExecutor(10) as executor:
        results = list(executor.map(task, url_files))
    return results



def total_balance():
    def safe_get_balance(cache_db, key, default=0.0):
        try:
            return float(cache_db.get(key))
        except (TypeError, ValueError):
            return default

    tapswap = 0
    hamster = 0
    cexio = 0
    blum = 0
    rabbit = 0
    hamster_earn_per_hour = 0

    for file in url_files:
        client_id = file.split('.json')[0]
        cache_db = SimpleCache(client_id)

        tapswap += safe_get_balance(cache_db, 'tapswap_balance')
        hamster += safe_get_balance(cache_db, 'hamster_balance')
        hamster_earn_per_hour += safe_get_balance(cache_db, 'hamster_earn_per_hour')
        cexio += safe_get_balance(cache_db, 'cex_io_balance')
        blum += safe_get_balance(cache_db, 'blum_balance')
        rabbit += safe_get_balance(cache_db, 'rabbit_balance')
        
    return tapswap, hamster, cexio, hamster_earn_per_hour, blum, rabbit

def account_balance(client_id):
    def safe_get_balance(cache_db, key, default=0.0):
        try:
            return float(cache_db.get(key))
        except (TypeError, ValueError):
            return default

    tapswap = 0
    hamster = 0
    cexio = 0
    blum = 0
    rabbit = 0
    hamster_earn_per_hour = 0


    cache_db = SimpleCache(client_id)

    tapswap += safe_get_balance(cache_db, 'tapswap_balance')
    hamster += safe_get_balance(cache_db, 'hamster_balance')
    hamster_earn_per_hour += safe_get_balance(cache_db, 'hamster_earn_per_hour')
    cexio += safe_get_balance(cache_db, 'cex_io_balance')
    blum += safe_get_balance(cache_db, 'blum_balance')
    rabbit += safe_get_balance(cache_db, 'rabbit_balance')
    account_data_json = cache_db.get('account_data')
    account_data = json.loads(account_data_json)
        
    return tapswap, hamster, cexio, hamster_earn_per_hour, blum, rabbit, account_data

def account_list():
    global url_files
    url_files = [f for f in os.listdir('cache') if f.endswith('.json')]
    accounts = []

    for file in url_files:
        try:
            client_id = file.split('.json')[0]
            cache_db = SimpleCache(client_id)
            
            account_data_json = cache_db.get('account_data')
            account_data = json.loads(account_data_json)
            first_name = account_data.get('first_name', 'Unknown')
            
            accounts.append(Button.inline(first_name, f'user_{client_id}'))
        except:
            continue

    grouped_buttons = [accounts[i:i + 3] for i in range(0, len(accounts), 3)]
    grouped_buttons.append([Button.inline('🔙', 'back')])
    return grouped_buttons


def convert_uptime(uptime):
    hours   = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)

