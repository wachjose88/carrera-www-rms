from random import randint
from PyQt5.QtCore import pyqtSlot
from . import Slots
from constants import SORT_MODE__LAPTIME


class Console(Slots):

    LINE_LENGTH = 42

    def _build_text(self, text):
        length = self.LINE_LENGTH - 4
        end = ' ' * (length - len(text))
        print(f'# {text[:length]}{end} #')

    @pyqtSlot()
    def idle_slot(self):
        tn = self.database.getConfigStr('TRACKNAME')
        tl = self.database.getConfigStr('TRACKLENGTH')
        print('#' * self.LINE_LENGTH)
        self._build_text(tn)
        choices = [
            f'{tl} mm', 'GO GO GO', 'RACE TIME IS NOW'
        ]
        self._build_text(choices[randint(0, len(choices) - 1)])
        print('#' * self.LINE_LENGTH)

    @pyqtSlot(str, int)
    def home_slot(self, track_name, track_length):
        print('#' * self.LINE_LENGTH)
        self._build_text(track_name)
        self._build_text(str(track_length) + ' mm')
        print('#' * self.LINE_LENGTH)

    @pyqtSlot(int)
    def start_sequence_slot(self, number):
        if number not in [0, 2, 3, 4, 5, 6, 100]:
            return
        print('#' * self.LINE_LENGTH)
        start_in = self.tr('Start in')
        if number == 2:
            self._build_text(f'{start_in}: 5')
        elif number == 3:
            self._build_text(f'{start_in}: 4')
        elif number == 4:
            self._build_text(f'{start_in}: 3')
        elif number == 5:
            self._build_text(f'{start_in}: 2')
        elif number == 6:
            self._build_text(f'{start_in}: 1')
        elif number == 0:
            self._build_text(self.tr('False start'))
        elif number == 100:
            self._build_text(self.tr('GO GO GO!'))
        print('#' * self.LINE_LENGTH)

    @pyqtSlot(dict, int)
    def competition_progress_slot(self, results, mode):
        print('#' * self.LINE_LENGTH)
        line_1 = ''
        line_2 = ''
        m_1 = []
        for addr, result in results.items():
            if result['rank'] == 1:
                m_1.append(addr)
        if len(m_1) > 1:
            result = results[m_1[0]]
            time = result['time']
            if mode == SORT_MODE__LAPTIME:
                time = result['bestlap']
            line_1 = f'1: {result["driver"]["name"]} {time}'
            result = results[m_1[1]]
            time = result['time']
            if mode == SORT_MODE__LAPTIME:
                time = result['bestlap']
            line_2 = f'1: {result["driver"]["name"]} {time}'
        else:
            for addr, result in results.items():
                time = result['time']
                if mode == SORT_MODE__LAPTIME:
                    time = result['bestlap']
                if result['rank'] == 1:
                    line_1 = f'1: {result["driver"]["name"]} {time}'
                if result['rank'] == 2:
                    line_2 = f'2: {result["driver"]["name"]} {time}'
        self._build_text(line_1)
        self._build_text(line_2)
        print('#' * self.LINE_LENGTH)

    @pyqtSlot(str)
    def competition_finished_slot(self, mode):
        print('#' * self.LINE_LENGTH)
        self._build_text(str(mode))
        print('#' * self.LINE_LENGTH)
