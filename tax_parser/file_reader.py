from pprint import pprint

from xlrd import open_workbook
from xlrd.sheet import XL_CELL_NUMBER
from xlwt import Workbook
import logging


class XlsFileReader:

    def __init__(self, filename):
        self._filename = filename

    def _numsym(self, number):
        alphabet = "ABCDEFGHIJKLMNOP"
        return alphabet[number]

    def _symnum(self, symbol):
        alphabet = "ABCDEFGHIJKLMNOP"
        return alphabet.find(symbol)

    def read_file(self):
        result = {}
        try:
            self._rb = open_workbook(filename=self._filename, formatting_info=True)
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

    def write_file(self, data):
        wb = Workbook()
        ws = wb.add_sheet('A Test Sheet')
        rows_count = len(data[list(data.keys())[0]])
        for key in data.keys():
            for row_number in range(rows_count):
                coll_number = self._symnum(key)
                cell_value = str(data[key][row_number])
                ws.write(row_number + 1, coll_number, cell_value)
        wb.save('../data.xls')


if __name__ == '__main__':
    f = XlsFileReader('../data.xls')
    data = f.read_file()
    f.write_file(data)
