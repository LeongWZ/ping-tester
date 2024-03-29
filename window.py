from PySide6.QtWidgets import QTableView, QPushButton, QGridLayout, QWidget, QHeaderView, QSizePolicy, QMessageBox, QCheckBox, QApplication
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor
from PySide6.QtCore import Slot, QThreadPool, Qt

from concurrentpingthread import ConcurrentPingThread
from intervalpingthread import IntervalPingThread
from exitprogresswindow import ExitProgressWindow

import os
import json
import time


class Window(QWidget):
    '''
    GUI window for Ping Tester
    Developed using PySide6 module (Qt 6 framework)
    '''

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ping Tester")
        self.resize(800, 400)

        self.server_list = self.getServers()

        self.activePingThreads = 0
        self.pingThread_list = list()
        self.threadpool = QThreadPool()

        self.initUI()

        self.show()

        self.exit = False

    def initUI(self):
        layout = QGridLayout()

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 18)
        layout.setColumnStretch(2, 1)

        # Exit progress window
        # Add this widget first before others and hide it
        self.exitProgressWindow = ExitProgressWindow(self)
        layout.addWidget(self.exitProgressWindow, 0, 1, 2, 1, Qt.AlignCenter)
        self.exitProgressWindow.hide()

        buttonLayout = QGridLayout()
        layout.addLayout(buttonLayout, 0, 1, 1, 1, Qt.AlignLeft)
        
        self.simultaneousCheckBox = QCheckBox("Ping simultaneously")
        self.simultaneousCheckBox.setFocusPolicy(Qt.NoFocus)
        buttonLayout.addWidget(self.simultaneousCheckBox, 0, 0)

        self.checkAllButton = QPushButton("Check All")
        self.checkAllButton.clicked.connect(self.checkAll)
        self.checkAllButton.setFocusPolicy(Qt.NoFocus)
        buttonLayout.addWidget(self.checkAllButton, 1, 0)

        self.uncheckAllButton = QPushButton("Uncheck All")
        self.uncheckAllButton.clicked.connect(self.uncheckAll)
        self.uncheckAllButton.setFocusPolicy(Qt.NoFocus)
        buttonLayout.addWidget(self.uncheckAllButton, 2, 0)

        self.startButton = QPushButton("Start")
        self.startButton.clicked.connect(self.start)
        self.startButton.setFocusPolicy(Qt.NoFocus)
        self.startButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        buttonLayout.addWidget(self.startButton, 1, 1, 2, 1)

        self.stopButton = QPushButton("Stop")
        self.stopButton.clicked.connect(self.stop)
        self.stopButton.setFocusPolicy(Qt.NoFocus)
        self.stopButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        buttonLayout.addWidget(self.stopButton, 1, 2, 2, 1)

        self.resetButton = QPushButton("Reset")
        self.resetButton.clicked.connect(self.reset)
        self.resetButton.setFocusPolicy(Qt.NoFocus)
        self.resetButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        buttonLayout.addWidget(self.resetButton, 1, 3, 2, 1)

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Name", "IP Address", "Status", "Last Time\nResponse", "Current", "Min", "Max", "Avg"])
        
        for server in self.server_list:
            name = QStandardItem(server[0])
            name.setCheckable(True)
            self.model.appendRow([name, QStandardItem(server[1]), QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem()])
        
        self.tableview = QTableView()
        self.tableview.setModel(self.model)
        self.tableview.setEditTriggers(QTableView.NoEditTriggers)
        self.tableview.setFocusPolicy(Qt.NoFocus)
        self.tableview.setSelectionMode(QTableView.NoSelection)

        header = self.tableview.horizontalHeader()
        for i in range(5, 8):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
            
        layout.addWidget(self.tableview, 1, 1)
        
        self.setLayout(layout)

        # info message box
        self.infoMsgBox = QMessageBox()
        self.infoMsgBox.setWindowTitle("Ping Tester - Info")
        self.infoMsgBox.setIcon(QMessageBox.Information)
        self.infoMsgBox.setStandardButtons(QMessageBox.Cancel)

        # warning message box
        self.warningMsgBox = QMessageBox()
        self.warningMsgBox.setWindowTitle("Ping Tester - Warning")
        self.warningMsgBox.setIcon(QMessageBox.Warning)
        self.warningMsgBox.setStandardButtons(QMessageBox.Cancel)
    
    def getServers(self) -> dict:
        json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "server_list.json")

        if os.path.isfile(json_path) and os.access(json_path, os.R_OK):
            with open(json_path) as json_file:
                d = json.load(json_file)
        else:
            with open(json_path, 'w') as json_file:
                d = {
                    "Google 1": "8.8.4.4",
                    "Google 2": "8.8.8.8"
                }
                
                json_file.write(json.dumps(d))

        server_list = []
        for name in d:
            server_list.append((name, d[name]))
        
        return server_list

    def checkAll(self):
        for row in range(self.model.rowCount()):
            if self.model.item(row, 0).isCheckable() and self.model.item(row, 0).checkState() == Qt.CheckState.Unchecked:
                self.model.item(row, 0).setCheckState(Qt.CheckState.Checked)

    def uncheckAll(self):
        for row in range(self.model.rowCount()):
            if self.model.item(row, 0).isCheckable() and self.model.item(row, 0).checkState() == Qt.CheckState.Checked:
                self.model.item(row, 0).setCheckState(Qt.CheckState.Unchecked)

    @Slot()
    def start(self):
        self.startButton.setEnabled(False)
        self.simultaneousCheckBox.setEnabled(False)
        if self.simultaneousCheckBox.isChecked():
            self.simultaneousPing()
        else:
            self.intervalPing()

    def simultaneousPing(self):
        for row, server in enumerate(self.server_list):
            if self.model.item(row, 0).checkState() == Qt.CheckState.Checked:
                self.model.item(row, 0).setCheckable(False)

                ip_address = server[1]
                t = ConcurrentPingThread(row, ip_address)
                t.signals.started.connect(self.on_start)
                t.signals.result.connect(self.update_result)
                t.signals.error.connect(self.on_error)
                t.signals.finished.connect(self.on_finished)

                self.pingThread_list.append(t)

        if len(self.pingThread_list) == 0:
            self.infoMsgBox.setText(f"No IP address has been selected")
            self.infoMsgBox.setInformativeText("Select an IP address by ticking the checkbox beside its name")
            self.infoMsgBox.exec()
            self.startButton.setEnabled(True)
            self.simultaneousCheckBox.setEnabled(True)
            return
        
        if len(self.pingThread_list) > self.threadpool.maxThreadCount():
            self.warningMsgBox.setText(f"Up to a maximum of {self.threadpool.maxThreadCount()} IP address can be simultaneously tested")
            self.warningMsgBox.setInformativeText(f"{len(self.pingThread_list)} IP address have been selected")
            self.warningMsgBox.exec()
            for pingThread in self.pingThread_list:
                self.model.item(pingThread.row, 0).setCheckable(True)
            del self.pingThread_list[:]
            self.startButton.setEnabled(True)
            self.simultaneousCheckBox.setEnabled(True)
            return

        for thread in self.pingThread_list:
            self.threadpool.start(thread)

    def intervalPing(self):
        rowIP_pairs = list()
        for row, server in enumerate(self.server_list):
            if self.model.item(row, 0).checkState() == Qt.CheckState.Checked:
                self.model.item(row, 0).setCheckable(False)
                ip_address = server[1]
                rowIP_pairs.append((row, ip_address))

        if len(rowIP_pairs) > 0:
            t = IntervalPingThread(rowIP_pairs)
            t.signals.started.connect(self.on_start)
            t.signals.result.connect(self.update_result)
            t.signals.error.connect(self.on_error)
            t.signals.finished.connect(self.on_finished)

            self.pingThread_list.append(t)
            self.threadpool.start(t)
        else:
            self.infoMsgBox.setText(f"No IP address has been selected")
            self.infoMsgBox.setInformativeText("Select an IP address by ticking the checkbox beside its name")
            self.infoMsgBox.exec()
            self.startButton.setEnabled(True)
            self.simultaneousCheckBox.setEnabled(True)
            
    @Slot()
    def stop(self):
        if len(self.pingThread_list) == 0:
            return

        for pingThread in self.pingThread_list:
            if pingThread.enabled:
                pingThread.enabled = False

    @Slot()
    def reset(self):
        try:
            # Reset during interval ping
            for pingTest in self.pingThread_list[0].pingTests:
                del pingTest.successQueue[:]
                pingTest.i = 0
                pingTest.lastResponseTime = ""
                pingTest.Min = None
                pingTest.Max = None
                pingTest.Avg = 0
        except IndexError:
            # Reset when there is no ping
            pass
        except AttributeError:
            # Reset during simultaneous ping
            for pingThread in self.pingThread_list:
                del pingThread.successQueue[:]
                pingThread.i = 0
                pingThread.lastResponseTime = ""
                pingThread.Min = None
                pingThread.Max = None
                pingThread.Avg = 0

        for row in range(self.model.rowCount()):
            if self.model.item(row, 2).text() == "Error, see Current" and self.activePingThreads > 0:
                for i in range(5, 8):
                    self.model.item(row, i).setText("")
            else:
                self.model.item(row, 2).setBackground(self.model.item(row, 1).background())
                for i in range(2, 8):
                    self.model.item(row, i).setText("")

    @Slot()
    def on_start(self):
        self.activePingThreads += 1

    @Slot()
    def on_error(self, error):
        self.model.item(error[0], 2).setText("Error, see Current")
        self.model.item(error[0], 2).setBackground(QColor("red"))
        self.model.item(error[0], 4).setText(str(error[2]))
    
    @Slot()
    def update_result(self, result):
        status = f"{result[1]} %"
        if self.model.item(result[0], 2).text() != status:
            # Status
            self.model.item(result[0], 2).setText(status)
        
            if result[1] >= 90:
                self.model.item(result[0], 2).setBackground(QColor(0, 153, 0))
            elif result[1] >= 70:
                self.model.item(result[0], 2).setBackground(QColor(102, 204, 0))
            elif result[1] >= 20:
                self.model.item(result[0], 2).setBackground(QColor("yellow"))
            else:
                self.model.item(result[0], 2).setBackground(QColor("red"))

        # Last Time Response
        self.model.item(result[0], 3).setText(result[2])

        # Current
        self.model.item(result[0], 4).setText(result[3][0])

        # Min
        self.model.item(result[0], 5).setText(result[3][1])

        # Max
        self.model.item(result[0], 6).setText(result[3][2])

        # Avg
        self.model.item(result[0], 7).setText(result[3][3])

    @Slot()
    def on_finished(self):
        self.activePingThreads -= 1
        if self.activePingThreads > 0:
            return
        
        if self.simultaneousCheckBox.isChecked():    
            for pingThread in self.pingThread_list:
                self.model.item(pingThread.row, 0).setCheckable(True)
                if self.model.item(pingThread.row, 2).text() != "Error, see Current":
                    self.model.item(pingThread.row, 2).setText("")
                    self.model.item(pingThread.row, 2).setBackground(self.model.item(pingThread.row, 1).background())
                    self.model.item(pingThread.row, 4).setText("")
        else:
            for pingTest in self.pingThread_list[0].pingTests:
                self.model.item(pingTest.row, 0).setCheckable(True)
                if self.model.item(pingTest.row, 2).text() != "Error, see Current":
                    self.model.item(pingTest.row, 2).setText("")
                    self.model.item(pingTest.row, 2).setBackground(self.model.item(pingTest.row, 1).background())
                    self.model.item(pingTest.row, 4).setText("")

        del self.pingThread_list[:]
        self.startButton.setEnabled(True)
        self.simultaneousCheckBox.setEnabled(True)
            
    def launchExitProgress(self):
        self.exitProgressWindow.show()
        self.exitProgressWindow.raise_()

        if self.activePingThreads == 0:
            self.exitProgressWindow.progressBar.setMinimum(-1)
            self.exitProgressWindow.progressBar.setValue(-1)
        else:
            self.exitProgressWindow.progressBar.setMinimum(0)
            self.exitProgressWindow.progressBar.setValue(0)

        self.exitProgressWindow.progressBar.setMaximum(self.activePingThreads)

    def closeEvent(self, event):
        if self.exit:
            return

        self.exit = True
        self.launchExitProgress()

        for pingThread in self.pingThread_list:
            if pingThread.enabled:
                pingThread.enabled = False

        activeThreadCount = self.threadpool.activeThreadCount()
        while activeThreadCount >= 0:
            killedThreadCount = self.exitProgressWindow.progressBar.maximum() - activeThreadCount
            if killedThreadCount > self.exitProgressWindow.progressBar.value():
                self.exitProgressWindow.progressBar.setValue(killedThreadCount)
                QApplication.processEvents()
                
            if activeThreadCount == 0:
                time.sleep(0.3)
                break

            activeThreadCount = self.threadpool.activeThreadCount()
        
        self.threadpool.waitForDone(1000)
        super().closeEvent(event)
