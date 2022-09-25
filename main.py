from PyQt5 import QtCore, QtWidgets, uic
import sys, gc
import requests


class CapControl():
    def __init__(self, url):
        self.url = url

    def connect(self):
        return requests.get(self.url + "/settings")

    def get_move(self, dir, step, speed):
        req = F"dir : {dir}, step : {step}, speed {speed}"
        return requests.post(self.url, json=req)


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        # Load the UI Page
        uic.loadUi('ui.ui', self)
        self.initUI()
        self.url = self.url_lineEdit.text()
        self.cap_ctrl = CapControl(self.url)
        self.connected = False
        self.direction = None
        self.step = None
        self.speed = None

    def initUI(self):
        self.upButton.clicked.connect(self.upButton_click)
        self.downButton.clicked.connect(self.downButton_click)
        self.connectButton.clicked.connect(self.connectButton_click)
        self.fineTuning.valueChanged.connect(self.fineTune)
        self.comboInit()

    def comboInit(self):
        self.step_comboBox.addItem("1")
        self.step_comboBox.addItem("5")
        self.step_comboBox.addItem("10")
        self.step_comboBox.addItem("25")
        self.step_comboBox.addItem("50")
        self.step_comboBox.addItem("100")
        self.step_comboBox.addItem("250")
        self.step_comboBox.addItem("500")
        self.step_comboBox.currentIndexChanged.connect(self.step_change)
        self.speed_comboBox.addItem("Low")
        self.speed_comboBox.addItem("Normal")
        self.speed_comboBox.addItem("High")
        self.speed_comboBox.currentIndexChanged.connect(self.speed_change)

    def upButton_click(self):
        print("Up")

    def downButton_click(self):
        print("Down")

    def fineTune(self):
        print(self.fineTuning.value())

    def step_change(self):
        print(self.step_comboBox.currentText())

    def speed_change(self):
        print(self.speed_comboBox.currentText())

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
