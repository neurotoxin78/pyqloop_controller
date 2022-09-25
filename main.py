import gc
import sys

import requests
from PyQt5 import QtCore, QtWidgets, uic


class CapControl():
    def __init__(self, url):
        self.url = url

    def connect(self):
        return requests.get(self.url + "/settings")


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
        self.statuslabel.setStyleSheet('border: 0; color:  blue;')
        self.url = self.url_lineEdit.text()
        self.statusbar.addPermanentWidget(self.statuslabel)
        self.statusbar.reformat()
        self.statusbar.setStyleSheet('border: 0; background-color: #FFF8DC;')
        self.statusbar.setStyleSheet("QStatusBar::item {border: none;}")
        self.setStylesheet("stylesheets/MacOs.qss")
        # Main Timer
        self.main_Timer = QtCore.QTimer()
        self.main_Timer.timeout.connect(self.mainTimer)
        self.main_Timer.start(5000)
        # Variables
        self.api_move = "/move"
        self.api_park = "/park"
        self.api_status = "/status"
        self.cap_ctrl = CapControl(self.url)
        self.connected = False
        self.direction = None
        self.step = None
        self.speed = None
        self.current_position = None
        self.max_position = None
        self.initUI()

    def initUI(self):
        self.upButton.clicked.connect(self.upButton_click)
        self.downButton.clicked.connect(self.downButton_click)
        self.connectButton.clicked.connect(self.connectButton_click)
        self.fineTuning.valueChanged.connect(self.fineTune)
        self.parkButton.clicked.connect(self.parkButton_click)
        self.comboInit()
        self.initVariables()

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

    def initVariables(self):
        self.step = self.step_comboBox.currentText()
        self.speed = self.speed_comboBox.currentText()

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
        json = self.cap_ctrl.connect().json()
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
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
