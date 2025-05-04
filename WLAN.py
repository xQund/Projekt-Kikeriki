#WLAN

#Ersteller: Paul Kramer
#Erstellungsdatum: 27.01.2025   
#Letzte Änderung: 04.05.2025

#Funktion:
    #Verbinden mit einem WLAN-Netz und zurückgeben des Verbindungsstatus

#Hardware Komponenten
    #Microcontroller: ESP32-S3-WROOM-1

#########Bibliotheken#########
import network
import time

#########WLAN Initialisieren#########
wlan = network.WLAN(network.STA_IF)

#########WLAN statische Verbindung#########
def STA(ssid, passwort):
    aktuelle_zeit = 0
    wlan.active(False)
    time.sleep(1)               #Sichergehen, dass das WLAN vollständig deaktiviert ist
    wlan.active(True)
    wlan.config(txpower=8.5)    #WiFi-Sende DB erhöht, da bei standard Einstellungen
                                #keine konstante Verbindung aufgebaut werden kann
    
    #Verbindungsaufbau
    wlan.connect(ssid, passwort)
    start_zeit = time.ticks_ms()         #Referenz Zeit für die Verbindungswartezeit
    print("Warte auf Verbindung...")
    
    #Auf die Verbindung wird maximal 5 Sekunden gewartet, um das Programm nicht aufzuhängen
    while not wlan.isconnected() and time.ticks_diff(aktuelle_zeit, start_zeit) < 5000:
        aktuelle_zeit = time.ticks_ms()  #Die aktuelle Zeit zum Vergleichen der Verbindungswartezeit
    
    #Der Verbindungsstatus wird für weitere Verwendung zurückgegeben
    if wlan.isconnected():
        print("WLAN ist verbunden:", wlan.ifconfig()[0])
        return None                             #None = Kein Fehler
    else:
        print("Verbindung ist gescheitert!")
        return "Keine WLAN Verbindung!"         #Fehler wird auf dem Display angezeigt
    