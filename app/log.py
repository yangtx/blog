import os
import sys
import datetime


class PrettyPrintLog:
    def __init__(self):
        self._path = os.path.join(sys.path[0], 'Log')

        os.mkdir(self._path) if not os.path.exists(self._path) else None

    def write_2_file(self, string, _file=None):
        file_name = _file if _file else str(datetime.date.today())
        _file = os.path.join(self._path, '{}.txt'.format(file_name))
        with open(_file, mode='a', encoding='utf-8') as f:
            f.write(string + '\n')
            f.flush()

    def normal(self, s):
        '''Normal Log'''
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            raise Exception
        except:
            traceback_frame = sys.exc_info()[2].tb_frame.f_back
        line_no = traceback_frame.f_lineno
        file_path = str(traceback_frame.f_code.co_filename)
        file_name = os.path.split(file_path)[-1]
        output = '[Normal][{}  {}  Line:{}]  {}'.format(
            now, file_name, line_no, s)
        print(output)
        self.write_2_file(output)

    def error(self):
        '''Error Log'''
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        e_type, e_value, e_traceback = sys.exc_info()
        e_name = e_type.__name__
        file_name = e_traceback.tb_frame.f_code.co_filename
        line_no = e_traceback.tb_lineno
        output = '[Error ][{}  {}  line:{}]  {}:  {} '.format(
            now, file_name, line_no, e_name, e_value)
        print(output)
        self.write_2_file(output)
        self.write_2_file(output, 'error')
