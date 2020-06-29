# MpptToMqtt
## Description
This script sends the data from the **SRNE SR-MT2410** solar charge controller to an MQTT server. I only tested this with this device, but maybe it also works for other charge controllers.
![SRNE SR-MT2410](/images/SRNE-SR-MT2410.jpg)
## Requirements

 - TTL Cable:
   [895-TTL-232R-5V](https://www.mouser.ch/ProductDetail/FTDI/TTL-232R-5V?qs=OMDV80DKjRorBEBwmlJ4Pg==&gclid=Cj0KCQjwoub3BRC6ARIsABGhnya3tCWSCe0dIKwnhwxVtWlH5CdFpzyQSQgBPCcao4L1b93XQLkidTYaAvbGEALw_wcB)
 - RJ12 cable

## Wiring
| Pin RJ12 | RJ12 function | PIN TTL Cable | TTL function |
|--|--|--|--|
| 1 | TX | 5 | RX |
| 2 | RX | 4 | TX |
| 3 | GND | 1 | GND |

## Configuration
All configuration values can be found in the **MpptToMqttConfig.py**:

    import logging
    
    serialPort = "/dev/tty.usbserial-FTBBWTC9"
    logFileName = "MpptToMqtt.log"
    logLevel = logging.ERROR
    controllerName = "MpptController01"
    mqttServer = "172.17.2.21"
    mqttPort = 1883
    reportInterval = 15
## MQTT topics
### Subscribable topics
| Topic | Description |
|--|--|
|/controllername/Led| Solarpanel led<br>**Bit 8**: led on<br>**Bit 8 & Bit 7**: blink fast<br>**Bit 8 & Bit 6**: blink slow |
|/controllername/ErrorCode| Error code |
|/controllername/Icons| **Bit 8**: Lamp symbol<br>**Bit 7**: Battery led blink slow<br>**Bit 6**: Battery led blink fast |
|/controllername/BatteryVoltage| Battery voltage |
|/controllername/PvVoltage| PV voltage |
|/controllername/ChargeCurrentAmpere| Current charge in ampere |
|/controllername/LoadCurrentAmpere| Current load in ampere |
|/controllername/Temperature| Temperature |
|/controllername/ChargeAmpere| Total ampere charged |
|/controllername/DischargeAmpere| Current discharge in ampere |
### Command topics
| Topic | Description |
|--|--|
| /controllername/Command | Topic for commands. Only command at the moment is **ResetChargeAmpere** to reset the total ampere charged. |
