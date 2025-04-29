#Projekt_Kikeriki

#Ersteller: Paul Kramer
#Erstellungsdatum: 11.03.2025   
#Letzte Änderung: 29.04.2025

#Funktion:
    #Steuern einer Hühnerklappe und Zählen der Hühner

#Hardware Komponenten
    #Microcontroller: ESP32-S3-WROOM-1
    #Helligkeitsensor: BH1750 (I2C)
    #RFID-Leser: 2x RDM6300 (UART)
    #Display: ST7789V2 (SPI)
    #Steppermotor: 28BYJ-48
    #Stepper-Control-Board: ULN2003 PCB

#Pin-Belegung
    #Steppermotor
        #Stepper Pin 1 = GPIO Pin 15
        #Stepper Pin 2 = GPIO Pin 16
        #Stepper Pin 3 = GPIO Pin 17
        #Stepper Pin 4 = GPIO Pin 18
    
    #I2C (Helligkeitssensor):
        #SCL  = GPIO Pin 4
        #SDA  = GPIO Pin 5

    #UART1 (RFID-Leser Eingang):
        #RX   = GPIO Pin 7 
        #TX   = GPIO Pin 9 (Nicht Angeklemmt)

    #UART2 (RFID-Leser Ausgang):
        #RX   = GPIO Pin 6 
        #TX   = GPIO Pin 8 (Nicht Angeklemmt)

    #SPI (Display):
        #SCK  = GPIO Pin 14 (Als SCL bezeichnet)
        #MOSI = GPIO Pin 13 (Als SDA bezeichnet)
        #MISO = GPIO Pin 8  (Nicht Angeklemmt)
        #CS   = GPIO Pin 10
    #ST7789 (Display):
        #RES  = GPIO Pin 12 (Reset)
        #DC   = GPIO Pin 11 (Befehls-/Daten-Pin)
        #BLK  = GPIO Pin 9  (Backlight)

#---------------------------------------------------------------------------------------------------------------
#########Bibliotheken#########
import time
from machine import Pin
import umqtt.simple
import ujson
import WLAN
import BH1750_Helligkeitssensor as sensor
from RDM6300_RFID import Rdm6300
import ST7789_Display as Display
import uln2003_stepper

#---------------------------------------------------------------------------------------------------------------
#########Variablen#########
lux = 0
klappenstatus = 0						#Mögliche Staten: "Öffnet", "Schließt", "Geöffnet", "Geschlossen"
draussen = []							#RFID-Nummern der sich draußen befindlichen Hühner
drinnen = []							#RFID-Nummern der sich drinnen befindlichen Hühner
anzahl_draussen = None
anzahl_drinnen = None
hell_zeit = time.ticks_ms()
dunkel_zeit = time.ticks_ms()
klappe = False
zaehler = 0
degree = 0
einstellung_node_red = {
    "lux_grenze": 200,					#Umschaltgrenze in Lux; Unter dem Wert = Klappe Schließt; Über dem Wert = Klappe Öffnet
    "uhrzeit": True,					#True = Die aktuell Uhrzeit ist innerhalb der Uhrzeit, in der die Klappe geöffnet sein soll
    "fahre_nach": "lux",
    "klappe": "Auto"
    }

#---------------------------------------------------------------------------------------------------------------
#########WLAN#########
WLAN.STA("heim")

#---------------------------------------------------------------------------------------------------------------
#########RFID-Leser Initialisieren#########
rfid_reader_eingang = Rdm6300(tx=19, rx=7, uart_nr=1)
rfid_reader_ausgang = Rdm6300(tx=20, rx=6, uart_nr=2)

#---------------------------------------------------------------------------------------------------------------
#########Stepper Motor Initialisieren#########
stepper = uln2003_stepper.FullStepMotor.frompins(15, 16, 17, 18)

#---------------------------------------------------------------------------------------------------------------
#########Einstellungen#########
def einstellungen(topic, msg):
    global einstellung_node_red
    daten = ujson.loads(msg)
    einstellung_node_red = daten
    
#---------------------------------------------------------------------------------------------------------------
#########Klappe Automatikbetrieb#########
def klappe_auto():
    global klappe, hell_zeit, dunkel_zeit
    if einstellung_node_red["fahre_nach"] == "lux":
        if lux >= einstellung_node_red["lux_grenze"]:
            hell_zeit = time.ticks_ms()
        elif lux < einstellung_node_red["lux_grenze"]:
            dunkel_zeit = time.ticks_ms()

        if time.ticks_diff(hell_zeit, dunkel_zeit) > 5000:
            klappe = True
        elif time.ticks_diff(dunkel_zeit, hell_zeit) > 5000:
            klappe = False
                
                
    elif einstellung_node_red["fahre_nach"] == "uhrzeit":
        klappe = einstellung_node_red["uhrzeit"]     

#---------------------------------------------------------------------------------------------------------------
#########JSON#########
def json_format():
    global json_daten
    json_daten = {
            "Helligkeit": lux,
            "Klappenstatus": klappenstatus,
            "Draussen": anzahl_draussen,
            "Drinnen": anzahl_drinnen        
            }

#---------------------------------------------------------------------------------------------------------------
#########MQTT#########
mqtt_client = umqtt.simple.MQTTClient("Kikeriki_ESP32", "192.168.178.47", 1883)
mqtt_client.set_callback(einstellungen)
mqtt_client.connect()
time.sleep(1)
mqtt_client.subscribe("Kikeriki/Node_Red/Einstellungen")

#---------------------------------------------------------------------------------------------------------------
#########Hauptprogramm#########
while True:
    try:
        mqtt_client.check_msg()
    except:
        print("msg nicht lesbar")
    
    lux = sensor.lux()
    karte_eingang = rfid_reader_eingang.read_card()
    karte_ausgang = rfid_reader_ausgang.read_card()
    
    
    
    print(f"""Karte Eingang: {karte_eingang}
Karte Ausgang: {karte_ausgang}""")
            
    #Klappe Fahren
    if einstellung_node_red["klappe"] == "Auto":
        klappe_auto()
    elif einstellung_node_red["klappe"] == "Hand_Auf":
        klappe = True
    elif einstellung_node_red["klappe"] == "Hand_Zu":
        klappe = False
    
    if klappe == True and zaehler < 18:
        klappenstatus = "Oeffnet"
        degree += 20
        if degree == 360:
            degree = 0
        stepper.step_until_angle(degree, dir=1)
        zaehler += 1
        
    elif klappe == False and zaehler > 0:
        klappenstatus = "Schliesst"
        degree -= 20
        if degree == -20:
            degree = 340
        stepper.step_until_angle(degree, dir=-1)
        zaehler -= 1

    elif zaehler == 0:
        klappenstatus = "Geschlossen"    
    elif zaehler == 36:
        klappenstatus = "Offen"
        
        
    #RFID
    if karte_ausgang == None:
        pass
    elif draussen.count(karte_ausgang) == 0:
        draussen.append(karte_ausgang)
        try:
            drinnen.remove(karte_ausgang)
        except:
            pass
        
    if karte_eingang == None:
        pass    
    elif drinnen.count(karte_eingang) == 0:
        drinnen.append(karte_eingang)
        try:
            draussen.remove(karte_eingang)
        except:
            pass

        
    if anzahl_draussen != len(draussen) or anzahl_drinnen != len(drinnen):
        anzahl_draussen = len(draussen)
        anzahl_drinnen = len(drinnen)
        Display.text(anzahl_draussen, anzahl_drinnen)
    
    #Daten zum Broker schicken
    json_format()
    json_daten = ujson.dumps(json_daten)
    print(json_daten)
    try:
        mqtt_client.publish("Kikeriki/ESP32/Daten", json_daten)
    except:
        print("Fehler bei MQTT")
    