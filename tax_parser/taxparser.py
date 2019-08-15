from pprint import pprint
from time import sleep
import logging
import requests
from math import ceil
from transliterate import translit, detect_language
from tax_parser.file_reader import XlsFileReader


# todo
#  add test for wait condition.
#  add input data preprocessor. +
#  add transliteration
#  add adress compartion
#  add file saving


# отказался от обработки строк сразу после чтения данных из файла. Буду их обрабатывать непосредственно перед поиском.
# Таким образом я избавился от лишнего обхода по данным.

# Перед каждой идеей спрашивай себя " А какие в ней недостатки?".

# Обрабатывай случаи когда приходит пустой ответ!!!!!

#  !!! Рассказать о не правильной транслитерации c = > к


class TaxParser:

    def __init__(self):
        self._excel_file = XlsFileReader()
        self._input_companies = []
        self._get_input_comany_list()

    def _get_input_comany_list(self):
        data = self._excel_file.read_file()
        self._input_companies = data

    @classmethod
    def string_preprocessor(cls, string):
        result = ''
        symbols_map = {'«': '"', '»': '"'}
        for symbol in symbols_map.keys():
            string = string.replace(symbol, symbols_map[symbol])

        for word in string.split():
            result += word + ' '
        result = result[:len(result) - 1]  # remove last space.
        return result

    @classmethod
    def custom_translit(cls, text):
        """
        Транслитерация текса на русский язык. Слово <<Company>> переводит как <<Компания>>.
        :param text: переменная с исходным текстом для транслитерации.
        :return: транслированный текст.
        """
        result = ''
        words = text.split()
        for word in words:
            word = word.upper().replace('COMPANY', 'КОМПАНИЯ')
            if detect_language(word) != 'ru':
                word = translit(word, 'ru')
            result += word + ' '
        result = result[:len(result) - 1]  # slice last space
        return result

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

        pages = 0

        if len(response_data) != 0:
            total = int(response_data[0]['tot'])  # get total elements count from first element
            pages = ceil(total / lines_per_page)

        for page in range(pages):  # all pages, except first page
            page += 1
            response = send_request(comp_name, page)
            response_data = response.json()['rows']
            result_list += response_data
            sleep(1)
        return result_list

    def _compare_names(self, first_name, second_name):
        return first_name == second_name

    def _compare_adresses(self, first_adress, second_adress):
        return True

    def _find_matches(self, name, adress, remote_data):
        name = name.upper()

        statuses = {
            'accurate': 'точное совпадение',
            'inaccurate': 'неточное совпадение',
            'not_found': 'не найдено'
        }

        match_list = []
        for element in remote_data:
            if self._compare_names(element['n'], name) and self._compare_adresses(adress, element['a']):
                match_list.append(element)

        result = {
            'status': statuses['accurate'],
            'result': match_list,
        }

        if len(match_list) > 1:  # if math not accurate changing status.
            result['status'] = statuses['inaccurate']
        elif len(match_list) == 0:
            result['status'] = statuses['not_found']
        return result

    def parse(self):
        for i in range(len(self._input_companies['A'])):
            comp_name = self._input_companies['A'][i]
            comp_adress = self._input_companies['B'][i]
            comp_name = self.string_preprocessor(comp_name)  # remove excess quotes and spaces
            remote_data = self._get_remote_data(comp_name)  # data from web site

            comp_name = TaxParser.custom_translit(comp_name)
            found_data = self._find_matches(comp_name, comp_adress, remote_data)
            print('====================================== NAME %s' % comp_name)
            print('STATUS: %s' % found_data['status'])
            for comp in found_data['result']:
                pprint(comp['n'])
            sleep(1)  # avoiding site blocking
            # self._add_to_result(found_data)

        # find the place of matched data after matching operation !!!

        # self.save_data()


def test_data_match():
    tp = TaxParser()
    tp.parse()
    # adress = '457040 ЧЕЛЯБИНСКАЯ ОБЛАСТЬ ГОРОД ЮЖНОУРАЛЬСК УЛИЦА СТАНИЧНАЯ 58'
    # remote_data = self._get_remote_data(name)
    # res = self._find_matches(name, adress, remote_data)
    # print(res)


def test_data_preprocessor():
    tp = TaxParser()
    name = 'АО  «ЦТК»'
    print('old:  %s ' % name)
    print('new:  %s ' % tp.string_preprocessor(name))


def test_translit():
    names = 'АО  «ЦТК»'


if __name__ == '__main__':
    # test_data_preprocessor()
    test_data_match()
