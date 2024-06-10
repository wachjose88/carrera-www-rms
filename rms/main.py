
import contextlib
import sys
import argparse
import locale
import json
from datetime import datetime

from PyQt5.QtCore import pyqtSlot, QTranslator, QLibraryInfo
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, \
    QStackedWidget

from bridge import CUBridge, StartSignal, IdleMonitor
from competition import Grid, ResultList, QualifyingSeq
from home import Home
from settings import Settings
from statistics import Statistics
from database import DatabaseHandler
from tts import TTSHandler, TTSThread
from utils import ThreadTranslation, get_by_py_path
from signals import RMSSignals
from constants import COMP_MODE__TRAINING, COMP_MODE__QUALIFYING_LAPS, \
                      COMP_MODE__QUALIFYING_TIME, \
                      COMP_MODE__QUALIFYING_LAPS_SEQ, \
                      COMP_MODE__QUALIFYING_TIME_SEQ, \
                      COMP_MODE__RACE_LAPS, \
                      COMP_MODE__RACE_TIME, \
                      SORT_MODE__LAPS, SORT_MODE__LAPTIME, \
                      DUMMY_IDS


class RMS(QMainWindow):

    def __init__(self, cu, cu_instance, rms_slots):
        super().__init__()
        self.cuv = cu.version()
        self.show_pits = True
        self.show_fuel = True
        self.database = DatabaseHandler(
            debug=True if self.cuv in DUMMY_IDS else False
        )
        self.rms_signals = RMSSignals()
        self.rms_slots = rms_slots(rms_signals=self.rms_signals,
                                   database=self.database)
        self.rms_slots.connect_slots()
        self.drivers = {}
        self.setDefaultDrivers()
        self.comp_mode = COMP_MODE__TRAINING
        self.comp_duration = 0
        self.comp_starttime = datetime.now()
        self.tts = TTSHandler()
        self.ttsthread = TTSThread(self.tts, self.database)
        self.ttsthread.ttsoverride_changed.connect(
            self.ttsthread.ttsoverride_changed_set)
        self.ttsthread.start()
        self.main_stack = QStackedWidget(self)
        self.qualifyingseq = QualifyingSeq(self)
        self.main_stack.addWidget(self.qualifyingseq)
        self.threadtranslation = ThreadTranslation()
        self.main_stack.addWidget(self.threadtranslation)
        self.idle = IdleMonitor(cu=cu, cu_instance=cu_instance,
                                rms_signals=self.rms_signals)
        self.bridge = CUBridge(cu=cu, cu_instance=cu_instance,
                               selected_drivers=self.drivers, tts=self.tts,
                               threadtranslation=self.threadtranslation)
        self.start_signal = StartSignal(cu=cu, cu_instance=cu_instance)
        self.grid = Grid(parent=self, tts=self.tts,
                         threadtranslation=self.threadtranslation,
                         signals=self.rms_signals)
        self.home = Home(parent=self, database=self.database)
        self.settings = Settings(parent=self, database=self.database)
        self.statistics = Statistics(parent=self, database=self.database)
        self.resultlist = ResultList(parent=self, database=self.database)
        self.main_stack.addWidget(self.home)
        self.main_stack.addWidget(self.grid)
        self.main_stack.addWidget(self.settings)
        self.main_stack.addWidget(self.statistics)
        self.main_stack.addWidget(self.resultlist)
        self.bridge.update_grid.connect(self.grid.driver_change)
        self.bridge.comp_state.connect(self.comp_state_update)
        self.bridge.comp_finished.connect(self.comp_finished_all)
        self.start_signal.ready_to_run.connect(self.startAfterSignal)
        self.start_signal.show_lights.connect(self.grid.showLight)
        self.idle.update_state.connect(self.show_state)
        self.bridge.update_state.connect(self.show_state)
        self.start_signal.update_state.connect(self.show_state)
        self.setCentralWidget(self.main_stack)
        self.initUI()

    def initUI(self):

        self.statusBar().showMessage('Ready')

        if self.cuv not in DUMMY_IDS:
            self.showMaximized()
        self.setWindowTitle('RMS')
        self.showHome()
        self.show()

    def setDefaultDrivers(self):
        self.drivers = {}
        driversjson = self.database.getConfigStr('DEFAULT_DRIVERS')
        if driversjson is not None:
            driversdb = json.loads(driversjson)
            for addr, driver in driversdb.items():
                addrt = int(addr)
                self.drivers[addrt] = driver

    def startBridgeThread(self):
        if not self.bridge.isRunning():
            self.bridge.stop = False
            self.bridge.start()

    def startIdleThread(self):
        if not self.idle.isRunning():
            self.idle.stop = False
            self.idle.start()

    def startStartSignalThread(self):
        if not self.start_signal.isRunning():
            self.start_signal.stop = False
            self.start_signal.start()

    def stopAllThreads(self):
        if self.bridge.isRunning():
            self.bridge.stop = True
            self.bridge.wait()
        if self.idle.isRunning():
            self.idle.stop = True
            self.idle.wait()
        if self.start_signal.isRunning():
            self.start_signal.stop = True
            self.start_signal.wait()

    def showSettings(self):
        self.setEnabled(False)
        self.settings.playerset.build_playerlist()
        self.settings.carset.build_carlist()
        self.setEnabled(True)
        self.main_stack.setCurrentWidget(self.settings)
        self.stopAllThreads()
        self.startIdleThread()

    def showStatistics(self):
        self.statistics.showLists()
        self.main_stack.setCurrentWidget(self.statistics)
        self.stopAllThreads()
        self.startIdleThread()

    def showHome(self):
        tn = self.database.getConfigStr('TRACKNAME')
        if tn is not None and len(tn) > 0:
            track_name = tn + ' ' + self.tr('RMS')
        else:
            track_name = self.tr('Carrera RMS')
        tl = self.database.getConfigStr('TRACKLENGTH')
        if tl is not None and len(tl) > 0:
            track_length = int(tl)
        else:
            track_length = 0
        self.home.headline.setText(track_name)
        self.rms_signals.home.emit(track_name, track_length)
        self.home.buildCarList()
        self.home.buildPlayerList()
        for i in range(0, 6):
            try:
                n = self.drivers[i]['name']
                c = self.drivers[i]['car']
                self.home.setOk(i, True)
                self.home.setName(i, n)
                self.home.setCar(i, c)
            except KeyError:
                self.home.setOk(i, False)
                self.home.setName(i, '')
                self.home.setCar(i, '')

        self.main_stack.setCurrentWidget(self.home)
        self.stopAllThreads()
        self.startIdleThread()
        self.database.updateStatistic()

    def showResultList(self, cu_drivers):
        self.stopAllThreads()
        self.resultlist.resetDrivers()
        self.resultlist.addDrivers(self.drivers, cu_drivers,
                                   self.grid.sort_mode)
        self.main_stack.setCurrentWidget(self.resultlist)
        self.rms_signals.competition_finished.emit(
            self.threadtranslation.finished())

    def showGrid(self):
        self.grid.resetDrivers(self.show_fuel, self.show_pits)
        seq_found = None
        for addr, driver in self.drivers.items():
            if self.comp_mode in [COMP_MODE__QUALIFYING_LAPS_SEQ,
                                  COMP_MODE__QUALIFYING_TIME_SEQ]:
                if seq_found is None and \
                        driver['qualifying_cu_driver'] is None:
                    self.grid.addDriver(addr, driver,
                                        self.show_fuel, self.show_pits)
                    seq_found = addr
            else:
                self.grid.addDriver(addr, driver,
                                    self.show_fuel, self.show_pits)

        self.main_stack.setCurrentWidget(self.grid)
        self.stopAllThreads()

    def startQualifying(self, mode, duration):
        self.comp_mode = mode
        self.comp_duration = duration
        self.grid.sort_mode = SORT_MODE__LAPTIME
        self.showGrid()
        self.bridge.reset(self.drivers, mode)
        self.startStartSignalThread()

    def startRace(self, mode, duration):
        self.comp_mode = mode
        self.comp_duration = duration
        self.grid.sort_mode = SORT_MODE__LAPS
        self.showGrid()
        self.bridge.reset(self.drivers, mode)
        self.startStartSignalThread()

    def startTraining(self):
        self.comp_mode = COMP_MODE__TRAINING
        self.grid.sort_mode = SORT_MODE__LAPTIME
        self.showGrid()
        self.bridge.reset(self.drivers, self.comp_mode)
        self.startStartSignalThread()

    @pyqtSlot()
    def startAfterSignal(self):
        self.comp_starttime = datetime.now()
        self.threadtranslation.mode = self.comp_mode
        self.startBridgeThread()

    @pyqtSlot(int, list)
    def comp_finished_all(self, rtime, drivers):
        tdrivers = drivers
        self.stopAllThreads()
        if self.comp_mode in [COMP_MODE__QUALIFYING_LAPS_SEQ,
                              COMP_MODE__QUALIFYING_TIME_SEQ]:
            seq_found = []
            next = None
            for addr, driver in self.drivers.items():
                if driver['qualifying_cu_driver'] is not None:
                    seq_found.append(driver)
                    if tdrivers[addr].time is not None:
                        driver['qualifying_cu_driver'] = tdrivers[addr]
                elif next is None:
                    next = driver
            if len(seq_found) == len(self.drivers):
                for addr, driver in self.drivers.items():
                    tdrivers[addr] = driver['qualifying_cu_driver']
                self.showResultList(tdrivers)
            else:
                self.qualifyingseq.setDrivers(seq_found[-1], next)
                self.main_stack.setCurrentWidget(self.qualifyingseq)
        else:
            self.showResultList(drivers)

    @pyqtSlot(int, list)
    def comp_state_update(self, rtime, cu_drivers):
        if self.comp_mode == COMP_MODE__TRAINING:
            self.grid.training_state.showTime(rtime=rtime)
        elif self.comp_mode == COMP_MODE__RACE_LAPS:
            self.grid.race_state.handleUpdateLaps(rtime=rtime,
                                                  laps=self.comp_duration,
                                                  cu_drivers=cu_drivers,
                                                  tts=self.tts)
        elif self.comp_mode == COMP_MODE__RACE_TIME:
            self.grid.race_state.handleUpdateTime(rtime=rtime,
                                                  minutes=self.comp_duration,
                                                  cu_drivers=cu_drivers,
                                                  tts=self.tts)
        elif self.comp_mode == COMP_MODE__QUALIFYING_LAPS:
            self.grid.qualifying_state.handleUpdateLaps(
                rtime=rtime,
                laps=self.comp_duration,
                cu_drivers=cu_drivers,
                tts=self.tts)
        elif self.comp_mode == COMP_MODE__QUALIFYING_TIME:
            self.grid.qualifying_state.handleUpdateTime(
                rtime=rtime,
                minutes=self.comp_duration,
                cu_drivers=cu_drivers,
                tts=self.tts)
        elif self.comp_mode == COMP_MODE__QUALIFYING_LAPS_SEQ:
            self.grid.qualifying_state.handleUpdateLapsSeq(
                rtime=rtime,
                laps=self.comp_duration,
                cu_drivers=cu_drivers,
                tts=self.tts)
        elif self.comp_mode == COMP_MODE__QUALIFYING_TIME_SEQ:
            self.grid.qualifying_state.handleUpdateTimeSeq(
                rtime=rtime,
                minutes=self.comp_duration,
                cu_drivers=cu_drivers,
                tts=self.tts)

    @pyqtSlot(int)
    def show_state(self, mode):
        binMode = "{0:04b}".format(mode)
        fuelmode = ''
        pitlane = ''
        lapcounter = ''
        if binMode[2] == '1':
            fuelmode = self.tr('Real')
            self.show_fuel = True
        elif binMode[3] == '1':
            fuelmode = self.tr('On')
            self.show_fuel = True
        elif binMode[3] == '0':
            fuelmode = self.tr('Off')
            self.show_fuel = False
        if binMode[1] == '1':
            pitlane = self.tr('Exists')
            self.show_pits = True
        else:
            pitlane = self.tr('Missing')
            self.show_pits = False
        if binMode[0] == '1':
            lapcounter = self.tr('Exists')
        else:
            lapcounter = self.tr('Missing')
        self.statusBar().showMessage(
            self.tr('CU version: ') + str(self.cuv)
            + self.tr(', Pitlane: ') + str(pitlane)
            + self.tr(', Fuelmode: ') + str(fuelmode)
            + self.tr(', Lapcounter: ') + str(lapcounter))

    def closeEvent(self, event):
        result = QMessageBox.question(
            self,
            self.tr("Confirm Exit..."),
            self.tr("Are you sure you want to exit ?"),
            QMessageBox.Yes | QMessageBox.No)
        event.ignore()

        if result == QMessageBox.Yes:
            event.accept()
            self.stopAllThreads()
            self.ttsthread.stop = True
            self.ttsthread.wait()
            self.database.removeSession()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    qtbase_translator = QTranslator()
    qtbase_translator.load(
        "qtbase_" + locale.getlocale()[0][0:2],
        QLibraryInfo.location(QLibraryInfo.TranslationsPath))
    app.installTranslator(qtbase_translator)
    qt_translator = QTranslator()
    qt_translator.load(
        "qt_" + locale.getlocale()[0][0:2],
        QLibraryInfo.location(QLibraryInfo.TranslationsPath))
    app.installTranslator(qt_translator)
    translator = QTranslator()
    translator.load("locales/carrera_" + locale.getlocale()[0][0:2])
    app.installTranslator(translator)
    parser = argparse.ArgumentParser(
        description='Advanced Race Management for Carrera Digital')
    parser.add_argument('-cu', '--controlunit',
                        help='cu address or dummy', required=True)
    parser.add_argument('-s', '--slots',
                        help='classname to use for the slots',
                        default='slots.console.Console')
    args = parser.parse_args()
    RMSSlots = get_by_py_path(args.slots)
    if args.controlunit in ['d', 'dummy']:
        from dummy import ControlUnit
    else:
        from carreralib import ControlUnit
        print(args.controlunit)
    with contextlib.closing(ControlUnit(str(args.controlunit),
                                        timeout=3.0)) as cu:
        print('CU version %s' % cu.version())
        ex = RMS(cu, ControlUnit, RMSSlots)
        sys.exit(app.exec_())
