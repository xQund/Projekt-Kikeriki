#projekt_kikeriki

#Ersteller: Paul Kramer
#Erstellungsdatum: 11.03.2025   
#Letzte Änderung: 05.05.2025

#Funktion:
    #Steuern einer Hühnerklappe und Zählen der Hühner ein und ausgehenden Hühner.
    #Es ist eine Weboberfläche für bessere Bedienung und ansehen der Daten vorhanden.
    #Die Klappe kann sowohl im Automatikbetrieb als auch im Handbetrieb bedient werden.
    #Auf der Weboberfläche können die Bedingungen für den Automatikbetrieb angepasst werden.

#Hardware Komponenten
    #Microcontroller: ESP32-S3-WROOM-1
    #Helligkeitsensor: BH1750 (I2C)
    #RFID-Leser: 2x RDM6300 (UART)
    #Display: ST7789V2 (SPI)
    #Stepper Motor: 28BYJ-48
    #Stepper-Control-Board: ULN2003 PCB

#Pin-Belegung:
    #Microcontroller (ESP32-S3-Wroom-1-N16R8) [U1]:
        #GPIO  4 = [U2] SCL
        #GPIO  5 = [U2] SDA
        #GPIO  6 = [U4] RX
        #GPIO  7 = [U3] RX
        #GPIO  8 = [U6] MISO (Nicht Angeklemmt)
        #GPIO  9 = [U6] BLK
        #GPIO 10 = [U6] CS
        #GPIO 11 = [U6] DC
        #GPIO 12 = [U6] RES
        #GPIO 13 = [U6] MOSI (Als SDA bezeichnet)
        #GPIO 14 = [U6] SCK  (Als SCL bezeichnet)
        #GPIO 15 = [U5] Input 1
        #GPIO 16 = [U5] Input 2
        #GPIO 17 = [U5] Input 3
        #GPIO 18 = [U5] Input 4
        #GPIO 19 = [U3] TX   (Nicht Angeklemmt)
        #GPIO 20 = [U4] TX   (Nicht Angeklemmt)
    
    #Helligkeitssensor (BH1750) [U2]:
        #SCL  = [U1] GPIO Pin 4
        #SDA  = [U1] GPIO Pin 5

    #RFID-Leser Eingang (RDM6300) [U3]:
        #RX   = [U1] GPIO Pin 7 
        #TX   = [U1] GPIO Pin 19 (Nicht Angeklemmt)

    #RFID-Leser Ausgang (RDM6300) [U4]:
        #RX   = [U1] GPIO Pin 6 
        #TX   = [U1] GPIO Pin 20 (Nicht Angeklemmt)

    #Stepper-Control-Board (ULN2003) [U5]:
        #Input 1 = [U1] GPIO Pin 15
        #Input 2 = [U1] GPIO Pin 16
        #Input 3 = [U1] GPIO Pin 17
        #Input 4 = [U1] GPIO Pin 18

    #Display (ST7789V2) [U6]:
        #SCK  = [U1] GPIO Pin 14 (Als SCL bezeichnet)
        #MOSI = [U1] GPIO Pin 13 (Als SDA bezeichnet)
        #MISO = [U1] GPIO Pin 8  (Nicht Angeklemmt)
        #CS   = [U1] GPIO Pin 10  
        #RES  = [U1] GPIO Pin 12 
        #DC   = [U1] GPIO Pin 11 
        #BLK  = [U1] GPIO Pin 9

#Benutzte Bibliotheken:
    #uln2003_stepper: https://github.com/larsks/micropython-stepper-motor/blob/master/motor.py
    #bh1750:          https://github.com/flrrth/pico-bh1750
    #st7789:          https://github.com/russhughes/st7789_mpy
    #vga1_16x32:      https://github.com/russhughes/st7789_mpy/blob/master/fonts/bitmap/vga1_16x32.py
    #vga1_8x8:        https://github.com/russhughes/st7789_mpy/blob/master/fonts/bitmap/vga1_8x8.py
    #rdm6300_rfid:    https://github.com/membermatters/urdm6300/blob/main/urdm6300/__init__.py

#---------------------------------------------------------------------------------------------------------------
####################Bibliotheken####################
import time
from machine import Pin
import umqtt.simple
import ujson
import wlan
import bh1750_helligkeitssensor as helligkeitssensor
from rdm6300_rfid import Rdm6300
import st7789_display as display
import uln2003_stepper

#---------------------------------------------------------------------------------------------------------------
####################Variablen####################
lux = None						#Gemessene Helligkeit vom BH1750(Helligkeitssensor)
klappenstatus = None			#Mögliche Staten: "Oeffnet", "Schliesst", "Offen", "Geschlossen"
draussen = []					#Liste mit allen RFID-Nummern der sich draußen befindenden Hühnern
drinnen = []					#Liste mit allen RFID-Nummern der sich drinnen befindenden Hühnern
registrierte_rfids = []			#Liste aller registrierten RFID-Karten
anzahl_draussen = None			#Anzahl der sich draussen befindenden Hühnern
anzahl_drinnen = None			#Anzahl der sich drinnen befindenden Hühnern                             
hell_zeit = time.ticks_ms()		#Referenzzeit, wird verwendet um herrauszufinden wie lange die lux_grenze schon überschritten ist
dunkel_zeit = time.ticks_ms()	#Referenzzeit, wird verwendet um herrauszufinden wie lange die lux_grenze schon unterschritten ist
klappe = False					#False = Klappe fährt zu  |  True = Klappe fährt auf
klappenposition = 0				#Hält fest wie weit die Klappe geöffnet ist    0=geschlossen | 18=geöffnet
grad = 0						#Die vom Steppermotor anzufahrende Position in Grad
klappenbetrieb = "Auto"			#Klappe im Auto- oder Handbetrieb
uhrzeit = False					#True = Die aktuell Uhrzeit ist innerhalb der Uhrzeit, in der die Klappe geöffnet sein soll
json_daten = None				#Analgendaten die zum Broker gepublished werden.
json_status = None				#Anlagenstatus der gepublished wird. True = Anlage in Betrieb   False = Anlage außer Betrieb
lux_zeit = None					#Gespeicherte Helligkeitszeit in ms. Sobald die Helligkeit die eingestellte Helligkeitsgrenze für die Dauer dieser Zeit über- oder unterschreitet, fährt die Klappe im Automatikbetrieb 

#WLAN
ssid = "BZTG-IoT"				#WLAN-SSID
passwort = "WerderBremen24"		#WLAN-Passwort
wlan_fehler = None				#WLAN-Verbindung   None= Erfolgreich  |  String= Gescheitert

#Alle von Node-Red kommenden Einstellungen
einstellung_node_red = {
    "lux_grenze": 200,			#Umschaltgrenze in Lux; Unter dem Wert = Klappe Schließt; Über dem Wert = Klappe Öffnet
    "lux_zeit": 300,			#Wird die lux_grenze für die angegeben Zeit überschritten, fährt die Klappe. Angabe ist in Sekunden
    "fahre_nach": "lux",		#Die Klappe wird nach "lux" oder "uhrzeit" gefahren
    "huehner_anzahl": 7,		#Anzahl der gesamten Hühner
    "auf_huehner_warten": True	#True = Vor dem Schließen der Klappe, wird gewartet bis alle Hühner im Stall sind
    }
#---------------------------------------------------------------------------------------------------------------
####################RFID-Leser Initialisieren####################
rfid_reader_eingang = Rdm6300(tx=19, rx=7, uart_nr=1)
rfid_reader_ausgang = Rdm6300(tx=20, rx=6, uart_nr=2)
    
#---------------------------------------------------------------------------------------------------------------
####################Stepper Motor Initialisieren####################
stepper = uln2003_stepper.FullStepMotor.frompins(15, 16, 17, 18)

#---------------------------------------------------------------------------------------------------------------
####################WLAN Initialisieren####################
wlan_fehler = wlan.sta(ssid, passwort)

#---------------------------------------------------------------------------------------------------------------
####################JSON Status####################
#Schreiben des Verbindungsstatus ins JSON-Format
def json_format_status(status):
    global json_status
    json_status = {"Status": status}
    json_status = ujson.dumps(json_status)  #Daten ins JSON-Format Umwandeln

#---------------------------------------------------------------------------------------------------------------
####################JSON Status####################
#Schreiben der Daten die zum Broker geschickt werden
def json_format_daten():
    global json_daten
    json_daten = {
            "Helligkeit": lux,
            "Klappenstatus": klappenstatus,
            "Draussen": anzahl_draussen,
            "Drinnen": anzahl_drinnen        
            }
    json_daten = ujson.dumps(json_daten)  #Daten ins JSON-Format Umwandeln
    
#---------------------------------------------------------------------------------------------------------------
####################Daten von Node-Red verarbeiten####################
def sub_node_red_daten(topic, msg):
    global einstellung_node_red, klappenbetrieb, uhrzeit
    daten = ujson.loads(msg)
    topic = topic.decode('utf-8')
    if topic == "Kikeriki/Node_Red/Einstellungen":
        einstellung_node_red = daten    #Die vorherigen Daten werden Überschrieben
    elif topic == "Kikeriki/Node_Red/Klappenbetrieb":
        klappenbetrieb = daten.get("klappenbetrieb")
    elif topic == "Kikeriki/Node_Red/Uhrzeit":
        uhrzeit = daten.get("uhrzeit")
        
#---------------------------------------------------------------------------------------------------------------
####################Klappe Automatikbetrieb####################
def klappe_auto():
    global klappe, hell_zeit, dunkel_zeit
    #Abfrage, ob vor dem runterfahren der Klappe auf alle Hühner gewartet werden soll
    if einstellung_node_red["auf_huehner_warten"]:
        if anzahl_drinnen == einstellung_node_red["huehner_anzahl"]:
            alle_hühner_drinnen = True
        else:
            alle_hühner_drinnen = False
    else:
        alle_hühner_drinnen = True
    
    #Klappe wird nach Helligkeit gefahren
    if einstellung_node_red["fahre_nach"] == "lux":
        #Vergleichszeiten bestimmen 
        if lux >= einstellung_node_red["lux_grenze"]:
            hell_zeit = time.ticks_ms()
        elif lux < einstellung_node_red["lux_grenze"]:
            dunkel_zeit = time.ticks_ms()
        
        #Klappe fährt erst nach der eingestellten Zeit in Sekunden über/unter der eingestellten Lux-Grenze auf/zu
        lux_zeit = einstellung_node_red["lux_zeit"] * 1000      #Zeit die in Sekunden angegeben ist, wird in Milisekunden abgeändert
        if time.ticks_diff(hell_zeit, dunkel_zeit) > lux_zeit:
            klappe = True
        elif time.ticks_diff(dunkel_zeit, hell_zeit) > lux_zeit and alle_hühner_drinnen:
            klappe = False
    
    #Klappe wird nach Uhrzeit gefahren (Die Auswertung der Uhrzeit geschieht in Node-Red)
    elif einstellung_node_red["fahre_nach"] == "uhrzeit":
        if uhrzeit:
            klappe = True
        elif not uhrzeit and alle_hühner_drinnen:
            klappe = False
    
    #Fährt die Klappe wieder hoch, falls ein Huhn beim runterfahren rausgeht
    if not alle_hühner_drinnen:
        klappe = True
    
#---------------------------------------------------------------------------------------------------------------
####################MQTT####################
mqtt_client = umqtt.simple.MQTTClient("Kikeriki_ESP32", "192.168.178.47", 1883)
mqtt_client.set_callback(sub_node_red_daten)
json_format_status(False)
mqtt_client.set_last_will("Kikeriki/ESP32/Status", json_status, retain=False, qos=2)  #Bei Verbindungsverlust oder Anlagenausfall wird das auf Node-Red angezeigt 
try:
    mqtt_client.connect()
    time.sleep(1)
    mqtt_client.subscribe("Kikeriki/Node_Red/Einstellungen")   
    mqtt_client.subscribe("Kikeriki/Node_Red/Klappenbetrieb")
    mqtt_client.subscribe("Kikeriki/Node_Red/Uhrzeit")
    json_format_status(True)
    mqtt_client.publish("Kikeriki/ESP32/Status", json_status, qos=1) #Erfolgreicher Verbindungsaufbau zu MQTT wird auf Node-Red angezeigt      
    print("MQTT ist Verbunden!")
except:
    print("Verbindungsaufbau zu MQTT Fehlgeschlagen!")



#---------------------------------------------------------------------------------------------------------------
####################Hauptprogramm####################
while True:
    ##############Daten vom Broker erhalten##############
    #MQTT Callback / Daten von Node-Red verarbeiten      
    try:                                                 
        mqtt_client.check_msg()                          
    except:                                              
        print("Fehler beim Erhalten der Daten von MQTT!")
        
    #----------------------------------------------------
    ####################Sensoren#########################
    #Lux-Wert wird gemessen
    lux = helligkeitssensor.lux()    #Wert von -1 = Messfehler
    
    #RFID-Karte am Eingang wird gelesen    None = keine Karte erkannt
    try:
        karte_eingang = rfid_reader_eingang.read_card()
    except:
        karte_eingang = None
    
    #RFID-Karte am Ausgang wird gelesen    None = keine Karte erkannt
    try:
        karte_ausgang = rfid_reader_ausgang.read_card()
    except:
        karte_ausgang = None
        
    #RFID-Auswertung Ausgang (Karten werden zu Draussen hinzugefügt, sofern sie Drinnen registriert waren)
    if karte_ausgang == None:    #Keine Karte erkannt
        pass
    elif draussen.count(karte_ausgang) == 0 and drinnen.count(karte_ausgang) == 1:  #Karte befindet sich Drinnen und noch nicht Draussen
        draussen.append(karte_ausgang)        #Karte nach Draussen hinzufügen
        drinnen.remove(karte_ausgang)         #Karte von Drinnen entfernen
    
    #RFID-Auswertung Eingang (Karten werden zu Drinnen hinzugefügt und können auch neu registriert werden)
    if karte_eingang == None:    #Keine Karte erkannt
        pass    
    elif drinnen.count(karte_eingang) == 0:  #Karte befindet sich noch nicht Drinnen
        drinnen.append(karte_eingang)        #Karte nach Drinnen hinzufügen
        try:
            draussen.remove(karte_eingang)   #Karte von Draussen entfernen
        except:
            pass
            
    #----------------------------------------------------
    #####################Aktoren#########################
    ####Display####
    #Das Display aktuallisiert sich nur ganz am Anfang, bei einem WLAN-Fehler, wenn ein Huhn raus- oder reinläuft oder die Hühneranzahl geändert wird
    if anzahl_draussen != len(draussen) or len(draussen) + len(drinnen) != einstellung_node_red["huehner_anzahl"] or wlan_fehler != None:
        anzahl_draussen = len(draussen)
        anzahl_drinnen =  einstellung_node_red["huehner_anzahl"] - anzahl_draussen
        display.text(anzahl_draussen, anzahl_drinnen, wlan_fehler)
        
    ####Klappe fahren####
    #Überprüfung ob die Klappe im Auto- oder Handbetrieb steht
    if klappenbetrieb == "Auto":
        klappe_auto()             #Automatikbetrieb
    elif klappenbetrieb == "Hand_Auf":
        klappe = True             #Hand auffahren
    elif klappenbetrieb == "Hand_Zu":
        klappe = False            #Hand zufahren
    
    #Klappe auffahren
    if klappe == True and klappenposition < 18:
        klappenstatus = "Oeffnet"
        grad += 20
        if grad == 360:   #Die maximale Position die der Motor fahren kann ist 359 Grad
            grad = 0                          #Der Motor wird immer nur um 20 Grad weiter verfahren,
        stepper.step_until_angle(grad, dir=1) #um das Programm nicht zu lange zu pausieren
        klappenposition += 1
    
    #Klappe zufahren
    elif klappe == False and klappenposition > 0 and karte_eingang == None and karte_ausgang == None:
        klappenstatus = "Schliesst"
        grad -= 20
        if grad == -20:   #Die minimale Position die der Motor fahren kann ist 0 Grad
            grad = 340                         #Der Motor wird immer nur um 20 Grad weiter verfahren, 
        stepper.step_until_angle(grad, dir=-1) #um das Programm nicht zu lange zu pausieren
        klappenposition -= 1 
    
    #Klappenstatus aktualisieren
    elif klappenposition == 0:
        klappenstatus = "Geschlossen"    
    elif klappenposition == 18:
        klappenstatus = "Offen"
        
    #----------------------------------------------------
    ##############Daten zum Broker schicken##############
    json_format_daten()   #Daten holen
    
    #Daten zum Broker schicken
    try:
        mqtt_client.publish("Kikeriki/ESP32/Daten", json_daten)
    except:
        print("Fehler beim Verschicken der Daten zu MQTT!")
    