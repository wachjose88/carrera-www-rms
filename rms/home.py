
from PyQt5.QtWidgets import QWidget, QGridLayout, QComboBox, \
                            QLabel, QVBoxLayout, QSizePolicy, \
                            QCheckBox, QPushButton, QHBoxLayout, \
                            QSpinBox, QTabWidget, QMessageBox
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont
from utils import HSep, VSep
from constants import COMP_MODE__QUALIFYING_LAPS, \
                      COMP_MODE__QUALIFYING_TIME, \
                      COMP_MODE__QUALIFYING_LAPS_SEQ, \
                      COMP_MODE__QUALIFYING_TIME_SEQ, \
                      COMP_MODE__RACE_LAPS, \
                      COMP_MODE__RACE_TIME, \
                      DUMMY_IDS


class CompTime(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vbox = QVBoxLayout(self)
        self.dtext = QLabel(self.tr('Duration in minutes:'))
        self.vbox.addWidget(self.dtext)
        self.duration = QSpinBox()
        self.duration.setMinimum(1)
        self.duration.setSuffix(self.tr(' Minutes'))
        self.duration.setValue(10)
        self.vbox.addWidget(self.duration)
        self.setLayout(self.vbox)


class CompLaps(QWidget):

    def __init__(self, parent=None, default=20):
        super().__init__(parent)
        self.vbox = QVBoxLayout(self)
        self.dtext = QLabel(self.tr('Duration in laps'))
        self.vbox.addWidget(self.dtext)
        self.duration = QSpinBox()
        self.duration.setMinimum(1)
        self.duration.setSuffix(self.tr(' Laps'))
        self.duration.setValue(default)
        self.vbox.addWidget(self.duration)
        self.setLayout(self.vbox)


class RaceParams(QWidget):

    def __init__(self, parent=None, default_laps=20):
        super().__init__(parent)
        self.vbox = QVBoxLayout(self)
        self.modetab = QTabWidget()
        self.vbox.addWidget(self.modetab)
        self.complaps = CompLaps(default=default_laps)
        self.modetab.addTab(self.complaps, self.tr('Laps'))
        self.comptime = CompTime()
        self.modetab.addTab(self.comptime, self.tr('Time'))
        self.setLayout(self.vbox)

    def getCompMode(self):
        if self.modetab.currentWidget() == self.complaps:
            return COMP_MODE__RACE_LAPS
        if self.modetab.currentWidget() == self.comptime:
            return COMP_MODE__RACE_TIME

    def getDuration(self):
        if self.modetab.currentWidget() == self.complaps:
            return self.complaps.duration.value()
        if self.modetab.currentWidget() == self.comptime:
            return self.comptime.duration.value()


class QualifyingParams(QWidget):

    def __init__(self, parent=None, default_laps=10):
        super().__init__(parent)
        self.vbox = QVBoxLayout(self)
        self.modetab = QTabWidget()
        self.vbox.addWidget(self.modetab)
        self.complaps = CompLaps(default=default_laps)
        self.modetab.addTab(self.complaps, self.tr('Laps'))
        self.comptime = CompTime()
        self.modetab.addTab(self.comptime, self.tr('Time'))
        self.sequential = QCheckBox()
        self.sequential.setText(self.tr('Sequential'))
        self.sequential.setChecked(True)
        self.vbox.addWidget(self.sequential)
        self.setLayout(self.vbox)

    def getCompMode(self):
        if self.modetab.currentWidget() == self.complaps:
            if self.sequential.isChecked():
                return COMP_MODE__QUALIFYING_LAPS_SEQ
            return COMP_MODE__QUALIFYING_LAPS
        if self.modetab.currentWidget() == self.comptime:
            if self.sequential.isChecked():
                return COMP_MODE__QUALIFYING_TIME_SEQ
            return COMP_MODE__QUALIFYING_TIME

    def getDuration(self):
        if self.modetab.currentWidget() == self.complaps:
            return self.complaps.duration.value()
        if self.modetab.currentWidget() == self.comptime:
            return self.comptime.duration.value()


class ControllerSet(QWidget):

    def __init__(self, parent=None, database=None):
        super().__init__(parent)
        self.database = database
        self.controller = QGridLayout()
        self.controller_ok = []
        self.controller_name = []
        self.controller_car = []
        cars = self.database.getAllCars()
        self.carlbl = self.tr('Select Car')
        self.carsep = '---'
        players = self.database.getAllPlayers()
        self.playerlbl = self.tr('Select Driver')
        self.playersep = '---'
        for i in range(0, 6):
            ok = QCheckBox()
            ok.setSizePolicy(QSizePolicy.Expanding,
                             QSizePolicy.Maximum)
            ok.setText(self.tr('Controller ') + str(i+1))
            self.controller.addWidget(ok, 0, i)
            self.controller_ok.append(ok)
            player = QComboBox()
            player.setMinimumContentsLength(9)
            player.setSizeAdjustPolicy(
                QComboBox.AdjustToMinimumContentsLengthWithIcon)
            player.addItem(self.playerlbl)
            player.addItem(self.playersep)
            for p in players:
                player.addItem(p.username)
            self.controller.addWidget(player, 1, i)
            self.controller_name.append(player)
            car = QComboBox()
            car.setMinimumContentsLength(9)
            car.setSizeAdjustPolicy(
                QComboBox.AdjustToMinimumContentsLengthWithIcon)
            car.addItem(self.carlbl)
            car.addItem(self.carsep)
            for c in cars:
                car.addItem(c.name)
            self.controller.addWidget(car, 2, i)
            self.controller_car.append(car)
        self.setLayout(self.controller)

    def getCar(self, addr):
        t = self.controller_car[addr].currentText()
        if t in [self.carlbl, self.carsep]:
            QMessageBox.information(
                self,
                self.tr("No car selected"),
                str(self.tr("Please select a car for Controller ")
                    + str(addr+1) + '.'),
                QMessageBox.Ok)
            raise KeyError
        return self.controller_car[addr].currentText()

    def getOk(self, addr):
        return self.controller_ok[addr].isChecked()

    def getName(self, addr):
        username = self.controller_name[addr].currentText()
        if username in [self.playerlbl, self.playersep]:
            QMessageBox.information(
                self,
                self.tr("Driver name missing"),
                str(self.tr("Please select a driver name for Controller ")
                    + str(addr+1) + '.'),
                QMessageBox.Ok)
            raise KeyError
        return username

    def setCar(self, addr, car):
        index = self.controller_car[addr].findText(car)
        if index >= 0:
            self.controller_car[addr].setCurrentIndex(index)

    def setOk(self, addr, checked):
        self.controller_ok[addr].setChecked(checked)

    def setName(self, addr, username):
        index = self.controller_name[addr].findText(username)
        if index >= 0:
            self.controller_name[addr].setCurrentIndex(index)

    def buildCarList(self):
        cars = self.database.getAllCars()
        for i in range(0, 6):
            cw = self.controller_car[i]
            car = cw.currentText()
            cw.clear()
            cw.addItem(self.carlbl)
            cw.addItem(self.carsep)
            for c in cars:
                cw.addItem(c.name)
            index = cw.findText(car)
            if index >= 0:
                cw.setCurrentIndex(index)

    def buildPlayerList(self):
        players = self.database.getAllPlayers()
        for i in range(0, 6):
            cw = self.controller_name[i]
            player = cw.currentText()
            cw.clear()
            cw.addItem(self.playerlbl)
            cw.addItem(self.playersep)
            for p in players:
                cw.addItem(p.username)
            index = cw.findText(player)
            if index >= 0:
                cw.setCurrentIndex(index)


class Home(QWidget):

    def __init__(self, parent=None, database=None):
        super().__init__(parent)
        self.database = database
        self.initUI()

    def initUI(self):
        self.controller = ControllerSet(self, self.database)
        self.vml = QVBoxLayout()
        self.vml.setSpacing(10)
        self.headFont = QFont()
        self.headFont.setPointSize(45)
        self.headFont.setBold(True)
        self.headline = QLabel(self.tr('Carrera RMS'))
        self.headline.setFont(self.headFont)
        self.vml.addWidget(self.headline)
        self.vml.addWidget(HSep())
        self.vml.addWidget(self.controller)
        self.vml.addWidget(HSep())
        self.starts = QHBoxLayout()
        self.vml.addLayout(self.starts)
        self.vml.addWidget(HSep())
        self.start_training = QPushButton()
        self.start_training.setText(self.tr('Training'))
        self.start_training.clicked.connect(self.startTraining_click)
        self.start_training.setSizePolicy(QSizePolicy.Expanding,
                                          QSizePolicy.Expanding)
        self.starts.addWidget(self.start_training)
        self.starts.addWidget(VSep())
        lq = self.database.getConfigStr('LAPSQUALI')
        if lq is None:
            lq = 10
        else:
            lq = int(lq)
        self.qualifyingparams = QualifyingParams(default_laps=lq)
        self.qualifyingparams.setSizePolicy(QSizePolicy.Expanding,
                                            QSizePolicy.Maximum)
        self.qhbox = QVBoxLayout()
        self.qhbox.addWidget(self.qualifyingparams)
        self.start_qualifying = QPushButton()
        self.start_qualifying.setText(self.tr('Qualifying'))
        self.start_qualifying.clicked.connect(self.startQualifying_click)
        self.start_qualifying.setSizePolicy(QSizePolicy.Expanding,
                                            QSizePolicy.Expanding)
        self.qhbox.addWidget(self.start_qualifying)
        self.starts.addLayout(self.qhbox)
        self.starts.addWidget(VSep())
        lr = self.database.getConfigStr('LAPSRACE')
        if lr is None:
            lr = 20
        else:
            lr = int(lr)
        self.raceparams = RaceParams(default_laps=lr)
        self.raceparams.setSizePolicy(QSizePolicy.Expanding,
                                      QSizePolicy.Maximum)
        self.rhbox = QVBoxLayout()
        self.rhbox.addWidget(self.raceparams)
        self.start_race = QPushButton()
        self.start_race.setText(self.tr('Race'))
        self.start_race.clicked.connect(self.startRace_click)
        self.start_race.setSizePolicy(QSizePolicy.Expanding,
                                      QSizePolicy.Expanding)
        self.rhbox.addWidget(self.start_race)
        self.starts.addLayout(self.rhbox)
        self.btnrow = QHBoxLayout()
        self.fullscreen = QPushButton()
        self.fullscreen.setText(self.tr('Fullscreen'))
        self.fullscreen.clicked.connect(self.fullscreen_click)
        self.btnrow.addWidget(self.fullscreen)
        self.statistics = QPushButton()
        self.statistics.setText(self.tr('Statistics'))
        self.statistics.clicked.connect(self.statistics_click)
        self.btnrow.addWidget(self.statistics)
        self.settings = QPushButton()
        self.settings.setText(self.tr('Settings'))
        self.settings.clicked.connect(self.settings_click)
        self.btnrow.addWidget(self.settings)
        self.vml.addLayout(self.btnrow)
        self.exitrms = QPushButton()
        self.exitrms.setText(self.tr('Exit'))
        self.exitrms.clicked.connect(self.exitrms_click)
        self.vml.addWidget(self.exitrms)
        self.setLayout(self.vml)

    @pyqtSlot()
    def statistics_click(self):
        self.parent().parent().showStatistics()

    @pyqtSlot()
    def settings_click(self):
        self.parent().parent().showSettings()

    @pyqtSlot()
    def exitrms_click(self):
        self.parent().parent().close()

    @pyqtSlot()
    def fullscreen_click(self):
        if self.parent().parent().windowState() & Qt.WindowFullScreen:

            if self.parent().parent().cuv not in DUMMY_IDS:
                self.parent().parent().showMaximized()
            else:
                self.parent().parent().showNormal()
            self.fullscreen.setText(self.tr('Fullscreen'))
        else:
            self.parent().parent().showFullScreen()
            self.fullscreen.setText(self.tr('Exit Fullscreen'))

    def getDrivers(self):
        d = {}
        for i in range(0, 6):
            if self.getOk(i):
                c = self.getCar(i)
                p = {'pos': 0, 'name': self.getName(i), 'car': c}
                if self.qualifyingparams.getCompMode() in [
                        COMP_MODE__QUALIFYING_LAPS_SEQ,
                        COMP_MODE__QUALIFYING_TIME_SEQ]:
                    p['qualifying_cu_driver'] = None
                d[i] = p
        return d

    @pyqtSlot()
    def startRace_click(self):
        try:
            self.parent().parent().drivers = self.getDrivers()
            self.parent().parent().startRace(self.raceparams.getCompMode(),
                                             self.raceparams.getDuration())
        except KeyError:
            pass

    @pyqtSlot()
    def startQualifying_click(self):
        try:
            self.parent().parent().drivers = self.getDrivers()
            self.parent().parent().startQualifying(
                self.qualifyingparams.getCompMode(),
                self.qualifyingparams.getDuration())
        except KeyError:
            pass

    @pyqtSlot()
    def startTraining_click(self):
        try:
            self.parent().parent().drivers = self.getDrivers()
            self.parent().parent().startTraining()
        except KeyError:
            pass

    def getCar(self, addr):
        return self.controller.getCar(addr)

    def getOk(self, addr):
        return self.controller.getOk(addr)

    def getName(self, addr):
        return self.controller.getName(addr)

    def setCar(self, addr, car):
        self.controller.setCar(addr, car)

    def setOk(self, addr, checked):
        self.controller.setOk(addr, checked)

    def setName(self, addr, name):
        self.controller.setName(addr, name)

    def buildCarList(self):
        self.controller.buildCarList()

    def buildPlayerList(self):
        self.controller.buildPlayerList()
