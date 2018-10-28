import sys
from PyQt5 import QtWidgets
import numpy as np
import pyqtgraph as pg
from collections import deque
import time
from scipy import signal
import socket
import binascii
import datetime as dt

"""
UDP server command reference:
    a - start
    b - stop
    c - reset
    d - select electrodes as source
    e - select test signal as source
    f - select internal input short as soGurce
    g - 1x gain
    h - 2x gain
    i - 4x gain
    j - 6x gain
    k - 12x gain
    l - select 500sps sampling rate
    m - select 1000sps sampling rate
    n - select 2000sps sampling rate
    o - select 4000sps sampling rate
    p - select 8000sps sampling rate
"""

class Window(QtWidgets.QWidget):

    def __init__(self):
        super(Window, self).__init__()
        self.init_ui()

    def init_ui(self):
        self.s = None

        self.Started = False
        self.Connected = False
        self.Recording = False
        self.notchStatus = False
        self.HPStatus = False

        self.display_speed = 2000 #fps
        self.display_time = 4 #seconds
        self.fs_options = [500.0, 1000.0, 2000.00, 4000.00, 8000.00]
        self.fs = self.fs_options[1]  # Sample frequency (Hz) - default, 1000Hz
        self.notch_f0 = 50  # Frequency to be removed from signal (Hz)
        self.timer2 = 0.0
        self.dataIn_dc = 0.0

        self.peakfreq = 0 # initialize

        self.gains = [1, 2, 4, 6, 12]

        self.selected_channel = 0
        self.PGA_Gain = self.gains[4]

        self.Q = 5  # Quality factor
        self.w0 = self.notch_f0/(self.fs/2)  # Normalized Frequency

#        self.display_length = int(self.fs*self.display_time)
        self.display_length = int(self.display_time*self.fs)
        self.b, self.a = signal.iirnotch(self.w0, self.Q)

        self.index = deque(maxlen = self.display_length)
        self.data = deque(maxlen = self.display_length)

        for i in range(self.display_length):
            self.index.append(0)
            self.data.append(0)

        self.setGeometry(300, 100, 800, 500)

        self.b1 = QtWidgets.QPushButton('Connect')
        self.b2 = QtWidgets.QPushButton('Start')
        self.b3 = QtWidgets.QPushButton('Reset')
        self.b4 = QtWidgets.QPushButton('Record')
        self.b5 = QtWidgets.QPushButton('Toggle 50Hz Filter')
        self.b6 = QtWidgets.QPushButton('Toggle HP Filter')
        self.b4.setStyleSheet('QPushButton {color: red;}')
        if self.notchStatus is True:
            self.notch_status_label = QtWidgets.QLabel('Notch filter is ON')
        else:
            self.notch_status_label = QtWidgets.QLabel('Notch filter is OFF')

        if self.HPStatus is True:
            self.HP_status_label = QtWidgets.QLabel('HP filter is ON')
        else:
            self.HP_status_label = QtWidgets.QLabel('HP filter is OFF')

        self.Sampling_rate_label = QtWidgets.QLabel('Select sampling rate:')
        self.Data_source_label = QtWidgets.QLabel('Select data source:')
        self.PGA_label = QtWidgets.QLabel('Select amplifier gain:')
        self.Channel_select_label = QtWidgets.QLabel('Select channel:')
        self.peakfreq_label = QtWidgets.QLabel('Peak frequency: ' + str(self.peakfreq))

        self.Sampling_rate = QtWidgets.QComboBox()
        self.PGA = QtWidgets.QComboBox()
        self.Channel_select = QtWidgets.QComboBox()

        self.radio_electrodes = QtWidgets.QRadioButton("Electrodes")
        self.radio_electrodes.setChecked(True)
        self.radio_test_sig = QtWidgets.QRadioButton("Test signal")
        self.radio_shorted = QtWidgets.QRadioButton("Shorted")

        pg.setConfigOption('background', 'w')
        self.timePlot = pg.PlotWidget()
        self.fftPlot = pg.PlotWidget()

        self.PGA.addItems(["1x", "2x", "4x", "6x", "12x"])
        self.PGA.setCurrentIndex(4)

        self.Sampling_rate.addItems(["500 Hz", "1000 Hz", "2000 Hz", "4000 Hz", "8000 Hz"])
        self.Sampling_rate.setCurrentIndex(1)

        self.Channel_select.addItems(["1", "2","3","4", "5", "6", "7", "8"])
        self.Channel_select.setCurrentIndex(0)

        self.l_realtime = QtWidgets.QLabel()
        self.l_freq = QtWidgets.QLabel()

        v_box_plots = QtWidgets.QVBoxLayout()
        v_box_plots.addWidget(self.timePlot)
        v_box_plots.addWidget(self.fftPlot)

        self.timePlot.plotItem.setLabel('left', text="Measured signal", units="V", unitPrefix=None)
        self.timePlot.plotItem.setLabel('bottom', text="Time", units="seconds", unitPrefix=None)
        self.fftPlot.plotItem.setLabel('left', text="Frequency spectrum", units=None, unitPrefix=None)
        self.fftPlot.plotItem.setLabel('bottom', text="Frequency", units="Hz", unitPrefix=None)

        v_box_controls = QtWidgets.QVBoxLayout()
        v_box_controls.addWidget(self.b1)
        v_box_controls.addWidget(self.b2)
        v_box_controls.addWidget(self.b3)
        v_box_controls.addWidget(self.b4)
        v_box_controls.addWidget(self.b5)
        v_box_controls.addWidget(self.b6)
        v_box_controls.addWidget(self.notch_status_label)
        v_box_controls.addWidget(self.HP_status_label)
        v_box_controls.addStretch()
        v_box_controls.addWidget(self.Data_source_label)
        v_box_controls.addWidget(self.radio_electrodes)
        v_box_controls.addWidget(self.radio_test_sig)
        v_box_controls.addWidget(self.radio_shorted)
        v_box_controls.addStretch()
        v_box_controls.addWidget(self.Sampling_rate_label)
        v_box_controls.addWidget(self.Sampling_rate)
        v_box_controls.addStretch()
        v_box_controls.addWidget(self.PGA_label)
        v_box_controls.addWidget(self.PGA)
        v_box_controls.addStretch()
        v_box_controls.addWidget(self.Channel_select_label)
        v_box_controls.addWidget(self.Channel_select)
        v_box_controls.addStretch()
        v_box_controls.addWidget(self.peakfreq_label)

        h_box = QtWidgets.QHBoxLayout()
        h_box.addLayout(v_box_plots)
        h_box.addStretch()
        h_box.addLayout(v_box_controls)
        h_box.addStretch()

        self.setLayout(h_box)
        self.setWindowTitle('Biosignals GUI')

        #signals
        self.b1.clicked.connect(self.Connect_button_click)
        self.b2.clicked.connect(self.Start_button_click)
        self.b3.clicked.connect(self.Reset_button_click)
        self.b4.clicked.connect(self.Record_button_click)
        self.b5.clicked.connect(self.Notch_button_click)
        self.b6.clicked.connect(self.HP_button_click)
        self.radio_electrodes.clicked.connect(self.radio_click_electrodes)
        self.radio_test_sig.clicked.connect(self.radio_click_test_sig)
        self.radio_shorted.clicked.connect(self.radio_click_shorted)
        self.PGA.currentIndexChanged.connect(self.PGASelectionChange)
        self.Sampling_rate.currentIndexChanged.connect(self.SamplingRateSelectionChange)
        self.Channel_select.currentIndexChanged.connect(self.ChannelSelectionChange)

        self.timer1 = pg.QtCore.QTimer()
        self.timer1.timeout.connect(self.update)
        self.timer1.start(1000/self.display_speed)

        self.show()

#callbacks:
##########################################################
    def ChannelSelectionChange(self, selection):
        if self.Connected is True:
            try:
                self.s
            except NameError:
                QtWidgets.QMessageBox.question(self, 'Biosignals GUI message', "Error connecting to device", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            else:
                print("Channel selection changed")
                self.selected_channel = selection
                print("Channel " + str(selection) + " selected.")

    def PGASelectionChange(self, selection):
        print("PGA selection changed")
        server_address = ('192.168.4.1', 4210) #ESP8266 IP address
        if self.Connected is True:
            try:
                self.s
            except NameError:
                QtWidgets.QMessageBox.question(self, 'Biosignals GUI message', "Error connecting to device", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            else:
                self.PGA_Gain = self.gains[selection]
                print("Sending PGA command..."),
                message = ["g", "h", "i", "j", "k"]
                self.s.sendto(message[selection].encode(), server_address)
                print("sent...")

    def SamplingRateSelectionChange(self, selection):
        print("Sampling Rate selection changed")
        server_address = ('192.168.4.1', 4210) #ESP8266 IP address
        if self.Connected is True:
            try:
                self.s
            except NameError:
                QtWidgets.QMessageBox.question(self, 'Biosignals GUI message', "Error connecting to device", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            else:
                self.fs = self.fs_options[selection]
                self.w0 = self.notch_f0/(self.fs/2)  # Normalized Frequency
#               self.display_length = int(self.fs*self.display_time)
                self.display_length = int(self.display_time*self.fs)
                self.index = deque(maxlen = self.display_length)
                self.data = deque(maxlen = self.display_length)
                for index in range(self.display_length):
                    self.index.append(index)
                    self.data.append(0)
                self.data_filtered = []
                self.b, self.a = signal.iirnotch(self.w0, self.Q)

                print("Sampling rate: " + str(self.fs) + "Hz")
                print("Sending Sampling Rate command..."),
                message = ["l", "m", "n", "o", "p"]
                self.s.sendto(message[selection].encode(), server_address)

                print("sent...")

    def Connect_button_click(self):
        client_address = ('192.168.4.2', 4210) #ESP8266 IP address
        if self.Connected is False:
            # auto-find COM port:
            print("Connecting..."),
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                self.s.bind(client_address)
            except Exception as e:
                QtWidgets.QMessageBox.about(self, "Connection error", "Failed to connect to EEG hardware. \nCheck wifi connection and try again. Exception: \n" + str(e) )
                print("connection failed")
                print(e)
            else:
                self.s.settimeout(0.01)
                print(" connected.")
                self.b1.setText("Disconnect")
                self.Connected = True
        else:
            self.Started = True
            self.Start_button_click()
            try:
                self.s
            except NameError:
                QtWidgets.QMessageBox.about(self, "Disconnection error", "Failed to properly disconnect from EEG hardware. \nCheck source code.")
            else:
                self.s.close()
            self.timePlot.plotItem.clear()
            self.timer2 = 0
            for i in range(self.display_length):
                self.data.append(0)
                self.index.append(0)
            print("Disconnected")
            self.b1.setText("Connect")
            self.Connected = False

    def Start_button_click(self):
        server_address = ('192.168.4.1', 4210) #ESP8266 IP address
        if self.Connected is True:
            self.Started = not self.Started
            if self.Started is True:
                print("Sending start command...")
                message = "a"
                try:
                    self.s.sendto(message.encode(), server_address)
                except Exception as e:
                    print("Error sending data %s" % e)
                    QtWidgets.QMessageBox.question(self, 'Biosignals GUI message', "Error connecting to device", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
                else:
                    print("sent...")
                    self.b2.setText("Pause") #change button text to "pause"
            else:
                print("Sending Stop command..."),
                message = "b"
                try:
                    self.s.sendto(message.encode(), server_address)
                except Exception as e:
                    print("Error sending data %s" % e)
                    QtWidgets.QMessageBox.question(self, 'Biosignals GUI message', "Error connecting to device", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
                else:
                    print("sent..."),
                    self.b2.setText("Start")
        else:
            QtWidgets.QMessageBox.question(self, 'Biosignals GUI message', "Not connected to device", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)


    def Reset_button_click(self):
        server_address = ('192.168.4.1', 4210) #ESP8266 IP address
        if self.Connected is True:
            try:
                self.s
            except NameError:
                QtWidgets.QMessageBox.question(self, 'Biosignals GUI message', "Error connecting to device", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            else:
                self.Started = False
                self.b2.setText("Start")
                print("Sending reset command..."),
                message = "c"
                self.s.sendto(message.encode(), server_address)
                print("sent..."),
        else:
            QtWidgets.QMessageBox.question(self, 'Biosignals GUI message', "Not connected to device", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

    def Record_button_click(self):
        try:
            self.file_object
        except AttributeError:
            date = dt.datetime.now()
            self.file_object  = open('./Biosignals_recording_' + date.strftime('%m-%d-%Y_%H-%M-%S') + '.csv', 'w+')

        self.Recording = not self.Recording
        if not self.Recording:
            self.b4.setText("Record")
        else:
            self.b4.setText("Stop recording")

    def Notch_button_click(self):
        self.notchStatus = not self.notchStatus
        if self.notchStatus is True:
            self.notch_status_label.setText("Notch filter is ON")
        else:
            self.notch_status_label.setText("Notch filter is OFF")

    def HP_button_click(self):
        self.HPStatus = not self.HPStatus
        if self.HPStatus is True:
            self.HP_status_label.setText("HP filter is ON")
        else:
            self.HP_status_label.setText("HP filter is OFF")

    def radio_click_electrodes(self):
        print("electrodes selected as signal source")
        server_address = ('192.168.4.1', 4210) #ESP8266 IP address
        if self.Connected is True:
            try:
                self.s
            except NameError:
                QtWidgets.QMessageBox.question(self, 'Biosignals GUI message', "Error connecting to device", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            else:
                print("Sending Source command..."),
                message = "d"
                self.s.sendto(message.encode(), server_address)
                print("sent..."),

    def radio_click_test_sig(self):
        print("Test signal selected as signal source")
        server_address = ('192.168.4.1', 4210) #ESP8266 IP address
        if self.Connected is True:
            try:
                self.s
            except NameError:
                QtWidgets.QMessageBox.question(self, 'Biosignals GUI message', "Error connecting to device", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            else:
                print("Sending Source command..."),
                message = "e"
                self.s.sendto(message.encode(), server_address)
                print("sent..."),

    def radio_click_shorted(self):
        print("internal short selected as signal source")
        server_address = ('192.168.4.1', 4210) #ESP8266 IP address
        if self.Connected is True:
            try:
                self.s
            except NameError:
                QtWidgets.QMessageBox.question(self, 'Biosignals GUI message', "Error connecting to device", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
            else:
                print("Sending Source command..."),
                message = "f"
                self.s.sendto(message.encode(), server_address)
                print("sent..."),

    def codes2volts(self, CH):
        if CH <= 0x7FFFFF:
          return float(CH)/0x7FFFFF*2.400;
        else:
          return (float(CH)/0x7FFFFF - 2)*2.400;

##########################################################
    def update(self):
        if self.Connected is True and self.Started is True:
            try:
                recvd, server = self.s.recvfrom(8192)
            except socket.timeout:
                pass
            else:
                try:
                    recvd = bin(int(binascii.hexlify(recvd),16)) #doesn't need to be decoded from a byte string for this step
                    recvd = recvd[2:] #remove "0b" from the beginning
                except Exception as e:
                    print(e);
                else:
                    while len(recvd) >= 120: #while recvd is at least 24 characters (three bytes, one reading)
                        status = recvd[:24] # status bytes - use to detect errors and checking lead off/GPIO status
                        if status[:4] == "1100": #basic error checking - all packets start with 1100
                            dataIn = (int("0b" + recvd[24*(self.selected_channel+1):24*(self.selected_channel+2)], 2)) #read 24-bit datapoints
                            dataInFloat = self.codes2volts(dataIn) #process bytes

                            if self.HPStatus is True:
                                self.dataIn_dc = self.dataIn_dc*0.995 + dataInFloat*0.005
                                dataInFloat = dataInFloat - self.dataIn_dc

                            self.timer2 = self.timer2 + 1/self.fs  # measure
                            self.index.append(self.timer2)         # Approximate time index
                            self.data.append(dataInFloat)          # measured in volts

                            if self.Recording is True:
                                self.file_object.write(str(self.timer2) + ', ' + str(dataInFloat*1000000) + '\n')
                        else:
                            print("bad packet!")
                        recvd = recvd[216:]  #discard from recvd string


                    if self.notchStatus is True:
                        self.data_filtered = signal.lfilter(self.b, self.a, self.data) #50Hz notch filter
                    else:
                        self.data_filtered = self.data # unfiltered

                self.timePlot.plotItem.clear()
                self.timePlot.plotItem.plot(self.index, self.data_filtered, pen=pg.mkPen('k', width=1))
                # self.timePlot.plotItem.setRange(xRange = (self.timer2-self.display_time*0.8, max(self.index)), yRange = (-0.00015, 0.00015))
                self.timePlot.plotItem.setRange(xRange = (self.timer2-self.display_time*0.8, self.timer2))

                fft = np.absolute(np.fft.fft(self.data_filtered))
                self.fft_index = np.linspace(0 , self.fs, num = len(fft))

                self.fftPlot.plotItem.clear()
                self.fftPlot.plotItem.plot(self.fft_index, fft, pen=pg.mkPen('k', width=1))
                self.fftPlot.plotItem.setRange(xRange = (0, self.fs/2))
    #            self.fftPlot.plotItem.setRange(xRange = (0, self.fs/2), yRange = (0, 0.01))
    #            self.fftPlot.plotItem.setRange(xRange = (00, 40), yRange = (0, 0.01))

                # display peak frequency in bottom corner:
                self.peakfreq = fft[:len(fft)//2].argmax()*self.fs/self.data.maxlen
                self.peakfreq_label.setText('Peak freq: ' + str(round(self.peakfreq, 1)) + ' Hz')

    def closeEvent(self, event):

        #stop update timer
        self.timer1.stop()

        #send tignal to ADS1298 to stop updating
        if self.Connected:
            self.Started = True
            self.Start_button_click()

        #if open, close file object
        try:
            self.file_object
        except:
            pass
        else:
            self.file_object.close()

        # if open, close socket
        if self.s is not None:
            try:
                self.s.close()
            except:
                print("Fail to disconnect")

        event.accept()


if __name__ == "__main__":
    # app = 0
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    a_window = Window()
    app.exec_()
