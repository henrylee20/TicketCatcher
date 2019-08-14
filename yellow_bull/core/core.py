import abc
import selenium.webdriver


class YellowBullCore:
    def __init__(self, browser: selenium.webdriver.Chrome, site_root_url: str, ticket_url: str, logger):
        self.browser = browser
        self.ticket_url = ticket_url

        self.browser.get(site_root_url)
        self.browser.set_window_size(1920, 1080)

        self.logger = logger

        self.__fill_ticket_info_process = list()
        self.__fill_ticket_info_process_args = list()
        self.__fill_ticket_info_process_kwargs = list()

        self.__fill_order_info_process = list()
        self.__fill_order_info_process_args = list()
        self.__fill_order_info_process_kwargs = list()

    @abc.abstractmethod
    def catch_ticket(self, config: dict):
        pass

    @abc.abstractmethod
    def supported_ticket_info(self) -> list:
        pass

    @abc.abstractmethod
    def supported_order_info(self) -> list:
        pass

    def _catch_ticket_process(self):
        if not self.__fill_ticket_info_process:
            self.logger.warning("No ticket info fill process.")
        if not self.__fill_order_info_process:
            self.logger.warning("No order info fill process.")

        while True:
            self.__jump_to_ticket()

            self.logger.info('Try catching.')
            if not self.__is_order_available():
                self.logger.info('Not start yet. Refreshing page.')
                continue

            self.logger.info('Start. Filling ticket info.')
            for i in range(len(self.__fill_ticket_info_process)):
                process = self.__fill_ticket_info_process[i]
                args = self.__fill_ticket_info_process_args[i]
                kwargs = self.__fill_ticket_info_process_kwargs[i]
                process(*args, **kwargs)

            self.logger.info('Trying to order.')
            self.__click_order_button()

            self.logger.info('Checking order page.')
            if not self.__is_in_order_page():
                self.logger.warning('Can not jump to order page, catching failed. Restart catch.')
                continue

            self.logger.info('Ordering. Filling order info.')
            for i in range(len(self.__fill_order_info_process)):
                process = self.__fill_order_info_process[i]
                args = self.__fill_order_info_process_args[i]
                kwargs = self.__fill_order_info_process_kwargs[i]
                process(*args, **kwargs)

            self.logger.info('Trying to pay.')
            self.__click_pay_button()

            self.logger.info('Checking pay page.')
            if not self.__is_in_pay_page():
                self.logger.warning('Can not jump to pay page, catching failed. Restart catch.')
                continue
            else:
                break

        self.logger.info('Saving Pay QR picture. Catch success.')
        self.__save_pay_info()
        return

    def _add_ticket_info_process(self, process, *args, **kwargs):
        self.__fill_ticket_info_process.append(process)
        self.__fill_ticket_info_process_args.append(args)
        self.__fill_ticket_info_process_kwargs.append(kwargs)

    def _add_order_info_process(self, process, *args, **kwargs):
        self.__fill_order_info_process.append(process)
        self.__fill_order_info_process_args.append(args)
        self.__fill_order_info_process_kwargs.append(kwargs)

    @abc.abstractmethod
    def __sign_in(self) -> bool:
        pass

    @abc.abstractmethod
    def __is_signed_in(self) -> bool:
        pass

    @abc.abstractmethod
    def __jump_to_ticket(self):
        pass

    @abc.abstractmethod
    def __is_order_available(self) -> bool:
        pass

    @abc.abstractmethod
    def __click_order_button(self):
        pass

    @abc.abstractmethod
    def __is_in_order_page(self) -> bool:
        pass

    @abc.abstractmethod
    def __click_pay_button(self):
        pass

    @abc.abstractmethod
    def __is_in_pay_page(self) -> bool:
        pass

    @abc.abstractmethod
    def __save_pay_info(self):
        pass
