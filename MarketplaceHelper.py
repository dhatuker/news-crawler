import re
import urllib

from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys


class ClickHelper(object):

    @staticmethod
    def scroll_shim(driver, obj):
        x = obj.location['x']
        y = obj.location['y']
        scroll_by_coord = 'window.scrollTo({},{});'.format(x, y)
        scroll_nav_out_of_way = 'window.scrollBy(0, -120);'
        driver.execute_script(scroll_by_coord)
        driver.execute_script(scroll_nav_out_of_way)

    @staticmethod
    def click_input_element(driver, input_element):
        if 'firefox' in driver.capabilities['browserName']:
            ClickHelper.scroll_shim(driver, input_element)
        # driver.execute_script("arguments[0].scrollIntoView();", input_element)
        action_chains = ActionChains(driver)
        # move to element
        action_chains.move_to_element(input_element).click(input_element)
        # execute
        action_chains.perform()

    @staticmethod
    def scroll_to_element(driver, input_element):
        driver.execute_script("arguments[0].scrollIntoView();", input_element)

    @staticmethod
    def click_type_enter_shopee(driver, input_element, keyword):
        input_element.clear()
        action_chains = ActionChains(driver)
        action_chains.move_to_element(input_element).click(input_element).perform()
        # self.driver.execute_script("arguments[0].value='%s';" % keyword, inputElement)
        # send/type keys
        searched_keyword = input_element.get_attribute("value").strip()
        if searched_keyword:
            for _ in searched_keyword:
                action_chains.send_keys(Keys.BACKSPACE)
            action_chains.send_keys(Keys.RETURN).send_keys(Keys.RETURN).perform()

        for char in keyword:
            if char == ' ':
                action_chains.send_keys(Keys.SPACE)
            else:
                action_chains.send_keys(char)
        action_chains.send_keys(Keys.RETURN).perform()

    @staticmethod
    def click_type_enter_tokopedia(driver, input_element, keyword):
        input_element.clear()
        action_chains = ActionChains(driver)
        action_chains.move_to_element(input_element).click(input_element).perform()
        # self.driver.execute_script("arguments[0].value='%s';" % keyword, inputElement)
        # send/type keys
        for char in keyword:
            if char == ' ':
                action_chains.send_keys(Keys.SPACE)
            else:
                action_chains.send_keys(char)
        action_chains.send_keys(Keys.RETURN).perform()

    @staticmethod
    def move_to_element(driver, input_element):
        action_chains = ActionChains(driver)
        action_chains.move_to_element(input_element).perform()


class ProductParsing(object):

    @staticmethod
    def parse_ml(title):
        number_mls = re.findall(r"([0-9]+)\s*ml", title.lower())
        if number_mls is not None and len(number_mls) > 0:
            # print("title: %s\n   ml's:" % title, ",".join(set(numberMls)))
            # self.logger.error("title: %s\n   mls: %s" % (title, ",".join(set(numberMls))))
            return number_mls[0]
        else:
            return None

    @staticmethod
    def parse_mg(title):
        number_mgs = re.findall(r"([0-9]+)\s*mg", title.lower())
        if number_mgs is not None and len(number_mgs) > 0:
            # print("title: %s\n   ml's:" % title, ",".join(set(numberMls)))
            # self.logger.error("title: %s\n   mgs: %s" % (title, ",".join(set(numberMls))))
            return number_mgs[0]
        else:
            return None

    @staticmethod
    def parse_pod(title):
        pods = re.findall(r"\b(pod[s]*)\b", title.lower())
        if pods is not None and len(pods) > 0:
            # print("title: %s\n   ml's:" % title, ",".join(set(numberMls)))
            # if ",".join(set(numberMls)) == 'pods':
            # self.logger.error("title: %s\n   pod: %s" % (title, ",".join(set(numberMls))))
            return True
        else:
            return False

    @staticmethod
    def parse_pack(title):
        packs = re.findall(r"\b(pack[s]*)\b", title.lower())
        if packs is not None and len(packs) > 0:
            # print("title: %s\n   ml's:" % title, ",".join(set(numberMls)))
            # if ",".join(set(numberMls)) == 'pods':
            # self.logger.error("title: %s\n   pack: %s" % (title, ",".join(set(numberMls))))
            return True
        else:
            return False

    @staticmethod
    def parse_closed_system(title):
        closed_systems = re.findall(r"\b(close[d]?\s*system[s]?)\b", title.lower())
        if closed_systems is not None and len(closed_systems) > 0:
            # print("title: %s\n   ml's:" % title, ",".join(set(numberMls)))
            # if ",".join(set(numberMls)) == 'pods':
            # self.logger.error("title: %s\n   closedsystem: %s" % (title, ",".join(set(numberMls))))
            return True
        else:
            return False

    @staticmethod
    def parse_store_name(url):
        o = urllib.parse.urlparse(url)
        # self.logger.info("%s => %s" % (url, o.path))
        if o.path is not None and len(o.path) > 0:
            match = re.search(r"^[/]([^/]+)[/].+", o.path)
            if match:
                # print(match.group(1),"<=",url)
                return match.group(1)

    @staticmethod
    def parse_value_of_number(num_str):
        num_str = num_str.strip()
        if 'rb' in num_str:
            num_str = num_str.replace('rb', '').replace(',', '.')
            return int(float(num_str) * 1000)
        elif 'jt' in num_str:
            num_str = num_str.replace('jt', '').replace(',', '.')
            return int(float(num_str) * 1000000)
        elif '' == num_str:
            return 0
        else:
            return int(num_str)

    @staticmethod
    def parse_price(num_str):
        if '.' in num_str:
            num_str = num_str.replace('.', '')
        return int(num_str)
