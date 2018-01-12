#/******************************
# *     Author: Omar Gamal     *
# *   c.omargamal@gmail.com    *
# *                            *
# *     Hardware: ESP8266      *
# *                            *
# *         12/4/2017          *
# *     ESP8266 Web Server     *
# ******************************/

#!/usr/bin/env python
###########################################
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QThread, SIGNAL

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import loadUiType

# import design.py for GUI things
import design
import sys

# to open files and sleep()
import os
import time

# for serial comm with NanoMCU
import serial

# used in USB Ports detection
import glob

# html parsing libraries
from urllib2 import urlopen
import urllib2
from httplib import BadStatusLine

from bs4 import BeautifulSoup
from lxml import html

# database libraries
import MySQLdb
from flask import Flask, render_template

###########################################
#we should erase input/output buffers whenever it's necessary
###########################################


# loading bullets thread
class loading_thread(QtCore.QThread):
    def __init__(self):
        super(loading_thread, self).__init__()

    def run(self):
        self.temp = 0

    	# when called, it increments and updates the graphic
    	# keeps looping until some function terminates the thread
        # time consumed here = 0.6*5 + 0.15*17 = 5.55s
        for i in range(22):
            self.emit(SIGNAL('loading_fn(int)'), self.temp)
            self.temp = self.temp + 1
            if (i%4 == 3):
            	time.sleep(0.6)

            else:
            	time.sleep(0.15)


        self.emit(SIGNAL('scan_tany()'))



# loading bullets thread
class _7amada_thread(QtCore.QThread):
    def __init__(self):
        super(_7amada_thread, self).__init__()

    def run(self):
        self.temp = 0

    	# when called, it increments and updates the graphic
    	# keeps looping until some function terminates the thread
        # time consumed 12.5s
        for i in range(55):
            self.emit(SIGNAL('loading_tany(int)'), self.temp)
            self.temp = self.temp + 1
            if (i%4 == 3):
           		time.sleep(0.6)

            else:
            	time.sleep(0.15)


            if (i == 4):
            	# send control signal to ESP
		        self.emit(SIGNAL('connect_b2a()'))

            if (i == 10):
            	# send wifi name
		        self.emit(SIGNAL('connect_tany()'))

            if (i == 14):
            	# send wifi password
		        self.emit(SIGNAL('connect_talet()'))

		# read the connection status
        self.emit(SIGNAL('connect_rabe3()'))



# live data acquisition thread
class acquisition_thread(QtCore.QThread):
    def __init__(self):
        super(acquisition_thread, self).__init__()

    def run(self):
    	# holds the analog reading
    	analog = ""

    	# holds the number of 'n' in the html line
    	count = 0

    	# holds the position of the cursor in the html line
    	iterator = 0

    	# when called, it gets the data from our webserver
    	# keeps looping until some function terminates the thread
    	while (1):
    		# time between GET Requests must be +400 ms to avoid server crash
    		time.sleep(0.5)
    		try:
				# open the server URL
				response = urlopen("http://172.28.128.232/")
				soup = response.read()
				tree = html.fromstring(soup)
				data = str(tree.xpath("//p/text()"))

				iterator = 0
				# parse the data until you find the useful information
				for char in data:
					iterator += 1

					if char == 'n':
						count += 1
						continue

					if count == 1:
						analog = analog + char

					if count == 2:						
						# calls the function that updates the live data progress bar
						self.emit(SIGNAL('update_acquisition(QString, QString)'), analog[:-3], data[iterator-1])

						# calls the insert-to-database function
						self.emit(SIGNAL('insert_database(QString, QString)'), analog[:-3], data[iterator-1])

						# resetting the values
						count = 0
						analog = ""

						# break from the loop because we got every useful thing we want
						break

			# some exceptions may happen if the server crashes or
			# the internet connection is lost
    		except BadStatusLine:
				break



# main GUI class
class mainApp(QtGui.QMainWindow, design.Ui_MainWindow):
	def __init__(self):
		super(mainApp, self).__init__()
		self.setupUi(self)

        # disable the wifi and acquisition sections until serial connect to ESP
		self.btn_scan.setEnabled(False)
		self.list_networks.setEnabled(False)
		self.lndt_password.setEnabled(False)
		self.btn_connect_wifi.setEnabled(False)
		self.chk_remember.setEnabled(False)
		self.chk_show.setEnabled(False)
		self.btn_start_acquisition.setEnabled(False)
		self.label.setEnabled(False)
		self.label_2.setEnabled(False)
		self.label_3.setEnabled(False)
		self.label_4.setEnabled(False)
		self.chk_save_db.setEnabled(False)
		self.chk_save_text.setEnabled(False)
		self.btn_print_report.setEnabled(False)

		# setting serial, wifi and acquisition status to "Unknown yet"
		self.lbl_serial_connected.setStyleSheet('color: gray')
		self.lbl_wifi_connected.setStyleSheet('color: gray')
		self.lbl_acquisition.setStyleSheet('color: grey')

		# setting loading bullets to gray, loading will be in black
		self.scanning_1.setStyleSheet('color: gray')
		self.scanning_2.setStyleSheet('color: gray')
		self.scanning_3.setStyleSheet('color: gray')

		self.connecting_1.setStyleSheet('color: gray')
		self.connecting_2.setStyleSheet('color: gray')
		self.connecting_3.setStyleSheet('color: gray')

		# hiding the loading bullets until they be used
		self.scanning_1.hide()
		self.scanning_2.hide()
		self.scanning_3.hide()

		self.connecting_1.hide()
		self.connecting_2.hide()
		self.connecting_3.hide()

		# creating threads instances
		# loading thread
		self.loading_thread = loading_thread()
		self.connect(self.loading_thread, SIGNAL('loading_fn(int)'), self.loading_fn)
		self.connect(self.loading_thread, SIGNAL('scan_tany()'), self.scan_tany)

		# connecting threads
		self._7amada_thread = _7amada_thread()
		self.connect(self._7amada_thread, SIGNAL('loading_tany(int)'), self.loading_tany)
		self.connect(self._7amada_thread, SIGNAL('connect_b2a()'), self.connect_b2a)
		self.connect(self._7amada_thread, SIGNAL('connect_tany()'), self.connect_tany)
		self.connect(self._7amada_thread, SIGNAL('connect_talet()'), self.connect_talet)
		self.connect(self._7amada_thread, SIGNAL('connect_rabe3()'), self.connect_rabe3)

		# acquisition update graphics thread
		self.acquisition_thread = acquisition_thread()
		self.connect(self.acquisition_thread, SIGNAL('update_acquisition(QString, QString)'), self.update_acquisition)
		self.connect(self.acquisition_thread, SIGNAL('error_fn(QString)'), self.error_fn)
		self.connect(self.acquisition_thread, SIGNAL('insert_database(QString, QString)'), self.insert_database)

		# setting flags
		self.is_serial_connected = False
		self.is_wifi_connected = False
		self.acquisition_status = False

		# calling the serial_ports() function to get the connected USBs list
		self.serial_ports_fn()

		# setting the password default to be masked in asterisks
		self.show_password_fn()

		# connecting each button with its functions
		self.btn_refresh_comm.clicked.connect(self.serial_ports_fn)
		self.btn_connect_serial.clicked.connect(self.connect_serial_fn)
		self.btn_scan.clicked.connect(self.scan_fn)
		self.btn_connect_wifi.clicked.connect(self.connect_wifi_fn)
		self.btn_start_acquisition.clicked.connect(self.start_acquisition_fn)
		self.btn_print_report.clicked.connect(self.print_report_fn)

		# detects change in show/mask password checkbox
		self.chk_show.stateChanged.connect(self.show_password_fn)

		# detects changes in wifi name list checkbox to check if password is available
		self.connect(self.list_networks, QtCore.SIGNAL("currentIndexChanged(const QString&)"), self.retrieve_password)



	# connects python to ESP
	def connect_serial_fn(self):
		# getting port name and baud rate from drop lists
		self.port = str(self.list_comm.currentText())
		self.baud = int(self.list_baud.currentText())

		# if the user chooses any port name other than this...
		if (self.port != '/dev/ttyS0'):
			try:
				# if we are not connected to ESP
				if (not(self.is_serial_connected)):
					# try connecting and wait until MCU resets
					# and be completely ready (not in ESP)
					self.arduinoData = serial.Serial(self.port, self.baud)
					time.sleep(1.55)

					# if the connection is established...
					if (self.arduinoData.isOpen()):
						# set "Serial is connected" parameters
						self.is_serial_connected = True
						self.lbl_serial_connected.setStyleSheet('color: green')
						self.btn_connect_serial.setText("Disconnect")

						# enable wifi scan button
						self.btn_scan.setEnabled(True)
						self.btn_connect_wifi.setEnabled(False)
						self.list_networks.setEnabled(False)
						self.lndt_password.setEnabled(False)
						self.chk_remember.setEnabled(False)
						self.chk_show.setEnabled(False)
						self.btn_start_acquisition.setEnabled(False)
						self.label.setEnabled(False)
						self.label_2.setEnabled(False)
						self.label_3.setEnabled(False)
						self.label_4.setEnabled(False)
						self.chk_save_db.setEnabled(False)
						self.chk_save_text.setEnabled(False)
						self.btn_print_report.setEnabled(False)

					# if connection isn't established...
					else:
						self.lbl_serial_connected.setStyleSheet('color: gray')
						self.error_fn('serial')



				# if we are connected to ESP
				elif (self.is_serial_connected):

					# disconnect wifi if it's already connected
					if (self.is_wifi_connected):
						self.connect_wifi_fn()
						time.sleep(0.7)

					# set "Serial is disconnected" parameters
					self.is_serial_connected = False
					self.lbl_serial_connected.setStyleSheet('color: red')
					self.btn_connect_serial.setText("Connect")
					self.list_networks.clear()

					self.bar.setValue(0)
					self.label.setText('0')

					self.bar_2.setValue(0)
					self.label_2.setText('0')					


					# close the communication with ESP
					self.arduinoData.close()

					# disable wifi and data acquisition sections
					self.btn_scan.setEnabled(False)
					self.btn_connect_wifi.setEnabled(False)
					self.list_networks.setEnabled(False)
					self.lndt_password.setEnabled(False)
					self.chk_remember.setEnabled(False)
					self.chk_show.setEnabled(False)
					self.btn_start_acquisition.setEnabled(False)
					self.label.setEnabled(False)
					self.label_2.setEnabled(False)
					self.label_3.setEnabled(False)
					self.label_4.setEnabled(False)
					self.chk_save_db.setEnabled(False)
					self.chk_save_text.setEnabled(False)
					self.btn_print_report.setEnabled(False)

			# if you're trying to disconnect a disconencted port it will raise an exception
			except (serial.serialutil.SerialException):
				self.error_fn('serial')

				#research the connected ports
				self.serial_ports_fn()

		else:
			#if trying to connect to ttyS0, it gives an error
			self.error_fn('serial')



	# asks ESP to scan for available networks
	def scan_fn(self):
		# if serial communication is established with ESP...
		if (self.is_serial_connected):
			# you may find a more elegant way to flush the buffers
			while (self.arduinoData.inWaiting() > 0):
				x = str(self.arduinoData.inWaiting())

			# send control signal to ESP to start searching for available wifi
			self.arduinoData.write("scan")

			# show the scan loading bullets
			self.scanning_1.show()
			self.scanning_2.show()
			self.scanning_3.show()

			# call the loading thread
			self.loading_thread.start()

		# if serial communication is not established with ESP...
		else:
			self.error_fn('serial')



	# reads the available networks
	def scan_tany(self):
		# when scan finishes, terminate the thread
		self.loading_thread.terminate()

		# hiding the scan loading bullets
		self.scanning_1.hide()
		self.scanning_2.hide()
		self.scanning_3.hide()


		# initializing variables
		networks = []
		temp = ''

		try:
			# read all the available wifi names coming through serial port
			while (self.arduinoData.inWaiting() > 0):
				temp = str(self.arduinoData.readline())
				networks.append(temp[:-2])

			# clear droplist and put the wifi names in their drop list
			self.list_networks.clear()
			self.list_networks.addItems(networks)

			# enabling wifi buttons and labels
			self.btn_scan.setEnabled(True)
			self.btn_connect_wifi.setEnabled(True)
			self.list_networks.setEnabled(True)
			self.lndt_password.setEnabled(True)
			self.chk_remember.setEnabled(True)
			self.chk_show.setEnabled(True)
			self.btn_start_acquisition.setEnabled(False)
			self.chk_save_db.setEnabled(False)
			self.chk_save_text.setEnabled(False)
			self.btn_print_report.setEnabled(False)

		# don't sure yet what causes this exception, I think it's strange data from serial port
		except IOError:
			self.error_fn('serial')
		


	# connects ESP to wifi given a wifi name and password
	def connect_wifi_fn(self):
		# if wifi is still disconnected...
		if (not(self.is_wifi_connected)):
			# save wifi name and password if checked by user
			if (self.chk_remember.isChecked()):
				self.save_password()

			# show wifi loading bullets
			self.connecting_1.show()
			self.connecting_2.show()
			self.connecting_3.show()

			# call the loading thread
			self._7amada_thread.start()



		# if wifi isn't connected
		elif (self.is_wifi_connected):
			# if acquisition is on, stop it
			if (self.acquisition_status):
				self.start_acquisition_fn()
				
			# send control signal to arduino
			self.arduinoData.write("disconnect")
			time.sleep(1.5)

			# set "Wifi is not conencted" parameters
			self.is_wifi_connected = False
			self.lbl_wifi_connected.setStyleSheet('color: red')
			self.btn_connect_wifi.setText("Connect")
			self.btn_start_acquisition.setEnabled(False)


	# sending "connect to wifi" control signal
	def connect_b2a(self):
		##
		self.arduinoData.write("connect")



	# sending wifi name to ESP
	def connect_tany(self):
		# send ssid and password separated by 1 second to avoid ESP crashing
		wifi = str(self.list_networks.currentText())

		self.arduinoData.write(str(wifi))



	# sending wifi password to ESP
	def connect_talet(self):
		passs = str(self.lndt_password.text())

		self.arduinoData.write(str(passs))



	# after connecting process has ended from ESP side
	def connect_rabe3(self):
		# stop connecting thread
		self._7amada_thread.terminate()

		# hide wifi loading bullets
		self.connecting_1.hide()
		self.connecting_2.hide()
		self.connecting_3.hide()

		# ESP will send the state of connection
		state = str(self.arduinoData.readline())
		state = state[:-2]

		# if ESP sends "connected"
		if (state == "Connected!"):
			# set "Wifi is connected" parameters
			self.is_wifi_connected = True
			self.lbl_wifi_connected.setStyleSheet('color: green')
			self.btn_connect_wifi.setText("Disconnect")

			self.btn_scan.setEnabled(True)
			self.btn_connect_wifi.setEnabled(True)
			self.list_networks.setEnabled(True)
			self.lndt_password.setEnabled(True)
			self.chk_remember.setEnabled(True)
			self.chk_show.setEnabled(True)
			self.btn_start_acquisition.setEnabled(True)
			self.label.setEnabled(True)
			self.label_2.setEnabled(True)
			self.label_3.setEnabled(True)
			self.label_4.setEnabled(True)
			self.chk_save_db.setEnabled(True)
			self.chk_save_text.setEnabled(True)
			self.btn_print_report.setEnabled(False)

		# if ESP sends "failed to conenct"
		elif (state == "Failed!"):
			# set "Wifi is not connected" parameters
			self.is_wifi_connected = False
			self.lbl_wifi_connected.setStyleSheet('color: red')
			self.btn_connect_wifi.setText("Connect")

			# raise error message
			self.error_fn('wifi')



	# show or mask password depending on check box
	def show_password_fn(self):
		# checked = show password
		if (self.chk_show.isChecked()):
			self.lndt_password.setEchoMode(QtGui.QLineEdit.Normal)

		# unchecked = masked in asterisks
		elif (not(self.chk_show.isChecked())):
			self.lndt_password.setEchoMode(QtGui.QLineEdit.Password)



	# save wifi name and its associated password in a text file
	def save_password(self):
		# initialize variables
		allow = False
		found = False

		# if new passwords file exists --> remove it 3shan nebda2 3la nadafa
		if (os.path.exists("new_pass.txt")):
			os.remove("new_pass.txt")


		# check if the password is already saved
		with open("passwords.txt", 'r') as pswrd:
			with open("new_pass.txt", 'a') as new:

				# parse password file lines
				for line in pswrd:
					# write the password under its wifi ame
					if (allow):
						new.write(self.lndt_password.text() + '\n')
						allow = False
						continue

					# if wifi name exists with a different password, replace it
					if (line == (self.list_networks.currentText() + '\n')):
						new.write(self.list_networks.currentText() + '\n')
						found = True
						allow = True

					# write down every other line
					else:
						new.write(line)

				# if the wifi and password are brand new, add them to the end of the file
				if (not(found)):
					new.write(self.list_networks.currentText() + '\n')
					new.write(self.lndt_password.text() + '\n')

		# open the passwords files once more but in different modes
		with open("new_pass.txt", 'r') as new:
			with open("passwords.txt", 'w') as pswrd:
				# parse password file lines
				for line in new:
					# ignore empty lines
					if line != '\n':
						pswrd.write(line)

				# copy lines from the temporary file to our backup file
				if line != '\n':
					pswrd.write('\n')

		# new_pass isn't useful anymore B|
		if (os.path.exists("new_pass.txt")):
			os.remove("new_pass.txt")



	# search for saved passwords and retrieve them
	def retrieve_password(self):
		# initialize "found the wifi name existing"
		found = False

		# open passwords backup file
		with open("passwords.txt", 'r') as pswrd:
			# parse the passwords
			for line in pswrd:
				# here we found the wifi name chosen by the user
				if (line[:-1] == str(self.list_networks.currentText())):
					found = True
					continue

				# didnt find the wifi name
				else:
					self.lndt_password.clear()

				# put the password line in the password text box
				if (found):
					self.lndt_password.setText(line[:-1])
					found = False
					break



	# check the available serial ports. Cross platform
	def serial_ports_fn(self):
		# initialize variable
		result = []

		# works only if serial is disconnected. because it shuts off ports
		# while testing their availability
		if (not(self.is_serial_connected)):
			# if we running on windows
			if sys.platform.startswith('win'):
				ports = ['COM%s' % (i + 1) for i in range(256)]

			# if we are running linux
			elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
				ports = glob.glob('/dev/tty[A-Za-z]*')

			# if we are running darwin
			elif sys.platform.startswith('darwin'):
				ports = glob.glob('/dev/tty.*')

			# if any other OS
			else:
				raise EnvironmentError('Unsupported platform')

			# test every port in the system
			for port in ports:
				try:
					s = serial.Serial(port)
					s.close()
					result.append(port)
				except (OSError, serial.SerialException):
					pass


			# put the ports names in the ports drop list
			self.list_comm.clear()
			self.list_comm.addItems(result)



	# raises an error message and an error sound to warn the user
	# that the arduino is not connected
	def error_fn(self, which):
		self.error_msg = QMessageBox()
		self.error_msg.setIcon(QMessageBox.Critical)

		# if serial communication error
		if (which == 'serial'):
			self.error_msg.setWindowTitle("Serial Connection Error")
			self.error_msg.setText("Make sure you are connected to the ESP first.")

		# if ESP wifi communication error
		elif (which == 'wifi'):
			self.error_msg.setWindowTitle("WiFi Connection Error")
			self.error_msg.setText("Couldn't connect to WiFi!")
			self.error_msg.setInformativeText("Scan networks and try again.")

		# if PC wifi communication error
		elif (which == 'net'):
			self.error_msg.setWindowTitle("Internet Connection Error")
			self.error_msg.setText("Connect your PC to the network!")


		self.error_msg.setStandardButtons(QMessageBox.Ok)
		self.error_msg.exec_()



	# start data acquisition
	def start_acquisition_fn(self):
		# if acquisition is stopped
		if (not(self.acquisition_status)):
			try:
				# disable print report
				self.btn_print_report.setEnabled(False)

				# check if your PC is connected to the internet
				urlopen('http://216.58.192.142', timeout=5)

				# send control signal to ESP
				self.arduinoData.write("start")

				# set "acquisition started" parameters
				self.acquisition_status = True
				self.lbl_acquisition.setStyleSheet('color: green')
				self.btn_start_acquisition.setText("Stop")

				# connect database
				self.connect_database()

				# put the header to indicate an acquisition at this moment
				with open('DAQ.txt', 'a') as DAQ:
					header = "======== " + time.strftime("%H:%M:%S") + " ~~~ " + time.strftime("%d/%m/%Y") + " ========" + '\n'
					DAQ.write(header)

				# call the data acquisition thread
				self.acquisition_thread.start()

			except urllib2.URLError as err: 
				self.error_fn('net')

		# if acquisituion is started
		elif (self.acquisition_status):
			# enable print report
			self.btn_print_report.setEnabled(True)

			# send control signal to ESP
			self.arduinoData.write("stop")
			time.sleep(1)

			# kill the thread
			self.acquisition_thread.terminate()

			# close database
			self.close_database()

			# set "acquisition stopped" parameters
			self.acquisition_status = False
			self.lbl_acquisition.setStyleSheet('color: red')
			self.btn_start_acquisition.setText("Start Acquisition")



	# update the graphics of acquisition on the GUI
	def update_acquisition(self, analog, digital):
		# setting analog sensor graphics
		self.bar.setValue(int(analog))
		self.label.setText(analog)

		# setting digital sensor graphics
		self.bar_2.setValue(int(digital))
		self.label_2.setText(digital)

		# if check box is checked --> save data into text file
		if (self.chk_save_text.isChecked()):
			with open('DAQ.txt', 'a') as DAQ:
				stringaya = '\t\t' + analog + "   " + digital + '\n'
				DAQ.write(stringaya)



	# graphics loading for scanning function
	def loading_fn(self, temp):
		if (temp%4 == 0):
			self.scanning_1.setStyleSheet('color: black')
			self.scanning_3.setStyleSheet('color: gray')
			self.scanning_1.setGeometry(130, 40, 16, 21)
			self.scanning_3.setGeometry(170, 45, 16, 21)

		elif (temp%4 == 1):
			self.scanning_2.setStyleSheet('color: black')
			self.scanning_1.setStyleSheet('color: gray')
			self.scanning_1.setGeometry(130, 45, 16, 21)
			self.scanning_2.setGeometry(150, 40, 16, 21)

		elif (temp%4 == 2):
			self.scanning_3.setStyleSheet('color: black')
			self.scanning_2.setStyleSheet('color: gray')
			self.scanning_2.setGeometry(150, 45, 16, 21)
			self.scanning_3.setGeometry(170, 40, 16, 21)

		elif (temp%4 == 3):
			self.scanning_3.setStyleSheet('color: gray')
			self.scanning_3.setGeometry(170, 45, 16, 21)



	# graphics loading for wifi connecting function
	def loading_tany(self, temp):
		if (temp%4 == 0):
			self.connecting_1.setStyleSheet('color: black')
			self.connecting_3.setStyleSheet('color: gray')
			self.connecting_1.setGeometry(390, 80, 16, 21)
			self.connecting_3.setGeometry(430, 85, 16, 21)

		elif (temp%4 == 1):
			self.connecting_2.setStyleSheet('color: black')
			self.connecting_1.setStyleSheet('color: gray')
			self.connecting_2.setGeometry(410, 80, 16, 21)
			self.connecting_1.setGeometry(390, 85, 16, 21)

		elif (temp%4 == 2):
			self.connecting_3.setStyleSheet('color: black')
			self.connecting_2.setStyleSheet('color: gray')
			self.connecting_3.setGeometry(430, 80, 16, 21)
			self.connecting_2.setGeometry(410, 85, 16, 21)

		elif (temp%4 == 3):
			self.connecting_3.setStyleSheet('color: gray')
			self.connecting_3.setGeometry(430, 85, 16, 21)



	# connect to database
	def connect_database(self):
		# open database connection
		self.db = MySQLdb.connect("localhost","cartera","Password1!","task0" )



	# insert to database
	def insert_database(self, analog, digital):
		if (self.chk_save_db.isChecked()):
			# prepare a cursor object using cursor() method
			cursor = self.db.cursor()

			analog = str(analog)
			digital = str(digital)

			# Prepare SQL query to INSERT a record into the database.
			sql = "INSERT INTO sensors(analog,digital,dt) VALUES (%s, %s, Now())"
			       
			try:
			   # Execute the SQL command
			   cursor.execute(sql, (analog, digital))
			   # Commit your changes in the database
			   self.db.commit()
			except:
				pass
			   # Rollback in case there is any error 
			   #self.db.rollback()
		else:
			pass



	def close_database(self):
		# disconnect from server
		if (self.chk_save_db.isChecked()):
			self.db.close()



	def print_report_fn(self):
		# opens an html report
		try:
			os.system('python hellow.py')
		except:
			pass



def main():
	App = QtGui.QApplication(sys.argv)
	form = mainApp()
	form.show()
	App.exec_()
	

if __name__ == '__main__':
	main()
