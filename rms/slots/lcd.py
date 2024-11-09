from random import randint
from PyQt5.QtCore import pyqtSlot
from . import Slots
from .lib import RGB1602
from constants import SORT_MODE__LAPTIME


class LCD(Slots):

    LINE_LENGTH = 16

    def __init__(self, rms_signals, database):
        super().__init__(rms_signals, database)
        self.lcd = RGB1602.RGB1602(16, 2)
        self.tn = self.database.getConfigStr('TRACKNAME')
        self.tl = self.database.getConfigStr('TRACKLENGTH')

    def _print_to_line(self, line, text):
        self.lcd.setCursor(0, line)
        self.lcd.printout(' ' * self.LINE_LENGTH)
        self.lcd.setCursor(0, line)
        self.lcd.printout(text[0:self.LINE_LENGTH])

    def _print_time(self, line, pos, name, time):
        self.lcd.setCursor(0, line)
        self.lcd.printout(' ' * self.LINE_LENGTH)
        str_time = str(time)
        len_time = len(str_time)
        start_time = self.LINE_LENGTH - len_time
        name_length = self.LINE_LENGTH - 3 - len_time
        str_name = str(name)
        name_trim = str_name[0:name_length]
        self.lcd.setCursor(0, line)
        self.lcd.printout(f'{pos} {name_trim}')
        self.lcd.setCursor(start_time, line)
        self.lcd.printout(str_time)

    @pyqtSlot()
    def idle_slot(self):
        choices = [
            f'{self.tl} mm', 'KEEP ON RACING', 'RACE TIME IS NOW'
        ]
        self.lcd.setColorWhite()
        self._print_to_line(0, self.tn)
        self._print_to_line(1, choices[randint(0, len(choices) - 1)])

    @pyqtSlot(str, int)
    def home_slot(self, track_name, track_length):
        self.lcd.setColorWhite()
        self._print_to_line(0, track_name)
        self._print_to_line(1, str(track_length) + ' mm')

    @pyqtSlot(int)
    def start_sequence_slot(self, number):
        if number not in [0, 2, 3, 4, 5, 6, 100]:
            return
        start_in = self.tr('Start in')
        if number == 2:
            self.lcd.setRGB(255, 0, 0)
            self._print_to_line(1, f'{start_in}: 5')
        elif number == 3:
            self.lcd.setRGB(255, 0, 0)
            self._print_to_line(1, f'{start_in}: 4')
        elif number == 4:
            self.lcd.setRGB(255, 0, 0)
            self._print_to_line(1, f'{start_in}: 3')
        elif number == 5:
            self.lcd.setRGB(255, 0, 0)
            self._print_to_line(1, f'{start_in}: 2')
        elif number == 6:
            self.lcd.setRGB(255, 0, 0)
            self._print_to_line(1, f'{start_in}: 1')
        elif number == 0:
            self.lcd.setRGB(255, 255, 0)
            self._print_to_line(1, self.tr('False start'))
        elif number == 100:
            self.lcd.setRGB(0, 255, 0)
            self._print_to_line(1, self.tr('GO GO GO!'))
        self._print_to_line(0, self.tn)

    @pyqtSlot(dict, int)
    def competition_progress_slot(self, results, mode):
        line_1 = [1, None, None]
        line_2 = [2, None, None]
        m_1 = []
        for addr, result in results.items():
            if result['rank'] == 1:
                m_1.append(addr)
        if len(m_1) > 1:
            result = results[m_1[0]]
            time = result['time']
            if mode == SORT_MODE__LAPTIME:
                time = result['bestlap']
            line_1 = [1, result["driver"]["name"], time]
            result = results[m_1[1]]
            time = result['time']
            if mode == SORT_MODE__LAPTIME:
                time = result['bestlap']
            line_2 = [2, result["driver"]["name"], time]
        else:
            for addr, result in results.items():
                time = result['time']
                if mode == SORT_MODE__LAPTIME:
                    time = result['bestlap']
                if result['rank'] == 1:
                    line_1 = [1, result["driver"]["name"], time]
                if result['rank'] == 2:
                    line_2 = [2, result["driver"]["name"], time]
        self._print_time(0, line_1[0], line_1[1], line_1[2])
        self._print_time(1, line_2[0], line_2[1], line_2[2])
