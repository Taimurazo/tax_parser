from time import sleep
import logging
import requests
from math import ceil
from transliterate import translit, detect_language
from tax_parser.file_reader import XlsFileReader



# todo
#  add test for wait condition.
#

def custom_translit(text):
    """
    Транслитерация текса на русский язык. Слово <<Company>> переводит как <<Компания>>.
    :param text: переменная с исходным текстом для транслитерации.
    :return: транслированный текст.
    """
    result = ''
    words = text.split()
    for word in words:
        if detect_language(word) != 'ru':
            if word.upper() == 'COMPANY':
                word = 'Компания'
            else:
                word = translit(word, 'ru')

        result += word + ' '
    result = result[:len(result) - 1]  # slice last space
    return result


class TaxParser:

    def __init__(self):
        self._excel_file = XlsFileReader()
        self._input_companies = []
        self._get_input_comany_list()

    def _get_input_comany_list(self):
        data = self._excel_file.read_file()
        self._input_companies = data['B']

    def _get_remote_data(self, comp_name):
        lines_per_page = 20
        result_list = []

        def send_request(name, page):
            post_url = 'https://egrul.nalog.ru/'
            get_url = 'https://egrul.nalog.ru/search-result/'

            # get request key
            payload = {
                'query': name,
                'page': page,
                'nameEq': 'on'

            }
            result = requests.post(url=post_url, data=payload)

            # get results
            request_key = result.json()['t']

            response = requests.get(get_url + request_key)

            if response.json().get('status') == 'wait':
                status = 'wait'
                while status == 'wait':
                    sleep(2)
                    response = requests.get(get_url + request_key)

            return response

        response = send_request(comp_name, 1)
        response_data = response.json()['rows']
        total = int(response_data[0]['tot'])  # get total elements count from first element
        pages = ceil(total / lines_per_page)

        for page in range(pages):  # all pages, except first page
            page += 1
            response = send_request(comp_name, page)
            response_data = response.json()['rows']
            result_list += response_data
            sleep(1)
        return result_list

    # a - adress
    # i - inn
    # n - name

    def test_request(self):
        print(self._get_remote_data('star'))

    def parse(self):
        for comp_name, comp_adress in self._input_companies:
            remote_data = self._get_remote_data(comp_name, comp_adress)
            found_data = self._find_matches(comp_name, comp_adress)
            self._add_to_result(found_data)
        self.save_data()


if __name__ == '__main__':
    TaxParser().test_request()
