from .core import DamaiCore
import selenium.common.exceptions

from ..process import Process


class OrderInfoProcess(Process):
    __processes = None

    @staticmethod
    def processes() -> dict:
        if OrderInfoProcess.__processes is None:
            OrderInfoProcess.__processes = {
                '配送方式': OrderInfoProcess.select_delivery_way,
                '观演人': OrderInfoProcess.select_buyers,
            }
        return OrderInfoProcess.__processes

    @staticmethod
    def select_delivery_way(core: DamaiCore, val: str):
        try:
            div_way_list = core.browser.find_element_by_class_name('dm-delivery-way').find_element_by_class_name('way-list').find_elements_by_class_name('way-item')
            core.logger.info("Num of ways: %d", len(div_way_list))
            for div_way in div_way_list:
                if div_way.find_element_by_class_name('way-title').text.find(val) != -1:
                    div_way.find_element_by_class_name('way-image').click()
                    return
            core.logger.warning('delivery way [%s] not found. using default info.', val)
        except selenium.common.exceptions.NoSuchElementException:
            core.logger.warning('delivery select boxes not found.')

    @staticmethod
    def select_buyers(core: DamaiCore, val: list):
        selected = list()
        try:
            div_buyer_list = core.browser.find_element_by_class_name("dm-ticket-buyer").find_element_by_class_name('ticket-buyer-select').find_elements_by_class_name("buyer-list-item")
            core.logger.info("Num of buyer: %d", len(div_buyer_list))
            for div_buyer in div_buyer_list:
                # select all if names is empty
                if not val or div_buyer.find_element_by_class_name('next-checkbox-label').text in val:
                    if div_buyer.get_attribute("class").find("checked") == -1:
                        div_buyer.click()
                        selected.append(div_buyer.find_element_by_class_name('next-checkbox-label').text)
        except selenium.common.exceptions.NoSuchElementException:
            core.logger.warning('buyers select boxes not found.')
        core.logger.info("selected buyers: %s.", str(selected))
