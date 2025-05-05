#bh1750_helligkeitssensor

#Ersteller: Paul Kramer
#Erstellungsdatum: 29.04.2025 
#Letzte Änderung: 05.05.2025

#Funktion:
    #Scannen des I2C-Busses, Initialisieren des Helligkeitssensors und weiterleiten der Messdaten

#Hardware Komponenten
    #Microcontroller: ESP32-S3-WROOM-1
    #Helligkeitsensor: BH1750

    #I2C (Helligkeitssensor):
        #SCL  = GPIO Pin 4
        #SDA  = GPIO Pin 5

#Benutzte Bibliothek:
    #bh1750:  https://github.com/flrrth/pico-bh1750
#########Bibliotheken#########
from machine import SoftI2C, Pin
from bh1750 import BH1750

#########Variablen#########
i2c = SoftI2C(scl=Pin(4), sda=Pin(5))
bh1750_sensor = None

#########I2C-Bus Scan und BH1750 Initialisierung#########
def init():
    global bh1750_sensor
    print("Scan I2C bus...")
    devices = i2c.scan()
    if len(devices) == 0:
        print("Helligkeitsensor BH1750 nicht gefunden!")
    else:
        bh1750_sensor = BH1750(0x23, i2c)
        print("Helligkeitsensor BH1750 Initialisiert.")

#########Helligkeit Messen#########
def lux():
    try:
        lux = round(bh1750_sensor.measurement)
        return lux
    except:
        print("Helligkeitssensor BH1750, fehler beim Messen!")
        return -1            #Gibt einen Fehler an

#########Selbst Initialiesierung#########
init()