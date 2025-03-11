#########Bibliotheken#########
import time
from mfrc522 import MFRC522
from machine import Pin, SoftSPI
import WLAN
import umqtt.simple
import ujson

#########Variablen#########
zaehler = 0
draussen = []
drinnen = []

#########WLAN#########
WLAN.STA()

#########Initialisierung vom SPI#########
spi = SoftSPI(
        baudrate=20000000,
        polarity=1,
        phase=0,
        sck=Pin(42),
        mosi=Pin(40),
        miso=Pin(38))

RFID = MFRC522(spi, rst=Pin(45, Pin.OUT), cs=Pin(36, Pin.OUT))

while True:
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
    
    print(draussen)
    
        
