import json
from json import JSONDecodeError
from urllib import request, error, parse

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QGridLayout, QSpinBox, \
    QLabel, QVBoxLayout, QSizePolicy, \
    QLineEdit, QPushButton, \
    QTabWidget, \
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, \
    QMessageBox
from sqlalchemy.exc import IntegrityError

from home import ControllerSet
from utils import HSep
from statistics import ShowDetails


class ScaleBox(QComboBox):

    CARRERA_124 = 'Carrera 124'
    CARRERA_132 = 'Carrera 132'

    def __init__(self, parent, car, database):
        super().__init__(parent)
        self.addItem('')
        self.addItem(ScaleBox.CARRERA_132)
        self.addItem(ScaleBox.CARRERA_124)
        if car.scale is None:
            self.setCurrentIndex(0)
        elif car.scale == 24:
            self.setCurrentIndex(2)
        elif car.scale == 32:
            self.setCurrentIndex(1)
        self.carid = car.id
        self.database = database
        self.currentTextChanged.connect(self.update_car)

    def update_car(self, scale):
        print("blabla")
        if len(scale) <= 0:
            self.database.updateCar(id=self.carid, scale='null')
            return
        elif scale == self.CARRERA_132:
            scale = int(32)
        elif scale == self.CARRERA_124:
            scale = int(24)
        self.database.updateCar(id=self.carid, scale=scale)


class PlayerItem(QTableWidgetItem):

    def __init__(self, playerid=None, text=None, type=None):
        if text is None:
            super().__init__('')
        else:
            super().__init__(str(text))
        self.playerid = playerid
        self.type = type


class PlayerSet(QWidget):

    def __init__(self, parent=None, database=None):
        super().__init__(parent)
        self.database = database
        self.mgrid = QGridLayout()
        self.usernamelbl = QLabel(self.tr('Username: '))
        self.usernamelbl.setSizePolicy(QSizePolicy.Maximum,
                                       QSizePolicy.Maximum)
        self.mgrid.addWidget(self.usernamelbl, 0, 0)
        self.username = QLineEdit()
        self.username.setSizePolicy(QSizePolicy.Expanding,
                                    QSizePolicy.Maximum)
        self.mgrid.addWidget(self.username, 0, 1)
        self.playernamelbl = QLabel(self.tr('Name: '))
        self.playernamelbl.setSizePolicy(QSizePolicy.Maximum,
                                         QSizePolicy.Maximum)
        self.mgrid.addWidget(self.playernamelbl, 1, 0)
        self.playername = QLineEdit()
        self.playername.setSizePolicy(QSizePolicy.Expanding,
                                      QSizePolicy.Maximum)
        self.mgrid.addWidget(self.playername, 1, 1)
        self.addplayer = QPushButton()
        self.addplayer.setText(self.tr('Add'))
        self.addplayer.clicked.connect(self.playername_finished)
        self.addplayer.setSizePolicy(QSizePolicy.Maximum,
                                     QSizePolicy.Expanding)
        self.mgrid.addWidget(self.addplayer, 0, 2, 2, 1)
        self.playerlist = QTableWidget()
        self.playerlist.setSortingEnabled(True)
        self.playerlist_allowchange = True
        self.playerlist.itemChanged.connect(self.change_player_item)
        #self.build_playerlist()
        self.mgrid.addWidget(self.playerlist, 2, 0, 1, 3)
        self.setLayout(self.mgrid)

    def build_playerlist(self):
        self.setEnabled(False)
        self.playerlist_allowchange = False
        self.playerlist.clear()
        self.playerlist.setSortingEnabled(False)
        self.playerlist.setColumnCount(5)
        self.playerlist.setHorizontalHeaderLabels([
            self.tr('Username'), self.tr('Name'),
            self.tr('# Trainings'), self.tr('# Qualifyings'),
            self.tr('# Races')
        ])
        i = 0
        players = self.database.getAllPlayersDetails()
        self.playerlist.setRowCount(len(players))
        self.playerlist.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents)
        self.playerlist.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch)
        self.playerlist.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents)
        self.playerlist.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeToContents)
        self.playerlist.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeToContents)

        for player in players:
            nameitem = PlayerItem(
                player['player'].id, player['player'].name, 'name')
            usernameitem = PlayerItem(
                player['player'].id, player['player'].username, 'username')
            numtrainingsitem = PlayerItem(
                player['player'].id,
                "{:04d} / {:04d}".format(player['numtrainingwins'], player['numtrainings']),
                'numtrainings')
            numtrainingsitem.setFlags(
                numtrainingsitem.flags() ^ Qt.ItemIsEditable)
            numqualifyingsitem = PlayerItem(
                player['player'].id,
                "{:04d} / {:04d}".format(player['numqualifyingwins'], player['numqualifyings']),
                'numqualifyings')
            numqualifyingsitem.setFlags(
                numqualifyingsitem.flags() ^ Qt.ItemIsEditable)
            numracesitem = PlayerItem(
                player['player'].id,
                "{:04d} / {:04d}".format(player['numracewins'], player['numraces']),
                'numraces')
            numracesitem.setFlags(
                numracesitem.flags() ^ Qt.ItemIsEditable)
            self.playerlist.setItem(i, 0, usernameitem)
            self.playerlist.setItem(i, 1, nameitem)
            self.playerlist.setItem(i, 2, numtrainingsitem)
            self.playerlist.setItem(i, 3, numqualifyingsitem)
            self.playerlist.setItem(i, 4, numracesitem)
            i = i + 1
        self.playerlist_allowchange = True
        self.playerlist.setSortingEnabled(True)
        self.setEnabled(True)

    @pyqtSlot(QTableWidgetItem)
    def change_player_item(self, item):
        if self.playerlist_allowchange is True:
            if item.type == 'name':
                self.database.updatePlayer(id=item.playerid, name=item.text())
            if item.type == 'username':
                saved = self.database.updatePlayer(id=item.playerid,
                                                   username=item.text())
                if not saved:
                    QMessageBox.warning(self, self.tr('Add player error'),
                                        self.tr('The username must be unique.'))
            self.build_playerlist()

    @pyqtSlot()
    def playername_finished(self):
        pn = str(self.playername.text()).strip()
        if len(pn) <= 0:
            QMessageBox.warning(self, self.tr('Add player error'),
                                self.tr('The playername is required.'))
            return
        pun = str(self.username.text()).strip()
        if len(pun) <= 0:
            QMessageBox.warning(self, self.tr('Add player error'),
                                self.tr('The username is required.'))
            return
        saved = self.database.setPlayer(pun, pn)
        if not saved:
            QMessageBox.warning(self, self.tr('Add player error'),
                                self.tr('The username must be unique.'))
            return
        self.username.setText('')
        self.playername.setText('')
        self.build_playerlist()
        self.parent().parent().parent().coreset.controller.buildPlayerList()



class CarItem(QTableWidgetItem):

    def __init__(self, carid=None, text=None, type=None):
        if text is None:
            super().__init__('')
        else:
            super().__init__(str(text))
        self.carid = carid
        self.type = type


class CarSet(QWidget):

    def __init__(self, parent=None, database=None):
        super().__init__(parent)
        self.database = database
        self.mgrid = QGridLayout()
        self.carnamelbl = QLabel(self.tr('Carname: '))
        self.carnamelbl.setSizePolicy(QSizePolicy.Maximum,
                                      QSizePolicy.Maximum)
        self.mgrid.addWidget(self.carnamelbl, 0, 0)
        self.carname = QLineEdit()
        self.carname.setSizePolicy(QSizePolicy.Expanding,
                                   QSizePolicy.Maximum)
        self.mgrid.addWidget(self.carname, 0, 1)
        self.carnumberlbl = QLabel(self.tr('Carnumber: '))
        self.carnumberlbl.setSizePolicy(QSizePolicy.Maximum,
                                        QSizePolicy.Maximum)
        self.mgrid.addWidget(self.carnumberlbl, 1, 0)
        self.carnumber = QLineEdit()
        self.carnumber.setSizePolicy(QSizePolicy.Expanding,
                                     QSizePolicy.Maximum)
        self.mgrid.addWidget(self.carnumber, 1, 1)
        self.cartireslbl = QLabel(self.tr('Tires: '))
        self.cartireslbl.setSizePolicy(QSizePolicy.Maximum,
                                       QSizePolicy.Maximum)
        self.mgrid.addWidget(self.cartireslbl, 2, 0)
        self.cartires = QLineEdit()
        self.cartires.setSizePolicy(QSizePolicy.Expanding,
                                    QSizePolicy.Maximum)
        self.mgrid.addWidget(self.cartires, 2, 1)
        self.carscalelbl = QLabel(self.tr('Scale: '))
        self.carscalelbl.setSizePolicy(QSizePolicy.Maximum,
                                       QSizePolicy.Maximum)
        self.mgrid.addWidget(self.carscalelbl, 3, 0)
        self.carscale = QComboBox()
        self.carscale.setSizePolicy(QSizePolicy.Expanding,
                                    QSizePolicy.Maximum)
        self.carscale.addItem(ScaleBox.CARRERA_132)
        self.carscale.addItem(ScaleBox.CARRERA_124)
        self.mgrid.addWidget(self.carscale, 3, 1)
        self.addcar = QPushButton()
        self.addcar.setText(self.tr('Add'))
        self.addcar.clicked.connect(self.carname_finished)
        self.addcar.setSizePolicy(QSizePolicy.Maximum,
                                  QSizePolicy.Expanding)
        self.mgrid.addWidget(self.addcar, 0, 2, 4, 1)
        self.carlist = QTableWidget()
        self.carlist_allowchange = True
        self.carlist.setSortingEnabled(True)
        self.carlist.itemChanged.connect(self.change_car_item)
        #self.build_carlist()
        self.mgrid.addWidget(self.carlist, 4, 0, 1, 3)
        self.setLayout(self.mgrid)

    def build_carlist(self):
        self.setEnabled(False)
        self.carlist_allowchange = False
        self.carlist.clear()
        self.carlist.setSortingEnabled(False)
        self.carlist.setColumnCount(7)
        self.carlist.setHorizontalHeaderLabels([
            self.tr('Carname'), self.tr('Carnumber'), self.tr('Tires'),
            self.tr('Scale'),
            self.tr('# Trainings'), self.tr('# Qualifyings'),
            self.tr('# Races')
        ])
        i = 0
        cars = self.database.getAllCarsDetails()
        self.carlist.setRowCount(len(cars))
        self.carlist.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch)
        self.carlist.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents)
        self.carlist.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents)
        self.carlist.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeToContents)
        self.carlist.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeToContents)
        self.carlist.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeToContents)
        self.carlist.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeToContents)
        for car in cars:
            nameitem = CarItem(car['car'].id, car['car'].name, 'name')
            numberitem = CarItem(car['car'].id, car['car'].number, 'number')
            tiresitem = CarItem(car['car'].id, car['car'].tires, 'tires')
            carscaleitem = ScaleBox(self.carlist, car['car'], self.database)
            numtrainingsitem = CarItem(
                car['car'].id,
                "{:04d} / {:04d}".format(car['numtrainingwins'], car['numtrainings']),
                'numtrainings')
            numtrainingsitem.setFlags(
                numtrainingsitem.flags() ^ Qt.ItemIsEditable)
            numqualifyingsitem = CarItem(
                car['car'].id,
                "{:04d} / {:04d}".format(car['numqualifyingwins'], car['numqualifyings']),
                'numqualifyings')
            numqualifyingsitem.setFlags(
                numqualifyingsitem.flags() ^ Qt.ItemIsEditable)
            numracesitem = CarItem(
                car['car'].id,
                "{:04d} / {:04d}".format(car['numracewins'], car['numraces']),
                'numraces')
            numracesitem.setFlags(
                numracesitem.flags() ^ Qt.ItemIsEditable)
            self.carlist.setItem(i, 0, nameitem)
            self.carlist.setItem(i, 1, numberitem)
            self.carlist.setItem(i, 2, tiresitem)
            self.carlist.setCellWidget(i, 3, carscaleitem)
            self.carlist.setItem(i, 4, numtrainingsitem)
            self.carlist.setItem(i, 5, numqualifyingsitem)
            self.carlist.setItem(i, 6, numracesitem)
            i = i + 1
        self.carlist_allowchange = True
        self.carlist.setSortingEnabled(True)
        self.setEnabled(True)

    @pyqtSlot(QTableWidgetItem)
    def change_car_item(self, item):
        if self.carlist_allowchange is True:
            if item.type == 'name':
                saved = self.database.updateCar(id=item.carid, name=item.text())
                if not saved:
                    QMessageBox.warning(self, self.tr('Add car error'),
                                        self.tr('The carname and carnumber must be unique.'))
            if item.type == 'number':
                saved = self.database.updateCar(id=item.carid, number=item.text())
                if not saved:
                    QMessageBox.warning(self, self.tr('Add car error'),
                                        self.tr('The carname and carnumber must be unique.'))
            if item.type == 'tires':
                self.database.updateCar(id=item.carid, tires=item.text())
            self.build_carlist()

    @pyqtSlot()
    def carname_finished(self):
        cn = str(self.carname.text()).strip()
        if len(cn) <= 0:
            QMessageBox.warning(self, self.tr('Add car error'),
                                self.tr('The carname is required.'))
            return
        cnr = str(self.carnumber.text()).strip()
        if len(cnr) <= 0:
            QMessageBox.warning(self, self.tr('Add car error'),
                                self.tr('The carnumber is required.'))
            return
        tires = str(self.cartires.text()).strip()
        scale = str(self.carscale.currentText()).strip()
        if len(scale) <= 0:
            return
        elif scale == ScaleBox.CARRERA_132:
            scale = int(32)
        elif scale == ScaleBox.CARRERA_124:
            scale = int(24)
        saved = self.database.setCar(cn, cnr, tires, scale)
        if not saved:
            QMessageBox.warning(self, self.tr('Add car error'),
                                self.tr('The carname and carnumber must be unique.'))
            return
        self.carname.setText('')
        self.carnumber.setText('')
        self.cartires.setText('')
        self.parent().parent().parent().coreset.controller.buildCarList()
        self.build_carlist()
        # self.carlist.clear()
        # i = 0
        # for car in self.database.getAllCars():
        #     self.carlist.insertItem(i, CarItem(car.name, car.number, car.tires))
        #     i = i + 1


class CoreSet(QWidget):

    def __init__(self, parent=None, database=None):
        super().__init__(parent)
        self.database = database
        self.vml = QVBoxLayout()
        self.mgrid = QGridLayout()
        self.tracknamelbl = QLabel(self.tr('Trackname: '))
        self.tracknamelbl.setSizePolicy(QSizePolicy.Maximum,
                                        QSizePolicy.Maximum)
        self.mgrid.addWidget(self.tracknamelbl, 0, 0)
        self.trackname = QLineEdit()
        tn = self.database.getConfigStr('TRACKNAME')
        if tn is not None:
            self.trackname.setText(tn)
        self.trackname.editingFinished.connect(self.trackname_finished)
        self.trackname.setSizePolicy(QSizePolicy.Expanding,
                                     QSizePolicy.Maximum)
        self.mgrid.addWidget(self.trackname, 0, 1)
        self.tracklengthlbl = QLabel(self.tr('Tracklength: '))
        self.tracklengthlbl.setSizePolicy(QSizePolicy.Maximum,
                                          QSizePolicy.Maximum)
        self.mgrid.addWidget(self.tracklengthlbl, 1, 0)
        self.tracklength = QSpinBox()
        self.tracklength.setMinimum(1)
        self.tracklength.setMaximum(2147483647)
        self.tracklength.setSuffix(self.tr(' mm'))
        self.tracklength.setValue(20000)
        tl = self.database.getConfigStr('TRACKLENGTH')
        if tl is not None:
            self.tracklength.setValue(int(tl))
        self.tracklength.editingFinished.connect(self.tracklength_finished)
        self.tracklength.setSizePolicy(QSizePolicy.Expanding,
                                       QSizePolicy.Maximum)
        self.mgrid.addWidget(self.tracklength, 1, 1)
        self.ttsoverridelbl = QLabel(self.tr('TTS override: '))
        self.ttsoverridelbl.setSizePolicy(QSizePolicy.Maximum,
                                          QSizePolicy.Maximum)
        self.mgrid.addWidget(self.ttsoverridelbl, 2, 0)
        self.ttsoverride = QLineEdit()
        tts = self.database.getConfigStr('TTSOVERRIDE')
        if tts is not None:
            self.ttsoverride.setText(tts)
        self.ttsoverride.editingFinished.connect(self.ttsoverride_finished)
        self.ttsoverride.setSizePolicy(QSizePolicy.Expanding,
                                       QSizePolicy.Maximum)
        self.mgrid.addWidget(self.ttsoverride, 2, 1)
        self.vml.addLayout(self.mgrid)
        self.vml.addWidget(HSep())
        self.dcs = QLabel(self.tr('Default Controller Settings:'))
        self.vml.addWidget(self.dcs)
        self.controller = ControllerSet(self, self.database)
        driversjson = self.database.getConfigStr('DEFAULT_DRIVERS')
        if driversjson is not None:
            driversdb = json.loads(driversjson)
            for addr, driver in driversdb.items():
                addrt = int(addr)
                self.controller.setOk(addrt, True)
                self.controller.setName(addrt, driver['name'])
                self.controller.setCar(addrt, driver['car'])
        self.vml.addWidget(self.controller)
        self.vml.addWidget(HSep())
        self.vml.addStretch(1)
        self.setLayout(self.vml)

    @pyqtSlot()
    def tracklength_finished(self):
        tl = str(self.tracklength.value()).strip()
        self.database.setConfig('TRACKLENGTH', tl)

    @pyqtSlot()
    def trackname_finished(self):
        tn = str(self.trackname.text()).strip()
        self.database.setConfig('TRACKNAME', tn)

    @pyqtSlot()
    def ttsoverride_finished(self):
        tts = str(self.ttsoverride.text()).strip()
        self.database.setConfig('TTSOVERRIDE', tts)
        self.parent().parent().parent().parent().parent()\
            .ttsthread.ttsoverride_changed.emit(tts)


class SyncSet(QWidget):

    def __init__(self, parent=None, database=None):
        super().__init__(parent)
        self.database = database
        self.vml = QVBoxLayout()
        self.mgrid = QGridLayout()
        self.apiurllbl = QLabel(self.tr('URL: '))
        self.apiurllbl.setSizePolicy(QSizePolicy.Maximum,
                                     QSizePolicy.Maximum)
        self.mgrid.addWidget(self.apiurllbl, 0, 0)
        self.apiurl = QLineEdit()
        apiurl = self.database.getConfigStr('APIURL')
        if apiurl is not None:
            self.apiurl.setText(apiurl)
        self.apiurl.editingFinished.connect(self.apiurl_finished)
        self.apiurl.setSizePolicy(QSizePolicy.Expanding,
                                  QSizePolicy.Maximum)
        self.mgrid.addWidget(self.apiurl, 0, 1)
        self.apiuserlbl = QLabel(self.tr('Username: '))
        self.apiuserlbl.setSizePolicy(QSizePolicy.Maximum,
                                      QSizePolicy.Maximum)
        self.mgrid.addWidget(self.apiuserlbl, 1, 0)
        self.apiuser = QLineEdit()
        apiuser = self.database.getConfigStr('APIUSER')
        if apiuser is not None:
            self.apiuser.setText(apiuser)
        self.apiuser.editingFinished.connect(self.apiuser_finished)
        self.apiuser.setSizePolicy(QSizePolicy.Expanding,
                                   QSizePolicy.Maximum)
        self.mgrid.addWidget(self.apiuser, 1, 1)
        self.apipwlbl = QLabel(self.tr('Password: '))
        self.apipwlbl.setSizePolicy(QSizePolicy.Maximum,
                                    QSizePolicy.Maximum)
        self.mgrid.addWidget(self.apipwlbl, 2, 0)
        self.apipw = QLineEdit()
        apipw = self.database.getConfigStr('APIPW')
        if apiurl is not None:
            self.apipw.setText(apipw)
        self.apipw.editingFinished.connect(self.apipw_finished)
        self.apipw.setSizePolicy(QSizePolicy.Expanding,
                                 QSizePolicy.Maximum)
        self.mgrid.addWidget(self.apipw, 2, 1)
        self.apirealmlbl = QLabel(self.tr('Realm: '))
        self.apirealmlbl.setSizePolicy(QSizePolicy.Maximum,
                                       QSizePolicy.Maximum)
        self.mgrid.addWidget(self.apirealmlbl, 3, 0)
        self.apirealm = QLineEdit()
        apirealm = self.database.getConfigStr('APIREALM')
        if apirealm is not None:
            self.apirealm.setText(apirealm)
        self.apirealm.editingFinished.connect(self.apirealm_finished)
        self.apirealm.setSizePolicy(QSizePolicy.Expanding,
                                    QSizePolicy.Maximum)
        self.mgrid.addWidget(self.apirealm, 3, 1)
        self.vml.addLayout(self.mgrid)
        self.vml.addWidget(HSep())
        self.syncprogress = QProgressBar()
        self.syncprogress.setOrientation(Qt.Horizontal)
        self.syncprogress.setMinimum(0)
        self.syncprogress.setMaximum(100)
        self.syncprogress.setValue(0)
        self.vml.addWidget(self.syncprogress)
        self.sync = QPushButton()
        self.sync.setText(self.tr('Synchronize'))
        self.vml.addWidget(self.sync)
        self.sync.clicked.connect(self.sync_click)
        self.statuslbl = QLabel('')
        self.vml.addWidget(self.statuslbl)
        self.vml.addStretch(1)
        self.setLayout(self.vml)

    @pyqtSlot()
    def sync_click(self):
        self.statuslbl.setText(self.tr('Synchronization started'))
        self.syncprogress.setValue(0)
        apiurl = self.database.getConfigStr('APIURL')
        if apiurl is None:
            return
        apiuser = self.database.getConfigStr('APIUSER')
        if apiuser is None:
            return
        apipw = self.database.getConfigStr('APIPW')
        if apipw is None:
            return
        apirealm = self.database.getConfigStr('APIREALM')
        if apirealm is None:
            return
        syncstatus = True
        try:
            auth_handler = request.HTTPBasicAuthHandler()
            auth_handler.add_password(realm=apirealm,
                                      uri=apiurl + 'upload',
                                      user=apiuser,
                                      passwd=apipw)
            opener = request.build_opener(auth_handler)
            self.statuslbl.setText(self.tr('Synchronizing cars'))
            cars = self.database.getCarsForSync()
            self.syncprogress.setValue(10)
            if cars is not None and len(cars) > 0:
                params = {
                    'cars': str(json.dumps(cars))
                }
                data = parse.urlencode(params)
                data = data.encode('ascii')
                response = opener.open(apiurl + 'upload', data, 15.0)
                response_data = response.read().decode('utf-8')
                print(response_data)
                carsr = json.loads(response_data)
                self.database.setCarsSync(carsr['cars'])
                self.syncprogress.setValue(15)
            self.statuslbl.setText(self.tr('Synchronizing players'))
            players = self.database.getPlayersForSync()
            # print(players)
            self.syncprogress.setValue(20)
            if players is not None and len(players) > 0:
                params = {
                    'players': str(json.dumps(players))
                }
                data = parse.urlencode(params)
                data = data.encode('ascii')
                response = opener.open(apiurl + 'upload', data, 15.0)
                response_data = response.read().decode('utf-8')
                playersr = json.loads(response_data)
                self.database.setPlayersSync(playersr['players'])
                self.syncprogress.setValue(25)
            self.statuslbl.setText(self.tr('Synchronizing racing players'))
            racingplayers = self.database.getRacingPlayersForSync()
            # print(racingplayers)
            if racingplayers is not None and len(racingplayers) > 0:
                params = {
                    'racingplayers': str(json.dumps(racingplayers))
                }
                data = parse.urlencode(params)
                data = data.encode('ascii')
                response = opener.open(apiurl + 'upload', data, 15.0)
                response_data = response.read().decode('utf-8')
                racingplayersr = json.loads(response_data)
                self.database.setRacingPlayersSync(racingplayersr['racingplayers'])
                self.syncprogress.setValue(30)
            self.statuslbl.setText(self.tr('Synchronizing laps'))
            laps = self.database.getLapsForSync()
            # print(laps)
            if laps is not None and len(laps) > 0:
                params = {
                    'laps': str(json.dumps(laps))
                }
                data = parse.urlencode(params)
                data = data.encode('ascii')
                response = opener.open(apiurl + 'upload', data, 15.0)
                response_data = response.read().decode('utf-8')
                lapsr = json.loads(response_data)
                self.database.setLapsSync(lapsr['laps'])
                self.syncprogress.setValue(35)
            self.statuslbl.setText(self.tr('Synchronizing competitions'))
            competitions = self.database.getCompetitionsForSync(ShowDetails())
            print(competitions)
            if competitions is not None and len(competitions) > 0:
                params = {
                    'competitions': str(json.dumps(competitions))
                }
                data = parse.urlencode(params)
                data = data.encode('ascii')
                response = opener.open(apiurl + 'upload', data, 15.0)
                response_data = response.read().decode('utf-8')
                competitionsr = json.loads(response_data)
                self.database.setCompetitionsSync(competitionsr['competitions'])
                self.syncprogress.setValue(80)

            self.statuslbl.setText(self.tr('Synchronizing settings'))
            tracklength = self.database.getConfigStr('TRACKLENGTH')
            if tracklength is not None:
                params = {
                    'tracklength': str(tracklength)
                }
                data = parse.urlencode(params)
                data = data.encode('ascii')
                response = opener.open(apiurl + 'upload', data, 15.0)
                response_data = response.read().decode('utf-8')
                tracklengthr = json.loads(response_data)
                print(tracklengthr)
                self.syncprogress.setValue(95)
        except (error.HTTPError, error.URLError, JSONDecodeError) as e:
            syncstatus = False
            self.statuslbl.setText(
                self.tr('Synchronization failed: ') + str(e))
            print(e)
        if syncstatus:
            self.syncprogress.setValue(100)
            self.statuslbl.setText(
                self.tr('Synchronization successfully finished'))
        else:
            self.syncprogress.setValue(0)

    @pyqtSlot()
    def apiurl_finished(self):
        apiurl = str(self.apiurl.text()).strip()
        self.database.setConfig('APIURL', apiurl)

    @pyqtSlot()
    def apiuser_finished(self):
        apiuser = str(self.apiuser.text()).strip()
        self.database.setConfig('APIUSER', apiuser)

    @pyqtSlot()
    def apipw_finished(self):
        apipw = str(self.apipw.text()).strip()
        self.database.setConfig('APIPW', apipw)

    @pyqtSlot()
    def apirealm_finished(self):
        apirealm = str(self.apirealm.text()).strip()
        self.database.setConfig('APIREALM', apirealm)


class Settings(QWidget):

    def __init__(self, parent=None, database=None):
        super().__init__(parent)
        self.database = database
        self.vbox = QVBoxLayout(self)
        self.headFont = QFont()
        self.headFont.setPointSize(33)
        self.headFont.setBold(True)
        self.headline = QLabel(self.tr('Settings'))
        self.headline.setFont(self.headFont)
        self.vbox.addWidget(self.headline)
        self.settab = QTabWidget()
        self.vbox.addWidget(self.settab)
        self.coreset = CoreSet(database=self.database)
        self.settab.addTab(self.coreset, self.tr('Core'))
        self.carset = CarSet(database=self.database)
        self.settab.addTab(self.carset, self.tr('Cars'))
        self.playerset = PlayerSet(database=self.database)
        self.settab.addTab(self.playerset, self.tr('Drivers'))
        self.syncset = SyncSet(database=self.database)
        self.settab.addTab(self.syncset, self.tr('Sync'))
        self.back = QPushButton()
        self.back.setText(self.tr('Back'))
        self.back.clicked.connect(self.back_click)
        self.vbox.addWidget(self.back)
        self.setLayout(self.vbox)

    @pyqtSlot()
    def back_click(self):
        dc = {}
        try:
            for i in range(0, 6):
                if self.coreset.controller.getOk(i) is True:
                    dc[i] = {
                        'pos': 1,
                        'name': self.coreset.controller.getName(i),
                        'car': self.coreset.controller.getCar(i)
                    }
            self.database.setConfig('DEFAULT_DRIVERS', str(json.dumps(dc)))
            self.parent().parent().setDefaultDrivers()
            self.parent().parent().showHome()
        except KeyError:
            pass
