import calclog
import logging
import requests
import coin
import time
import json
import os
from datetime import datetime
from tabulate import tabulate

calclog = logging.getLogger('calc')

def load_difficulty(url,name):
    new_num = ''
    difficulty_loaded = False

    if "crypto-coinz" in url:
        while not difficulty_loaded:
            difficulty_loaded = False
            try:
                response = requests.get(url)
                txt = response.text
                num = txt.find("Difficulty:")
                for i in range(15):
                    if txt[num+19+i].isdigit() or txt[num+19+i] == '.':
                        new_num += txt[num+19+i]
                difficulty = float(new_num)
                difficulty_loaded = True
            except (requests.exceptions.HTTPError, ValueError) as err:
                calclog.error("Error loading " + name + " difficuly. Retrying in 10 seconds...")
                time.sleep(10)
            except:
                calclog.error("Could not load the difficulty for " + name + ". Skipping coin")
                difficulty = 0
                return difficulty, difficulty_loaded

    elif "fsight" in url:
        difficulty_loaded = False
        while not difficulty_loaded:
            try:
                temp = requests.get(url).json()
                difficulty = float(temp["difficulty"])
                difficulty_loaded = True
            except (requests.exceptions.HTTPError, ValueError) as err:
                calclog.error("Error loading " + name + " difficuly. Retrying in 10 seconds...")
                time.sleep(10)
            except:
                calclog.error("Could not load the difficulty for " + name + ". Skipping coin")
                difficulty = 0
                return difficulty, difficulty_loaded
    
    elif "trezar" in url or "denarius" in url:
        difficulty_loaded = False
        while not difficulty_loaded:
            try:
                temp = requests.get(url).json()
                difficulty = float(temp["proof-of-work"])
                difficulty_loaded = True
            except (requests.exceptions.HTTPError, ValueError) as err:
                calclog.error("Error loading " + name + " difficuly. Retrying in 10 seconds...")
                time.sleep(10)
            except:
                calclog.error("Could not load the difficulty for " + name + ". Skipping coin")
                difficulty = 0
                return difficulty, difficulty_loaded

    else:
        difficulty_loaded = False
        while not difficulty_loaded:
            try:
                difficulty  = float(requests.get(url).text)
                difficulty_loaded = True
            except (requests.exceptions.HTTPError, ValueError) as err:
                calclog.error("Error loading " + name + " difficuly. Retrying in 10 seconds...")
                time.sleep(10)
            except:
                calclog.error("Could not load the difficulty for " + name + ". Skipping coin")
                difficulty = 0
                return difficulty, difficulty_loaded

    return difficulty, difficulty_loaded

def calc(coin_info,neoscrypt_config,equihash_config,xevan_config,lyra2v2_config,bitcore_config,skunk_config,nist5_config,skein_config,tribus_config):
    coins = {}
    all_coins = {}
    #coin_name_list = []
    price_list = []
    coins_mined = 0.0
    coin_profit = 0.0
    prices_loaded = False
    se_prices = ''
    ts_prices = ''
    sx_prices = ''
    ct_prices = ''
    cb_prices = ''
    buy_price_se = 0.0
    buy_price_ts = 0.0
    difficulty = 0.0
    most_profitable_coin_list = []

    # Begin fetching the price of each coin
    calclog.info("Fetching coin prices...")

    # Load the prices of coins on stocks exchange.
    while not prices_loaded:
        try:
            se_prices = requests.get('https://stocks.exchange/api2/prices').json()
            prices_loaded = True
        except (requests.exceptions.HTTPError, ValueError) as err:
            prices_loaded = False
            calclog.error("Error loading prices from Stocks.Exchange api, trying again in 30 seconds...")
            time.sleep(30)
            
    prices_loaded = False

    # Load prices from trade satoshi.
    while not prices_loaded:
        try:
            ts_prices = requests.get('https://tradesatoshi.com/api/public/getmarketsummaries').json()
            prices_loaded = True
        except (requests.exceptions.HTTPError, ValueError) as err:
            prices_loaded = False
            calclog.error("Error loading prices from Trade Satoshi api, trying again in 30 seconds...")
            time.sleep(30)

    prices_loaded = False

    # Load prices from Southxchange.
    while not prices_loaded:
        try:
            sx_prices = requests.get('https://www.southxchange.com/api/prices').json()
            prices_loaded = True
        except (requests.exceptions.HTTPError, ValueError) as err:
            prices_loaded = False
            calclog.error("Error loading prices from Southxchange api, trying again in 30 seconds...")
            time.sleep(30)
            
    prices_loaded = False

    # Load prices from Cryptopia.
    while not prices_loaded:
        try:
            ct_prices = requests.get('https://www.cryptopia.co.nz/api/GetMarkets').json()
            prices_loaded = True
        except (requests.exceptions.HTTPError, ValueError) as err:
            prices_loaded = False
            calclog.error("Error loading prices from Cryptopia api, trying again in 30 seconds...")
            time.sleep(30)
            
    prices_loaded = False

    # Load prices from Crypto-bridge.
    while not prices_loaded:
        try:
            cb_prices = requests.get('https://api.crypto-bridge.org/api/v1/ticker').json()
            prices_loaded = True
        except (requests.exceptions.HTTPError, ValueError) as err:
            prices_loaded = False
            calclog.error("Error loading prices from Crypto-bridge api, trying again in 30 seconds...")
            time.sleep(30)
            
    prices_loaded = False

    # Load the price of BTC from coinbase.
    while not prices_loaded:
        try:
            btc_price = requests.get('https://api.coinbase.com/v2/exchange-rates?currency=BTC').json()
            prices_loaded = True
        except (requests.exceptions.HTTPError, ValueError) as err:
            prices_loaded = False
            calclog.error("Error loading prices from Coinbase api, trying again in 30 seconds...")
            time.sleep(30)
            
    calclog.info("Coin prices successfully loaded.")

    # Load the coins from the file and store them into a list
    calclog.info("Loading coins...")
    """
    for key in coin_info:
        coin_is_listed = False
        # Store only the coins supported by the exchange
        for i in range(len(se_prices)):
            if se_prices[i]['market_name'] == key['coin'] + '_BTC':
                calclog.debug("Found " + key['coin'] + " on Stocks Exchange")	
                coin_is_listed = True
                break

        for i in range(len(ts_prices['result'])):
            if ts_prices['result'][i]['market'] == key['coin'] + '_BTC':
                calclog.debug("Found " + key['coin'] + " on Trade Satoshi")   	
                coin_is_listed = True
                break
        
        for i in range(len(sx_prices)):
            if sx_prices[i]['Market'] == key['coin'] + '/BTC':
                calclog.debug("Found " + key['coin'] + " on Southxchange")   	
                coin_is_listed = True
                break

        for i in range(len(ct_prices['Data'])):
            if ct_prices['Data'][i]['Label'] == key['coin'] + '/BTC':
                calclog.debug("Found " + key['coin'] + " on Cryptopia")   	
                coin_is_listed = True
                break
        
        for i in range(len(cb_prices)):
            if cb_prices[i]['id'] == key['coin'] + '_BTC':
                calclog.debug("Found " + key['coin'] + " on Crypto-Bridge")   	
                coin_is_listed = True
                break

        if not coin_is_listed:
            calclog.info(key['coin'] + " is not listed on your exchanges.")
        else:
            coin_name_list.append(key['coin'])

    calclog.info("Coins successfully loaded, total amount of coins: " + str(len(coin_name_list)))

    calclog.info("Calculating profitability for each coin...")
    """
    for key in coin_info:
        buy_price_se = 0.0
        buy_price_ts = 0.0
        buy_price_sx = 0.0
        buy_price_ct = 0.0
        buy_price_cb = 0.0
        exchange = ''
        coin_name = key['coin']

        # Get the difficulty and block reward for each coin.     
        url = key['api_url']
        block_reward = key['block_reward']
        pool_url = key['pool_url']
        port = key['port']
        algorithm = key['algo']
        difficulty,difficulty_loaded = load_difficulty(url,coin_name)
            
        if not difficulty_loaded:
            pass
            calclog.debug("Skipping coin: " + coin_name)
        else:
            # Add stocks exchange prices
            for i in range(len(se_prices)):
                if se_prices[i]['market_name'] == coin_name + '_BTC':
                    try:
                        buy_price_se = float(se_prices[i]['buy'])
                    except TypeError:
                        buy_price_se = 0.0
                    break
            
            # Add trade satoshi exchange prices
            for i in range(len(ts_prices['result'])):
                if ts_prices['result'][i]['market'] == coin_name + '_BTC':
                    try:
                        buy_price_ts = float(ts_prices['result'][i]['last'])
                    except TypeError:
                        buy_price_ts = 0.0
                    break

            # Add Southxchange exchange prices
            for i in range(len(sx_prices)):
                if sx_prices[i]['Market'] == coin_name + '/BTC':
                    try:
                        buy_price_sx = float(sx_prices[i]['Last'])
                    except TypeError:
                        buy_price_sx = 0.0
                    break
            
            # Add Cryptopia exchange prices
            for i in range(len(ct_prices['Data'])):
                if ct_prices['Data'][i]['Label'] == coin_name + '/BTC':
                    buy_price_ct = float(ct_prices['Data'][i]['LastPrice'])
                    break

            # Add Crypto-bridge exchange prices
            for i in range(len(cb_prices)):
                if cb_prices[i]['id'] == coin_name + '_BTC':
                    buy_price_cb = float(cb_prices[i]['last'])
                    break

            # Find the BTC price in the json file queried from coinbase, then calculate it's value in USD.
            usd_price = float(btc_price["data"]["rates"]["USD"])

            calclog.debug(" Stocks.Exchange Price: " +  str(buy_price_se) + " Trade Satoshi Price: " + str(buy_price_ts) + " Southxchange Price: " + str(buy_price_sx) + " Cryptopia Price: " + str(buy_price_ct) + " Crypto-Bridge Price: " + str(buy_price_cb))

            buy_prices = [buy_price_ct,buy_price_se,buy_price_sx,buy_price_ts,buy_price_cb]
            buy_prices.sort(reverse=True)

            # List the exchange with the highest value of the coin.
            calclog.debug("Highest Price: " + str(buy_prices))

            for i in range(len(buy_prices)):
                if buy_prices[i] == buy_price_se and not key['exchange']['Stocks.Exchange'] == "NA":
                    coin_price = buy_price_se * usd_price
                    calclog.debug(" Stocks.Exchange Price: " +  str(buy_price_se) + " USD price: " + str(coin_price))
                    exchange = "Stocks.Exchange"
                    break
                elif buy_prices[i] == buy_price_ts and not key['exchange']['Trade Satoshi'] == "NA":
                    coin_price = buy_price_ts * usd_price
                    calclog.debug(" Trade Satoshi Price: " + str(buy_price_ts) + " USD price: " + str(coin_price))
                    exchange = "Trade Satoshi"
                    break
                elif buy_prices[i] == buy_price_sx and not key['exchange']['Southxchange'] == "NA":
                    coin_price = buy_price_sx * usd_price
                    calclog.debug(" Southxchange Price: " + str(buy_price_sx) + " USD price: " + str(coin_price))
                    exchange = "Southxchange"
                    break
                elif buy_prices[i] == buy_price_ct and not key['exchange']['Cryptopia'] == "NA":
                    coin_price = buy_price_ct * usd_price
                    calclog.debug(" Cryptopia Price: " + str(buy_price_ct) + " USD price: " + str(coin_price))
                    exchange = "Cryptopia"
                    break
                elif buy_prices[i] == buy_price_cb and not key['exchange']['Crypto-Bridge'] == "NA":
                    coin_price = buy_price_cb * usd_price
                    calclog.debug(" Crypto-Bridge Price: " +  str(buy_price_cb) + " USD price: " + str(coin_price))
                    exchange = "Crypto-Bridge"
                    break

            # Initialize an object for each coin and the object as a key in a dictionary, then calculate the 24 hour
            # profitiability of the coin and store it as the value in the dictionary.
            # e.g. { "coin" : 12.34 }
            new_coin = coin.Coin(coin_name,coin_price,usd_price,exchange,block_reward,difficulty,algorithm)

            if algorithm == "neoscrypt":
                hashrate = neoscrypt_config['hashrate']
                electricity_costs = neoscrypt_config['electricity_costs']
                power_consumption = neoscrypt_config['power_consumption']
            if algorithm == "equihash":
                hashrate = equihash_config['hashrate']
                electricity_costs = equihash_config['electricity_costs']
                power_consumption = equihash_config['power_consumption']
            if algorithm == "xevan":
                hashrate = xevan_config['hashrate']
                electricity_costs = xevan_config['electricity_costs']
                power_consumption = xevan_config['power_consumption']
            if algorithm == "lyra2v2":
                hashrate = lyra2v2_config['hashrate']
                electricity_costs = lyra2v2_config['electricity_costs']
                power_consumption = lyra2v2_config['power_consumption']
            if algorithm == "bitcore":
                hashrate = bitcore_config['hashrate']
                electricity_costs = bitcore_config['electricity_costs']
                power_consumption = bitcore_config['power_consumption']
            if algorithm == "skunk":
                hashrate = skunk_config['hashrate']
                electricity_costs = skunk_config['electricity_costs']
                power_consumption = skunk_config['power_consumption']
            if algorithm == "nist5":
                hashrate = nist5_config['hashrate']
                electricity_costs = nist5_config['electricity_costs']
                power_consumption = nist5_config['power_consumption']
            if algorithm == "skein":
                hashrate = skein_config['hashrate']
                electricity_costs = skein_config['electricity_costs']
                power_consumption = skein_config['power_consumption']
            if algorithm == "tribus":
                hashrate = tribus_config['hashrate']
                electricity_costs = tribus_config['electricity_costs']
                power_consumption = tribus_config['power_consumption']
            
            if not algorithm == "equihash" and not coin_name == "HUSH" and not coin_name == "CROP":
                # Convert KH/s to H/s
                hashrate *= 1000
                coins_mined = (hashrate/(difficulty*(2**32))*86400*block_reward)
            elif coin_name == "CROP":
                # Convert KH/s to H/s
                hashrate *= 1000
                coins_mined = (hashrate/(difficulty*(2**25))*86400*block_reward)
            elif coin_name == "HUSH":
                coins_mined = (hashrate/(difficulty*(2.001313))*86400*block_reward)
            else:
                coins_mined = (hashrate/(difficulty*(2**13))*86400*block_reward)
            
            coin_profit = coins_mined * new_coin.getPrice()

            calclog.debug("Coin: " + coin_name + " Hashrate: " + str(hashrate) + " Difficulty: " + str(difficulty) + " Price: " + str(coin_price) + " Block reward: " + str(block_reward) + " Reward: " + str(coins_mined) + " Revenue: " + str(coin_profit))

            coins[new_coin] = coin_profit
            calclog.debug("Currently processing" + coin_name)
            wallet_address = key['exchange'][new_coin.getExchange()]
            daily_electricity_costs = ((power_consumption/1000)*24)*float(electricity_costs)
            all_coins[coin_name] = [coin_profit, coins_mined, difficulty, new_coin.getPrice(), new_coin.getBTCPrice(), new_coin.getExchange(), pool_url, wallet_address,algorithm,port,daily_electricity_costs]
            calclog.info(coin_name + " coin has been loaded.")

    # Store info on each coin as a list of dictionaries sorted by most profitable to least profitable.
    for key, value in sorted(all_coins.items(), key=lambda item: (item[1], item[0]), reverse=True):
        for key2, value2 in coins.items():
            if value2 == value[0]:
                most_profitable_coin_list.append({'coin' : key,
                'est_block_reward' : all_coins[key][1],
                'difficulty' : all_coins[key][2],
                'price' : all_coins[key][3],
                'exchange' : all_coins[key][5],
                'btc_price' : all_coins[key][4],
                'pool_url' : all_coins[key][6],
                'wallet_address' : all_coins[key][7],
                'algorithm' : all_coins[key][8],
                'port' :  all_coins[key][9],
                'electricity_costs' :  all_coins[key][10],
                'estimated_revenue' : all_coins[key][0],
                'estimated_profits' : all_coins[key][0] - all_coins[key][10]})

    with open('most_profitable_coins.json', 'w') as outfile:
        json.dump(most_profitable_coin_list, outfile)

    return most_profitable_coin_list

def print_coins(coin_list):
    tablist = []

    for key in coin_list:
        tablist.append([key['coin'],
        key['algorithm'],
        key['difficulty'],
        key['est_block_reward'],
        "$" +  str("%.4f" % key['price']),
        key['exchange'],
        "$" +  str(key['btc_price']),
        "$" + str("%.2f" % key['estimated_revenue']),
        "$" + str("%.2f" % key['estimated_profits'])])
    
    calclog.info("\n" + tabulate(tablist, headers=['Coin', 'Algorithm', 'Difficulty', 'Reward', "Price", "Exchange", "BTC Price", "Revenue", "Profits"], stralign="center", numalign="right", floatfmt=".4f"))

def load_config():
    load_successful = False
    config = {}
    try:
        config = json.load(open('config.json'))
        load_successful = True
        return load_successful,config
    except (IOError, ValueError) as err:
        return load_successful,config

def load_algo_config(config,algo):
    neoscrypt_config = {} 
    equihash_config = {} 
    xevan_config = {}
    lyra2v2_config = {}
    bitcore_config = {} 
    skunk_config = {} 
    nist5_config = {}
    skein_config = {}
    tribus_config = {}
    load_successful = False
    
    if algo == "neoscrypt":
        try:
            neoscrypt_config = config[0][algo]
            calclog.debug("Found " + algo + " in config file")
            load_successful = True
            return load_successful,algo,neoscrypt_config
        except (KeyError, IndexError) as err:
            calclog.info(algo + " not found in file")
            return load_successful,algo,neoscrypt_config
    if algo == "equihash":
        try:
            equihash_config = config[1][algo]
            calclog.debug("Found " + algo + " in config file")
            load_successful = True
            return load_successful,algo,equihash_config
        except (KeyError, IndexError) as err:
            calclog.info(algo + " not found in file")
            return load_successful,algo,equihash_config
    if algo == "xevan":
        try:
            xevan_config = config[2][algo]
            calclog.debug("Found " + algo + " in config file")
            load_successful = True
            return load_successful,algo,xevan_config
        except (KeyError, IndexError) as err:
            calclog.info(algo + " not found in file")
            return load_successful,algo,xevan_config
    if algo == "lyra2v2":
        try:
            lyra2v2_config = config[3][algo]
            calclog.debug("Found " + algo + " in config file")
            load_successful = True
            return load_successful,algo,lyra2v2_config
        except (KeyError, IndexError) as err:
            calclog.info(algo + " not found in file")
            return load_successful,algo,lyra2v2_config
    if algo == "bitcore":
        try:
            bitcore_config = config[4][algo]
            calclog.debug("Found " + algo + " in config file")
            load_successful = True
            return load_successful,algo,bitcore_config
        except (KeyError, IndexError) as err:
            calclog.info(algo + " not found in file")
            return load_successful,algo,bitcore_config
    if algo == "skunk":
        try:
            skunk_config = config[5][algo]
            calclog.debug("Found " + algo + " in config file")
            load_successful = True
            return load_successful,algo,skunk_config
        except (KeyError, IndexError) as err:
            calclog.info(algo + " not found in file")
            return load_successful,algo,skunk_config
    if algo == "nist5":
        try:
            nist5_config = config[6][algo]
            calclog.debug("Found " + algo + " in config file")
            load_successful = True
            return load_successful,algo,nist5_config
        except (KeyError, IndexError) as err:
            calclog.info(algo + " not found in file")
            return load_successful,algo,nist5_config
    if algo == "skein":
        try:
            skein_config = config[7][algo]
            calclog.debug("Found " + algo + " in config file")
            load_successful = True
            return load_successful,algo,skein_config
        except (KeyError, IndexError) as err:
            calclog.info(algo + " not found in file")
            return load_successful,algo,skein_config
    if algo == "tribus":
        try:
            tribus_config = config[8][algo]
            calclog.debug("Found " + algo + " in config file")
            load_successful = True
            return load_successful,algo,tribus_config
        except (KeyError, IndexError) as err:
            calclog.info(algo + " not found in file")
            return load_successful,algo,tribus_config

if __name__ == "__main__":
    # Check if the person has a configuration file. If not, start benchmarking.
    config_load_successful,config = load_config()

    if not config_load_successful:
        calclog.error("Config file not found, try running the benchmark first.")

    if config_load_successful:
        coin_info = json.load(open('coininfo.json'))

        new_algo_config = {}
        neoscrypt_config = {} 
        equihash_config = {} 
        xevan_config = {}
        lyra2v2_config = {}
        bitcore_config = {} 
        skunk_config = {} 
        nist5_config = {}
        skein_config = {}
        tribus_config = {}
        algorithm_list = []

        algorithm_list.append(coin_info[0]['algo'])
        for key in coin_info:      
            if not key['algo'] in algorithm_list:
                algorithm_list.append(key['algo'])

        for algo in algorithm_list:
            algo_config_load_successful,algo,new_algo_config = load_algo_config(config,algo)
            if not algo_config_load_successful:
                calclog.error("Some algorithms are missing from your config file, please run benchmark first...")
                
            if algo == "neoscrypt":
                neoscrypt_config = new_algo_config
            elif algo == "equihash":
                equihash_config = new_algo_config
            elif algo == "xevan":
                xevan_config = new_algo_config
            elif algo == "lyra2v2":
                lyra2v2_config = new_algo_config
            elif algo == "bitcore":
                bitcore_config = new_algo_config
            elif algo == "skunk":
                skunk_config = new_algo_config
            elif algo == "nist5":
                nist5_config = new_algo_config
            elif algo == "skein":
                skein_config = new_algo_config
            elif algo == "tribus":
                tribus_config = new_algo_config

        most_profitable_coins = calc(coin_info,neoscrypt_config,equihash_config,xevan_config,lyra2v2_config,bitcore_config,skunk_config,nist5_config,skein_config,tribus_config)

        print_coins(most_profitable_coins)

        # Store the most profitable coin's name.
        most_profitable_coin_name = most_profitable_coins[0]['coin']

        calclog.info("Your most profitable coin is: " + most_profitable_coin_name)