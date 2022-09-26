import gc
import sys
import json as jconf
import requests
from PyQt5 import QtCore, QtWidgets, uic



def extended_exception_hook(exctype, value, traceback):
    # Print the error and traceback
    print(exctype, value, traceback)
    # Call the normal Exception hook after
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)

class Jconfig():
    def __init__(self):
        pass

    def get_config(self):
        try:
            with open("config.json", "r") as f:
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

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        # Load the UI Page
        uic.loadUi('ui.ui', self)
        self.statuslabel = QtWidgets.QLabel("Статус: ")
        self.statusbar.addPermanentWidget(self.statuslabel)
        self.statusbar.reformat()
        # self.setStylesheet("stylesheets/cap_control.qss")
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
        self.initUI()
        self.configure()

    def configure(self):
        config = self.jconfig.get_config()
        if "api" in config:
            api = config["api"]
            self.url = api["url"]
            self.api_move = api["move"]
            self.api_park = api["park"]
            self.api_status = api["status"]
            self.url_lineEdit.setText(self.url)
            self.cap_ctrl = CapControl()
        else:
            raise KeyError("Error: Key 'api' not found in config file.")
    def initUI(self):
        self.upButton.clicked.connect(self.upButton_click)
        self.downButton.clicked.connect(self.downButton_click)
        self.connectButton.clicked.connect(self.connectButton_click)
        self.fineTuning.valueChanged.connect(self.fineTune)
        self.parkButton.clicked.connect(self.parkButton_click)
        self.comboInit()
        self.step = self.step_comboBox.currentText()
        self.speed = self.speed_comboBox.currentText()

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
        self.step_comboBox.addItem("10")
        self.step_comboBox.addItem("25")
        self.step_comboBox.addItem("50")
        self.step_comboBox.addItem("100")
        self.step_comboBox.addItem("250")
        self.step_comboBox.addItem("500")
        self.step_comboBox.setCurrentIndex(3)
        self.step_comboBox.currentIndexChanged.connect(self.step_change)
        self.speed_comboBox.addItem("5")
        self.speed_comboBox.addItem("10")
        self.speed_comboBox.addItem("16")
        self.speed_comboBox.setCurrentIndex(1)
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
