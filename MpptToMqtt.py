#!/usr/bin/python3

import serial
import binascii
import struct
import math
import logging
import paho.mqtt.client as mqtt
import MpptToMqttConfig as cfg
import threading
import sys
from threading import Timer

logging.basicConfig(filename=cfg.logFileName, level=cfg.logLevel, format='%(asctime)s %(message)s', datefmt='%d.%m.%Y %H:%M:%S')
logger = logging.getLogger(__name__)

ledTopic = "/" + cfg.controllerName + "/Led"
errorCodeTopic = "/" + cfg.controllerName + "/ErrorCode"
iconsTopic = "/" + cfg.controllerName + "/Icons"
batteryVoltageTopic = "/" + cfg.controllerName + "/BatteryVoltage"
pvVoltageTopic = "/" + cfg.controllerName + "/PvVoltage"
chargeCurrentAmpereTopic = "/" + cfg.controllerName + "/ChargeCurrentAmpere"
loadCurrentAmpereTopic = "/" + cfg.controllerName + "/LoadCurrentAmpere"
temperatureTopic = "/" + cfg.controllerName + "/Temperature"
chargeAmpereTopic = "/" + cfg.controllerName + "/ChargeAmpere"
dischargeAmpereTopic = "/" + cfg.controllerName + "/DischargeAmpere"

commandTopic = "Command"

client = mqtt.Client()

queryValuesTimer = None

ser = serial.Serial(
    port=cfg.serialPort,
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=3
)

ser.isOpen()

serialLock = threading.Lock()

# This request has to be sent to get the current data from the mppt solar charge controller.
dataRequest = bytearray.fromhex ("55000000001E0002325255")

# This request resets the charged ampere's
resetChargeAmpere = bytearray.fromhex("55000000002b00901a0000000000000000000000000000000000000000000000d555")

def message(logLevel, *args, **kwargs):
    logger.log(logLevel, *args, **kwargs)
    print(args)

def on_connect(client, userdata, flags, rc):
    message(logging.INFO, "MQTT Connected with result code ", str(rc))
    client.subscribe("/{}/{}".format(cfg.controllerName, commandTopic))
    startTimer()

def on_message(client, userdata, msg):
    msgPayload = msg.payload.decode("utf-8")
    message(logging.DEBUG, "Incoming message: " + msg.topic + " " + msgPayload)
    if msgPayload == "ResetChargeAmpere":
        serialLock.acquire()
        ser.write(resetChargeAmpere)
        message(logging.DEBUG, "Charge ampere reset")
        serialLock.release()

def on_log(client, userdata, level, buf):
    if (level == mqtt.MQTT_LOG_DEBUG):
        message(logging.DEBUG, buf)
    elif (level == mqtt.MQTT_LOG_INFO):
        message(logging.INFO, buf)
    elif (level == mqtt.MQTT_LOG_NOTICE):
        message(logging.INFO, buf)
    elif (level == mqtt.MQTT_LOG_WARNING):
        message(logging.WARNING, buf)
    elif (level == mqtt.MQTT_LOG_ERR):
        message(logging.ERROR, buf)

def calculateModulo(input):
    return sum(input) % 256

def sendValue(topic, value):
    client.publish(topic, str(value))

def startTimer():
    queryValuesTimer = Timer(cfg.reportInterval, QueryValues)
    queryValuesTimer.daemon = True
    queryValuesTimer.start()

def QueryValues():
    try:
        serialLock.acquire()

        ser.flushInput()
        ser.write(dataRequest)
        response = ser.read(59)
        
        if len(response) < 59:
            message(logging.ERROR, "Timeout when receiving response")
        elif response[0] == 0x55 and response[58] == 0x55:
            responseChecksum = response[57]
            data = bytearray(response[1:57])

            calculatedChecksum = calculateModulo(data)

            if responseChecksum == calculatedChecksum:
                led = data[6] # Solarpanel LED 0x00 off, 0x01 und 0x02 on, 0x03 blink
                errorCode = data[8] # Error code
                icons = data[10] # Icons: 1 = lamp symbol, 2 and 3 = battery blink, 4+ battery blink fast
                batteryVoltage = data[11] * 2.368 # Battery voltage (max 42) multiplied with 2.368
                batteryVoltage += data[12] * 0.00925 # Battery voltage int value multiplied with 0.00925
                pvVoltage = data[13] * 9.45 # PV voltage (max 105) multiplied with 9.45
                pvVoltage += data[14] * 0.037 # PV voltage (max 255) multiplied with 0.037
                chargeCurrentAmpere = data[17] + 0.0039 if data[17] > 0 else 0 # Charge current ampere + 0.0039
                chargeCurrentAmpere += data[18] * 0.0039 # Charge current ampere multiplied with 0.0039
                loadCurrentAmpere = data[21] + 0.0039 if data[21] > 0 else 0 # Load current ampere + 0.0039
                loadCurrentAmpere += data[22] * 0.0039 # Load current ampere multiplied with 0.0039
                temperature = data[24] if data[24] <= 128 else -(data[24] - 128) # Temperature in degrees 0 - 128 = positive values 129 - 255 = negative values
                chargeAmpere = data[35] * 65793 # Charge ampere multiplied with 65793
                chargeAmpere += data[36] * 257 # Charge ampere multiplied with 257
                chargeAmpere += data[37] # Charge ampere multiplied with 1
                #responseData2[38] ?
                dischargeAmpere = data[39] * 65793 # Discharge ampere multiplied with 65793
                dischargeAmpere += data[40] * 257 # Discharge ampere multiplied with 257
                dischargeAmpere += data[41] # Discharge ampere multiplied with 1

                sendValue(ledTopic, led)
                sendValue(errorCodeTopic, errorCode)
                sendValue(iconsTopic, icons)
                sendValue(batteryVoltageTopic, batteryVoltage)
                sendValue(pvVoltageTopic, pvVoltage)
                sendValue(chargeCurrentAmpereTopic, chargeCurrentAmpere)
                sendValue(loadCurrentAmpereTopic, loadCurrentAmpere)
                sendValue(temperatureTopic, temperature)
                sendValue(chargeAmpereTopic, chargeAmpere)
                sendValue(dischargeAmpereTopic, dischargeAmpere)
            else:
                message(logging.ERROR, "Wrong checksum:")
                message(logging.ERROR, binascii.hexlify(response))
        else:
            message(logging.ERROR, "Wrong message headers:")
            message(logging.ERROR, binascii.hexlify(response))
    except Exception as e:
        message(logging.ERROR, e)

    serialLock.release()
    startTimer()

def main():
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_log = on_log
    client.connect(cfg.mqttServer, cfg.mqttPort, 60)

    client.loop_forever()

def cleanup():
    queryValuesTimer.cancel()
    client.disconnect()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        message(logging.ERROR, e)
        cleanup()