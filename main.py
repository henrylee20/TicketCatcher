import os
import sys
import time
import json
import logging
import threading
import yellowbull
from selenium import webdriver

kDefaultCfgPath = 'cfg.json'
kQRPicPath = 'QR.png'
kCookiesPath = 'cookies.json'
kLogPath = 'test.log'

# TI9 url
#kTicketUrl = 'https://detail.damai.cn/item.htm?spm=a2oeg.home.card_2.ditem_0.591b23e14q0SEE&id=593089517773'

kTicketUrl = "https://detail.damai.cn/item.htm?spm=a2oeg.search_category.0.0.227928dfOlpXzC&id=600583263497"

# Test url
#kTicketUrl = 'https://detail.damai.cn/item.htm?spm=a2oeg.home.card_0.ditem_4.715223e1babBKN&id=594317472320'


class BullThread(threading.Thread):
    def __init__(self, browser_opt, cfg: dict, logger):
        threading.Thread.__init__(self)
        self.browser_opt = browser_opt
        self.cfg = cfg
        self.logger = logger

    def run(self) -> None:
        browser = webdriver.Chrome(options=self.browser_opt)
        bull = yellowbull.YellowBull(browser, self.cfg['ticket_url'], self.cfg['qr_path'],
                                     self.cfg['cookie_path'], self.logger)

        bull.login()
        bull.catch_ticket(self.cfg['perform_session'], self.cfg['perform_price'], self.cfg['ticket_num'])


def get_logger(log_file):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter('[%(asctime)s] [%(threadName)s: %(thread)d] [%(filename)s:%(lineno)d] [%(levelname)s]: '
                            '%(message)s')
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt)
    logger.addHandler(sh)
    logger.addHandler(fh)

    return logger


def main(argv):
    options = webdriver.ChromeOptions()
    options.add_argument('headless')

    if len(argv) == 2:
        cfg_path = argv[1]
    else:
        print('Usage: python main.py <config_json_file>')
        return 0

    if not os.path.exists(cfg_path):
        cfg_path = kDefaultCfgPath
        default_cfg = {
            'ticket_url': kTicketUrl,
            'qr_path': kQRPicPath,
            'cookie_path': kCookiesPath,
            'perform_session': '8月22-23日套票，包含两张门票',
            'perform_price': '499元',
            'ticket_num': 1,
            'log_file': kLogPath,
            'thread_num': 8,
            'thread_interval_time': 0.5,
        }
        with open(cfg_path, 'w', encoding='utf-8') as fp:
            fp.write(json.dumps(default_cfg))
        print('Config file not found. Generating default config file: ' + kDefaultCfgPath)
        print('Modify your real config.')
        print('Exiting.')
        return 0

    with open(cfg_path, encoding='utf-8') as fp:
        cfg_str = fp.read()

    cfg = json.loads(cfg_str, encoding='utf-8')

    logger = get_logger(cfg['log_file'])

    print('Now config: ')
    for key in cfg.keys():
        print(key + ': ' + str(cfg[key]))

    bulls = []
    for i in range(cfg['thread_num']):
        bull = BullThread(options, cfg, logger)
        bulls.append(bull)

    for bull in bulls:
        bull.start()
        time.sleep(cfg['thread_interval_time'])

    for bull in bulls:
        bull.join()


if __name__ == '__main__':
    main(sys.argv)
