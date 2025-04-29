#ST7789_Display

#Ersteller: Paul Kramer
#Erstellungsdatum: 29.04.2025   
#Letzte Änderung: 29.04.2025

#Funktion:
    #Initialisierung des Displays und Anzeigen von den sich drinnen und draussen befindlichen Hühnern

#Hardware Komponenten
    #Microcontroller: ESP32-S3-WROOM-1
    #Display: ST7789V2

#Pin-Belegung
    #SPI (Display):
        #SCK  = GPIO Pin 14 (Als SCL bezeichnet)
        #MOSI = GPIO Pin 13 (Als SDA bezeichnet)
        #MISO = GPIO Pin 8  (Nicht Angeklemmt)
        #CS   = GPIO Pin 10
    #ST7789 (Display):
        #RES  = GPIO Pin 12 (Reset)
        #DC   = GPIO Pin 11 (Befehls-/Daten-Pin)
        #BLK  = GPIO Pin 9  (Backlight)

#########Bibliotheken#########
import time
from machine import Pin, SoftSPI
from st7789 import ST7789         #Display Bibliothek
import vga1_16x32 as font         #Schriftgröße: 16 Pixel Breit & 32 Pixel Hoch

#########Dictionarys#########
Farben = {                     #Hexadezimal-Code der angegebnenen Farben
"black": 0x0000,
"blue": 0x001F,
"red": 0xF800,
"green": 0x07E0,
"cyan": 0x07FF,
"magenta": 0xF81F,
"yellow": 0xFFE0,
"white": 0xFFFF}

#########Variablen#########
#display_rand = Angabe der vorhandenen Pixel auf dem Display für alle Richtungen
display_rand = [(240, 280, 0, 20),
                (280, 240, 20, 0),
                (240, 280, 0, 20),
                (280, 240, 20, 0)]
display_breite = 240    #Anzahl der vertikalen Pixel

#########SPI Initialisieren#########
spi = SoftSPI(
        baudrate=20000000,
        polarity=1,
        phase=0,
        sck=Pin(14),
        mosi=Pin(13),
        miso=Pin(8))

#########Display Initialisieren#########
display = ST7789(
    spi,
    width=240,
    height=280,
    reset=Pin(12, Pin.OUT),
    dc=Pin(11, Pin.OUT),
    cs=Pin(10, Pin.OUT),
    backlight=Pin(9, Pin.OUT),
    table=display_rand,
    rotation=0)

#########Text anzeigen#########
def text(draussen, drinnen, schriftfarbe="white", hgfarbe="black"):
    #drinnen:		Angezeigter Text auf dem Display als String (Zeigt die Anzahl der sich drinnen befindlichen Hühner an)
    #draussen:		Angezeigter Text auf dem Display als String (Zeigt die Anzahl der sich draussen befindlichen Hühner an)
    #schriftfarbe:	Schriftfarbe als String (siehe Dictionary Farben)
    #hgfarbe:		Hintergrundfarbe als String (siehe Dictionary Farben)
    
    #Zu String umwandeln, da nur Strings auf dem Display angezeigt werden können
    draussen = str(draussen)
    drinnen = str(drinnen)
    
    #Die als String eingetragenen Farben zu Hexadezimal-Codes umwandeln
    try:
        schriftfarbe = Farben[schriftfarbe]
        hgfarbe = Farben[hgfarbe]
    except:
        print ("Fehler: Ausgewählte Displayfarbe nicht vorhanden! \nStandard Farben werden stattdessen benutzt.")
        schriftfarbe = Farben["white"]
        hgfarbe = Farben["black"]
    
    
    
    #Mittige Formatierung für die Anzahl der sich draussen befindlichen Hühner anpassen
    mittige_formatierung = int(display_breite /2 - round((len(draussen) *8)))
    
    #Text auf dem Display anzeigen
    display.text(font, "Huehner", 64, 20, schriftfarbe, hgfarbe)
    display.text(font, "Draussen:", 48, 55, schriftfarbe, hgfarbe)
    display.text(font, draussen, mittige_formatierung, 95, schriftfarbe, hgfarbe)
    
    
    #Mittige Formatierung für die Anzahl der sich drinnen befindlichen Hühner anpassen
    mittige_formatierung = int(display_breite /2 - round((len(drinnen) *8)))
    
    #Text auf dem Display anzeigen
    display.text(font, "Drinnen:", 56, 160, schriftfarbe, hgfarbe)
    display.text(font, drinnen, mittige_formatierung, 200, schriftfarbe, hgfarbe)
    
   


        
