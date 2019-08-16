from pprint import pprint

import xlwt
from xlutils.copy import copy
from xlrd import open_workbook
from xlrd.sheet import XL_CELL_NUMBER
from xlutils.styles import Styles

import logging


class XlsFileReader:

    def __init__(self, input_filename='../data.xls', output_filename='../data.xls'):
        self._input_filename = input_filename
        self._output_filename = output_filename
        self._styles = None

    def _numsym(self, number):
        alphabet = "ABCDEFGHIJKLMNOP"
        return alphabet[number]

    def _symnum(self, symbol):
        alphabet = "ABCDEFGHIJKLMNOP"
        return alphabet.find(symbol)

    def read_file(self):
        result = {}
        try:
            self._rb = open_workbook(filename=self._input_filename, formatting_info=True)
            self._styles = Styles(self._rb)
        except Exception as e:
            logging.error(e)

        if self._rb.nsheets != 0:
            sheet = self._rb.sheet_by_index(0)
            for colnum in range(sheet.ncols):
                tm_list = []
                for row in range(1, sheet.nrows):
                    if sheet.cell_type(row, colnum) == XL_CELL_NUMBER:
                        tm_list.append(int(sheet.cell_value(row, colnum)))
                    else:
                        tm_list.append(sheet.cell_value(row, colnum))
                result[self._numsym(colnum)] = tm_list
        else:
            logging.error('Empty file.')
        return result

    def _get_style(self, column):
        style = xlwt.XFStyle()
        pattern = xlwt.Pattern()
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        if column in 'BCD':
            pattern.pattern_fore_colour = xlwt.Style.colour_map['yellow']
        else:
            pattern.pattern_fore_colour = xlwt.Style.colour_map['turquoise']

        borders = xlwt.Borders()
        borders.left = 1
        borders.right = 1
        borders.top = 1
        borders.bottom = 1
        style.pattern = pattern
        style.borders = borders
        return style

    def write_file(self, data):
        self._wb = copy(self._rb)
        ws = self._wb.get_sheet(0)  # get first sheet
        rows_count = len(data[list(data.keys())[0]])
        for key in data.keys():
            coll_number = self._symnum(key)
            local_style = self._get_style(key)
            local_style.alignment.wrap = 1
            for row_number in range(rows_count):
                cell_value = str(data[key][row_number])
                ws.write(row_number + 1, coll_number, cell_value, style=local_style)
        self._wb.save(self._output_filename)


if __name__ == '__main__':
    f = XlsFileReader('../data.xls')
    data = f.read_file()
    f.write_file(data)
