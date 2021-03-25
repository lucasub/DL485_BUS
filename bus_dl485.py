import serial
import time
from log import Log
import sys

class BusDL485():
    """
    Class to decode and encode DL485 bus communication
    """
        
    def __init__(self, file, logstate):
        print("-- BusDL485 --")
        self.INITCRC = 0x55
        self.appcrc = []
        self.buffricn = []  # Buffer RX trama
        self.buffricnapp = []  # Contiene i primi 7 byte per poi completarli con i bit residui (b7)
        self.buffricnlung = 0
        self.Connection = False
        self.crcric = self.INITCRC
        self.crctrasm = 0x55
        self.lastfinepacc = True
        self.crcdoppio = 1
        self.system = ''
        self.log = Log(file='log.txt', logstate=2)

                
    def ser(self, port='/dev/ttyAMA0', baudrate=19200):
        """
        Instance of serial
        """
        return serial.Serial(port, baudrate)

    def send_data_serial(self, Connection, databyte):
        if self.system == 'Domoticz':
            Connection.Send(Message=bytes(databyte), Delay=0)
        else:
            Connection.write(bytes(databyte))  # invia alla seriale

    def calccrc(self, b, crc):
        """
        Calc CRC of trama
        """
        a = 0xff00 | b
        while a > 255:
            crc = ((((crc ^ a) & 1) * 280) ^ crc) // 2
            a = a // 2
        return crc

    def labinitric(self):
        """
        Reset variable when trama is received
        """
        self.crcric = self.INITCRC
        self.buffricnlung = 0
        self.buffricn = []
        self.appcrc = []
        self.buffricnapp = []

    def seven2eight(self):
        """
        Trasforma la string ricevuta dalla seriale (dati a 7 bit) in byte da 8 bit
        Ogni 7 byte ricevuti, viene trasmesso l'ottavo BIT di ciascun byte.
        """
        bitresidui = self.buffricnapp.pop()
        i = len(self.buffricnapp) -1
        while i >= 0:
            if bitresidui & 1:
                self.buffricnapp[i] |= 128
            bitresidui >>= 1
            i -= 1
        self.buffricn += self.buffricnapp
        self.buffricnapp = []

    def readSerial(self, inSerial):
        """
        Calculate trama and return list with right values
        """
        if self.buffricnlung > 100:  # Errore 3
            self.log.write("ERR 3 Pacchetto troppo lungo")
            self.labinitric()
            return []

        if self.lastfinepacc == True:
            self.lastfinepacc = False
            auscrc = (inSerial & 0x0f) | ((inSerial & 0xE0)//2)
            self.crcric = self.calccrc(self.crcric + 0xaa, self.crcric)  # aggiorna crc
            ric = self.buffricn
            if (auscrc ^ self.crcric) & 0x7f == 0:  # crc corretto e fine pacchetto veramente
                self.labinitric()
                return ric
            else:
                self.log.write(f'ERRORE secondo CRC, calcolato - Ricevuto {hex(self.crcric)}, {hex(auscrc)}, len buffricn= {len(self.buffricn)} {self.buffricnlung}')
                self.labinitric()
                return []

        if (inSerial & 0x38) == 0x18 or (inSerial & 0x38) == 0x20:  # Fine pacchetto
            inSerial = (inSerial & 0x0f) | ((inSerial & 0xc0) // 4)
            if (inSerial ^ self.crcric) & 0x3F == 0:  # crc corretto

                appn = len(self.buffricn) + len(self.buffricnapp)
                if appn > 2:  # non è un ping
                    if self.buffricnapp:
                        self.seven2eight()  # sistema gli ultimi residui
                    ric = self.buffricn
                else:
                    ric = self.buffricnapp

                if len(self.buffricn) > 1:  # Non è un PING
                    if self.crcdoppio == 1:
                        self.lastfinepacc = True
                        return []

                    self.labinitric()
                    return ric

                else: # è un PING
                    self.labinitric()
                    return ric

            else:
                self.log.write(str(self.buffricn) + " * " + str(self.buffricnapp))
                self.log.write("PRIMO CRC ERRATO       calcolato {} ricevuto {} len buffricn={} {}".format(self.crcric, inSerial, len(self.buffricn), self.buffricnlung))
                self.labinitric()
                return []

        elif inSerial == 0:  # Errore 1
            self.log.write("ERR 1: Tre 0 ricevuti, byte={}".format(hex(inSerial)))
            self.labinitric()
            return []

        elif inSerial == 0x38:  # Errore 2
            self.log.write("ERR 2: Tre 1 ricevuti, byte={}".format(hex(inSerial)))
            self.labinitric()
            return []

        else:  # carattere normale
            self.crcric = self.calccrc(inSerial, self.crcric)  # aggiorna crc
            self.buffricnapp.insert(self.buffricnlung, ((inSerial & 0x0f) | ((inSerial & 0xE0)//2)))  # inserisce carattere decodificato
            if len(self.buffricnapp) == 8:  # E' arrivato il byte con i bit residui
                self.seven2eight()
            self.buffricnlung += 1
            return []

    def send_data_serial(self, Connection, databyte):
        if self.system == 'Domoticz':
            Connection.Send(Message=bytes(databyte), Delay=0)
        else:
            Connection.write(bytes(databyte))  # invia alla seriale

    def encodeMsgCalcCrcTx(self, msg):
        """
        Codifica byte messaggio con bit sincronismo e codice di fine trama piu crc finale
        """
        bytedatrasm = []
        self.crctrasm = self.INITCRC
        for txapp in msg:
            txapp1 = (txapp & 0x0f) | (((txapp & 0x78) ^ 8) * 2)
            bytedatrasm.append(txapp1)
            self.crctrasm = self.calccrc(txapp1, self.crctrasm)
        bytedatrasm.append((self.crctrasm & 0x0f) | (self.crctrasm & 8)*2 | (self.crctrasm & 0x38 ^ 8)*4)
        if self.crcdoppio == 1 and len(msg) > 2:

            txapp1 = self.calccrc(self.crctrasm + 0xaa, self.crctrasm)
            txapp1 = (txapp1 & 0x0f) | (((txapp1 & 0x78) ^ 8) * 2)
            bytedatrasm.append(txapp1)
        return bytedatrasm

if __name__ == '__main__':
    bus_port = '/dev/ttyAMA0'
    bus_baudrate = 19200
    b = BusDL485(file="test_log.txt", logstate=1)
    b.Connection = b.ser(bus_port, bus_baudrate)    

    while 1:
        rxbytes = b.Connection.read()

        if not rxbytes: continue

        for d in rxbytes:
            rxtrama = b.readSerial(d)
            if not rxtrama or len(rxtrama)<2: continue
            
            print(rxtrama)
        time.sleep(0.0001)