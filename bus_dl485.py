import serial
import time
from log import Log
import sys


class BusDL485(Log):
    """
    Class to decode and encode DL485 bus communication
    """

    def __init__(self, file, logstate):
        super().__init__(logstate)
        print("-- BusDL485 --")
        self.INITCRC = 0x55
        self.appcrc = []
        self.buffricn = []  # Buffer RX trama
        self.buffricnapp = []  # Contiene i primi 7 byte + byte residui
        self.buffricnlung = 0
        self.Connection = False
        self.crcric = self.INITCRC
        self.crctrasm = 0x55
        self.lastfinepacc = True
        self.crcdoppio = 1
        self.system = ''
        # self.log = Log(file='log.txt', logstate=2)

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
        Trasforma la string ricevuta dalla seriale (dati a 7 bit)
        in byte da 8 bit.
        Ogni 7 byte ricevuti, viene trasmesso l'ottavo BIT di ciascun byte.
        """
        bitresidui = self.buffricnapp.pop()
        i = len(self.buffricnapp) - 1
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
            self.writelog("ERR 3 Pacchetto troppo lungo")
            self.labinitric()
            return []

        if self.lastfinepacc:
            self.lastfinepacc = False
            auscrc = (inSerial & 0x0f) | ((inSerial & 0xE0)//2)
            self.crcric = self.calccrc(self.crcric + 0xaa, self.crcric)  # aggiorna crc
            ric = self.buffricn
            if (auscrc ^ self.crcric) & 0x7f == 0:  # right crc & end trama
                self.labinitric()
                return ric
            else:
                self.writelog(
                    f'SECONDO CRC ERRATO     Ricevuto {hex(auscrc)}    calcolato - {hex(self.crcric)} len_buffricn={len(self.buffricn)} self.buffricnlung:{self.buffricnlung} inSerial:{str(inSerial)}', 'RED')
                self.labinitric()
                return []

        if (inSerial & 0x38) == 0x18 or (inSerial & 0x38) == 0x20:  # end trama
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

                else:  # è un PING
                    self.labinitric()
                    return ric

            else:  # CRC Errato
                self.writelog(
                    f"PRIMO CRC ERRATO       calcolato {self.crcric:>3} ricevuto {inSerial:>3} Len_buffricn={len(self.buffricn):>3} {self.buffricnlung}, {str(self.buffricn)} {str(self.buffricnapp)}", 'RED')
                self.labinitric()
                return []

        elif inSerial == 0:  # Errore 1
            self.writelog("ERR 1:                 Tre 0 ricevuti, byte={}".format(
                hex(inSerial)), 'RED')
            self.labinitric()
            return []

        elif inSerial == 0x38:  # Errore 2
            self.writelog("ERR 2:                 Tre 1 ricevuti, byte={}".format(
                hex(inSerial)), 'RED')
            self.labinitric()
            return []

        else:  # carattere normale
            self.crcric = self.calccrc(inSerial, self.crcric)  # aggiorna crc
            self.buffricnapp.insert(
                self.buffricnlung, ((inSerial & 0x0f) | ((inSerial & 0xE0) // 2)) )  # inserisce carattere decodificato
            if len(self.buffricnapp) == 8:  # Arrivato byte con i bit residui
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
        Codifica byte messaggio con bit sincronismo
        e codice di fine trama piu crc finale
        """
        bytedatrasm = []
        self.crctrasm = self.INITCRC
        for txapp in msg:
            txapp1 = (txapp & 0x0f) | (((txapp & 0x78) ^ 8) * 2)
            bytedatrasm.append(txapp1)
            self.crctrasm = self.calccrc(txapp1, self.crctrasm)
        bytedatrasm.append((self.crctrasm & 0x0f) |
                           (self.crctrasm & 8)*2 |
                           (self.crctrasm & 0x38 ^ 8)*4)
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

        if not rxbytes:
            continue

        for d in rxbytes:
            rxtrama = b.readSerial(d)
            if not rxtrama or len(rxtrama) < 2:
                continue
            print(rxtrama)
        time.sleep(0.0001)
