from .core import DamaiCore
from ..process import Process
import selenium.common.exceptions


class TicketInfoProcess(Process):
    __processes = None

    @staticmethod
    def processes() -> dict:
        if not TicketInfoProcess.__processes:
            TicketInfoProcess.__processes = {
                '特权码': TicketInfoProcess.set_privilege_code,
                '场次': TicketInfoProcess.set_perform_ticket_info,
                '票档': TicketInfoProcess.set_perform_ticket_info,
                '数量': TicketInfoProcess.set_ticket_num,
            }
        return TicketInfoProcess.__processes

    @staticmethod
    def set_privilege_code(core: DamaiCore, val):
        try:
            input_privilege_val = core.browser.find_element_by_id('privilege_val')
            input_privilege_val.send_keys(val)
            btn_privilege_sub = core.browser.find_element_by_class_name('privilege_sub')
            btn_privilege_sub.click()
        except selenium.common.exceptions.NoSuchElementException:
            core.logger.warning('privilege code input box not found.')

    @staticmethod
    def set_perform_ticket_info(core: DamaiCore, key, val):
        try:
            if not TicketInfoProcess.__set_perform_infos(core, key, val):
                core.logger.warning('Ticket info [%s] not found. using default.', key)
        except selenium.common.exceptions.NoSuchElementException:
            core.logger.warning('Ticket info [%s] select boxes not found.', key)

    @staticmethod
    def set_ticket_num(core: DamaiCore, val):
        core.logger.info('Trying to set number of tickets: %d', val)
        try:
            input_ticket_num = core.browser.find_element_by_class_name('cafe-c-input-number-input')
            input_ticket_num.clear()
            input_ticket_num.send_keys(str(val))
        except selenium.common.exceptions.NoSuchElementException:
            core.logger.warning('ticket num input box not found.')

    @staticmethod
    def __set_perform_infos(core: DamaiCore, key, val):
        div_perform_infos = core.browser.find_elements_by_class_name('perform__order__select')
        core.logger.debug('Trying to set perform infos. Number of type: %d', len(div_perform_infos))
        for div_perform_info in div_perform_infos:
            div_info_name = div_perform_info.find_element_by_class_name('select_left')
            div_info_vals = div_perform_info.find_elements_by_class_name('select_right_list_item')
            core.logger.debug('Trying to set %s', div_info_name.text)

            if div_info_name.text.find(key) != -1:
                core.logger.info("Ticket info [%s] found: [%s]", key, div_info_name.text)
                return TicketInfoProcess.__choose_one_perform_info(core, div_info_vals, val)
        core.logger.warning('ticket info key [%s] not found', key)
        return False

    @staticmethod
    def __choose_one_perform_info(core: DamaiCore, div_info_vals, val):
        found = False
        for div_info_val in div_info_vals:
            if div_info_val.text.find(val) != -1:
                core.logger.info("Ticket info selecting [%s].", div_info_val.text)
                div_info_val.click()
                found = True
                core.browser.implicitly_wait(1)
                break
        return found
