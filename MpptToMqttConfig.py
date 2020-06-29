import logging

serialPort = "/dev/tty.usbserial-FTBBWTC9"
logFileName = "MpptToMqtt.log"
logLevel = logging.ERROR
controllerName = "MpptController01"
mqttServer = "172.17.2.21"
mqttPort = 1883
reportInterval = 15