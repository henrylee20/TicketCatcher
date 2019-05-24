import os
import sys
import time
import json
import selenium.common
import selenium.webdriver

from selenium.webdriver.support.expected_conditions import title_contains
from selenium.webdriver.support.ui import WebDriverWait


kDamaiUrl = 'https://www.damai.cn/'
kLoginUrl = 'https://passport.damai.cn/login?ru=https%3A%2F%2Fwww.damai.cn%2F'


class YellowBull:
    def __init__(self, browser, ticket_url, qr_file, cookie_file, logger):
        self.browser = browser
        self.ticket_url = ticket_url
        self.qr_file = qr_file
        self.cookie_file = cookie_file

        self.browser.get(kDamaiUrl)
        self.browser.set_window_size(1920, 1080)

        self.__logger = logger

    def check_login(self):
        login_text = self.browser.find_element_by_class_name('span-user').text
        return login_text != '登录'

    def login(self):
        return self.__cookie_login() or self.__qr_code_login()

    def catch_ticket(self, perform_session, perform_price, ticket_num):
        self.__jump_to_ticket()

        self.__logger.info('Start catching.')
        while self.browser.title.find('确认订单') == -1:
            self.__logger.info('Try catching.')
            self.__set_perform_infos(perform_session, perform_price)
            self.__set_ticket_num(ticket_num)

            btn_buy = self.browser.find_element_by_class_name('buybtn')

            if btn_buy.text == '立即预定' or btn_buy.text == '立即购买':
                btn_buy.click()
                self.browser.implicitly_wait(1)

                # check err
                if not self.__check_jump_to_order_err():
                    continue

                # order
                if not self.__order_ticket():
                    self.__jump_to_ticket()
                    continue
                else:
                    break
            elif btn_buy.text == '即将开抢':
                self.__logger.info('Not start yet. refreshing')
                self.__jump_to_ticket()
            else:
                self.__logger.error('Unknown status. refreshing. status: %s', btn_buy.text)
                self.__jump_to_ticket()

        self.__logger.info('Finish catching.')
        self.browser.save_screenshot('test2.png')
        return True

    def __cookie_login(self):
        if not os.path.exists(self.cookie_file):
            self.__logger.warning("Cookies not found")
            return False

        self.__logger.info("Found login cookies at: %s", self.cookie_file)
        with open(self.cookie_file, 'r', encoding='utf-8') as fp:
            cookies_json = fp.read()
        self.__logger.debug(cookies_json)

        cookies = json.loads(cookies_json)
        for cookie in cookies:
            self.browser.add_cookie(cookie)
        self.browser.refresh()
        return True

    def __qr_code_login(self):
        self.__logger.info("Using QR Code login. QR picture save to: %s", self.qr_file)
        self.browser.get(kLoginUrl)
        while self.browser.title != '中文登录':
            self.__logger.info('Waiting for login page')
            self.browser.implicitly_wait(1)

        time.sleep(2)
        self.browser.switch_to.frame('alibaba-login-box')

        btn_wx_login = self.browser.find_element_by_class_name('icon-weixin')

        btn_wx_login.click()
        time.sleep(3)

        windows = self.browser.window_handles
        now = self.browser.current_window_handle

        for w in windows:
            if w != now:
                self.browser.switch_to.window(w)
                self.browser.save_screenshot(self.qr_file)

        while len(self.browser.window_handles) > 1:
            self.__logger.info("Waiting for scan")
            time.sleep(1)

        self.__logger.info("Scanned")
        self.browser.switch_to.window(now)

        cookies_json = json.dumps(self.browser.get_cookies())
        with open(self.cookie_file, 'w', encoding='utf-8') as fp:
            fp.write(cookies_json)

        return True

    def __choose_one_perform_info(self, div_info_vals, info):
        found = False
        for div_info_val in div_info_vals:
            self.__logger.debug(div_info_val.text)
            if div_info_val.text.find(info) != -1:
                div_info_val.click()
                found = True
                self.browser.implicitly_wait(1)
                break
        return found

    def __set_perform_infos(self, perform_session, perform_price):
        # check ticket info
        div_perform_infos = self.browser.find_elements_by_class_name('perform__order__select')
        self.__logger.debug('Trying to set perform infos. Number of type: %d', len(div_perform_infos))
        for div_perform_info in div_perform_infos:
            div_info_name = div_perform_info.find_element_by_class_name('select_left')
            div_info_vals = div_perform_info.find_elements_by_class_name('select_right_list_item')
            self.__logger.debug('Trying to set %s', div_info_name.text)

            if div_info_name.text.find('场次') != -1:
                found = self.__choose_one_perform_info(div_info_vals, perform_session)
                if not found:
                    self.__logger.warning('Perform session not found. using default.')
            elif div_info_name.text.find('票档') != -1:
                found = self.__choose_one_perform_info(div_info_vals, perform_price)
                if not found:
                    self.__logger.warning('Perform price not found. using default.')

    def __set_ticket_num(self, ticket_num):
        self.__logger.debug('Trying to set number of tickets: %d', ticket_num)
        try:
            input_ticket_num = self.browser.find_element_by_class_name('cafe-c-input-number-input')
            input_ticket_num.send_keys(str(ticket_num))
        except selenium.common.exceptions.NoSuchElementException:
            pass

    def __jump_to_ticket(self):
        self.browser.get(self.ticket_url)
        if not self.check_login():
            self.login()
            self.browser.get(self.ticket_url)
        self.browser.implicitly_wait(1)

    def __check_jump_to_order_err(self):
        try:
            div_err = self.browser.find_element_by_class_name('error-msg')
            if div_err.text.find('稍后再试') != -1:
                # back and retry
                self.__logger.error("Fxxk damai's potato server. retrying.")
                self.__jump_to_ticket()
                return False
            div_err = self.browser.find_element_by_class_name('next-feedback-title-content')
            if div_err.text.find('稍后再试') != -1:
                # back and retry
                self.__logger.error("Fxxk damai's potato server. retrying.")
                self.__jump_to_ticket()
                return False
        except selenium.common.exceptions.NoSuchElementException:
            pass

        return True

    def __order_ticket(self):
        self.__logger.info('Start order process')
        if self.browser.title.find('确认订单') == -1:
            self.__logger.error('Order err. Wrong page.')
            return False

        try:
            btn_order = self.browser.find_element_by_class_name('submit-wrapper').find_element_by_class_name('next-btn')
        except selenium.common.exceptions.NoSuchElementException:
            self.__logger.error('Order err. Cannot order.')
            return False

        btn_order.click()
        self.__logger.info('Finish order process')

        try:
            result = WebDriverWait(self.browser, 20).until(title_contains('支付宝'))
        except selenium.common.exceptions.TimeoutException:
            self.__logger.error('Jump to Alipay timeout, order may failed. retry order')
            return False

        if result:
            self.__logger.info('Order Success')
        else:
            self.__logger.error('Jump to Alipay failed, order may failed. retry order')
        return result


def main(argv):
    kQRPicPath = 'QR.png'
    kCookiesPath = 'cookies.json'
    kLogPath = 'test.log'
    kTicketUrl = 'https://detail.damai.cn/item.htm?spm=a2oeg.home.card_0.ditem_4.715223e1babBKN&id=594317472320'

    def get_logger(log_file):
        import logging
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

    options = selenium.webdriver.ChromeOptions()
    options.add_argument('headless')
    browser = selenium.webdriver.Chrome(options=options)

    bull = YellowBull(browser, kTicketUrl, kQRPicPath, kCookiesPath, get_logger(kLogPath))

    bull.login()
    print(bull.check_login())

    bull.catch_ticket('8月22-23日套票，包含两张门票', '499元', 2)


if __name__ == '__main__':
    main(sys.argv)
