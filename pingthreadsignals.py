from PySide6.QtCore import QObject, Signal


class PingThreadSignals(QObject):
    '''
    Defines the signals available from PingThread.

    Supported signals are:

    started
        No data

    error
        tuple (exctype, value, traceback.format_exc())

    result
        tuple (row, successRate)

    finished
        No data
    '''
    started = Signal()
    result = Signal(tuple)
    error = Signal(tuple)
    finished = Signal()
    