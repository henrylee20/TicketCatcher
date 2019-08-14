import os
import json
import time
import logging
import selenium.common
import selenium.webdriver

from selenium.webdriver.support.expected_conditions import title_contains
from selenium.webdriver.support.ui import WebDriverWait

from ..core import YellowBullCore
from .order_info_process import OrderInfoProcess
from .ticket_info_process import TicketInfoProcess


kDamaiUrl = 'https://www.damai.cn/'
kLoginUrl = 'https://passport.damai.cn/login?ru=https%3A%2F%2Fwww.damai.cn%2F'


class DamaiCore(YellowBullCore):
    def __init__(self, browser: selenium.webdriver.Chrome, ticket_url: str,
                 cookie_filename, sign_in_qr_filename, pay_qr_filename, logger=logging):
        super().__init__(browser, kDamaiUrl, ticket_url, logger)

        self.cookie_filename = cookie_filename
        self.sign_in_qr_filename = sign_in_qr_filename
        self.pay_qr_filename = pay_qr_filename

    def catch_ticket(self, config: dict):
        ticket_processes = TicketInfoProcess.processes()
        order_processes = OrderInfoProcess.processes()

        for k, v in config.items():
            if k in ticket_processes.keys():
                super()._add_ticket_info_process(ticket_processes[k], key=k, val=v)
            elif k in order_processes.keys():
                super()._add_order_info_process(order_processes[k], key=k, val=v)

        super()._catch_ticket_process()

    def supported_ticket_info(self) -> list:
        return list(TicketInfoProcess.processes().keys())

    def supported_order_info(self) -> list:
        return list(OrderInfoProcess.processes().keys())

    def __sign_in(self) -> bool:
        return self.__cookie_sign_in() or self.__qr_sign_in()

    def __is_signed_in(self) -> bool:
        login_text = self.browser.find_element_by_class_name('span-user').text
        return login_text != '登录'

    def __jump_to_ticket(self):
        self.browser.get(self.ticket_url)
        if not self.__is_signed_in():
            self.logger.info("Not signed in. Now try to sign in")
            self.__sign_in()
            self.browser.get(self.ticket_url)
        self.browser.implicitly_wait(1)

    def __is_order_available(self) -> bool:
        btn_buy = self.browser.find_element_by_class_name('buybtn')
        if btn_buy.text.find('立即') != -1:
            return True
        else:
            self.logger.info('Order not available. Text: %s', btn_buy.text)
            return False

    def __click_order_button(self):
        js2 = "var q=document.getElementsByClassName('buybtn')[0].click()"
        self.browser.execute_script(js2)
        self.browser.implicitly_wait(1)

    def __is_in_order_page(self) -> bool:
        if not self.__check_jump_to_order_err():
            return False

        for i in range(5):
            if self.browser.title.find('确认订单') == -1:
                if i < 4:
                    time.sleep(0.25)
                    self.logger.info("Retrying.")
                    continue
                else:
                    self.logger.error('Order err. Wrong page. Title: %s', self.browser.title)
                    return False
            else:
                break

        try:
            btn_order = self.browser.find_element_by_class_name('submit-wrapper').find_element_by_class_name('next-btn')
        except selenium.common.exceptions.NoSuchElementException:
            self.logger.error('Order err. Order button not found.')
            return False
        return True

    def __click_pay_button(self):
        btn_order = self.browser.find_element_by_class_name('submit-wrapper').find_element_by_class_name('next-btn')
        btn_order.click()

    def __is_in_pay_page(self) -> bool:
        try:
            result = WebDriverWait(self.browser, 20).until(title_contains('支付宝'))
        except selenium.common.exceptions.TimeoutException:
            self.logger.error('Jump to Alipay timeout, order may failed. retry order')
            return False

        if result:
            self.logger.info('Order Success')
        else:
            self.logger.error('Jump to Alipay failed, order may failed. retry order')
        return result

    def __save_pay_info(self):
        self.browser.save_screenshot(self.pay_qr_filename)

    def __cookie_sign_in(self) -> bool:
        if not os.path.exists(self.cookie_filename):
            self.logger.warning("Cookies not found")
            return False

        self.logger.info("Found login cookies at: %s", self.cookie_filename)
        with open(self.cookie_filename, 'r', encoding='utf-8') as fp:
            cookies_json = fp.read()
        self.logger.debug(cookies_json)

        cookies = json.loads(cookies_json)
        for cookie in cookies:
            if 'expiry' in cookie:
                del cookie['expiry']
            self.browser.add_cookie(cookie)
        self.browser.refresh()
        return True

    def __qr_sign_in(self) -> bool:
        self.logger.info("Using QR Code login. QR picture save to: %s", self.sign_in_qr_filename)
        self.browser.get(kLoginUrl)
        while self.browser.title != '大麦登录':
            self.logger.info('Waiting for login page')
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
                self.browser.save_screenshot(self.sign_in_qr_filename)

        while len(self.browser.window_handles) > 1:
            self.logger.info("Waiting for scan")
            time.sleep(1)

        self.logger.info("Scanned")
        self.browser.switch_to.window(now)

        cookies_json = json.dumps(self.browser.get_cookies())
        with open(self.cookie_filename, 'w', encoding='utf-8') as fp:
            fp.write(cookies_json)

        return True

    def __check_jump_to_order_err(self):
        try:
            div_err = self.browser.find_element_by_class_name('error-msg')
            if div_err.text.find('稍后再试') != -1:
                self.logger.error("Fxxk damai's potato server. retrying.")
                return False
            div_err = self.browser.find_element_by_class_name('next-feedback-title-content')
            if div_err.text.find('稍后再试') != -1:
                self.logger.error("Fxxk damai's potato server. retrying.")
                return False
        except selenium.common.exceptions.NoSuchElementException:
            pass

        return True
