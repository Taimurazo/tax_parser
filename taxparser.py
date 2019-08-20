from pprint import pprint
from time import sleep
import logging
import requests
from math import ceil
from transliterate import translit, detect_language
from file_reader import XlsFileReader

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


# Рассказать о максимальном количестве страниц.

# Рассказать об ограничениях по времени


REQUEST_DEALY = 2
LINES_PER_PAGE = 20


class TaxParser:

    def __init__(self):
        self._excel_file = XlsFileReader(input_filename='data.xls', output_filename='data_output.xls')
        self._excel_file_part = XlsFileReader(input_filename='data.xls', output_filename='data_output_part.xls')
        self._excel_file_part.read_file()

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
        result_list = []

        def send_request(name, page):

            post_url = 'https://egrul.nalog.ru/'
            get_url = 'https://egrul.nalog.ru/search-result/'
            result = []

            # get request key
            payload = {
                'query': name,
                'page': page,
                'nameEq': 'on'

            }
            try:
                result = requests.post(url=post_url, data=payload)
                # get results
                request_key = result.json()['t']

                response = requests.get(get_url + request_key)
                # print("second request " , response.status_code)

                if response.json().get('status') == 'wait':
                    status = 'wait'
                    while status == 'wait':
                        sleep(REQUEST_DEALY)
                        response = requests.get(get_url + request_key)
                else:
                    result = response.json().get('rows')
            except Exception as e:
                pass
            return result

        response_data = send_request(comp_name, 1)

        return response_data

    def _compare_names(self, first_name, second_name):
        return first_name == second_name

    def _compare_adresses(self, first_adress, second_adress):
        return True

    def _find_matches(self, name, adress, remote_data):
        name = name.upper()

        statuses = {
            'accurate': 'точное совпадение',
            'inaccurate': 'неточное совпадение',
            'not_found': 'не найдено',
            'gt_five': 'более пяти элементов'
        }

        result = {
            'status': statuses['accurate'],
            'result': [],
        }

        if len(remote_data) == 0:
            result['status'] = statuses['not_found']
            result['result'] = []
            return result

        for element in remote_data:
            if self._compare_names(element['n'], name) and self._compare_adresses(adress, element['a']):
                result['status'] = statuses['accurate']
                result['result'] = [element, ]
                return result
            else:
                result['result'].append(element)

        if len(result['result']) > 5:
            result['result'] = result['result'][:5]
            result['status'] = statuses['gt_five']
            return result

        result['status'] = statuses['inaccurate']
        return result

    def _add_to_result(self, index, found_data):
        self._input_companies['D'][index] = found_data['status']  # Результат
        self._excel_file_part.write_part(index + 1, 'D', found_data['status'])

        for data in found_data['result']:
            self._input_companies['C'][index] += data.get('i', 'значение отсутствует') + '\n'  # INN
            self._input_companies['B'][index] += data.get('n', 'значение отсутствует') + '\n'  # NAMES
        self._excel_file_part.write_part(index + 1, 'C', self._input_companies['C'][index])
        self._excel_file_part.write_part(index + 1, 'B', self._input_companies['B'][index])

    def save_data(self):
        self._excel_file.write_file(self._input_companies)

    def parse(self):
        for i in range(len(self._input_companies['A'])):
            comp_name = self._input_companies['A'][i]
            comp_adress = self._input_companies['B'][i]
            comp_name = self.string_preprocessor(comp_name)  # remove excess quotes and spaces
            if comp_name != '':
                print("=========== #%d %s " % (i, comp_name))
                print("   - Получение данных ...")
                remote_data = self._get_remote_data(comp_name)  # data from web site
                comp_name = TaxParser.custom_translit(comp_name)
                print("   - Сравнение данных ...")
                found_data = self._find_matches(comp_name, comp_adress, remote_data)
                sleep(REQUEST_DEALY)  # avoiding site blocking
                self._add_to_result(i, found_data)
            else:
                print('Пустое название организации.')
        print("Сохранение всех данных в файл ...")
        self.save_data()
        print("Конец. Пара - пара - пам!")



if __name__ == '__main__':
    tp = TaxParser()
    tp.parse()
