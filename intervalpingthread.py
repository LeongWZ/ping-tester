from PySide6.QtCore import QObject, QRunnable, QDateTime

from pingthreadsignals import PingThreadSignals

import platform
import subprocess
import sys
import traceback
import re
import ipaddress


class IntervalPingThread(QRunnable):
    def __init__(self, rowIP_pairs):
        super().__init__()

        self.rowIP_pairs = rowIP_pairs
        self.signals = PingThreadSignals()
        self.system = platform.system()
        self.enabled = None
        self.pingTests = None

    def run(self):
        self.pingTest()

    def pingTest(self):
        self.enabled = True
        self.signals.started.emit()

        self.pingTests = self.getPingTests()
        while self.enabled:
            for test in self.pingTests:
                if test.enabled:
                    test.run()
                if not self.enabled:
                    break
        
        self.signals.finished.emit()

    def getPingTests(self):
        pingTests = list()
        for rowIP in self.rowIP_pairs:
            row = rowIP[0]
            ip_address = rowIP[1]
            pingTests.append(IntervalPingTest(self, row, ip_address))

        return pingTests

class IntervalPingTest(QObject):
    def __init__(self, parent, row, ip_address):
        super().__init__()

        self.parent = parent
        self.row = row
        self.ip_address = ip_address
        self.enabled = True

        self.successQueue = []

        self.i = 0
        self.lastResponseTime = ""
        self.Min = None
        self.Max = None
        self.Avg = 0

    def run(self):
        if not self.isIPAddressValid():
            self.enabled = False
            return

        try:
            ping_response = self.ping()
        except:
            exctype, value = sys.exc_info()[:2]
            self.parent.signals.error.emit((self.row, exctype, value, traceback.format_exc()))
            self.enabled = False
            return

        if len(ping_response) == 4 and len(self.successQueue) < 10:
            self.successQueue.append(1)

            self.lastResponseTime = ping_response[0]

            current = ping_response[3]
            self.Min = min(self.Min, ping_response[1]) if self.Min is not None else ping_response[1]
            self.Max = max(self.Max, ping_response[2]) if self.Max is not None else ping_response[2]
            self.Avg = round((self.i * self.Avg + current) / (self.i + 1))
            stats = [f"{current} ms", f"{self.Min} ms", f"{self.Max} ms", f"{self.Avg} ms"]
            self.i += 1
        elif len(ping_response) == 4:
            self.successQueue.pop(0)
            self.successQueue.append(1)

            self.lastResponseTime = ping_response[0]

            current = ping_response[3]
            self.Min = min(self.Min, ping_response[1]) if self.Min is not None else ping_response[1]
            self.Max = max(self.Max, ping_response[2]) if self.Max is not None else ping_response[2]
            self.Avg = round((self.i *self. Avg + current) / (self.i + 1))
            stats = [f"{current} ms", f"{self.Min} ms", f"{self.Max} ms", f"{self.Avg} ms"]
            self.i += 1
        elif len(self.successQueue) < 10:
            self.successQueue.append(0)

            current = ping_response[0]
            stats = [current, f"{self.Min} ms", f"{self.Max} ms", f"{self.Avg} ms"] if self.i > 0 else [current, "", "", ""]
        else:
            self.successQueue.pop(0)
            self.successQueue.append(0)

            current = ping_response[0]
            stats = [current, f"{self.Min} ms", f"{self.Max} ms", f"{self.Avg} ms"] if self.i > 0 else [current, "", "", ""]
        
        successRate = round(self.successQueue.count(1) / len(self.successQueue) * 100)
        self.parent.signals.result.emit((self.row, successRate, self.lastResponseTime, stats))

    def isIPAddressValid(self):
        try:
            ipaddress.ip_address(self.ip_address)
        except ValueError:
            exctype, value = sys.exc_info()[:2]
            self.parent.signals.error.emit((self.row, exctype, value, traceback.format_exc()))
            return False

        return True

    def ping(self):
        pingCount = 1
        if self.parent.system == "Windows":
            return self.pingOnWindows(pingCount)

        if self.parent.system == "Darwin":
            return self.pingOnMac(pingCount)

        return self.pingOnLinux(pingCount)

    def pingOnWindows(self, pingCount):
        timeOut = 1000  # in milliseconds

        cmd = 'ping -n %d -w %d %s' % (pingCount, timeOut, self.ip_address)
        ping_response = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
        time = QDateTime.currentDateTime().toString("dd/MM/yyyy  hh:mm:ss")
        stdout = ping_response.stdout.decode("utf-8")

        stdout_lines = [line.strip() for line in stdout.split('\n') if line.strip() != '']

        if "TTL" in stdout:
            return [time] + [int(x.strip("ms")) for x in re.findall("\d+ms", stdout_lines[-1])]

        return [stdout_lines[1].strip(".")]

    def pingOnMac(self, pingCount):
        timeOut = 1000  # in milliseconds

        cmd = 'ping -c %d -W %d %s' % (pingCount, timeOut, self.ip_address)
        ping_response = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
        time = QDateTime.currentDateTime().toString("dd/MM/yyyy  hh:mm:ss")
        stdout = ping_response.stdout.decode("utf-8")

        stdout_lines = [line.strip() for line in stdout.split('\n') if line.strip() != '']

        if "round-trip" in stdout:
            result = [time] + [round(float(x.strip("/"))) for x in re.findall("\d+.\d+/", stdout_lines[-1])]
            result[2], result[3] = result[3], result[2]
            return result

        if "Destination Host Unreachable" in stdout_lines[1]:
            ip = re.findall("\d+.\d+.\d+.\d+", stdout_lines[1])[0]
            return [f"Reply from {ip}: Destination host unreachable"]

        if "Request timeout" in stdout_lines[1]:
            return ["Request timed out"]

        return [stdout_lines[1]]

    def pingOnLinux(self, pingCount):
        timeOut = 1    # in seconds

        cmd = 'ping -c %d -W %d %s' % (pingCount, timeOut, self.ip_address)
        ping_response = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
        time = QDateTime.currentDateTime().toString("dd/MM/yyyy  hh:mm:ss")
        stdout = ping_response.stdout.decode("utf-8")

        stdout_lines = [line.strip() for line in stdout.split('\n') if line.strip() != '']
        
        if "ttl" in stdout:
            result = [time] + [round(float(x.strip("/"))) for x in re.findall("\d+.\d+/", stdout_lines[-1])]
            result[2], result[3] = result[3], result[2]
            return result
        
        return ["Destination host unreachable"]
