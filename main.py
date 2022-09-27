import gc
import sys
import json as jconf
import requests
from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtCore import (QDate, QDateTime, QRegExp, QSortFilterProxyModel, Qt,
                          QTime)


def extended_exception_hook(exctype, value, traceback):
    # Print the error and traceback
    print(exctype, value, traceback)
    # Call the normal Exception hook after
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)


class AddDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('add_dialog.ui', self)

    def set_fields_values(self, band, step, desc):
        self.bandlineEdit.setText(band)
        self.steplineEdit.setText(step)
        self.desclineEdit.setText(desc)

    def get_fields_values(self):
        band = self.bandlineEdit.text()
        step = self.steplineEdit.text()
        desc = self.desclineEdit.text()
        return {"band": band, "step" : step, "desc" : desc}


class Jconfig():
    def __init__(self):
        pass

    def get_config(self):
        try:
            with open("api.json", "r") as f:
                config = jconf.load(f)
            return config
        except:
            raise FileNotFoundError("File config.json not found.")

    def get_defaults(self):
        try:
            with open("stored_defaults.json", "r") as f:
                config = jconf.load(f)
            return config
        except:
            raise FileNotFoundError("File config.json not found.")


class CapControl():
    def __init__(self):
        pass

    def connect(self, url):
        # Реалізувати обробку помилки
        req = requests.get(url + "/settings")
        return req


class VLine(QtWidgets.QFrame):
    # a simple VLine, like the one you get from designer
    def __init__(self):
        super(VLine, self).__init__()
        self.setFrameShape(self.VLine | self.Sunken)


class MainWindow(QtWidgets.QMainWindow):
    BAND, STEPS, DESCRIPTION = range(3)

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        # Load the UI Page
        uic.loadUi('ui.ui', self)
        self.statuslabel = QtWidgets.QLabel("Статус: ")
        self.statusbar.addPermanentWidget(self.statuslabel)
        self.statusbar.reformat()
        self.setStylesheet("stylesheets/cap_control.qss")
        self.add_dialog = AddDialog()
        # Main Timer
        self.main_Timer = QtCore.QTimer()
        self.main_Timer.timeout.connect(self.mainTimer)
        self.main_Timer.start(5000)
        # Variables
        self.jconfig = Jconfig()
        self.connected = False
        self.direction = None
        self.step = None
        self.speed = None
        self.current_position = None
        self.max_position = None
        self.api_status = None
        self.api_park = None
        self.api_move = None
        self.url = None
        self.cap_ctrl = CapControl()
        self.initUI()
        self.configure()
        self.bandTreeViewConfig()

    def store_defaults(self):
        defaults = {"defaults": {"step": self.step, "speed": self.speed}}
        defaults = jconf.dumps(defaults, indent=4)
        jsondefs = jconf.loads(defaults)
        try:
            with open("stored_defaults.json", "w") as f:
                jconf.dump(jsondefs, f)
        except:
            raise FileNotFoundError("File stored_defaults.json not found.")

    def configure(self):
        config = self.jconfig.get_config()
        if "api" in config:
            api = config["api"]
            self.url = api["url"]
            self.api_move = api["move"]
            self.api_park = api["park"]
            self.api_status = api["status"]
            self.url_lineEdit.setText(self.url)
        else:
            raise KeyError("Error: Key 'api' not found in config file.")
        defaults = self.jconfig.get_defaults()
        if "defaults" in defaults:
            d = defaults["defaults"]
            self.step = d["step"]
            self.speed = d["speed"]
            step_index = self.step_comboBox.findText(self.step)
            self.step_comboBox.setCurrentIndex(step_index)
            speed_index = self.speed_comboBox.findText(self.speed)
            self.speed_comboBox.setCurrentIndex(speed_index)
        else:
            raise KeyError("Error: Key 'defaults' not found in config file.")

    def bandTreeViewConfig(self):
        self.bandtreeView.setRootIsDecorated(False)
        self.bandtreeView.setAlternatingRowColors(True)
        model = self.createBandTreeModel(self)
        self.bandtreeView.setModel(model)
        self.addTreeItem(model, '40M', '8500', '7,000 - 7,200')

    def createBandTreeModel(self, parent):
        model = QStandardItemModel(0, 3, parent)
        model.setHeaderData(self.BAND, Qt.Horizontal, "Діапазон")
        model.setHeaderData(self.STEPS, Qt.Horizontal, "Кроки")
        model.setHeaderData(self.DESCRIPTION, Qt.Horizontal, "Опис")
        return model

    def addTreeItem(self, model, band, steps, desc):
        model.insertRow(0)
        model.setData(model.index(0, self.BAND), band)
        model.setData(model.index(0, self.STEPS), steps)
        model.setData(model.index(0, self.DESCRIPTION), desc)

    def initUI(self):
        self.upButton.clicked.connect(self.upButton_click)
        self.downButton.clicked.connect(self.downButton_click)
        self.connectButton.clicked.connect(self.connectButton_click)
        self.fineTuning.valueChanged.connect(self.fineTune)
        self.parkButton.clicked.connect(self.parkButton_click)
        self.addButton.clicked.connect(self.addButton_click)
        self.comboInit()

    def addButton_click(self):
        self.add_dialog.set_fields_values("Діапазон", self.current_position_label.text(), "")
        answer = self.add_dialog.exec()
        if answer == AddDialog.Accepted:
            print(self.add_dialog.get_fields_values())
        else:
            print("Cancel")



    def get_info(self):
        if self.connected:
            resp = requests.get(self.url + self.api_status)
            json = resp.json()
            if 'step_count' in json:
                self.current_position_label.setText(str(json['step_count']))
                self.current_position = int(json['step_count'])
                self.max_position = int(json['max_position'])
                self.fineTuning.setMaximum(self.max_position)
                self.fineTuning.setValue(int(self.current_position))
            if 'status' in json:
                self.statuslabel.setText(F"Статус: {json['status']}")
        else:
            self.statusbar.showMessage("Не з'єднано")

    def mainTimer(self):
        gc.collect()

    def moveTo(self, dir, step, speed):
        if self.connected:
            json = {'dir': dir, 'step': step, 'speed': speed}
            resp = requests.post(self.url + self.api_move, json=json)
            json = resp.json()
            if 'step_count' in json:
                self.current_position_label.setText(str(json['step_count']))
            if 'status' in json:
                self.statuslabel.setText(F"Статус: {json['status']}")

    def setStylesheet(self, filename):
        with open(filename, "r") as fh:
            self.setStyleSheet(fh.read())

    def comboInit(self):
        step_items = ["1", "5", "10", "25", "50", "100", "250", "500"]
        speed_items = ["5", "10", "16"]
        self.step_comboBox.addItems(step_items)
        self.step_comboBox.currentIndexChanged.connect(self.step_change)
        self.speed_comboBox.addItems(speed_items)
        self.speed_comboBox.currentIndexChanged.connect(self.speed_change)

    def parkButton_click(self):
        if self.connected:
            resp = requests.get(self.url + self.api_park)
            json = resp.json()
            if 'step_count' in json:
                print(json['step_count'])
                self.current_position_label.setText(str(json['step_count']))
            if 'status' in json:
                self.statuslabel.setText(F"Статус: {json['status']}")

    def upButton_click(self):
        self.moveTo(0, self.step, self.speed)
        self.fineTuning.setValue(int(self.current_position))

    def downButton_click(self):
        self.moveTo(1, self.step, self.speed)
        self.fineTuning.setValue(int(self.current_position))

    def fineTune(self):
        if self.connected:
            if self.fineTuning.value() > self.current_position:
                self.moveTo(0, 1, 15)
            else:
                self.moveTo(1, 1, 15)

    def step_change(self):
        self.step = self.step_comboBox.currentText()

    def speed_change(self):
        self.speed = self.speed_comboBox.currentText()

    def connectButton_click(self):
        self.url = self.url_lineEdit.text()
        json = self.cap_ctrl.connect(self.url).json()
        if 'ip' in json:
            self.statusbar.showMessage(json['ip'] + " з'єднано")
            self.connected = True
            self.get_info()
        else:
            self.statusbar.showMessage("Error: No API found, check URI")
            self.connected = False

    def closeEvent(self, event):
        print("Closing")
        self.store_defaults()
        print("Storing defaults")
        event.accept()
        sys.exit()


def main():
    sys._excepthook = sys.excepthook
    sys.excepthook = extended_exception_hook
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
