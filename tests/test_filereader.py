import pytest
import filecmp
from tax_parser.file_reader import XlsFileReader

def test_output_file_compare():
    f = XlsFileReader(input_filename='control_input.xls', output_filename='test_output.xls')
    data = f.read_file()
    f.write_file(data)
    assert filecmp.cmp('test_output.xls', 'control_input.xls'), 'files not equal'



