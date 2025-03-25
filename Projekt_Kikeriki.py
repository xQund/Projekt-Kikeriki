#Projekt_Kikeriki
#11.03.2025   Paul Kramer
#Letzte Änderung: 25.03.2025
#Steuern einer Hühnerklappe und Zählen der Hühner
#ESP32-S3

#---------------------------------------------------------------------------------------------------------------
#########Bibliotheken#########
import time
from mfrc522 import MFRC522
from machine import Pin, SoftSPI
import WLAN
import umqtt.simple
import I2C_Bus as sensor
import ujson

#---------------------------------------------------------------------------------------------------------------
#########Variablen#########
zaehler = 0
lux = 0
draussen = []
drinnen = []
klappe = Pin(8, Pin.OUT)
hell_zeit = time.ticks_ms()
dunkel_zeit = time.ticks_ms()

#---------------------------------------------------------------------------------------------------------------
#########WLAN#########
WLAN.STA()

#---------------------------------------------------------------------------------------------------------------
#########Initialisierung vom SPI#########
spi = SoftSPI(
        baudrate=20000000,
        polarity=1,
        phase=0,
        sck=Pin(42),
        mosi=Pin(40),
        miso=Pin(38))

RFID = MFRC522(spi, rst=Pin(45, Pin.OUT), cs=Pin(36, Pin.OUT))

#---------------------------------------------------------------------------------------------------------------
#########MQTT#########
mqtt_client = umqtt.simple.MQTTClient("Kikeriki_ESP32", "192.168.1.165", 1883)

#---------------------------------------------------------------------------------------------------------------
#########JSON#########
def json_format():
    return {
            "Helligkeit":lux,
            "Draussen": len(draussen),
            "Drinnen": len(drinnen)
            }

#---------------------------------------------------------------------------------------------------------------
#########Hauptprogramm#########
while True:
    lux = sensor.lux()
    if lux >= 300:
        hell_zeit = time.ticks_ms()
    elif lux < 100:
        dunkel_zeit = time.ticks_ms()
        
    if time.ticks_diff(hell_zeit, dunkel_zeit) > 5000:
        klappe.on()
        
    elif time.ticks_diff(dunkel_zeit, hell_zeit) > 5000:
        klappe.off()
        
    card = RFID.read_card()
    if card == None:
        pass
    elif draussen.count(card[0]) == 0:
        draussen.append(card[0])
        try:
            drinnen.remove(card[0])
        except:
            pass
    elif drinnen.count(card[0]) == 0:
        drinnen.append(card[0])
        try:
            draussen.remove(card[0])
        except:
            pass
    else:
        time.sleep(1)
        
    json_daten = ujson.dumps(json_format())
    
    try:
        mqtt_client.connect()
        mqtt_client.publish("Kikeriki/ESP32/Daten", json_daten)
        mqtt_client.disconnect()
    except:
        print("Fehler bei MQTT")
    
    
        
