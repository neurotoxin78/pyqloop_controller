from PyQt5 import QtCore, QtWidgets, uic
import sys, gc
import requests


class CapControl():
    def __init__(self, url):
        self.url = url

    def connect(self):
        return requests.get(self.url + "/settings")

class VLine(QtWidgets.QFrame):
    # a simple VLine, like the one you get from designer
    def __init__(self):
        super(VLine, self).__init__()
        self.setFrameShape(self.VLine|self.Sunken)

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        # Load the UI Page
        uic.loadUi('ui.ui', self)
        self.setStylesheet("stylesheets/MacOs.qss")
        self.statuslabel = QtWidgets.QLabel("Статус: ")
        self.statuslabel.setStyleSheet('border: 0; color:  blue;')
        self.url = self.url_lineEdit.text()
        self.statusbar.addPermanentWidget(self.statuslabel)
        self.statusbar.reformat()
        self.statusbar.setStyleSheet('border: 0; background-color: #FFF8DC;')
        self.statusbar.setStyleSheet("QStatusBar::item {border: none;}")
        #Variables
        self.api_move = "/move"
        self.api_park = "/park"
        self.cap_ctrl = CapControl(self.url)
        self.connected = False
        self.direction = None
        self.step = None
        self.speed = None
        self.initUI()


    def initUI(self):
        self.upButton.clicked.connect(self.upButton_click)
        self.downButton.clicked.connect(self.downButton_click)
        self.connectButton.clicked.connect(self.connectButton_click)
        self.fineTuning.valueChanged.connect(self.fineTune)
        self.parkButton.clicked.connect(self.parkButton_click)
        self.comboInit()
        self.initVariables()

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
        self.step_comboBox.currentIndexChanged.connect(self.step_change)
        self.speed_comboBox.addItem("5")
        self.speed_comboBox.addItem("10")
        self.speed_comboBox.addItem("16")
        self.speed_comboBox.currentIndexChanged.connect(self.speed_change)

    def parkButton_click(self):
        resp = requests.get(self.url + self.api_park)
        json = resp.json()
        if 'step_count' in json:
            print(json['step_count'])
            self.current_position_label.setText(str(json['step_count']))
        if 'status' in json:
            self.statuslabel.setText(F"Статус: {json['status']}")


    def upButton_click(self):
        if self.connected:
            json = {'dir': 0, 'step': self.step, 'speed': self.speed}
            resp = requests.post(self.url + self.api_move, json=json)
            json = resp.json()
            if 'step_count' in json:
                self.current_position_label.setText(str(json['step_count']))
            if 'status' in json:
                self.statuslabel.setText(F"Статус: {json['status']}")


    def downButton_click(self):
        if self.connected:
            json = {'dir': 1, 'step': self.step, 'speed': self.speed}
            print(json)
            resp = requests.post(self.url + self.api_move, json=json)
            json = resp.json()
            if 'step_count' in json:
                print(json['step_count'])
                self.current_position_label.setText(str(json['step_count']))
            if 'status' in json:
                self.statuslabel.setText(F"Статус: {json['status']}")

    def fineTune(self):
        print(self.fineTuning.value())

    def step_change(self):
        self.step = self.step_comboBox.currentText()

    def speed_change(self):
        self.speed = self.speed_comboBox.currentText()

    def connectButton_click(self):
        json = self.cap_ctrl.connect().json()
        if 'ip' in json:
            self.statusbar.showMessage(json['ip'] + ' connected')
            self.connected = True
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
