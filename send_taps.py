import json, time

from scripts.tapswap     import TapSwap
from scripts.hamster     import HamsterCombat
from scripts.cexio       import Cex_IO
from scripts.blum        import Blum
from scripts.rockyrabbit import RockyRabbitAPI
from scripts.logger      import setup_custom_logger
from scripts.cache_data  import SimpleCache

from concurrent.futures import ThreadPoolExecutor


executor = ThreadPoolExecutor(15)
logger   = setup_custom_logger("tapper")

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
    blum_clicker     = data['blum_clicker']
    rabbit_clicker   = data['rabbit_clicker']
        
    cexio_ref_code   = data['cexio_ref_code']
    blum_ref_code    = data['blum_ref_code']

url_files = [f for f in os.listdir('cache') if f.endswith('.json')]

def connect(file):
    try:
        client_id = file.split('.json')[0]
        logger.debug("Starting: " + client_id)
        cache_db = SimpleCache(client_id)
        
        tapswap_url = cache_db.get('tapswap_url')
        hamster_url = cache_db.get('hamster_url')
        cex_io_url  = cache_db.get('cex_io_url')
        blum_url    = cache_db.get('blum_url')
        rabbit_url  = cache_db.get('rabbit_url')
        
        if tapswap_url and tapswap_clicker == "on":
            start_tapswap_client(file, client_id, cache_db, tapswap_url, auto_upgrade, max_charge_level, max_energy_level, max_tap_level)

        if hamster_url and hamster_clicker == "on":
            start_hamster_client(file, client_id, cache_db, hamster_url, max_days_for_return)
        
        if cex_io_url and cexio_clicker == "on":
            start_cex_io_client(file, client_id, cache_db, cex_io_url)
        
        if blum_url and blum_clicker == "on":
            start_blum_client(file, client_id, cache_db, blum_url, blum_ref_code)
        
        if rabbit_url and rabbit_clicker == "on":
            start_rabbit_client(file, client_id, cache_db, rabbit_url)
        
    except Exception as e:
        logger.error(f'Error in building client[{file}]: ' + str(e))
        
def start_tapswap_client(file, client_id, cache_db, tapswap_url, auto_upgrade, max_charge_level, max_energy_level, max_tap_level):
    next_tapswap_click = cache_db.get('next_tapswap_click')
    if next_tapswap_click and time.time() < next_tapswap_click:
        return
    try:
        cache_db.set('next_tapswap_click', time.time() + (60*15))
        tapswap_client = TapSwap(tapswap_url, auto_upgrade, max_charge_level, max_energy_level, max_tap_level, client_id)
        if tapswap_client.isReady():
            tapswap_client.click_all()
            next_tap = time.time() + tapswap_client.time_to_recharge()
            cache_db.set('next_tapswap_click', next_tap)
            cache_db.set('tapswap_balance', tapswap_client.shares())
    except Exception as e:
        logger.error(f'Error in building TapSwap[{file}]: ' + str(e))

def start_hamster_client(file, client_id, cache_db, hamster_url, max_days_for_return):
    next_hamster_click = cache_db.get('next_hamster_click')
    
    if next_hamster_click and time.time() < next_hamster_click:
        return
    
    try:
        cache_db.set('next_hamster_click', time.time() + (60*15))
        hamster_client = HamsterCombat(hamster_url, max_days_for_return, client_id)
        hamster_client.tap_all()
        hamster_client.update_all()
        next_tap = time.time() + hamster_client.time_to_recharge()
        cache_db.set('next_hamster_click', next_tap)
        cache_db.set('hamster_balance', hamster_client.balance_coins())
        cache_db.set('hamster_earn_per_hour', hamster_client.earn_passive_per_hour)
    except Exception as e:
        logger.error(f'Error in building Hamster[{file}]: ' + str(e))

def start_cex_io_client(file, client_id, cache_db, cex_io_url):
    next_cexio_click = cache_db.get('next_cexio_click')
    if next_cexio_click and time.time() < next_cexio_click:
        return
    try:
        cex_io_client = Cex_IO(cex_io_url, client_id)
        cex_io_client.check_for_clicks()
        cache_db.set('next_cexio_click', cex_io_client.farms_end_time())
        cache_db.set('cex_io_balance', cex_io_client.balance())
    except Exception as e:
        logger.error(f'Error in building Cex_IO[{file}]: ' + str(e))

def start_blum_client(file, client_id, cache_db, blum_url, referralToken):
    next_blum_click = cache_db.get('next_blum_click')
    if next_blum_click and time.time() < next_blum_click:
        return
    try:
        cache_db.set('next_blum_click', time.time() + (60*15))
        blum_client = Blum(blum_url, client_id, referralToken)
        blum_client.claim_pass()
        blum_client.check_claim_and_play()
        cache_db.set('next_blum_click', time.time() + (60*60*8 + 5*60))
        cache_db.set('blum_balance', blum_client.balance()['availableBalance'])
    except Exception as e:
        logger.error(f'Error in building blum[{file}]: ' + str(e))

def start_rabbit_client(file, client_id, cache_db:SimpleCache, rabbit_url):
    next_rabbit_click = cache_db.get('next_rabbit_click')
    if next_rabbit_click and time.time() < next_rabbit_click:
        return
    try:
        cache_db.set('next_rabbit_click', time.time() + (60*15))
        if time.time() - cache_db.get('rabbit_url_time') > 60*60*3:
            return
        rabbit_client = RockyRabbitAPI(rabbit_url, client_id)
        if not cache_db.exists('rabbit_init'):
            rabbit_client.account_init()
            cache_db.set('rabbit_init', time.time())
        
        time_for_recharge = rabbit_client.tap_all()
        if time_for_recharge == 'init data':
            return
        rabbit_client.auto_upgrade()
        cache_db.set('next_rabbit_click', time.time() + time_for_recharge)
        cache_db.set('rabbit_balance', rabbit_client.balance())
    except Exception as e:
        logger.error(f'Error in building rabbit[{file}]: ' + str(e))

def start_clickers():
    tasks = []
    
    for file in url_files:
        tasks.append(executor.submit(connect, file))
    
    for t in tasks:
        try:
            t.result()
        except Exception as e:
            logger.warning(f"Error in task execution: {str(e)}")

def main():
    if not os.path.exists('start.txt'):
        with open('start.txt', 'w') as f:
            f.write("START")

        try:
            start_clickers()
        except Exception as e:
            logger.error(f"Error in create_clickers: {e}")
        finally:
            os.unlink('start.txt')


if __name__ == '__main__':
    main()
