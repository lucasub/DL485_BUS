#!/usr/bin/python3.4
# -*- coding: utf-8 -*-
"""
Class protocol DL485
"""
import sys
import os
print("Working PATH:", os.getcwd())
import arduinoserial
from pprint import pprint
import time
import logging
import math
import json
import re
import curses

class Log:
    def __init__(self, file='log.txt', logstate=0):
        self.logstate = logstate
        self.file = file
        logging.basicConfig(format = '%(asctime)s %(message)s',
            datefmt = '%m/%d/%Y %H:%M:%S',
            filename = self.file,
            level=logging.DEBUG)

    def write(self, data=''):
        """
        Write log to file or screen
        """
        if self.logstate & 1:
            logging.debug('%s' %data)  # Write LOG to file
        if self.logstate & 2:
            print('%s' %data)  # Show log to terminal

"""
ERRORI DA CORREGGERE:
quando IO disabilitato, non inserire sui dizionari della configurazione
"""

class Bus:
    EEPROM_LANGUAGE = 1  # 1=NEW,  0=old
    code = {  # Dict with all COMAND
        0: 'INPUT',
        1: 'OUTPUT',
        2: 'CR_TRASPORTO_STR',
        3: 'CR_RD_PARAM_IO',  # Read parametro EEPROM 2 byte ricevuti
        0: 'BROADCAST',  # Invia il comando a tutti i nodi. Da inserire al posto dell'indirizzo Board
        4: 'CR_RD_EE',  # Comando per leggere la EE
        5: 'CR_WR_PARAM_IO',  # Write parametro EEPROM 2 byte
        6: 'CR_WR_EE',  # Comando per scrivere la EE
        7: 'CR_RD_IN',  # Leggi valore ingresso
        8: 'CR_WR_OUT',  # Scrivi valore uscita
        10: 'CR_INIT_SINGOLO_IO',  # Mandare per aggiunare singola configurazione IO oppure REBOOT totale
        11: 'CR_REBOOT',  # Fa il reboot della scheda
        12: 'CR_GET_TIPO_BOARD',  # Ritorna il tipo di board
        13: 'ERRORE',  # Errore generico
        14: 'COMUNICA_IO',  # Mitt. COmando comunica IO, N. ingresso, valore inresso
        15: 'I2C ACK',  # Mitt. COmando comunica IO, N. ingresso, valore inresso
        16: 'CLEARIO_REBOOT', #cancella area io e fa reboot

        'INPUT': 0,
        'OUTPUT': 1,
        'CR_TRASPORTO_STR': 2,
        'CR_RD_PARAM_IO': 3,  # Read parametro EEPROM 2 byte ricevuti
        'BROADCAST': 0,  # Invia il comando a tutti i nodi. Da inserire al posto dell'indirizzo Board
        'CR_RD_EE': 4,  # Comando per leggere la EE
        'CR_WR_PARAM_IO': 5,  # Write parametro EEPROM 2 byte
        'CR_WR_EE': 6,  # Comando per scrivere la EE
        'CR_RD_IN': 7,  # Leggi valore ingresso
        'CR_WR_OUT': 8,  # Scrivi valore uscita
        'CR_INIT_SINGOLO_IO': 10,  # Mandare per aggiunare singola configurazione IO oppure REBOOT totale
        'CR_REBOOT': 11,  # Fa il reboot della scheda
        'CR_GET_TIPO_BOARD': 12,  # Ritorna il tipo di board
        'ERRORE': 13,  # Errore generico
        'COMUNICA_IO': 14,  # Mitt. COmando comunica IO, N. ingresso, valore inresso
        'I2C ACK': 15,  # Mitt. COmando comunica IO, N. ingresso, valore inresso
        'CLEARIO_REBOOT': 16
    }

    disable_io = 0x3e
    enable_io = 0xff

    error = {  # Dict with ERROR type
        1: "Errore 3 zeri",
        2: "Errore 3 uni",
        3: "Errore CRC",
        4: "Pacchetto sentito uguale a se stesso",
        5: "Indirizzo mittente fuori range",  # da 0 a 24
        6: "Manca indirizzo destinatario",
        7: "Manca parametri",
        8: "Troppi Byte pacchetto",
        9: "Manca parametri",
        10: "I2C occupata",
        11: "Manca Byte residui",
        12: "Troppi Byte dati",
        13: "Errore comando a zero parametri",
        14: "Errore comando a 1 parametro",
        15: "Errore comando a 2 parametri",
        16: "Errore comando a 3 parametri",
        17: "Errore comando a 4 parametri",
        18: "Errore comando n parametri non previsto ",
        19: "Pacchetto ricevuto troppo lungo",
        20: "I2C occupata",
        21: "I2C Timeout",
        22: "OneWire Occupata",
        23: "Ricevuto pacchetto nullo",
        24: "OneWire Occupata",
        25: "Lettura numero ingreso fuori range",
        26: "Dimensione pacchetto non conforme",
        27: "Accesso EE oltre limite indirizzo",
        28: "Scrittura numero uscita fuori range",
        29: "Numero parametro fuori range",
        30: "Nodo occupato da ordine precedente",
        31: "Accesso EE sotto spazio EE IO",
    }

    i2c_const = {  # Const I2C
        'CONCATENA': 128,
        'NON_CONCATENA': 0,
        'BYTE_OPZIONI_LETTURA': 64,
        'BYTE_OPZIONI_SCRITTURA': 0,
        'FLAG_PAUSA': 0x20, #definizione per vecchio linguaggio
    }
    if EEPROM_LANGUAGE == 1:  # nuovo linguaggio
            i2c_const['FLAG_PAUSA'] = 128

    # Micro function
    mf = {
        'D': 'DIGITAL',
        'A': 'ANALOG',
        'P': 'PWM',
        'SDA': 'I2C_SDA',
        'SCL': 'I2C_SCL',
        'I': 'INPUT',
        'O': 'OUTPUT',
        'VCC': 'VCC',
        'GND': 'GND',
        'X': 'CRYSTAL',
        'PR': 'PUSH PROGRAMMER',
        'LT': 'LED TX',
        'LR': 'LED RX',
        'MI': 'MISO',
        'MO': 'MOSI',
        'SC': 'SCK',

    }

    # Function PIN map: I=input, O=output, P=pwm, SDA=sda, VCC=VCC, GND=GND, X=xtal, PROG=prog_button, LED_TX=led TX,
    #                  LED_RX=led RX, MO=MOSI, MI=MISO, SC=Serial clock, TX_BUS=BUS, AT=Atemega temp, 
    mapmicro = {  # MAP PIN Atmega328P QFN32PIN
         1: {'name': 'PD3',         'iomicro':    3,    'function': ['I', 'O', 'P']},
         2: {'name': 'PD4',         'iomicro':    4,    'function': ['I', 'O']},
         3: {'name': 'PE0',         'iomicro':   21,    'function': ['I', 'O', 'SDA']},
         4: {'name': 'VCC',         'iomicro':   99,    'function': ['VCC']},
         5: {'name': 'GND',         'iomicro':   99,    'function': ['GND']},
         6: {'name': 'PE1',         'iomicro':   22,    'function': ['I', 'O', 'A']},
         7: {'name': 'XTAL1',       'iomicro':   99,    'function': ['X']},
         8: {'name': 'XTAL2',       'iomicro':   99,    'function': ['X']},
         9: {'name': 'PD5',         'iomicro':    5,    'function': ['PROG']},
        10: {'name': 'PD6',         'iomicro':    6,    'function': ['LED_TX']},
        11: {'name': 'PD7',         'iomicro':    7,    'function': ['LR']},
        12: {'name': 'PB0',         'iomicro':    8,    'function': ['I', 'O']},
        13: {'name': 'PB1',         'iomicro':    9,    'function': ['I', 'O', 'P']},
        14: {'name': 'PB2',         'iomicro':   10,    'function': ['I', 'O', 'P']},
        15: {'name': 'PB3',         'iomicro':   11,    'function': ['I', 'O', 'MO']},
        16: {'name': 'PB4',         'iomicro':   12,    'function': ['I', 'O', 'MI']},
        17: {'name': 'PB5',         'iomicro':   13,    'function': ['I', 'O', 'SC']},
        18: {'name': 'AVCC',        'iomicro':   99,    'function': ['VCC']},
        19: {'name': 'ADC6 PE2',    'iomicro':   23,    'function': []},
        20: {'name': 'AREF',        'iomicro':   99,    'function': []},
        21: {'name': 'GND',         'iomicro':   99,    'function': []},
        22: {'name': 'ADC7 PE3',    'iomicro':   24,    'function': []},
        23: {'name': 'PC0',         'iomicro':   14,    'function': []},
        24: {'name': 'PC1',         'iomicro':   15,    'function': []},
        25: {'name': 'PC2',         'iomicro':   16,    'function': []},
        26: {'name': 'PC3',         'iomicro':   17,    'function': []},
        27: {'name': 'PC4',         'iomicro':   18,    'function': []},
        28: {'name': 'PC5',         'iomicro':   19,    'function': []},
        29: {'name': 'RST',         'iomicro':   99,    'function': []},
        30: {'name': 'PD0',         'iomicro':    0,    'function': []},
        31: {'name': 'PD1',         'iomicro':    1,    'function': ['TX_BUS']},
        32: {'name': 'PD2',         'iomicro':    2,    'function': ['']},
        33: {'name': 'BME280',      'iomicro':   18,    'function': []},
        34: {'name': 'BME280',      'iomicro':   18,    'function': []},
        35: {'name': 'DS18B20',     'iomicro':    3,    'function': []},
        37: {'name': 'TEMP_ATMEGA', 'iomicro':   25,    'function': ['AT']},
        38: {'name': 'AM2320',      'iomicro':   18,    'function': ['AM2320']},
        41: {'name': 'VIRT1',       'iomicro':   40,    'function': ['VIRTUAL1']},
        42: {'name': 'VIRT2',       'iomicro':   40,    'function': ['VIRTUAL2']},
        43: {'name': 'VIRT3',       'iomicro':   40,    'function': ['VIRTUAL3']},
        44: {'name': 'VIRT4',       'iomicro':   40,    'function': ['VIRTUAL4']},
        45: {'name': 'VIRT5',       'iomicro':   40,    'function': ['VIRTUAL5']},
    }

    iomap = { # MAP IO of board
        1: {  # DL485M
            'PB0':          {'pin':  12,  'name':   'IO4'},
            'PB1':          {'pin':  13,  'name':   'IO5'},
            'PB2':          {'pin':  14,  'name':   'IO8'},
            'PB3':          {'pin':  15,  'name':   'IO15'},
            'PB4':          {'pin':  16,  'name':   'IO13'},
            'PB5':          {'pin':  17,  'name':   'IO14'},
            'PD3':          {'pin':   1,  'name':   'IO6'},
            'PD4':          {'pin':   2,  'name':   'IO7'},
            'PC0':          {'pin':  23,  'name':   'IO9'},
            'PC1':          {'pin':  24,  'name':   'IO10'},
            'PC2':          {'pin':  25,  'name':   'IO11'},
            'PC3':          {'pin':  26,  'name':   'IO12'},
            'PC4':          {'pin':  27,  'name':   'IO11'},
            'PC5':          {'pin':  28,  'name':   'IO12'},
            'PE0':          {'pin':   3,  'name':   'SDA'},
            'PE1':          {'pin':   6,  'name':   ''},
            'PE2':          {'pin':  19,  'name':   ''},
            'VIN':          {'pin':  22,  'name':   'VIN'},
            'PCA9535':      {'pin':   0,  'name':   'PCA9535'},
            'BME280':       {'pin':   0,  'name':   'BME280'},
            'BME280B':      {'pin':   0,  'name':   'BME280'},
            'AM2320':       {'pin':   0,  'name':   'AM2320'},
            'TSL2561':      {'pin':   0,  'name':   'TSL2561'},
            'DS18B20-1':    {'pin':  35,  'name':   'DS18B20'},
            'DS18B20-2':    {'pin':  35,  'name':   'DS18B20'},
            'DS18B20-3':    {'pin':  35,  'name':   'DS18B20'},
            'DS18B20-4':    {'pin':  35,  'name':   'DS18B20'},
            'DS18B20-5':    {'pin':  35,  'name':   'DS18B20'},
            'DS18B20-6':    {'pin':  35,  'name':   'DS18B20'},
            'DS18B20-7':    {'pin':  35,  'name':   'DS18B20'},
            'TEMP_ATMEGA':  {'pin':  37,  'name':   'TEMP_ATMEGA'},
            'DS18B20-6':    {'pin':  35,  'name':   'DS18B20'},
        },

        2: {  # DL485B
            'IO1':          {'pin':  23,  'name':    'IO1',       'function': ['I', 'O', 'A']},
            'IO2':          {'pin':  24,  'name':    'IO2',       'function': ['I', 'O', 'A']},
            'IO3':          {'pin':  25,  'name':    'IO3',       'function': ['I', 'O', 'A']},
            'IO4':          {'pin':  26,  'name':    'IO4',       'function': ['I', 'O', 'A']},
            'OUT1':         {'pin':   3,  'name':    'RELE1',     'function': ['O']},
            'OUT2':         {'pin':   2,  'name':    'RELE2',     'function': ['O']},
            'OUT3':         {'pin':   1,  'name':    'RELE3',     'function': ['O']},
            'VIN':          {'pin':  22,  'name':    'VIN',       'function': ['VIN']},
            'SDA':          {'pin':  27,  'name':    'SDA',       'function': ['SDA']},
            'SCL':          {'pin':  28,  'name':    'SCL',       'function': ['SCL']},
            'PCA9535':      {'pin':   0,  'name':    'PCA9535'},
            'BME280A':      {'pin':   0,  'name':    'BME280'},
            'BME280B':      {'pin':   0,  'name':    'BME280'},
            'TSL2561':      {'pin':   0,  'name':    'TSL2561'},
            'DS18B20':      {'pin':  35,  'name':    'DS18B20'},
            'TEMP_ATMEGA':  {'pin':  37,  'name':    'TEMP_ATMEGA'},
            'VIRT1':        {'pin':  41,  'name':    'VIRT1'},
            'VIRT2':        {'pin':  42,  'name':    'VIRT2'},
            'VIRT3':        {'pin':  43,  'name':    'VIRT3'},
            'VIRT4':        {'pin':  44,  'name':    'VIRT4'},
            'VIRT5':        {'pin':  45,  'name':    'VIRT5'},
        },

        5: {  # DL485P V.2.2
            'PC0':          {'pin':  23},
            'PC1':          {'pin':  24},
            'PC2':          {'pin':  25},
            'PC3':          {'pin':  26},
            'SDA':          {'pin':  27},
            'SCL':          {'pin':  28},
            'PD3':          {'pin':   1},
            'PE0':          {'pin':   3},
            'PD5':          {'pin':   9},
            'PE2':          {'pin':  19},
            'PE1':          {'pin':   6},
            'PD6':          {'pin':  10},
            'PB2':          {'pin':  14},
            'PB1':          {'pin':  13},
            'PB5':          {'pin':  17},            
            'PB4':          {'pin':  16},
            'PB3':          {'pin':  15},
            'VIN':          {'pin':  22, 'function': ['VIN']},
            'TEMP_ATMEGA':  {'pin':  37},
            'PCA9535':      {'pin':   0},
            'BME280':       {'pin':   0},
            'BME280B':      {'pin':   0},
            'AM2320':       {'pin':   0},
            'TSL2561':      {'pin':   0},
        },

        3: {  # DL485P OLD VERIONS 2.1
            'SDA':          {'pin':  27},
            'SCL':          {'pin':  28},
            'PD7':          {'pin':  11},
            'PD6':          {'pin':  10},
            'PB0':          {'pin':  12},
            'PB1':          {'pin':  13},
            'PD3':          {'pin':   1},
            'PD4':          {'pin':   2},
            'PB2':          {'pin':  14},
            'PC0':          {'pin':  23},
            'PC1':          {'pin':  24},
            'PC2':          {'pin':  25},
            'PC3':          {'pin':  26},
            'PB4':          {'pin':  16},
            'PB5':          {'pin':  17},
            'PB3':          {'pin':  15},
            'PE0':          {'pin':   3},
            'PE1':          {'pin':   6},
            'PE2':          {'pin':  19},
            'PE3':          {'pin':  22},
            'VIN':          {'pin':  22, 'function': ['VIN']},
            'TEMP_ATMEGA':  {'pin':  37},
            'PCA9535':      {'pin':   0},
            'BME280':       {'pin':   0},
            'BME280B':      {'pin':   0},
            'AM2320':       {'pin':   0},
            'TSL2561':      {'pin':   0},
        },

        4: {  # Board DL485R
            'IO1':          {'pin':  15,   'name':     'IO1',       'function': ['I', 'O', 'A']},
            'IO2':          {'pin':  16,  'name':      'IO2',       'function': ['I', 'O', 'A']},
            'IO3':          {'pin':  25,  'name':      'IO3',       'function': ['I', 'O', 'A']},
            'IO4':          {'pin':  26,  'name':      'IO4',       'function': ['I', 'O', 'A']},
            'OUT1':         {'pin':   2,  'name':      'RELE1',     'function': ['O']},
            'OUT2':         {'pin':   1,  'name':      'RELE2',     'function': ['O']},
            'VIN':          {'pin':  22,  'name':      'VIN',       'function': ['VIN']},
            'SDA':          {'pin':  27,  'name':      'SDA',       'function': ['SDA']},
            'SCL':          {'pin':  28,  'name':      'SCL',       'function': ['SCL']},
            'PCA9535':      {'pin':   0,  'name':      'PCA9535'},
            'BME280A':      {'pin':   0,  'name':      'BME280'},
            'BME280B':      {'pin':   0,  'name':      'BME280'},
            'TSL2561':      {'pin':   0,  'name':      'TSL2561'},
            'DS18B20':      {'pin':  35,  'name':      'DS18B20'},
            'TEMP_ATMEGA':  {'pin':  37,  'name' :     'TEMP_ATMEGA'},
            'VIRT1':        {'pin':  41,  'name' :     'VIRT1'},
            'VIRT2':        {'pin':  42,  'name' :     'VIRT2'},
            'VIRT3':        {'pin':  43,  'name' :     'VIRT3'},
            'VIRT4':        {'pin':  44,  'name' :     'VIRT4'},
            'VIRT5':        {'pin':  45,  'name' :     'VIRT5'},
        },
    }

    def __init__(self, config_file_name, logstate=0):
        self.buffricnlung = 1  # Lenght RX buffer
        self.buffricn = []  # Buffer RX trama
        self.appcrc = []  # Per calcolo CRC
        self.INITCRC = 0x55
        self.crcric = self.INITCRC
        self.crctrasm = 0x55
        self.BOARD_ADDRESS = 0
        self.MAX_BOARD_ADDRESS = 63
        self.config = {}  # Configuration dict
        self.status = {}  # Stauts of all IO Board
        self.buffricnapp = []  # Contiene i primi 7 byte per poi completarli con i bit residui (b7)
        self.mapiotype = {}  # Tipi di IO disponibili
        self.mapproc = {}  # Procedure associate agli ingressi verso le uscite
        self.poweroff_voltage_n = 0  # Time to make shutdown for unvervoltage limit
        self.poweroff_voltage_limit = 10
        self.getJsonConfig(config_file_name)
        self.BOARD_ADDRESS = int(self.config['GENERAL']['board_address'])  # Legge ID assegnato a Raspberry PI per accedere al Bus
        self.MAX_BOARD_ADDRESS = int(self.config.get('GENERAL')['max_board_address'])  # Legge ID assegnato a Raspberry PI per accedere al Bus
        self.dictBoardIo()  # Crea il DICT con i valori IO basato sul file di configurazione (solo boards attive)
        self.bus_baudrate = int(self.config['GENERAL']['bus_baudrate'])  # Legge la velocità del BUS
        self.bus_port = self.config['GENERAL']['bus_port']  # Legge la porta del BUS di Raspberry PI
        self.TIME_PRINT_LOG = 10  # intervallo di tempo in secondi per la stampa periodica del log a schermo
        self.nowtime = self.oldtime = 0
        self.RXtrama = []
        self.TXmsg = []  # Lista che contiene le liste da trasmettere sul BUS
        self.board_ready = {}
        self.BUFF_MSG_TX = {} # dizionario dei messaggi trasmessi indicizzato secondo indirizzo destinatario
        self.NLOOPTIMEOUT = 4  # numero di giri del loop dopo i quali si ritrasmettera il messaggio
        self.log = Log('log.txt', logstate)  # Instazia la classe Log
        self.Connection = self.ser(self.bus_port, self.bus_baudrate)  # Setup serial
        self.ping = self.ping()  # init variabile di appoggio con ping di questo nodo


    def getJsonConfig(self, config_file_name):
        """
        Create self.config from JSON configuration file
        """
        config = open(config_file_name, 'r')
        config = config.read()
        config = re.sub(r'#.*\n', '\n', config)
        config = re.sub(r'\\\n', '', config)
        config = re.sub(r'//.*\n', '\n', config)
        config = json.loads(config)
        self.config = config

    def dictBoardIo(self):
        """
        Crea la mappa dove saranno inseriti i valori dei vari di tutti gli IO presenti in self.config
        Crea inoltre il DICT self.mapiotype che permette di recuparare dati utili in breve tempo
        """
        for b in self.config:
            if 'BOARD' in b:
                idbus = int(b[5:])
                boardtype = int(self.config[b]['GENERAL']['boardtype'])
                name = self.config[b]['GENERAL']['name']
                self.status[idbus] = {}
                self.status[idbus]['boardtype'] = boardtype
                self.status[idbus]['name'] = name
                try:
                    self.status[idbus]['io'] = [0] * len(self.iomap[boardtype])
                    self.status[idbus]['boardtypename'] = self.config['TYPEB']["%s" %boardtype]
                except:
                    print("BOARD TYPE %s non esistente" %boardtype)
                    sys.exit()

                board_enable = 0
                for bb in self.config[b]:
                    if 'GENERAL' in bb:
                        # print("-------Board_id", idbus, self.config[b][bb])
                        board_enable = self.config[b][bb]['enable']  # Board enable
                        # pprint(board_enable)


                for bb in self.config[b]:
                    if not 'GENERAL' in bb:
                        io_logic = int(self.config[b][bb]['io_logic'])
                        io_type = 'other' if not 'io_type' in self.config[b][bb] else self.config[b][bb]['io_type']
                        # print("=============== board_id:%s, io_logic:%s, io_type:%s" %(b, io_logic, io_type))
                        device_name = '' if not 'device_name' in  self.config[b][bb] else self.config[b][bb]['device_name']

                        if not idbus in self.mapiotype: self.mapiotype[idbus] = {}

                        inverted = int(self.config[b][bb]['inverted']) if 'inverted' in self.config[b][bb] else 0
                        default_startup_value = 0  if not 'default_startup_value' in self.config[b][bb] else int(self.config[b][bb]['default_startup_value'])
                        # print("board_enable", board_enable)
                        self.mapiotype[idbus][io_logic] = {
                            'board_enable': board_enable,
                            'io_logic': io_logic,
                            'io_type': io_type,
                            'device_name': device_name,
                            'write_ee': [] if not 'write_ee' in self.config[b][bb] else self.config[b][bb]['write_ee'],
                            'Rvcc': 1 if not 'Rvcc' in self.config[b][bb] else int(self.config[b][bb]['Rvcc']),
                            'Rgnd': 10000 if not 'Rgnd' in self.config[b][bb] else int(self.config[b][bb]['Rgnd']),
                            'offset_altitude': 0 if not 'offset_altitude' in self.config[b][bb] else int(self.config[b][bb]['offset_altitude']),  # OFFSET altitudine
                            'offset_t': 0 if not 'offset_t' in self.config[b][bb] else int(self.config[b][bb]['offset_t']),  # OFFSET temperature
                            'offset_h': 0 if not 'offset_h' in self.config[b][bb] else int(self.config[b][bb]['offset_h']),  # OFFSET humidity
                            'offset_p': 0 if not 'offset_p' in self.config[b][bb] else int(self.config[b][bb]['offset_p']),  # OFFSET pression
                            'description': self.config[b][bb]['description'] if 'description' in self.config[b][bb] else 'NO description',
                            'direction': self.config[b][bb]['direction'] if 'direction' in self.config[b][bb] else 'other',
                            'dtype': self.config[b][bb]['dtype'] if 'dtype' in self.config[b][bb] else 'Switch',
                            'enable': int(self.config[b][bb]['enable']) if 'enable' in self.config[b][bb] else 0,
                            'filter': int(self.config[b][bb]['filter']) if 'filter' in self.config[b][bb] else 127,
                            'n_refresh_off': int(self.config[b][bb]['n_refresh_off']) if 'n_refresh_off' in self.config[b][bb] else 16000,
                            'n_refresh_on': int(self.config[b][bb]['n_refresh_on']) if 'n_refresh_on' in self.config[b][bb] else 16000,
                            'name': self.config[b][bb]['name'] if 'name' in self.config[b][bb] else 'NO Name',
                            'time_refresh': int(self.config[b][bb]['time_refresh']) if 'time_refresh' in self.config[b][bb] else 0,
                            'inverted': inverted,
                            'default_startup_value': default_startup_value,
                            'only_fronte_on': int(self.config[b][bb]['only_fronte_on']) if 'only_fronte_on' in self.config[b][bb] else 0,
                            'only_fronte_off': int(self.config[b][bb]['only_fronte_off']) if 'only_fronte_off' in self.config[b][bb] else 0,
                            'function': self.config[b][bb]['function'] if 'function' in self.config[b][bb] else 0,
                            'plc_function': self.config[b][bb]['plc_function'] if 'plc_function' in self.config[b][bb] else 'disable',
                            'plc_linked_board_id_io_logic': self.config[b][bb]['plc_linked_board_id_io_logic'] if 'plc_linked_board_id_io_logic' in self.config[b][bb] else [],
                            'default_startup_filter_value': int(self.config[b][bb]['default_startup_filter_value']) if 'default_startup_filter_value' in self.config[b][bb] else 0,
                            'kmul': self.config[b][bb]['kmul'] if 'kmul' in self.config[b][bb] else 1,
                            'kadd': self.config[b][bb]['kadd'] if 'kadd' in self.config[b][bb] else 0,
                        }

                        plc_linked_board_id_io_logic = self.config[b][bb]['plc_linked_board_id_io_logic'] if 'plc_linked_board_id_io_logic' in self.config[b][bb] else [],
                        linked_proc = self.config[b][bb]['linked_proc'] if 'linked_proc' in self.config[b][bb] else [],

                        if plc_linked_board_id_io_logic:
                            for x in plc_linked_board_id_io_logic[0]:
                                if not x in self.mapproc:
                                    self.mapproc[x] = {}
                                self.mapproc[x]["%s-%s" %(idbus, io_logic)] = {'linked_proc': linked_proc[0]}

    def make_inverted(self, board_id, io_logic, value):
        """
        Invert IO value. To use if not PLC function on board
        """
        if not board_id in self.mapiotype or not io_logic in self.mapiotype[board_id]:
            return 0
        inverted = self.mapiotype[board_id][io_logic]['inverted']
        if inverted:
            value = 1 - value & 1
            self.status[board_id]['io'][io_logic - 1] = value  # Valore corrente IO
        # print("value2", value)
        return value

    def calcCrcDS(self, b, crc):
        """
        Calc CRC of DS18xxx
        """
        a = 0xff00 | b
        # print("CRC: ", b, crc, end=" ")
        while 1:
            crc = ((((crc ^ a) & 1) * 280) ^ crc) // 2
            a = a // 2
            # print("==>", crc, end=" ")
            if (a <= 255):
                # print()
                return crc

    def ADC_value(self, VIN, Rvcc, Rgnd):
        """
        Dato il valore della tensione e le resistenze del partitore, ricavo la tensione in ingresso ADC del micro
        """
        try:
            value = VIN / (Rvcc + Rgnd) * Rgnd *930
            return int(value)
        except:
            print("ERROR ADC_value", VIN, Rvcc, Rgnd)
            return 0

    def voltageLimit(self, board_id, io_logic, value):
        """
        Funzione che sotto una certa tensione, Raspberry PI viene spento (batteria scarica)
        """
        poweroff_voltage = 0 if not 'poweroff_voltage' in self.config.get('GENERAL') else float(self.config.get('GENERAL')['poweroff_voltage'])  # Read if need shutdown below the  voltage limit
        if poweroff_voltage:
            poweroff_board_id = 0 if not 'poweroff_board_id' in self.config.get('GENERAL') else int(self.config.get('GENERAL')['poweroff_board_id'])  # Read board_id to for shutdown voltage limit
            poweroff_io_logic = 0 if not 'poweroff_io_logic' in self.config.get('GENERAL') else int(self.config.get('GENERAL')['poweroff_io_logic'])  # Read io_logic to for shutdown voltage limit
            # print("poweroff ===>>>> Voff:%s  Voltage:%s, B.ID:%s, IO:%s" %(poweroff_voltage, value, poweroff_board_id, poweroff_io_logic))
            # print("board_id:%s  io_logic:%s" %(board_id, io_logic))
            if board_id == poweroff_board_id and io_logic == poweroff_io_logic:
                if value < poweroff_voltage and value > 0:
                    self.poweroff_voltage_n += 1
                    print("************ Make SHUTDOWN OK ************* Count:%s LIMIT:%s" %(self.poweroff_voltage_n, self.poweroff_voltage_limit))
                    if self.poweroff_voltage_n  >= 10:
                        pass
                        self.shutdownRequest()
                else:
                    if self.poweroff_voltage_n > 0:
                        self.poweroff_voltage_n -= 1
                    print("************ Make SHUTDOWN NO ************* Count:%s LIMIT:%s" %(self.poweroff_voltage_n, self.poweroff_voltage_limit))


    def calculate(self, board_id, io_logic, value):
        """
        Ritorna il valore calcolato a seconda del tipo e del dispositivo connesso:
            Temperature:
                DS18B20         -> Temp
                BME280          -> Temp + Hum + Bar
                ATMEGA CHIP     -> Temp
                AM2320          -> Temp + Hum
                TSL2561         -> Light
            Voltage:
                Analog Input
            Digital:
                Digital input
            PowerMeter
        """

        # print("CALCULATE: board_id:%s, io_logic:%s, value:%s, io_type:%s, PLC_FUNCTION:%s" %(board_id, io_logic, value, self.mapiotype[board_id][io_logic]['io_type'], self.mapiotype[board_id][io_logic]['plc_function']))

        if board_id in self.mapiotype and io_logic in self.mapiotype[board_id]:
            kmul = self.mapiotype[board_id][io_logic]['kmul']
            kadd = self.mapiotype[board_id][io_logic]['kadd']           

            adjust = lambda value : (value * kmul) + kadd # Funzione che aggiusta il risultato

            type_io = self.mapiotype[board_id][io_logic]['io_type']
            
            plc_function = self.mapiotype[board_id][io_logic]['plc_function']
            # print(type_io, plc_function)
            
            
            if type_io == 'onewire':
                if self.mapiotype[board_id][io_logic]['device_name'] == 'DS18B20':
                    crc = 0
                    for x in value[0:8]:
                        crc = self.calcCrcDS(x, crc)
                    if crc == value[8]:
                        value = ((value[1] << 8) + value[0]) * 0.0625
                        # print(value)
                        (value * kmul) + kadd
                        return round(value + self.mapiotype[board_id][io_logic]['offset_t'], 1)
                    else:
                        print("=====>>>>> Errore CRC DS", ((value[1] << 8) + value[0]) * 0.0625)
                        return None

            elif type_io == 'digital' and plc_function == 'powermeter' :
                # print(plc_function, value)
                value = value[0] + (value[1] * 256)
                # return (value * kmul) + kadd
                return adjust(value)

            elif type_io == 'digital' and plc_function == 'time_meter' :
                # print(plc_function, value)

                return value[0] + (value[1] * 256)
                

            elif type_io == 'i2c':
                # print(self.mapiotype[board_id][io_logic]['io_type'], self.mapiotype[board_id][io_logic]['device_name'] )
                if self.mapiotype[board_id][io_logic]['device_name'] == 'BME280':
                    value = self.getBME280(value)
                    return value
                if self.mapiotype[board_id][io_logic]['device_name'] == 'AM2320':
                    # print ("VALUE=",value)
                    
                    hum = ((value[1] * 256 + value[2]) / 10.0) + self.mapiotype[board_id][io_logic]['offset_h']

                    temp = (((value[3]&0x7F) * 256 + value[4]) / 10.0) + self.mapiotype[board_id][io_logic]['offset_t']
                    if value[3] & 0x80 == 0x80: temp = -temp
                    # print("AM2320", hum, temp)
                    return [temp, hum]

                if self.mapiotype[board_id][io_logic]['device_name'] == 'TSL2561':
                    # print("TSL2561 Data:", value)
                    ch0 = value[0] + (value[1] * 256)
                    ch1 = value[2] + (value[3] * 256)
                    if ch0 > 0:
                        a = ch1 / ch0
                        if a <= 0.5:
                            lux = (0.0304 * ch0) - (0.062 * ch0 * (a ** 1.4))
                        elif a <= 0.61:
                            lux = (0.0224 * ch0) - (0.031 * ch1)
                        elif a <= 0.8:
                            lux = (0.0128 * ch0) - (0.0153 * ch1)
                        elif a <= 1.3:
                            lux = (0.00146 * ch0) - (0.001122 * ch1)
                        else:
                            lux = 0
                    else:
                        lux = 0
                    # print("LUX:%s, CH0:%s, CH1:%s, A:%s" %(lux, ch0, ch1, a) )
                    value = round(lux, 1)
                    # return (value * kmul) + kadd
                    return adjust(value)


            elif type_io == 'temp_atmega':
                value = (value[0] + (value[1] * 256)) - 270 + 25
                return round(value + self.mapiotype[board_id][io_logic]['offset_t'], 1)
                # return round(value, 1)

            elif type_io == 'analog' or self.mapiotype[board_id][io_logic]['io_type'] == 'virtual':
                Rvcc =  self.mapiotype[board_id][io_logic]['Rvcc']
                Rgnd =  self.mapiotype[board_id][io_logic]['Rgnd']
                # print(Rvcc, Rgnd, value)
                try:
                    # print("\t\t\t\t\t\t\t\t\t\t\t\tANALOG", value[0] + (value[1] * 256))
                    value = round((value[0] + (value[1] * 256)) * (Rvcc + Rgnd) / (Rgnd * 930), 1)
                except:
                    print("Analog Error: Value:", value)
                    return 0
                return value

            elif type_io == 'digital':
                # b0: dato filtrato
                # b1: dato istantaneo
                # b2: fronte OFF
                # b3: fronte ON
                # b4: fronte OFF da trasmettere
                # b5: fronte ON da trasmettere
                # value = value[0]
                # value_io = value & 1

                # if 'only_fronte_on' in self.mapiotype[board_id][io_logic] and self.mapiotype[board_id][io_logic]['only_fronte_on'] == 1:
                    # value_io ^= 1


                # fronte = ''
                # if value & 0b1000:  # Fronte ON
                    # fronte = '↑'
                # elif value & 0b100:  # Fronte OFF
                    # fronte = '↓'
                # print("==========>>>>>  VALORE IO:", board_id, io_logic, value_io)
                # print("IO Digital: Board_id:%s, io_logic:%s, fronti:%s, value:%s" %(board_id, io_logic, fronte, value))
                # pprint( self.status[board_id]['io'])
                # self.status[board_id]['io'][io_logic - 1] = "%s%s" % (value_io, fronte
                value = value[0]
                # value = self.inverted(board_id, io_logic, value)

                # self.status[board_id]['io'][io_logic - 1] = value
                return value
            else:
                print("calculate ERROR: Tipo dispositivo NON trovato:", board_id, io_logic)
                return value
        else:
            print("calculate ERROR: Board o IO_LOGICO non presenti sul file di configurazione. Comunica IO ignorato. board_id:%s, io_logic:%s" % (board_id,  io_logic))
            return 0

    def printStatus(self):
        """
        Show to screen the IO status
        """

        print("\n", "-" * 83, "STATUS IO", "-" * 83)
        print(" ID Name        BoardType  IO:", end='')
        for i in range(1, 31):  # estremo superiore viene escluso
            print("{:>4} ".format(i), end='')
        print()
        for b in self.status:
            print("{:>3} {:<11} {} {:>5}     ".format(b, self.status[b]['name'][:11], self.status[b]['boardtype'], self.status[b]['boardtypename']), end='')

            for i in self.status[b]['io']:
                
                print("{:>5}".format(str(i)), end='')
            print()
        print("-" * 83, "END STATUS", "-" * 83, "\n")


    def int2hex(self, msg):
        """
        Convert list data from INT to HEX
        """
        return ['{:02X}'.format(a) for a in msg]

    def ser(self, port='/dev/ttyAMA0', baudrate=9600):
        """
        Instance of serial
        """
        return arduinoserial.SerialPort(port, baudrate)

    def send_data_serial(self, Connection, databyte):
        Connection.write(bytes(databyte))  # invia alla seriale

    def calccrc(self, b, crc):
        """
        Calc CRC of trama
        """
        a = 0xff00 | b
        while 1:
            crc = ((((crc ^ a) & 1) * 280) ^ crc) // 2
            a = a // 2
            if (a <= 255):
                return crc

    def labinitric(self):
        """
        Reset variable when trama is received
        """
        self.crcric = self.INITCRC
        self.buffricnlung = 1
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

    crcdoppio = 1   # se 0 sistema vecchio con CRC e fine pacchetto insieme null'ultimo byte
                    # se 1 sistema nuovo con, oltre al sistema vecchio, viene trasmesso un ulteriore byte CRC calcolato passando come dato l'ultimo CRC negato
    lastfinepacc = False

    def readSerial(self, inSerial):
        """
        Calculate trama and return list with right values
        """
        app=inSerial
        # print("ByRicSer: ",hex(inSerial), chr(int(inSerial)))

#        if inSerial!=0x90: print("ByRicSer: ",hex(inSerial),chr(inSerial))
#        else: print("ByRicSer: ",hex(inSerial))
            
        if self.buffricnlung > 100:  # Errore 3
            print("ERR 3 Pacchetto troppo lungo")
            self.labinitric()
            return []

        if self.lastfinepacc == True:
            # print("Arrivato secondo CRC", hex(inSerial), end='')
            self.lastfinepacc = False
            auscrc = (inSerial & 0x0f) | ((inSerial & 0xE0)//2)
#            print(", Decodificato CRC:", hex(auscrc))
#            print("Calcolo CRC da:", hex(self.crcric))
            self.crcric = self.calccrc(self.crcric + 0xaa, self.crcric)  # aggiorna crc
#            print("CRC calcolato:", hex(self.crcric),", 7bit==>", hex(self.crcric & 0x7f))
            ric = self.buffricn
            if (auscrc ^ self.crcric) & 0x7f == 0:  # crc corretto e fine pacchetto veramente
#                print("Secondo crc OK")
                self.labinitric()
                return(ric)
            else:
                print("ERRORE secondo CRC, calcolato - Ricevuto", hex(self.crcric), hex(auscrc))
                self.labinitric()
                return []

        if (inSerial & 0x38) == 0x18 or (inSerial & 0x38) == 0x20:  # Fine pacchetto
            # print("---------", inSerial)
#            print("Ricevuto fine pacchetto",hex(inSerial))
            inSerial = (inSerial & 0x0f) | ((inSerial & 0xc0) // 4)
#            print("fine pacchetto decodificato:", hex(inSerial),", 6bit==>",hex(inSerial&0x3F), "confrontare con:", hex(self.crcric & 0x3F) )
#            print("confrontare con:            ", hex(self.crcric),", 6bit==>",hex(self.crcric & 0x3F), end="" )
            if (inSerial ^ self.crcric) & 0x3F == 0:  # crc corretto
#                print(" CRC OK",end="")
                # print(inSerial)
                
                appn=len(self.buffricn)+len(self.buffricnapp)                
                if appn>2:  # non è un ping
                    if self.buffricnapp:
#                        print("sistema ultimi residui")
                        self.seven2eight()  # sistema gli ultimi residui
                    ric = self.buffricn
                else:
                    ric=self.buffricnapp
                
                if len(self.buffricn) > 1:  # Non è un PING
                    # ric.append()
                    
                    if self.crcdoppio == 1:
#                        print("Aspetto secondo CRC")
                        self.lastfinepacc = True
                        return []
                    
                    self.labinitric()
                    return(ric)

                else: # è un PING
#                    print(" E' UN PING")
                    self.labinitric()
                    return(ric)

            else:
#                print(" CRC ERRATO")
                self.labinitric()
                return []

        elif inSerial == 0:  # Errore 1
            print("ERR: 1 Tre 0 ricevuti, byte=", hex(inSerial))
            self.labinitric()
            return []

        elif inSerial == 0x38:  # Errore 2
            print("ERR: 2 Tre 1 ricevuti, byte=", hex(inSerial))
            self.labinitric()
            return []

        else:  # carattere normale
            self.crcric = self.calccrc(inSerial, self.crcric)  # aggiorna crc
            self.buffricnapp.insert(self.buffricnlung - 1, ((inSerial & 0x0f) | ((inSerial & 0xE0)//2)))  # insersce carattere decodificato
            if len(self.buffricnapp)==8:  # E' arrivato il byte con i bit residui  
                # print("+++++++++++++++++", self.buffricn, self.buffricnapp)
                self.seven2eight()
            self.buffricnlung += 1
            # print("-----------------", self.buffricn, self.buffricnapp)
            return []

    def eight2seven(self, msg):
        """
        Convert 8 to 7 bytes with additional bytes.
        When transmit the trama to BUS
        """

        trama = []
        resto = 0
        n = 0
        for b in msg:
            resto <<= 1
            trama.append(b & 0x7f)
            resto |= b >> 7
            n += 1
            if n == 7:
                n = 0
                trama.append(resto)
                resto = 0
        if n > 0:
            trama.append(resto)
        return trama

    
    def encodeMsgCalcCrcTx(self, msg):
        """
        Codifica byte messaggio con bit sincronismo, e codice di fine trama piu crc finale
        """

        app = 0

        bytedatrasm = []
        self.crctrasm = self.INITCRC
        for txapp in msg:
            txapp1 = (txapp & 0x0f) | (((txapp & 0x78) ^ 8) * 2)
            bytedatrasm.append(txapp1)
            self.crctrasm = self.calccrc(txapp1, self.crctrasm)
        bytedatrasm.append((self.crctrasm & 0x0f) | (self.crctrasm & 8)*2 | (self.crctrasm & 0x38 ^ 8)*4)
        # Sistema per CRC doppio
        # print(msg)
        if self.crcdoppio == 1 and len(msg) > 2:
#            print("A**********", hex(self.crctrasm), hex(self.crctrasm + 0xaa))

            txapp1 = self.calccrc(self.crctrasm + 0xaa, self.crctrasm)
#            print("B**********", hex(txapp1&0X7F))
            # txapp = 0x35
            txapp1 = (txapp1 & 0x0f) | (((txapp1 & 0x78) ^ 8) * 2)
            
#            print("C**********", hex(txapp1))
            
            bytedatrasm.append(txapp1)
            # bytedatrasm.append(txapp1)
            # bytedatrasm.append(txapp1)
            # bytedatrasm.append(app)

#        print("-D---------", self.int2hex(bytedatrasm))
        return bytedatrasm

    def shutdownRequest(self):
        """
        Command poweroff Domoticz: example when battery is low
        """
        os.system("nohup sudo /home/pi/domocontrol/shutdown.sh -h now &")  # Poweroff Domoticz and then raspberry
        # os.system("nohup sudo shutdown -h now &")

    def boardReboot(self, board_id):
        """
        Command to board REBOOT (0 for all board in the BUS)
        """
        return [self.BOARD_ADDRESS, self.code['CR_REBOOT'], board_id] # Fa reboot scheda

    def clearIO_boardReboot(self, board_id):
        """
        Command to board REBOOT (0 for all board in the BUS)
        """
        return [self.BOARD_ADDRESS, self.code['CLEARIO_REBOOT'], board_id] # cancella prog io e fa reboot scheda

    def getTypeBoard(self, board_id):
        """
        Ritorna: Tipo Board, Versione board, Data software: Day, Month, Year, configurazione software interna
        """
        return [self.BOARD_ADDRESS, self.code['CR_GET_TIPO_BOARD'], board_id] # Get board type

    def setMaxBoardAddress(self, max_board_address):
        """
        Setta il numero massimo di boards presenti nella rete. Serve per velocizzare il loop
        """
        return [self.BOARD_ADDRESS, self.code['CR_WR_EE'], 0, 6, 0, max_board_address] # Max Board Address

    # def calcAddressLsMs7(self, address):
    #     LS = address & 127
    #     MS = address >> 7
    #     return LS, MS

    def calcAddressLsMs8(self, address):
        """
        scompone word in due byte
        """            
        LS = address & 255
        MS = address >> 8
        return LS, MS

    def readEEadd(self, board_id, address, nbyte):
        """
        Read bytes of EEPROM
        """
        LS, MS = self.calcAddressLsMs8(address)
        return [self.BOARD_ADDRESS, self.code['CR_RD_EE'], board_id, LS, MS, nbyte] # Read EE

    def readEEnIOoffset(self, board_id, io_logic, offset, nbyte):
        """
        Read EEPROM bytes + offset
        """
        address = (io_logic * 32) + offset
        return self.readEEadd(board_id, address, nbyte)

    def writeEEadd(self, board_id, address, data):
        """
        Write EEPROM bytes
        """
        LS, MS = self.calcAddressLsMs8(address)
        msg = [self.BOARD_ADDRESS, self.code['CR_WR_EE'], board_id, LS, MS] + data # Read EE
        return msg

    def writeEEnIOoffset(self, board_id, io_logic, offset, data):
        """
        Write EEPROM bytes
        """
        address = (io_logic * 32) + offset
        return self.writeEEadd(board_id, address, data)
        

    def readIO(self, board_id, io_logic):
        """
        Read IO status
        """
        data = [self.BOARD_ADDRESS, self.code['CR_RD_IN'], board_id, io_logic, 0]
        # print("ReadIO:", data)
        return data # Read EE

    def writeIO(self, board_id, io_logic, data, ms=0):
        """
        Write IO
        """
        # Su analogico è necessario inviare anche un MS byte per andare fino al valore 1023 (7 bit LS + 3 bit MS)
        data = [self.BOARD_ADDRESS, self.code['CR_WR_OUT'], board_id, io_logic, ] + data + [ms]
        return data # Read EE

    def writeOneWire(self, board_id, io_logic, byteopzioni, data=[]):
        """
        Write One Wire command
        """
        # Su analogico è necessario inviare anche un MS byte per andare fino al valore 1023 (7 bit LS + 3 bit MS)
        # Byteopzioni:
        # b0: reset iniziali
        # b1: 1 bit a 1 su OneWire
        # b2: scrive BIT a ZERO
        # b3: Occupa BUS

        data = [self.BOARD_ADDRESS, self.code['CR_WR_OUT'], board_id, io_logic, byteopzioni] + data
        return data # Read EE

    def readOneWire(self, board_id, io_logic, byteopzioni, data=[]):
        """
        Read OneWire data
        """
        # Su analogico è necessario inviare anche un MS byte per andare fino al valore 1023 (7 bit LS + 3 bit MS)
        # Byteopzioni:
        # b0: reset iniziali
        # b1: 1 bit a 1 su OneWire
        # b2: scrive BIT a ZERO
        # b3: Occupa BUS

        data = [self.BOARD_ADDRESS, self.code['CR_RD_IN'], board_id, io_logic, byteopzioni] + data
        return data # Read EE

    def writeI2C(self, board_id, io_logic, byteopzioni, data):
        """
        Write I2C command
        """
        # byteOpzioni comando scrittura:
        # bit0: start iniziale
        #    1: stop finale
        #    2: ritorno stato ultimo ACK
        #    3: termina trasmissione per ridare start senza stop
        #    4: manda start dopo ultimo trasmissione di ultimo byte
        #    5: reset I2c prima di iniziare

        # print(board_id, io_logic, byteopzioni, data)
        # data = self.get8to7(data)
        data = [self.BOARD_ADDRESS, self.code['CR_WR_OUT'], board_id, io_logic, byteopzioni] + data
        # print("WriteI2C:", data)
        return data

    def readI2C(self, board_id, io_logic, byteopzioni, data):
        """
        Read I2C byte
        """
        # byteOpzioni comando scrittura:
        # bit0: start iniziale
        #    1: stop finale
        #    2: ritorno stato ultimo ACK
        #    3: termina trasmissione per ridare start senza stop
        #    4: manda start dopo ultimo trasmissione di ultimo byte

        # byteOpzioni comando letture:
        # bit0: start iniziale
        #    1: stop finale
        #    2: ritorno stato ultimo ACK
        #    3:6 Numero byte da leggere

        # print(board_id, io_logic, byteopzioni, data)
        # data = self.get8to7(data)
        data = [self.BOARD_ADDRESS, self.code['CR_RD_IN'], board_id, io_logic, byteopzioni] + data
        # print("WriteI2C:", data)
        return data

    def initIO(self, board_id, io_logic):
        """
        Init IO of board (read configuration in EEPROM)
        """
        data = [self.BOARD_ADDRESS, self.code['CR_INIT_SINGOLO_IO'], board_id, io_logic]
        return data

    def ping(self):
        """
        Make Ping
        """
        data = [self.BOARD_ADDRESS]
        return data

    # Speed Baudate
    speed = {
        1: 1200,
        2: 2400,
        3: 4800,
        4: 9600, # Default
        5: 14400,
        6: 19200,
        7: 28800,
        8: 38400,
        9: 57600,
        0: 115200, 

        1200: 1,
        2400: 2,
        4800: 3,
        9600: 4,
        14400: 5,
        19200: 6,
        28800: 7,
        38400: 8,
        57600: 9,
        115200: 0,
    }

    def enableSerial(self, board_id, speed):
        """
        Enable serial from BUS. (function disabled)
        """
        # Abilita la seriale RS232
        # Byte4
        # b0: (1) Trasmissione su RS232 di cosa il nodo trasmette sul BUS
        # b1: (1) Trasmissione su RS232 di cosa il nodo riceve sul BUS
        # b2: (1) Trasmissione su RS232 dei PING
        data = [self.BOARD_ADDRESS, self.code['CR_WR_EE'], board_id, 4, 0, self.speed[speed] ]
        return data

    def setSerialBaudrate(self, board_id, baudrate):
        """
        Set baudrate of serial
        1: 1200
        2: 2400
        3: 4800
        4: 9600
        5:
        6:
        7:
        8:
        9:
        10:
        """
        data = [self.BOARD_ADDRESS, self.code['CR_WR_EE'], board_id, 3, 0, self.speed[baudrate]]
        return data

    def setBusBaudrate(self, board_id, baudrate):
        """
        Set baudrate of serial
        """
        data = [self.BOARD_ADDRESS, self.code['CR_WR_EE'], board_id, 2, 0, self.speed[baudrate]]
        return data

    def setPCA9535(self, board_id):
        """
        Procedura per scrittura PCA9535:
        Scrittura uscite:
        messageTx.append(b.readI2C(4, 1, 3, [0x4E, 6, 0x0, 0x0]))  # Comando di direzione IO come uscite
        messageTx.append(b.readI2C(4, 1, 3, [0x4E, 2, 0xff, 0xff]))  # Scrittura uscite

        Ricezione uscite:
        messageTx.append(b.writeI2C(4, 1, 3, [0x4E, 6, 0xff, 0xff]))  # Comando di direzione IO come ingresso
        messageTx.append(b.writeI2C(4, 1, 0b1001, [0x4e, 0]))
        messageTx.append(b.readI2C(4, 1, 3 | 0x10 , [0x4f]))

        Procedura per scrittura BME280:
        messageTx.append(b.writeI2C(4, 1, 3, [0xec, 0xf4, 0x83]))  # Campiona in continuazione
        messageTx.append(b.writeI2C(4, 1, 0b1001, [0xec, 0xf7]))  # Da quale indirizzo leggere i dati
        messageTx.append(b.readI2C(4, 1, 0b11001, [0xec | 1]))  # Lettura dei primi 3 byte pressione

        messageTx.append(b.writeI2C(4, 1, 0b1001, [0xec, 0xfa]))  # Da quale indirizzo leggere i dati
        messageTx.append(b.readI2C(4, 1, 0b11001, [0xec | 1]))  # Lettura dei primi 3 byte temperatura

        messageTx.append(b.writeI2C(4, 1, 0b1001, [0xec, 0xfd]))  # Da quale indirizzo leggere i dati
        messageTx.append(b.readI2C(4, 1, 0b10001, [0xec | 1]))  # Lettura dei primi 2 byte umidità

        """
        print("Return Configuration PCA9535")
        msg = [5, 3, 0x4e, 2, 0x0a, 0xa0]

    def getBME280(self, value):
        """
        From bytes to value Temp, Hum, Press of BME280
        """
        calib = [101, 109, 65, 103, 50, 0, 54, 146, 12, 214, 208, 11, 9, 32, 56, 255, 249, 255, 172, 38, 10, 216, 189, 16] + [75] + [90, 1, 0, 22, 4, 0, 30]

        dig_T1 = calib[1] * 256 + calib[0]
        dig_T2 = calib[3] * 256 + calib[2]
        if dig_T2 >= 0x8000: dig_T2 = dig_T2 - 65536
        dig_T3 = calib[5] * 256 + calib[4]
        if dig_T3 >= 0x8000: dig_T3 = dig_T3 - 65536

        # print("DIG_T:", dig_T1, dig_T2, dig_T3)

        dig_P1 = calib[7] * 256 + calib[6]
        dig_P2 = calib[9] * 256 + calib[8]
        if dig_P2 >= 0x8000: dig_P2 = dig_P2 - 65536
        dig_P3 = calib[11] * 256 + calib[10]
        if dig_P3 >= 0x8000: dig_P3 = dig_P3 - 65536
        dig_P4 = calib[13] * 256 + calib[12]
        if dig_P4 >= 0x8000: dig_P4 = dig_P4 - 65536
        dig_P5 = calib[15] * 256 + calib[14]
        if dig_P5 >= 0x8000: dig_P5 -= 65536
        dig_P6 = calib[17] * 256 + calib[16]
        if dig_P6 >= 0x8000: dig_P6 -= 65536
        dig_P7 = calib[19] * 256 + calib[18]
        if dig_P7 >= 0x8000: dig_P7 -= 65536
        dig_P8 = calib[21] * 256 + calib[20]
        if dig_P8 >= 0x8000: dig_P8 -= 65536
        dig_P9 = calib[23] * 256 + calib[22]
        if dig_P9 >= 0x8000: dig_P9 -= 65536

        # print("DIG_P:", dig_P1, dig_P2, dig_P3, dig_P4, dig_P5, dig_P6, dig_P7, dig_P8, dig_P9)

        dig_H1 = calib[24]
        dig_H2 = calib[26] * 256 + calib[25]
        if dig_H2 >= 0x8000: dig_H2 -= 65536
        dig_H3 = calib[27]
        dig_H4 = calib[28] * 16 | (calib[29] & 0xf0f)
        dig_H5 = calib[30] * 16 | ((calib[29] & 0xf0) >> 4)
        dig_H6 = calib[31]
        if dig_H6 & 0x80 > 0: dig_H6 -= 256

        # print("DIG_H:", dig_H1, dig_H2, dig_H3, dig_H4, dig_H5, dig_H6)

        # bmeValue = [84, 71, 0, 134, 153, 0, 125, 154]
        bmeValue = value

        pres_raw = (bmeValue[0] << 12) | (bmeValue[1] << 4) | (bmeValue[2] >> 4)
        temp_raw = (bmeValue[3] << 12) | (bmeValue[4] << 4) | (bmeValue[5] >> 4)
        hum_raw  = (bmeValue[6] << 8)  |  bmeValue[7]

        v1 = (temp_raw / 16384.0 - dig_T1 / 1024.0) * dig_T2
        v2 = (math.pow((temp_raw / 131072.0 - dig_T1 / 8192.0) , 2)) * dig_T3
        tfine = (v1 + v2)
        t = round(tfine / 5120.0, 2)

        var1 = tfine - 128000
        var2 = (var1 * var1 * dig_P6 / 131072.0 + var1 * dig_P5) + (dig_P4 * 262144.0)
        var1 = var1 * (dig_P3 * var1 / 1048576.0 + dig_P2) / 262144.0
        var1 = (1 + var1 / 131072 ) * dig_P1
        if var1 == 0: dpressure = 0
        else: dpressure = 1048576 - pres_raw
        dpressure = ((dpressure - var2 / 16384) * 6250) / var1
        var1 = dig_P9 * dpressure * dpressure / 2147483648
        var2 = dpressure * dig_P8 / 32768
        dpressure = dpressure + (var1 + var2 + dig_P7) / 16
        pressure = round(dpressure / 100, 1)

        hh=tfine-76800.0
        hh=(hum_raw - (dig_H4 * 64.0 + dig_H5 / 16384.0 * hh))*(dig_H2/65536.0*(1.0+dig_H6/67108864.0*hh*(1.0+dig_H3/67108864.0*hh)));
        hh *= (1.0 - dig_H1*hh/524288.0);
        hh = round(hh, 1)

        tot = [t, hh, pressure]
        # print("Termperatura BME280 ==>>", t, pressure, hh, tot)
        return tot

    def resetEE(self, board_id, io_logic):
        """
        Mette a 0 gli enable dei vari IO logici.
        Se io_logic=0, disabilita gli i dispositivi da 1 a 24
        """
        TXtrama = []
        if io_logic == 0:
            for x in range(1, 25):
                msg = self.writeEEnIOoffset(board_id, io_logic, 0, [0,0])
                TXtrama.append(msg)
                TXtrama.append(self.initIO(board_id, io_logic))

        else:
            msg = self.writeEEnIOoffset(board_id, io_logic, 0, [0, 0])
            # print(msg)
            TXtrama.append(msg)
            TXtrama.append(self.initIO(board_id, io_logic))
        TXtrama.append(self.boardReboot(board_id))
        return(TXtrama)

    def getConfiguration(self):
        """
        Make configuration to send to boards
        """
        msg = []
        for bb in self.config:
            print("BB", bb)
            if "BOARD" in bb:  # Seleziona le BOARD
                boards = self.config.get(bb)
                idbus = int(bb[5:])
                if boards['GENERAL']['enable']==0:
                    print("Configurazione boards: BOARD DISABILITATA: ", idbus)
                    continue
                
                msg.append(self.clearIO_boardReboot(idbus))
                for board in boards:
                    boardenable = int(boards.get('GENERAL')['enable'])
                    boardtype = int(boards.get('GENERAL')['boardtype'])
                    boardname = boards.get('GENERAL')['name']

                    if  not 'GENERAL' in board:
                        message_conf_app = []
                        io_logic = int(boards[board]['io_logic'])
                        write_ee = [] if not 'write_ee' in boards[board] else boards.get(board)['write_ee']  # write_ee
                        enable = 0 if not 'enable' in boards[board] else int(boards.get(board)['enable'])  # Enable
                        # print("IO ABILITATI %s: %s" %(enable, io_logic))
                        if not enable: continue 
                        
                        if io_logic >= 30:
                            print("Configurazione boards ERROR: io_logic non può essere superiore a 29. IO_logic=%s", io_logic)
                            continue

                        pin = 0 if not board in self.iomap[boardtype] else self.iomap[boardtype][board]['pin']
                        if pin:
                            byte0 = self.mapmicro.get(pin)['iomicro']
                        else:
                            byte0 = 0

                        eels, eems = self.calcAddressLsMs8(io_logic * 32)
                        byte1 = 1 if boards.get(board).get('direction') == 'output' else 0

                        io_type = boards.get(board).get('io_type')
                        device_name = boards.get(board).get('device_name')
                        # print("-----", io_type)
                        if not enable: io_type = 'disable' # Non fa configurazione se enable = 0
                        if io_type == 'analog' or io_type == 'temp_atmega':
                            byte1 |= 0b10
                        elif io_type == 'digital':
                            byte1 |= 0b00
                        elif io_type == 'i2c':
                            byte1 |= 0b1000
                            enable = 0 if not 'enable' in boards[board] else int(boards.get(board)['enable'])  # Enable
                            if enable == 0:
                                byte1 = 0
                        elif io_type == 'onewire' or io_type == 'onewire_test':
                            byte1 |= 0b00100
                        elif io_type == 'virtual':
                            byte1 |= 0b1100
                        elif io_type == 'disable':
                            byte1 |= 0b00000
                        else:
                            print("Configurazione boards: ERROR: io_type non riconosciuto. IO: %s" %board, io_type, bb)
                            continue

                        enable = 0 if not 'enable' in boards[board] else int(boards.get(board)['enable'])  # Enable
                        if enable == 0:
                            byte1 = 0
                        # print("Configurazione boards: boards:%s, io_logic:%s" %(boardname, io_logic))
                        byte1 |= 0x40 if int(boards.get(board)['enable']) == 1 else 0  # Settimo BIT

                        direction = boards.get(board).get('direction', 0)

                        if direction == 'input':
                            byte2 = 0 if not 'pullup' in boards.get(board) else int(boards.get(board)['pullup'])
                            byte3 = 0
                        elif direction == 'output':
                            default_startup_value = int(boards.get(board)['default_startup_value']) if 'default_startup_value' in boards[board] else 0
                            default_startup_value = default_startup_value
                            byte2, byte3 = self.calcAddressLsMs8(default_startup_value)
                        elif io_type == 'i2c' or io_type == 'onewire' or io_type == 'onewire_test':
                            byte2 = byte3 = 0
                        else:
                            byte2 = byte3 = 0
                            print("ERROR: DIRECTION su configurazione non riconosciuto. IO: %s" %board)
                            # continue



                        if io_type == 'analog' or io_type == 'digital':
                            byte4 = 0 if not 'n_refresh_on' in boards.get(board) else int(boards.get(board)['n_refresh_on'])  # Byte 4: rinfreschi rete sui fronti ON
                            byte4 |= 0 if not 'n_refresh_off' in boards.get(board) else int(boards.get(board)['n_refresh_off']) << 3  # Byte 4: rinfreschi rete sui fronti OFF
                        else:
                            byte4 = 0

                        inverted = 0 if 'inverted' not in boards.get(board) else int(boards.get(board)['inverted'])
                        if inverted:  # Invert OUTPUT. Se inverted, lo stato ON in uscita di un rele si ha con lo stato zero.
                            byte4 |= 128
                        # byte5 = int(boards.get(board)['time_refresh']) & 255  # Byte 5: rinfresco periodico ls in decimi di secondo
                        # byte6 = int(boards.get(board)['time_refresh']) >> 8  # Byte 6: rinfresco periodico ms (14 bit = 16383) (0=sempre, 16383=mai)
                        byte5, byte6 = self.calcAddressLsMs8(int(boards.get(board)['time_refresh']))# Byte 5: rinfresco periodico ls in decimi di secondo, Byte 6: rinfresco periodico ms (14 bit = 16383) (0=sempre, 16383=mai)
                        # print("RINFRESCHI", byte5, byte6)

                        if io_type == 'analog' or io_type == 'digital':
                            byte7 = 0 if not 'filter' in boards.get(board) else int(boards.get(board)['filter'])
                        else:
                            byte7 = 0

                        message_conf_app.append(self.BOARD_ADDRESS)  # Mio indirizzo IDBUS
                        message_conf_app.append(self.code['CR_WR_EE'])  # Comando scrittura EEPROM, 4 per leggere
                        message_conf_app.append(idbus)  # IDBUS Board destinazione
                        message_conf_app.append(eels)  # Indirizzo scrittura EE ls
                        message_conf_app.append(eems)  # Indirizzo scrittura EE ms
                        message_conf_app.append(byte0)  # Port fisico
                        message_conf_app.append(byte1)  # Definizione input / output
                        message_conf_app.append(byte2)  # Valore default LS
                        message_conf_app.append(byte3)  # Valore default MS
                        message_conf_app.append(byte4)  # rinfreschi rete sui fronti ON / OFF
                        message_conf_app.append(byte5)  # Byte 5: rinfresco periodico ls
                        message_conf_app.append(byte6)  # Byte 6: rinfresco periodico ms
                        message_conf_app.append(byte7)  # Byte 7:  Filtro

                       # print("TRAMA CONFIGURAZIONE:             ", message_conf_app)
                    
                        msg.append(message_conf_app)
                        # msg.append(self.initIO(idbus, io_logic))  # iNIt io

                        # Funzioni PLC:
                        # 0 DISABLE -> se non si usa il PLC
                        # 1 EQUAL -> funzione "="
                        # 2 AND
                        # 3 OR
                        # 4 XOR
                        # 5 ODD -> Funzione DISPARI
                        # 6 TOGGLE_ON -> su fronte ON
                        # 7 TOGGLE_OFF -> su fronte OFF
                        # 8 TOGGLE_ON_OFF su fronte ON OFF
                        # 9 TIMER
                        # 30 POWER_ON => Uscita per comandare il rele di reset alimentazione RAPBERRY quando non risponde sulla seriale per un certo tempo.
                        # OR 128 = uscita negata

                        # Ogni uscita con funzione associata ad ingressi digitali puo' avere al massimo 8 ingressi
                        # Ogni uscita con funzione associata ad ingressi analogici puo' avere al massimo 2 ingressi

                        """
                        OFFSET 8: codice funzione PLC
                        """
                        plc_function =  {
                            'disable': 0,
                            'equal': 1,
                            'nequal': 1 | 128,
                            'and': 2,
                            'nand': 2 | 128,
                            'or': 3,
                            'nor': 3 | 128,
                            'xor': 4,
                            'nxor': 4 | 128,
                            'odd': 5,
                            'even': 5 | 128,
                            'toggle_on': 6,
                            'toggle_off': 7,
                            'toggle_on_off': 8,
                            'timer': 9,
                            'ntimer': 9 | 128,
                            'autostart_timer': 10,
                            'nautostart_timer': 10 | 128,
                            'test_nio_>=_n': 11,
                            'ntest_nio_>=_n': 11 | 128,
                            'test_nio_into_n': 12,
                            'ntest_nio_into_n': 12 | 128,
                            'test_schmitt_nio': 13,
                            'ntest_schmitt_nio': 13 | 128,
                            'or_transition_on': 15,
                            'nor_transition_on': 15 | 128,
                            'or_transition_on_all': 16,
                            'nor_transition_on_all': 16 | 128,
                            'analog_in_=_n': 20,
                            'nanalog_in_=_n': 20 | 128,
                            'analog_in_>_n': 21,
                            'nanalog_in_>_n': 21 | 128,
                            'analog_in_>=_n': 22,
                            'nanalog_in_>=_n': 22 | 128,
                            'analog_in_schmitt_n': 23,
                            'nanalog_in_schmitt_n': 23 | 128,
                            'if_analog_in1_=_analog_in2': 24,
                            'nif_analog_in1_=_analog_in2': 24 | 128,
                            'if_analog_in1_>_analog_in2': 25,
                            'nif_analog_in1_>_analog_in2': 25 | 128,
                            'if_analog_in1_>=_analog_in2': 26,
                            'nif_analog_in1_>=_analog_in2': 26 | 128,
                            'if_analog_in1_-_analog_in2_schmitt_value': 27,
                            'nif_analog_in1_-_analog_in2_schmitt_value': 27 | 128,
                            'last_change': 28,
                            'nlast_change': 28 | 128,
                            'last_change_all': 29,
                            'nlast_change_all': 29 | 128,
                            'power_on': 30, # Funzione che gestische l'alimentazione raspberry
                            'counter_up': 32,
                            'counter_dw': 33,
                            'counter_up_dw': 34,
                            'time_meter': 35,
                            'powermeter': 36,
                            'analog_in_+_n': 40,
                            'analog_in_-_n': 41,
                            'analog_in_*_n': 42,
                            'analog_in_/_n': 43,
                            'analog_in_%_n': 44,
                            'analog_in_min_n': 45,
                            'analog_in_max_n': 46,
                            'analog_in1_+_analog_in2': 50,
                            'analog_in1_-_analog_in2': 51,
                            'analog_in1_*_analog_in2': 52,
                            'analog_in1_/_analog_in2': 53,
                            'analog_in1_%_analog_in2': 54,
                            'analog_in1_min_analog_in2': 55,
                            'analog_in1_max_analog_in2': 56,
                            'sampletrigger': 60,
                        }

                        # pprint(boards.get(board))
                        sbyte8 = 'disable' if not 'plc_function' in boards.get(board) or boards.get(board)['plc_function'] == 'disable' else boards.get(board)['plc_function']
                        # print("PLC_FUNCTION:************************", plc_function[byte8], byte8)

                        if sbyte8 == "disable" or not enable:
                            # print("PLC DISABILITATO", io_logic, plc_function[sbyte8])
                            message_conf_app.append(0)

                        else:  # byte8 != "disable":
                            # if inverted:
                                # plc_function[byte8] ^= 0x80
                            plc_params = 0 if not 'plc_params' in boards.get(board) else boards.get(board)['plc_params']
                            plc = []

                            message_conf_app.append(plc_function[sbyte8])
                            list_plc_linked_board_id_io_logic = []
                            if sbyte8 == 'power_on':
                                # print("plc_params", plc_params, float(plc_params[3]), int(plc_params[4]), int(plc_params[5]))
                                value_dac_in = self.ADC_value(float(plc_params[3]), int(plc_params[4]), int(plc_params[5]))
#                                plc.extend((int(plc_params[0]), int(plc_params[1]) & 255, int(plc_params[1]) >> 8, int(plc_params[2]) & 255, int(plc_params[2]) >> 8, value_dac_in & 255, value_dac_in >> 8 ))
                                plc += [int(plc_params[0])] + list(self.calcAddressLsMs8(int(plc_params[1]))) + list(self.calcAddressLsMs8(int(plc_params[2]))) + list(self.calcAddressLsMs8(value_dac_in))
                                # print("POWER_ON data:", byte8, value_dac_in, plc)

                            else:  # Funzione PLC
                                plc_xor_input = 0
                                plc_linked_board_id_io_logic = [] if not 'plc_linked_board_id_io_logic' in boards.get(board) else boards.get(board)['plc_linked_board_id_io_logic']
                                if plc_linked_board_id_io_logic:
                                    
                                    for plc_bio in plc_linked_board_id_io_logic:
                                        plc_bio = plc_bio.split("-")      # esempi: 5-8 !5-8  !15-8 *-8  !*-8   /*-8
                                        
                                        if plc_bio[0][0] == '!':  # sistema la negazione degli ingressi
                                            plc_bio[0] = plc_bio[0][1:]
                                            plc_xor_input = plc_xor_input * 2 + 1
                                        else:
                                            plc_xor_input = plc_xor_input * 2
                                        
                                        if '*' in plc_bio[0]:  # sistema asterisco con stesso id-board eliminando i casi 1* *7
                                           plc_bio[0] = idbus 
                                            
                                        list_plc_linked_board_id_io_logic.append(int(plc_bio[0]))
                                        list_plc_linked_board_id_io_logic.append(int(plc_bio[1]))
                                else:
                                    print("BOARD_ID and IO_LOGIC not defined on CONFIGURATION File")

                                plc_xor_input_old = 0 if not 'plc_xor_input' in boards.get(board) else int(boards.get(board)['plc_xor_input'])
                                if plc_xor_input_old:
                                    print("""NON USARE la Funzione: plc_xor_input. Per negare gli ingressi, mettere il carattere ! prima dell'board_id. 
                                    Es:  "plc_linked_board_id_io_logic": ["!18-3", "17-3"]""")
                                    sys.exit()
                                
                                plc.append(plc_xor_input)  # OFFSET 31: BYTE con NEGAZIONE ingressi. Mettere davanti a plc_linked_board_id_io_logic il carattere ! per negare gli ingresso

                                plc_preset_input = 0 if not 'plc_preset_input' in boards.get(board) else int(boards.get(board)['plc_preset_input'])
                                plc.append(plc_preset_input)  # OFFSET 30: BYTE PRESET valore default prima che arrivino i dati dalla rete

                                
                                plc.append(len(plc_linked_board_id_io_logic))  # OFFSET 29: Numero ingressi per la funzione PLC
                                
                                # print("list_plc_linked_board_id_io_logic", list_plc_linked_board_id_io_logic)
                                plc += list_plc_linked_board_id_io_logic
                                
                                # if plc_linked_board_id_io_logic:
                                #     for plc_bio in plc_linked_board_id_io_logic:
                                #         plc_bio = plc_bio.split("-")
                                #         plc.append(int(plc_bio[0]))  # OFFSET 28: BOARD_ID
                                #         plc.append(int(plc_bio[1]))  # OFFSET 27: IO_LOGICO
                                # else:
                                #     print("BOARD_ID and IO_LOGIC not defined on CONFIGURATION File")
                                
                                print("Funzione PLC:", sbyte8)
                                if sbyte8 in ["timer", "ntimer", "autostart_timer", "nautostart_timer"]:
                                    # Se timer, dopo elenco di BOARD_ID e IO_LOGIC, seguono questi parametri:
                                    # Modo TIMER:   b1:b0
                                    #                       0:0 innesca su fronte ON e su fronte OFF (se b2==1 => b0=stato uscita)
                                    #                       0:1 innesca su fronte ON (se b2==1 => Con che valore partire)
                                    #                       1:0 spegne su fronte OFF
                                    #                       1:1 innesca su fronte ON e spegne su fronte OFF
                                    #               b3:b2
                                    #                       0:0 Non usato
                                    #                       0:1 Uscita ferma con ingresso a 1 (b0 indica lo stato di uscita ferma e b1 indica lo stato di partenza per l'uscita)
                                    #                       1:0 sospende conteggio con ingresso a 1
                                    #                       1:1 partenza con stato off per inneschi normali
                                    #               b5:b4
                                    #                       0:0 esclusi inneschi con timer innescato
                                    #                       0:1 se arriva innesco, reinit tempo timer
                                    #                       1:0 se arriva innesco, somma tempo timer al tempo residuoi
                                    #                       1:1 se arriva innesco, cambia stato timer
                                    #               b6 e b7: 0 0 centesimi di secondo
                                    #               b6 e b7: 1 0 decimi di secondo
                                    #               b6 e b7: 0 1 secondi
                                    #               b6 e b7: 1 1 2.5 secondi
                                    # Byte: numero massimo di commutazioni. 0 = infinito
                                    # Byte: Tempo ON LS
                                    # Byte: Tempo ON MS
                                    # Byte: Tempo OFF LS
                                    # Byte: Tempo OFF MS

                                    plc_mode_timer = 0 if not 'plc_mode_timer' in boards.get(board) else int(boards.get(board)['plc_mode_timer'])

                                    plc_time_unit = 0.01 if not 'plc_time_unit' in boards.get(board) else boards.get(board)['plc_time_unit']
                                    # Unità di tempo
                                    plc_time_unit_app = 0
                                    if plc_time_unit == 1:
                                        plc_time_unit_app = 0x80
                                    elif plc_time_unit == 0.1:
                                        plc_time_unit_app = 0x40
                                    elif plc_time_unit == 0.01:  # Centesimi
                                        plc_time_unit_app = 0
                                    elif plc_time_unit == 2.5:
                                        plc_time_unit_app = 0xC0
                                    
                                    plc.append((plc_mode_timer & 0x3F) | plc_time_unit_app)

                                    plc_timer_n_transitions = 0 if not 'plc_timer_n_transitions' in boards.get(board) else int(boards.get(board)['plc_timer_n_transitions'])
                                    if plc_timer_n_transitions > 255:
                                        print("ERRORE CONFIGURATION: plc_timer_n_transitions 0...255")
                                        sys.exit()
                                    plc.append(plc_timer_n_transitions)

                                    plc_time_on = 0 if not 'plc_time_on' in boards.get(board) else int(boards.get(board)['plc_time_on'])
                                    # plc.append(plc_time_on & 255)
                                    # plc.append(plc_time_on >> 8)
                                    plc += list(self.calcAddressLsMs8(plc_time_on))

                                    plc_time_off = 0 if not 'plc_time_off' in boards.get(board) else int(boards.get(board)['plc_time_off'])
                                    # plc.append(plc_time_off & 255)
                                    # plc.append(plc_time_off >> 8)
                                    plc += list(self.calcAddressLsMs8(plc_time_off))

                                elif sbyte8 in ["equal", "nequal"]:

                                    plc_time_unit = 0.01 if not 'plc_time_unit' in boards.get(board) else boards.get(board)['plc_time_unit']

                                    # Unità di tempo
                                    if plc_time_unit == 1:
                                        plc.append(0x80)
                                    elif plc_time_unit == 0.1:
                                        plc.append(0x40)
                                    elif plc_time_unit == 0.01:  # Centesimi
                                        plc.append(0)
                                    elif plc_time_unit == 2.5:
                                        plc.append(0xC0)

                                    plc.append(0) # Numero massimo di coomutazioni (ignorato)

                                    plc_delay_on_off = 0 if not 'plc_delay_on_off' in boards.get(board) else int(boards.get(board)['plc_delay_on_off'])
                                    # plc.append(plc_delay_on_off & 0xff)
                                    # plc.append(plc_delay_on_off >> 8)
                                    plc += list(self.calcAddressLsMs8(plc_delay_on_off))

                                    plc_delay_off_on = 0 if not 'plc_delay_off_on' in boards.get(board) else int(boards.get(board)['plc_delay_off_on'])
                                    # plc.append(plc_delay_off_on & 0xff)
                                    # plc.append(plc_delay_off_on >> 8)
                                    plc += list(self.calcAddressLsMs8(plc_delay_off_on))

                                elif sbyte8 in ['test_nio_>_n', 'ntest_nio_>_n', 'test_nio_into_n', 'ntest_nio_into_n', 'test_schmitt_nio', 'ntest_schmitt_nio']:
                                    plc_params_val = int(plc_params)
                                    plc.append(plc_params_val)

                                elif sbyte8 in ['analog_in_=_n', 'nanalog_in_=_n', 'analog_in_>_n', 'nanalog_in_>_n', 'analog_in_>=_n', 'nanalog_in_>=_n']:
                                    plc_params_val = int(plc_params)
                                    # plc.append(plc_params_val & 255)
                                    # plc.append(plc_params_val >> 8)
                                    plc += list(self.calcAddressLsMs8(plc_params_val))

                                elif sbyte8 in ['analog_in_schmitt_n','nanalog_in_schmitt_n']:
                                    plc_params_val = list(plc_params)
                                    # plc.append(plc_params_val[0] & 255)
                                    # plc.append(plc_params_val[0] >> 8)
                                    plc += list(self.calcAddressLsMs8(plc_params_val[0]))
                                    # plc.append(plc_params_val[1] & 255)
                                    # plc.append(plc_params_val[1] >> 8)
                                    plc += list(self.calcAddressLsMs8(plc_params_val[1]))

                                elif sbyte8 in ['if_analog_in1_=_analog_in2', 'nif_analog_in1_=_analog_in2', 'if_analog_in1_>_analog_in2', 'nif_analog_in1_>_analog_in2', 'if_analog_in1_>=_analog_in2', 'nif_analog_in1_>=_analog_in2']:
                                    pass

                                elif sbyte8 in ['if_analog_in1_-_analog_in2_schmitt_value','nif_analog_in1_-_analog_in2_schmitt_value']:
                                    plc_params_val = list(plc_params)
                                    # plc.append(plc_params_val[0] & 255)
                                    # plc.append(plc_params_val[0] >> 8)
                                    plc += list(self.calcAddressLsMs8(plc_params_val[0]))
                                    # plc.append(plc_params_val[1] & 255)
                                    # plc.append(plc_params_val[1] >> 8)
                                    plc += list(self.calcAddressLsMs8(plc_params_val[1]))

                                elif sbyte8 == 'last_change':
                                    pass

                                elif sbyte8 == 'last_change_all':
                                    pass

                                elif sbyte8 in ['analog_in_+_n', 'analog_in_-_n', 'analog_in_*_n', 'analog_in_/_n', 'analog_in_%_n', 'analog_in_min_n', 'analog_in_max_n']:

                                    plc_params_val = int(plc_params)
                                    # plc.append(plc_params_val & 255)
                                    # plc.append(plc_params_val >> 8)
                                    plc += list(self.calcAddressLsMs8(plc_params_val))

                                elif sbyte8 in ['analog_in1_+_analog_in2', 'analog_in1_-_analog_in2', 'analog_in1_*_analog_in2', 'analog_in1_/_analog_in2', \
                                                'analog_in1_/_analog_in2', 'analog_in1_%_analog_in2', 'analog_in1_min_analog_in2', 'analog_in1_max_analog_in2']:
                                    pass

                                elif sbyte8 in ['counter_up', 'counter_dw']:
                                    counter_mode = 0 if not 'counter_mode' in boards.get(board) else int(boards.get(board)['counter_mode'])
                                    plc.append(counter_mode)
                                    counter_filter = 0 if not 'counter_filter' in boards.get(board) else int(boards.get(board)['counter_filter'])
                                    plc.append(counter_filter)
                                    counter_timeout = 0 if not 'counter_timeout' in boards.get(board) else int(boards.get(board)['counter_timeout'])
                                    # plc.append(counter_timeout & 255)
                                    # plc.append(counter_timeout >> 8)
                                    plc += list(self.calcAddressLsMs8(counter_timeout))

                                elif sbyte8 == 'time_meter':
                                    counter_mode = 0 if not 'counter_mode' in boards.get(board) else int(boards.get(board)['counter_mode'])
                                    plc.append(counter_mode)
                                    counter_filter = 0 if not 'counter_filter' in boards.get(board) else int(boards.get(board)['counter_filter'])
                                    plc.append(counter_filter)
                                    counter_timeout = 0 if not 'counter_timeout' in boards.get(board) else int(boards.get(board)['counter_timeout'])
                                    # plc.append(counter_timeout & 255)
                                    # plc.append(counter_timeout >> 8)
                                    plc += list(self.calcAddressLsMs8(counter_timeout))

                                elif sbyte8 == 'powermeter':
                                    counter_mode = 0 if not 'counter_mode' in boards.get(board) else int(boards.get(board)['counter_mode'])
                                    plc.append(counter_mode)
                                    counter_filter = 0 if not 'counter_filter' in boards.get(board) else int(boards.get(board)['counter_filter'])
                                    plc.append(counter_filter)
                                    counter_timeout = 0 if not 'counter_timeout' in boards.get(board) else int(boards.get(board)['counter_timeout'])
                                    # plc.append(counter_timeout & 255)
                                    # plc.append(counter_timeout >> 8)
                                    plc += list(self.calcAddressLsMs8(counter_timeout))
                                    counter_min_period_time = 0 if not 'counter_min_period_time' in boards.get(board) else int(boards.get(board)['counter_min_period_time'])
                                    plc.append(counter_min_period_time)
                                    powermeter_k = 0 if not 'powermeter_k' in boards.get(board) else int(boards.get(board)['powermeter_k'])
                                    # plc.append(powermeter_k & 255)
                                    # plc.append(powermeter_k >> 8)
                                    #plc += [powermeter_k & 255, powermeter_k >> 8]
                                    plc += list(self.calcAddressLsMs8(powermeter_k))

                                elif sbyte8 == 'or' or sbyte8 == 'odd' or sbyte8 == 'even' or sbyte8 == 'toggle_off' or sbyte8 == 'toggle_on' or sbyte8 == 'toggle_on_off'  :
                                    pass


                                else:
                                    log.write('FUNZIONE PLC NON TROVATA: %s' %sbyte8)    
                                    sys.exit()

                            plclen = len(plc)
                            print("CONFIGURAZIONE PLC =======>>>>>: ", plc)
                            plc.reverse()

                            plc_EE_start = (io_logic * 32) + 32 - plclen
                            plc_data = self.writeEEadd(idbus, plc_EE_start, plc)
                            # print("PLC_DATA:", plc_data)
                            msg.append(plc_data)

                        # Configurazione relativa ai sensori I2C e OneWire

                        if io_type == 'i2c':
                            if device_name == 'PCA9535':
                                print("==>> Inserisce trama di confgurazione I2C per PCA9535")
                                # msg.append(self.writeEE(idbus, eels + 10, eems, [5, 3, 0x4e, 2, 0x0a, 0xa0]))
                                # msg.append(self.writeEE(idbus, eels + 16, eems, [5, 3, 0x4e, 6, 0, 0])) # Impostare direzione OUT (inizializzazione)
                                # msg.append(self.writeEE(idbus, eels + 22, eems, [5, 3, 0x4e, 2, 0xa0, 0x0a]))
                            elif device_name == 'BME280':
                                if self.EEPROM_LANGUAGE == 0:
                                    print("EEPROM_LANGUAGE OLD")
                                    msg.append(self.writeEEnIOoffset(idbus, io_logic, 10, [3 | self.i2c_const['CONCATENA'], 1 | 8, 0xec, 0xf7]))  # 3|128: 128 per concatenare con prg. successivo), 32 reset +
                                    msg.append(self.writeEEnIOoffset(idbus, io_logic, 14, [2 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 3 | 64, 0xec | 1]))  # 2|64: lettura I2C. 3+64: 64 byte da leggere

                                    msg.append(self.writeEEnIOoffset(idbus, io_logic, 17, [4 | self.i2c_const['CONCATENA'], 3 | 32, 0xec, 0xf2, 0x03]))  # Inizializzazione BME e Oversampling umidità
                                    msg.append(self.writeEEnIOoffset(idbus, io_logic, 22, [4 | self.i2c_const['NON_CONCATENA'], 3, 0xec, 0xf4, 0x8f]))  # Inizializzazione BME temperatura + pressione  (Oversampling)
                                elif self.EEPROM_LANGUAGE == 1:
                                    print("EEPROM_LANGUAGE NEW")
                                    msg.append(self.writeEEnIOoffset(idbus, io_logic, 10, [3, 1 | 8, 0xec, 0xf7]))  # 3|128: 128 per concatenare con prg. successivo), 32 reset +
                                    msg.append(self.writeEEnIOoffset(idbus, io_logic, 14, [2 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 3 | 64, 0xec | 1, 0]))  # 2|64: lettura I2C. 3+64: 64 byte da leggere

                                    msg.append(self.writeEEnIOoffset(idbus, io_logic, 18, [4, 3 | 32, 0xec, 0xf2, 0x03]))  # Inizializzazione BME e Oversampling umidità
                                    msg.append(self.writeEEnIOoffset(idbus, io_logic, 23, [4, 3, 0xec, 0xf4, 0x8f, 0]))  # Inizializzazione BME temperatura + pressione  (Oversampling)


                            elif device_name == 'AM2320':
                                print("CONFIGURAZIONE AM2320")
                                if self.EEPROM_LANGUAGE == 0:  # vecchio linguaggio
                                    i2cconf = []
                                    i2cconf.append(self.writeEEnIOoffset(idbus, io_logic, 10, [2 | self.i2c_const['CONCATENA'] | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 3, 0xb8]))  # 3|128: 128 per concatenare con prg. successivo), 32 reset +
                                    i2cconf.append(self.writeEEnIOoffset(idbus, io_logic, 13, [5 | self.i2c_const['CONCATENA'] | self.i2c_const['BYTE_OPZIONI_SCRITTURA'],  3, 0xb8, 0x03, 0x00, 0x04]))
                                    i2cconf.append(self.writeEEnIOoffset(idbus, io_logic, 19, [3 | self.i2c_const['FLAG_PAUSA'] | self.i2c_const['BYTE_OPZIONI_LETTURA'], 100, 3 | 64, 0xb9, 0 ]))
                                elif self.EEPROM_LANGUAGE == 1:  # nuovo linguaggio
                                    i2cconf = []
                                    i2cconf.append(self.writeEEnIOoffset(idbus, io_logic, 10, [2 | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 3, 0xb8]))  #3=start+stop, 0xb8=indirizzo dispositivo*2 serve per risveglio dispositivo 
                                    i2cconf.append(self.writeEEnIOoffset(idbus, io_logic, 13, [5 | self.i2c_const['BYTE_OPZIONI_SCRITTURA'],  3, 0xb8, 0x03, 0x00, 0x04]))  #3=start+stop, 0xb8=indirizzo dispositivo*2,03=?, 00=indirizzo primo byte da leggere, 4=numero byte da leggere 
                                    i2cconf.append(self.writeEEnIOoffset(idbus, io_logic, 19, [1 | self.i2c_const['FLAG_PAUSA'] , 100 ])) #100=decine di microsecondi di pausa, totale 1 ms
                                    i2cconf.append(self.writeEEnIOoffset(idbus, io_logic, 19, [3 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 3|40 , 0xb9, 0, 0, 0 ])) #3=start+stop|40=numero byte da leggere*8=5*8, 5 perchè servono 4 byte e inizia col numero di byte (4)+b,b,b,b, 0xb9=indirizzo dispositivo+flag lettura, 0=nessun programma seguente, 0=nessun programma setup
                                msg.extend(i2cconf)

                            elif device_name == 'TSL2561':
                                print("CONFIGURAZIONE TSL2561")
                                if self.EEPROM_LANGUAGE == 0:
                                    i2cconf = []
                                    i2cconf.append(self.writeEEnIOoffset(idbus, io_logic, 10, [3 | self.i2c_const['CONCATENA'] | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 1, 0x72, 0xAC]))
                                    i2cconf.append(self.writeEEnIOoffset(idbus, io_logic, 14, [2 | self.i2c_const['CONCATENA'] | self.i2c_const['BYTE_OPZIONI_LETTURA'], 3 | 32, 0x72 | 1  ]))

                                    i2cconf.append(self.writeEEnIOoffset(idbus, io_logic, 17, [3 | self.i2c_const['CONCATENA'] | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 1, 0x72, 0x80]))
                                    i2cconf.append(self.writeEEnIOoffset(idbus, io_logic, 21, [3 | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 3, 0x72, 0x03]))
                                
                                elif self.EEPROM_LANGUAGE == 1:
                                    i2cconf = []
                                    i2cconf.append(self.writeEEnIOoffset(idbus, io_logic, 10, [3 | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 1, 0x72, 0xAC]))
                                    i2cconf.append(self.writeEEnIOoffset(idbus, io_logic, 14, [2 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 3 | 32, 0x72 | 1  ]))

                                    i2cconf.append(self.writeEEnIOoffset(idbus, io_logic, 17, [3 | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 1, 0x72, 0x80]))
                                    i2cconf.append(self.writeEEnIOoffset(idbus, io_logic, 21, [3 | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 3, 0x72, 0x03, 0, 0]))

                                msg.extend(i2cconf)
                                # print("CONFIGURAZIONE I2C:", i2cconf)

                        elif io_type == 'onewire':
                            if device_name == 'DS18B20':
                                if self.EEPROM_LANGUAGE == 0:
                                    msg.append(self.writeEEnIOoffset(idbus, io_logic, 10, [3 | self.i2c_const['CONCATENA'] | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 1, 0xcc, 0x44]))  # num. byte, byte opzioni, campionamento di tutte le sonde, campiona temperatura
                                    address = 0 if 'address' not in boards.get(board) else boards.get(board).get('address')
                                    print("ADDRESS ID ONE WIRE:", address)                                 
                                    if address:
                                        address = [int(x, 16) for x in address]
                                        msg.append(self.writeEEnIOoffset(idbus, io_logic, 14, [11 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 1+72, 0x55] + address +  [0xbe, 0]))  # num. byte, byte opzioni, S/N sonda, ID, 0xbe leggi temp
                                    else:
                                        msg.append(self.writeEEnIOoffset(idbus, io_logic, 14, [3 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 1+72, 0xCC] + [0xbe, 0]))  # num. byte, byte opzioni, S/N sonda, ID, 0xbe leggi temp

                                elif  self.EEPROM_LANGUAGE == 1:  
                                    msg.append(self.writeEEnIOoffset(idbus, io_logic, 10, [3 | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 1, 0xcc, 0x44]))  # num. byte, byte opzioni, campionamento di tutte le sonde, campiona temperatura
                                    address = 0 if 'address' not in boards.get(board) else boards.get(board).get('address')
                                    print("ADDRESS ID ONE WIRE:", address)
                                    if address:
                                        address = [int(x, 16) for x in address]
                                        msg.append(self.writeEEnIOoffset(idbus, io_logic, 14, [11 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 1+72, 0x55] + address +  [0xbe, 0]))  # num. byte, byte opzioni, S/N sonda, ID, 0xbe leggi temp
                                    else:
                                        msg.append(self.writeEEnIOoffset(idbus, io_logic, 14, [3 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 1+72, 0xCC] + [0xbe, 0, 0]))  # num. byte, byte opzioni, S/N sonda, ID, 0xbe leggi temp                                
                            
                            elif device_name == 'GENERIC':
                                # Go To programma di altro IO logico
                                # print("WRITE_EE", write_ee, idbus, eels + 10, eems, [32 | 3, 0, 0])
                                if write_ee:
                                    msg.append(self.writeEEnIOoffset(idbus, io_logic, 10, [32 | 3, 0, 0]))  # [32: Go_TO | 3: IO logico, 0: offset (0=10), 0=non ci sono altri programmi da eseguire ]
                                else:
                                    print("********************")
                                    msg.append(self.writeEEnIOoffset(idbus, io_logic, 10, [32 | 3, 0, 0]))  # [32: Go_TO | 3: IO logico, 0: offset (0=10), 0=non ci sono altri programmi da eseguire ]
                        
                        else:
                            # If not I2C or OneWire, set 0, 0 at address 10 and 11.
                            msg.append(self.writeEEnIOoffset(idbus, io_logic, 10, [0,0]))  # 0 = lunghezza programma periodico, 0 = lunghezza prg. inizializzazione


                # print("ADD REBOOT")
                # msg.append(self.boardReboot(idbus))
        # msg.append(self.getTypeBoard(5))
        # print("RESET TOTALE")
        # msg.append(self.setMaxBoardAddress(self.MAX_BOARD_ADDRESS))
        if msg:
            msg.append(self.boardReboot(0))
        else:
            print("NESSUNA CONFIGURAZIONE BOARD DA INVIARE")    
        pprint(msg)
        
        # mmsg = msg.pop(0)
        # print("***");
        # pprint(msg)
        # print("***");
        # msg.append(mmsg)
        # pprint(msg)
        # print("***");
        # kkkk;
        return msg

    def arrivatatrama(self): # utilizzatore: 0=dl485, 1=domoticz
        # arrivata una trama completa (PING e trame piu lunghe)
        self.nowtime = int(time.time())  # seleziona la parte intera dei secondi
        # print(b.RXtrama)
        self.board_ready[self.RXtrama[0]] = self.nowtime  # Aggiorna la data di quando è stato ricevuto la trama del nodo, serve per dizionario delle boards rilevate sul bus

        if self.RXtrama[0] + 1 == self.BOARD_ADDRESS:  # test su address ricevuto, e' ora di trasmettere

            for x in self.BUFF_MSG_TX:  ## aggiornamento timeout
                ##print(b.BUFF_MSG_TX[x][1])
                if self.BUFF_MSG_TX[x][1]: self.BUFF_MSG_TX[x][1] -= 1

            for x in self.BUFF_MSG_TX: ##cerca msg in timeout, fatto in un secondo ciclo for perchè questa modifica il dizionario e crea un errore se si continua la ricerca dopo la modifica
                if not self.BUFF_MSG_TX[x][1]:  ## trovato messaggio in timeout
                    # print("TIMEOUT MSG:",b.BUFF_MSG_TX[x][0])
                    self.log.write("{:<11} {}    {:<18}".format(self.nowtime, 'CONFIG. TIMEOUT MSG', str(self.BUFF_MSG_TX[x][0])))
                    
                    self.TXmsg.insert(0,self.BUFF_MSG_TX[x][0])  ## lo mette al primo posto nella lista di trasmissione
                    # print(b.TXmsg)
                    del self.BUFF_MSG_TX[x] ## lo cancella per poterlo reinserire tutto perche non c'è il goto
                    break  ## esce dal for
                
            if len(self.TXmsg): #se qualcosa da trasmettere
                
                msg = self.TXmsg.pop(0)  # prende dalla lista la prima trama da trasmettere (msg piu vecchio)
                ##print(msg, msg[2], b.BUFF_MSG_TX)
                if (len(msg)>1): print("****FORSE TRASMETTE: %s            %s" %(len(self.TXmsg), self.int2hex(msg)))
                if (len(msg)>1) and (msg[1]==self.code['CR_REBOOT']):  # il comando reboot va trasmesso alla fine della configurazione
                    if self.BUFF_MSG_TX or self.TXmsg:
                        self.log.write("{:<12}    {:<18}".format(self.nowtime, 'REBOOT RIMESSO IN LISTA X ATTESA DIZIONARIO VUOTO'))
                        # print(" REBOOT RIMESSO IN LISTA X ATTESA DIZIONARIO VUOTO")
                        self.TXmsg.append(msg)  #lo rimetto in fondo alla lista perchè attesa dizionario vuoto
                    else:   
                        # print(" OKTRASM REBOOT")
                        self.log.write("{:<11} TX                    {:<18} {} {}".format(self.nowtime, str(self.int2hex(msg)), 'OKTRASM REBOOT', ''))
                        if len(msg) > 1:
                            msg1 = self.eight2seven(msg)  # trasforma messaggio in byte da 7 bit piu byte dei residui 
                        else:
                            msg1 = msg
                        msg2 = self.encodeMsgCalcCrcTx(msg1) # restituisce il messaggio codificato e completo di crc (1 o 2 crc in base al flag crcdoppio)
                        self.send_data_serial(self.Connection, msg2)  # invia alla seriale
                        # ser.write(bytes(msg2))  # invia alla seriale
                else:
                    if (len(msg)>1) and (msg[2] in self.BUFF_MSG_TX): # controllo se nodo deve ancora dare feedback a un msg precedente
                        self.log.write("{:<11} {:<18}".format(self.nowtime, 'CONFIGURAZIONE, REINSERIMENTO IN LISTA ATTESA FEEDBACK'))
                        self.TXmsg.append(msg)  #attesa feedback dallo stesso nodo: lo rimetto in lista al primo posto perchè deve stare prima di reboot 
                    else: #tx messaggio lungo o ping
                        # if (len(msg)>1):print(" OKTRASM, ATTESA FEEDBACK")
                        self.log.write("{:<11} TX                     {:<18} {} {}".format(self.nowtime, str(self.int2hex(msg)), 'OKTRASM, ATTESA FEEDBACK', ''))
#                        print("****SENZA BYTE RESIDUI*******",self.int2hex(msg))
                        if len(msg) > 1: # non è un ping, aggiunge byte residui
                            msg1 = self.eight2seven(msg)  # trasforma messaggio in byte da 7 bit piu byte dei residui 
                            print("******CON BYTE RESIDUI*******", self.int2hex(msg1))
                        else: # è un ping non aggiunge i residui
                            msg1 = msg
#                            print ("TXPING:", int2hex(msg));
                        msg2 = self.encodeMsgCalcCrcTx(msg1) # restituisce il messaggio codificato e completo di crc (1 o 2 crc in base al flag crcdoppio)
#                        if self.crcdoppio == 1: print("******CON AGGIUNTO 2°CRC*****", self.int2hex(msg2)) #test per stampe debug con secondo crc
                            
                        self.send_data_serial(self.Connection, msg2)  # invia alla seriale
                        if (len(msg)>1) and (msg[1]==6):  # inserisce solo se comando writeEE
                            self.BUFF_MSG_TX[msg[2]] = [msg, self.NLOOPTIMEOUT+len(msg)]  # inserisce in dizionario messaggio originale per controllo feedback

        self.RXtrama[0] &= 0x3F  # Trasforma la trama di nodo occupato in libero (serve solo per la trasmissione) 

#                b.labinitric()  # Reset buffer ricezione e init crc ricezione per prossimo pacchetto da ricevere

        if len(self.RXtrama) > 1:  # Analizza solo comunicazioni valide (senza PING)
            # print(b.code['COMUNICA_IO'], b.code['CR_WR_OUT'])
#                    print("Arrivata trama: ",b.int2hex(b.RXtrama))
            if self.RXtrama[1] == 0x26: # CR_WR_EE <<<==============================
                self.log.write("{:<11} TX                     {:<18} {} {}".format(self.nowtime, 'VERIFICA_FEEDBACK, TRAMA RIC:', self.int2hex(self.RXtrama), ''))
                print("VERIFICA_FEEDBACK, TRAMA RIC:", self.int2hex(self.RXtrama), end='')
                if self.RXtrama[0] in self.BUFF_MSG_TX:
                    msgapp = self.BUFF_MSG_TX[self.RXtrama[0]][0]
                    #  print(", TROVATO STESSO INDIRIZZO", msgapp, ", VERIFICA CONTENUTO...", end='')
                    #  siccome sono salvati in dizionario soltanto i comandi di scrittura e2 si evita di verificare
                    #  se feedback sia feedback di scrittura e2
                    if msgapp[3:] == self.RXtrama[2:]:
                        self.log.write("{:<11} {:<18} {} {}".format(self.nowtime, 'VERIFICA OK', '', ''))
                        print(" VERIFICA OK")
                        del self.BUFF_MSG_TX[self.RXtrama[0]]
                    else: print(" ERR VERIFICA BUFF=", msgapp[3:]," TRAMARIC=", self.RXtrama[2:])        
                else:
                    print(" ERR RICEVUTO FEEDBACK DI MSG MAI INVIATO")


            if self.RXtrama[1] in [self.code['COMUNICA_IO'], self.code['CR_WR_OUT']]:  # COMUNICA_IO / Scrive valore USCITA
                value = self.calculate(self.RXtrama[0], self.RXtrama[2], self.RXtrama[3:])  # Ritorna il valore calcolato a seconda del tipo e del dispositivo connesso
                try:
                    self.status[self.RXtrama[0]]['io'][self.RXtrama[2] - 1] = value
                except:
                    print("chiave non trovata")    
            
                self.log.write("{:<11} RX  {:<18} {} {}".format(self.nowtime, self.code[self.RXtrama[1]], self.int2hex(self.RXtrama), self.RXtrama))

            elif self.RXtrama[1] & 32:
                apprx=self.RXtrama[1]-32 # ricava comando associato a questa risposta
                if apprx in self.code:
                    err = ''
                    if apprx == 0x2D - 32:
                        """
                        Comando di errore ritornato: ID SCHEDA, COMANDO ERRORE (2D), COMANDO ARRIVATO (255 se non disponibile), IO Logico (255 se non disponibile), Tipo errore
                        """
                        err = self.error[self.RXtrama[4]] if self.RXtrama[4] in self.error else 'ERRORE NON DEFINITO'
                    self.log.write("{:<11} RX  {:<18} {} {}".format(self.nowtime, self.code[apprx], self.int2hex(self.RXtrama), err))
        # else: print("RXPING",int2hex(self.RXtrama))            

    def writeLog(self):
            #  parte che stampa il log ogni TIME_PRINT_LOG e aggiorna le board presenti
            if (not len(self.TXmsg)) and (self.nowtime - self.oldtime > self.TIME_PRINT_LOG):
                self.oldtime = self.nowtime  # Not remove
                self.TXmsg.append(self.ping)  # Not remove. Is neccesary to reset shutdown counter
                # Routine che aggiorna le BOARD presenti sul BUS
                board_to_remove = []
                for k, v in self.board_ready.items():
                    # b.log.write(v, b.nowtime-v, v)
                    if (self.nowtime - v) > 5:  # rimuove board se i suoi pacchetti mancano da piu di 5 secondi
                        board_to_remove.append(k)
                for k in board_to_remove:
                    del self.board_ready[k]
                # b.BOARD_ADDRESS = max(list(b.board_ready.keys())) + 1
                br = list(self.board_ready.keys())
                br.sort()
                self.log.write("{:<12} BOARD_READY           {:<18} ".format(int(self.nowtime), str(br)))
                self.printStatus()  # Print status of IO
                
        

# END BUS Class

# INIZIO PARTE MAIN
if __name__ == '__main__':
    print("*" * 20, "START DL485 program", "*" * 20)
    if len(sys.argv) > 1:  # analisi parametro sulla riga di comando
        # print(sys.argv)
        if sys.argv[1] == 'w':  # stampa log su file
            logstate = 1
        elif sys.argv[1] == 'p':  # stampa a schermo
            logstate = 2
        elif sys.argv[1] == 'wp':  # stampa a schermo e su file
            logstate = 3
        else:  # parametro non valido
            logstate = 0
            print("errore parametro di riga non valido, parametri LOG: w=write to file, p=print, wp=write+print")
            sys.exit()
    else:
        logstate = 0
        print("Programma senza richiesta di log su schermo/file. parametri possibili w (log su file), p (log a schermo), wp (log a schermo e file)", end="\n\n")


    
    config_file_name = "./config.json"  # specifica nome file di configurazione
    b = Bus(config_file_name, logstate)  # Istanza la classe bus
#    log = Log('log.txt', logstate)  # Instazia la classe Log
    

    # righe da eseguire dopo aver specificato il file di configurazione
    print("BUS_BAUDRATE:%s, BUS_PORT:%s, BOARD_ADDRESS:%s" %(b.bus_baudrate, b.bus_port, b.BOARD_ADDRESS))

    """ Reset parametri SCHEDE """
    # se serve si resetta una o tutte le schede con le tre righe sotto
    # msg = b.resetEE(2, 0)  # Board_id, io_logic. Se io_logic=0, resetta tutti gli IO
    # print("RESET IO SCHEDE:", msg)
    # b.TXmsg = msg

    """ Configurazione SCHEDE in base al file in config_file_name """
    # reset = b.resetEE(0, 0)
    # b.TXmsg += reset

    b.TXmsg += b.getConfiguration()  # Set configuration of boardsx e mette la configurazione in coda da inviare

    b.oldtime = int(time.time()) - 10  # init oldtime per stampe dizionario con i/o per stampa subito al primo loop
    
    """ LOOP """
    while int(time.time()) - b.oldtime < 5:
        """ Svuta il buffer della seriale1 """
        res = b.Connection.read()        

    while 1:
        RXbytes = b.Connection.read() #legge uno o piu caratteri del buffer seriale
        if not RXbytes: continue  # seriale senza caratteri non entra nel for sotto

        for d in RXbytes:  # analizza i caratteri ricevuti
            b.RXtrama = b.readSerial(d)  # accumula i vari caratteri e restituisce il pacchetto finito quando trova il carattere di fine pacchetto
            # print(b.RXtrama)
            if not b.RXtrama: continue
            
            b.arrivatatrama()

            b.writeLog()
            

            # log.write("T", b.nowtime)
            # try:
                # conn, addr = sock.accept()
                # log.write("AA")
            # except:
                # pass

            # try:  # Routine per la Ricezione comandi da django e altro via UDP
                # conn.setblocking(0)
                # data = conn.recv(BUFFER_SIZE)
                # log.write("X", b.nowtime)
                # if data:
                    # data = data.decode('utf-8')
                    # data = data.split(';')
                    # if 'onCommand' in data:
                        # board_id = int(data[1])
                        # io_logic = int(data[2])
                        # value = json.loads(data[3])[0]
                        # message = "MSG ricevuto da Domoticz: board_id:%s, io_logic:%s, value prima:%s" %(board_id, io_logic, value)
                        # value = b.checkIO(board_id, io_logic, [value])
                        # msg = b.writeIO(board_id, io_logic, [value])
                        # log.write(message + " Value dopo:%s, msg:%s" %(value, msg))

                        # addTX(msg)

            b.RXtrama = []  # Azzera trama ricezione
            time.sleep(0.0005)  # Delay per non occupare tutta la CPU


    log.write("FINE SCRIPT")
