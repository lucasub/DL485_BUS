#!/usr/bin/python3.4
# -*- coding: utf-8 -*-
"""
Class protocol DL485
"""

import sys
import os

if os.getcwd() == "/home/pi/danbus/DL485":
    import arduinoserial
if os.getcwd() == "/home/pi/danbus/DLSERIAL":
    import arduinoserial
if os.getcwd() == "/home/pi/domoticz/plugin/DL485-serial":
    import arduinoserial
import arduinoserial

from pprint import pprint
import time
import logging
import math
import json
# import commentjson
import jstyleson

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

class Bus:
    code = {  # Dict with all COMAND
        0: 'INPUT',
        1: 'OUTPUT',
        2: 'CR_TRASPORTO_STRINGA',
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

        'INPUT': 0,
        'OUTPUT': 1,
        'CR_TRASPORTO_STRINGA': 2,
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
    }

    disable_io = 0x3e
    enable_io = 0xff

    error = {  # Dict with ERROR type
        0: "Errore inizializzazione / timeout I2C",
        1: "Errore 3 zeri",
        2: "Errore 3 uni",
        3: "Pacchetto ricevuto troppo lungo",
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
        14: "Errore comando a 1 parametro sconosciuto",
        15: "Errore comando a 2 parametri sconosciuto",
        16: "Errore comando a 3 parametri sconosciuto",
        17: "Errore comando a 4 parametri sconosciuto",
        18: "Errore comando n parametri non previsto ",
        19: "Errore CRC",
        20: "I2C occupata",
        21: "I2C Timeout",
        22: "OneWire Occupata",

        24: "OneWire Occupata",
        25: "Lettura numero ingreso fuori range",
        26: "Dimensione pacchetto non conforme",
        27: "Lettura EE oltre limite indirizzo",
        28: "Scrittura numero uscita fuori range",
        29: "Numero parametro fuori range",
        30: "Nodo occupato da ordine precedente",
    }

    i2c_const = {  # Const I2C
        'CONCATENA': 128,
        'NON_CONCATENA': 0,
        'BYTE_OPZIONI_LETTURA': 64,
        'BYTE_OPZIONI_SCRITTURA': 0,
        'FLAG_PAUSA': 0x20,
    }

    mapmicro = {  # MAP PIN Atmega328P QFN32PIN
         1: {'name': 'PD3',         'iomicro':    3,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
         2: {'name': 'PD4',         'iomicro':    4,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
         3: {'name': 'PE0',         'iomicro':   21,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
         4: {'name': 'VCC',         'iomicro':   99,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
         5: {'name': 'GND',         'iomicro':   99,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
         6: {'name': 'PE1',         'iomicro':   22,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
         7: {'name': 'XTAL1',       'iomicro':   99,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
         8: {'name': 'XTAL2',       'iomicro':   99,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
         9: {'name': 'PD5',         'iomicro':    5,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        10: {'name': 'PD6',         'iomicro':    6,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        11: {'name': 'PD7',         'iomicro':    7,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        12: {'name': 'PB0',         'iomicro':    8,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        13: {'name': 'PB1',         'iomicro':    9,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        14: {'name': 'PB2',         'iomicro':   10,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        15: {'name': 'PB3',         'iomicro':   11,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        16: {'name': 'PB4',         'iomicro':   12,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        17: {'name': 'PB5',         'iomicro':   13,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        18: {'name': 'AVCC',        'iomicro':   99,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        19: {'name': 'ADC6 PE2',    'iomicro':   23,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        20: {'name': 'AREF',        'iomicro':   99,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        21: {'name': 'GND',         'iomicro':   99,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        22: {'name': 'ADC7 PE3',    'iomicro':   24,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        23: {'name': 'PC0',         'iomicro':   14,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        24: {'name': 'PC1',         'iomicro':   15,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        25: {'name': 'PC2',         'iomicro':   16,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        26: {'name': 'PC3',         'iomicro':   17,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        27: {'name': 'PC4',         'iomicro':   18,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        28: {'name': 'PC5',         'iomicro':   19,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        29: {'name': 'RST',         'iomicro':   99,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        30: {'name': 'PD0',         'iomicro':    0,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        31: {'name': 'PD1',         'iomicro':    1,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        32: {'name': 'PD2',         'iomicro':    2,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        33: {'name': 'BME280',      'iomicro':   18,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        34: {'name': 'BME280',      'iomicro':   18,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        35: {'name': 'DS18B20',     'iomicro':    3,    'function': {'D': 1, 'A': 0, 'PWM': 1, 'IN': 1, 'OUT': 1, 'SDA': 0, 'SCL': 0}},
        37: {'name': 'TEMP_ATMEGA', 'iomicro':   25,    'function': ['ATMEGA temperature'] },
        38: {'name': 'AM2320',      'iomicro':   18,    'function': ['AM2320']},

    }

    iomap = {  # MAP IO of board
        1: {  # Board 1 DomoOne
            'PB0':          {'pin':  12,  'name':     'IO4'},
            'PB1':          {'pin':  13,  'name':     'IO5'},
            'PB2':          {'pin':  14,  'name':     'IO8'},
            'PB3':          {'pin':  15,  'name':      'IO15'},
            'PB4':          {'pin':  16,  'name':      'IO13'},
            'PB5':          {'pin':  17,  'name':      'IO14'},
            'PD3':          {'pin':   1,  'name':     'IO6'},
            'PD4':          {'pin':   2,  'name':     'IO7'},
            'PC0':          {'pin':  23,  'name':     'IO9'},
            'PC1':          {'pin':  24,  'name':      'IO10'},
            'PC2':          {'pin':  25,  'name':      'IO11'},
            'PC3':          {'pin':  26,  'name':      'IO12'},
            'PC4':          {'pin':  27,  'name':      'IO11'},
            'PC5':          {'pin':  28,  'name':      'IO12'},
            'PE0':          {'pin':   3,  'name':      'SDA'},
            'PE1':          {'pin':   6,  'name':      ''},
            'PE2':          {'pin':  19,  'name':      ''},
            'VIN':          {'pin':  22,  'name':      'VIN'},
            'PCA9535':      {'pin':   0,  'name':      'PCA9535'},
            'BME280':       {'pin':   0,  'name':      'BME280'},
            'BME280B':      {'pin':   0,  'name':      'BME280'},
            'AM2320':       {'pin':   0,  'name':      'AM2320'},
            'TSL2561':      {'pin':   0,  'name':      'TSL2561'},
            'DS18B20-1':    {'pin':  35,  'name':      'DS18B20'},
            'DS18B20-2':    {'pin':  35,  'name':      'DS18B20'},
            'DS18B20-3':    {'pin':  35,  'name':      'DS18B20'},
            'DS18B20-4':    {'pin':  35,  'name':      'DS18B20'},
            'DS18B20-5':    {'pin':  35,  'name':      'DS18B20'},
            'DS18B20-6':    {'pin':  35,  'name':     'DS18B20'},
            'DS18B20-6':    {'pin':  35,  'name':     'DS18B20'},
            'TEMP_ATMEGA':  {'pin':  37,  'name':     'TEMP_ATMEGA'},
        },

        3: {  # Board DL485PCB  #
            'SDA':          {'pin':  27,  'name':     'IO1'},  # IO Logico: IO Fisico
            'SCL':          {'pin':  28,  'name':     'IO2'},
            'PD7':          {'pin':  11,  'name':     'IO3'},
            'PB0':          {'pin':  12,  'name':     'IO4'},
            'PB1':          {'pin':  13,  'name':     'IO5'},
            'PD3':          {'pin':   1,  'name':     'IO6'},
            'PD4':          {'pin':   2,  'name':     'IO7'},
            'PB2':          {'pin':  14,  'name':     'IO8'},
            'PC0':          {'pin':  23,  'name':     'IO9'},
            'PC1':          {'pin':  24,  'name':     'IO10'},
            'PC2':          {'pin':  25,  'name':     'IO11'},
            'PC3':          {'pin':  26,  'name':     'IO12'},
            'PB4':          {'pin':  16,  'name':     'IO13'},
            'PB5':          {'pin':  17,  'name':     'IO14'},
            'PB3':          {'pin':  15,  'name':     'IO15'},
            'PE0':          {'pin':   3,  'name':     'IO8'},
            'PE1':          {'pin':   6,  'name':     'IO8'},
            'PE2':          {'pin':  19,  'name':     'ADC'},
            'PE3':          {'pin':  22,  'name':     'VIN'},
            'PCA9535':      {'pin':   0,  'name':     'PCA9535'},
            'BME280':       {'pin':   0,  'name':     'BME280'},
            'BME280B':      {'pin':   0,  'name':     'BME280'},
            'AM2320':       {'pin':   0,  'name':     'AM2320'},
            'TSL2561':      {'pin':   0,  'name':     'TSL2561'},
            'DS18B20-1':    {'pin':  35,  'name':     'DS18B20'},
            'DS18B20-2':    {'pin':  35,  'name':     'DS18B20'},
            'DS18B20B':     {'pin':  36,  'name':     'DS18B20'},
            'TEMP_ATMEGA':  {'pin':  37,  'name':     'TEMP_ATMEGA'}
        },

        2: {  # Board DL485BOX
            'IO1':          {'pin':  23,  'name':      'IO1'},
            'IO2':          {'pin':  24,  'name':      'IO2'},
            'IO3':          {'pin':  25,  'name':      'IO3'},
            'IO4':          {'pin':  26,  'name':      'IO4'},
            'OUT1':         {'pin':   3,  'name':      'RELE1'},
            'OUT2':         {'pin':   2,  'name':      'RELE2'},
            'OUT3':         {'pin':   1,  'name':      'RELE3'},
            'VIN':          {'pin':  22,  'name':      'VIN'},
            'SDA':          {'pin':  27,  'name':      'SDA'},
            'SCL':          {'pin':  28,  'name':      'SCL'},
            'PCA9535':      {'pin':   0,  'name':      'PCA9535'},
            'BME280A':      {'pin':   0,  'name':      'BME280'},
            'BME280B':      {'pin':   0,  'name':      'BME280'},
            'TSL2561':      {'pin':   0,  'name':      'TSL2561'},
            'DS18B20':      {'pin':  35,  'name':      'DS18B20'},
            'TEMP_ATMEGA':  {'pin':  37,  'name' :     'TEMP_ATMEGA'}
        },
    }

    def __init__(self):
        self.buffricnlung = 1  # Lenght RX buffer
        self.flagerrore = 0  # Flag errore
        self.buffricn = []  # Buffer RX trama
        self.appcrc = []  # Per calcolo CRC
        self.INITCRC = 0x55
        self.crcric = self.INITCRC
        self.inSerial = 0
        self.crctrasm = 0x55
        self.BOARD_ADDRESS = 0
        self.config = {}  # Configuration dict
        self.status = {}  # Stauts of all IO Board
        self.buffricnapp = []  # Contiene i primi 7 byte per calolare il resto
        self.mapiotype = {}  # Tipi di IO disponibili
        self.mapproc = {}  # Procedure associate agli ingressi verso le uscite
        self.logstate = 0

    # def getConfig(self, config_file="config.txt"):
    #     """
    #     Create self.config from JSON configuration file
    #     """
    #     self.config = dict(ConfigObj(config_file))  # Legge il file di configurazione

    def getJsonConfig(self, config_file):
        """
        Create self.config from JSON configuration file
        """
        config = open(config_file, 'r')
        config = config.read()
        self.config = jstyleson.loads(config)
        
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
                self.status[idbus]['io'] = [0] * len(self.iomap[boardtype])
                self.status[idbus]['boardtypename'] = self.config['TYPEB']["%s" %boardtype]

                for bb in self.config[b]:
                    if not 'GENERAL' in bb:
                        # print("************************************")
                        # pprint(self.config[b][bb])
                        # print("************************************")
                        io_logic = int(self.config[b][bb]['io_logic'])
                        io_type = 'other' if not 'io_type' in self.config[b][bb] else self.config[b][bb]['io_type']
                        device_name = '' if not 'device_name' in  self.config[b][bb] else self.config[b][bb]['device_name']

                        if not idbus in self.mapiotype: self.mapiotype[idbus] = {}

                        inverted = int(self.config[b][bb]['inverted']) if 'inverted' in self.config[b][bb] else 0
                        default_startup_value = 0  if not 'default_startup_value' in self.config[b][bb] else int(self.config[b][bb]['default_startup_value'])
                        print("*** Board_id:%s,  io_logic=%s,  inverted=%s,  default_startup_value=%s,  default_startup_value_new=%s" %(idbus, io_logic, inverted, default_startup_value, default_startup_value ^ inverted))
                        default_startup_value = default_startup_value ^ inverted

                        self.mapiotype[idbus][io_logic] = {
                            'io_logic': io_logic,
                            'io_type': io_type,
                            'device_name': device_name,
                            'Rvcc': 0 if not 'Rvcc' in self.config[b][bb] else int(self.config[b][bb]['Rvcc']),
                            'Rgnd': 0 if not 'Rgnd' in self.config[b][bb] else int(self.config[b][bb]['Rgnd']),
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
                            'linked_board_id_io_logic': self.config[b][bb]['linked_board_id_io_logic'] if 'linked_board_id_io_logic' in self.config[b][bb] else [],

                        }

                        linked_board_id_io_logic = self.config[b][bb]['linked_board_id_io_logic'] if 'linked_board_id_io_logic' in self.config[b][bb] else [],
                        linked_proc = self.config[b][bb]['linked_proc'] if 'linked_proc' in self.config[b][bb] else [],


                        if linked_board_id_io_logic:
                            # print(linked_board_id_io_logic, linked_board_id_io_logic[0], type(linked_board_id_io_logic[0]))
                            for x in linked_board_id_io_logic[0]:
                                if not x in self.mapproc:
                                    self.mapproc[x] = {}
                                self.mapproc[x]["%s-%s" %(idbus, io_logic)] = {'linked_proc': linked_proc[0]}

        # pprint(self.mapiotype)
        pprint(self.mapproc)

    def inverted(self, board_id, io_logic, value):
        """
        Invert IO value
        """
        inverted = self.mapiotype[board_id][io_logic]['inverted']
        if inverted:
            value = 1 - value & 1
            self.status[board_id]['io'][io_logic - 1] = value  # Valore corrente IO
        # print("value2", value)
        return value

    def checkIO(self, board_id, io_logic, value):
        """
        Verifica se l'IO deve essere manipolato prima di essere spedito al BUS
        **** Funzione NON USATA perché su plugin DOMOTICZ***
        """

        if board_id in self.mapiotype and io_logic in self.mapiotype[board_id]:

            if self.mapiotype[board_id][io_logic]['io_type'] == 'onewire':
                if self.mapiotype[board_id][io_logic]['device_name'] == 'DS18B20':
                    # Formula calcolo temperatura DS18B20: ((secondo byte << 8) + primo byte) * 0.0625
                    value1 = round(((value[1] << 8) + value[0]) * 0.0625, 1)
                    # print("Calcola temperatura OneWire ============>> Board_id:%s io_logic:%s value:%s" %(board_id, io_logic, value1))
                    return value1
            elif self.mapiotype[board_id][io_logic]['io_type'] == 'i2c':
                if self.mapiotype[board_id][io_logic]['device_name'] == 'BME280':
                    # print("Calcola temperatura I2C ============>> Board_id:%s io_logic:%s value:%s" %(board_id, io_logic, value))
                    value = self.getBME280(value)
                    return value
            elif self.mapiotype[board_id][io_logic]['io_type'] == 'analog':
                Rvcc = self.mapiotype[board_id][io_logic]['Rvcc']
                Rgnd = self.mapiotype[board_id][io_logic]['Rgnd']
                Vin = (value[0] + (value[1] * 128)) * (Rvcc + Rgnd) / (Rgnd * 930)
                # print("Analog input: Board_id:%s, io_logic:%s, Rvcc:%s, Rgnd:%s, Vin:%s" %(board_id, io_logic, Rvcc, Rgnd, Vin))
                return round(Vin, 1)
            elif self.mapiotype[board_id][io_logic]['io_type'] == 'digital':

                # b0: dato filtrato
                # b1: dato istantaneo
                # b2: fronte OFF
                # b3: fronte ON
                # b4: fronte OFF da trasmettere
                # b5: fronte ON da trasmettere

                value = value[0]
                # print("===>>>checkIO", board_id, io_logic, value, self.mapiotype[board_id][io_logic]['io_type'])

                # print("CHECK IO: Board_id:%s, io_logic:%s, value:%s" %(board_id, io_logic, value))
                return value
            else:
                print("IO**: Board_id:%s, io_logic:%s, Value:%s" %(board_id, io_logic, value))
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

    def calculate(self, board_id, io_logic, value):
        """
        Ritorna il valore calcolato a seconda del dispositivo connesso:
            Temperature:
                DS18B20         -> Temp
                BME280          -> Temp + Hum + Bar
                ATMEGA CHIP     -> Temp
                AM2320          -> Temp + Hum
            Voltage:
                Analog Input
            Digital:
                Digital input
        """
        if board_id in self.mapiotype and io_logic in self.mapiotype[board_id]:
            # print(self.mapiotype[board_id])
            # print("IO_TYPE",self.mapiotype[board_id][io_logic]['io_type'], "Value:", value)
            if self.mapiotype[board_id][io_logic]['io_type'] == 'onewire':
                if self.mapiotype[board_id][io_logic]['device_name'] == 'DS18B20':
                    crc = 0
                    for x in value[0:8]:
                        crc = self.calcCrcDS(x, crc)
                    if crc == value[8]:
                        # print("CRC OK")
                        value = ((value[1] << 8) + value[0]) * 0.0625
                        return round(value, 1)
                    else:
                        print("Errore CRC DS")
                        return None

            elif self.mapiotype[board_id][io_logic]['io_type'] == 'i2c':
                if self.mapiotype[board_id][io_logic]['device_name'] == 'BME280':
                    value = self.getBME280(value)
                    return value
                if self.mapiotype[board_id][io_logic]['device_name'] == 'AM2320':
                    hum = (value[2] * 256 + value[3]) / 10.0
                    temp = (value[4] * 256 + value[5]) / 10.0
                    return [temp, hum]

            elif self.mapiotype[board_id][io_logic]['io_type'] == 'temp_atmega':
                value = (value[0] + (value[1] * 256)) - 270 + 25
                return round(value, 1)

            elif self.mapiotype[board_id][io_logic]['io_type'] == 'analog':
                Rvcc = self.mapiotype[board_id][io_logic]['Rvcc']
                Rgnd = self.mapiotype[board_id][io_logic]['Rgnd']
                try:
                    value = (value[0] + (value[1] * 128)) * (Rvcc + Rgnd) / (Rgnd * 930)
                    return round(value, 1)
                except:
                    print("Analog Error: Value:", value)
                    return 0

            elif self.mapiotype[board_id][io_logic]['io_type'] == 'digital':
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
        print("\n", "-" * 40, "STATUS IO", "-" * 40)
        print("ID  Name         BoardType  IO:", end=' ')
        for i in range(1, 23):
            print("{:<6} ".format(i), end='')
        print()
        for b in self.status:
            print("{:<4}{:<10} {} {:<13}".format(b, self.status[b]['name'], self.status[b]['boardtype'], self.status[b]['boardtypename']), end='')

            for i in self.status[b]['io']:
                print(' %s ' % i, end='')
            print()
        print("-" * 40, "END STATUS", "-" * 40, "\n")

    def int2hex(self, msg):
        """
        Convert list data from INT to HEX
        """
        return ['{:02X} '.format(a) for a in msg]

    def ser(self, port='/dev/ttyUSB0', baudrate=57600):
        """
        Instance of serial
        """
        return arduinoserial.SerialPort(port, baudrate)

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

    def seven2eight(self):
        """
        Trasforma la string ricevuta dalla seriale (dati a 7 bit) in byte da 8 bit
        Ogni 7 byte ricevuti, viene trasmesso l'ottavo BIT di ciascun byte.
        """
        resto = self.buffricnapp.pop()
        i = len(self.buffricnapp) -1
        while i >= 0:
            if resto & 1:
                self.buffricnapp[i] += 128
            resto >>= 1
            i -= 1
        self.buffricn += self.buffricnapp
        self.buffricnapp = []

    def readSerial(self, inSerial):
        """
        Calculate trama and return list with right values
        """
        # self.inSerial = inSerial
        if self.buffricnlung > 100:  # Errore 3
            self.flagerrore = 3
            self.labinitric()
            print("ERR 3 Pacchetto troppo lungo")
            return []

        if (inSerial & 0x38) == 0x18 or (inSerial & 0x38) == 0x20:  # Fine pacchetto
            inSerial = (inSerial & 0x0f) | ((inSerial & 0xc0) // 4)
            if (inSerial ^ self.crcric) & 0x3f == 0:  # crc corretto
                if not self.buffricnapp:
                    ric = self.buffricn
                    self.labinitric()
                    return ric
                self.seven2eight()  # Converti i byte da 7 a 8 bit
                ric = self.buffricn
                # ric.append()
                self.labinitric()
                return(ric)
            else:
                self.buffricnapp = []
                self.labinitric()
                return []

        elif inSerial == 0:  # Errore 1
            self.flagerrore = 1
            self.labinitric()
            inSerial = 0
            print("ERR 1 Tre 0 ricevuti")
            return []

        elif inSerial == 0x38:  # Errore 2
            self.flagerrore = 2
            self.labinitric()
            inSerial = 0
            print("ERR 2 Tre 1 ricevuti")
            return []

        else:  # carattere normale
            # print("Carattere normale", inSerial)
            self.crcric = self.calccrc(inSerial, self.crcric)  # aggiorna crc
            # print(inSerial, self.crcric, )
            self.buffricnapp.insert(self.buffricnlung - 1, ((inSerial & 0x0f) | ((inSerial & 0xE0)//2)))  # insersce carattere decodificato

            if (self.buffricnlung % 8) == 0 and self.buffricnlung > 0:  # E' il byte resto
                self.seven2eight()
            self.buffricnlung += 1
            return []

    def eight2seven(self, msg):
        """
        Convert 8 to 7 bytes with additional bytes
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

    def calcCrcTx(self, msg):
        """
        Calc CRC of TX trama
        """
        bytedatrasm = []
        self.crctrasm = self.INITCRC
        for txapp in msg:
            txapp1 = (txapp & 0x0f) | (((txapp & 0x78) ^ 8) * 2)
            bytedatrasm.append(txapp1)
            self.crctrasm = self.calccrc(txapp1, self.crctrasm)
        bytedatrasm.append((self.crctrasm & 0x0f) | (self.crctrasm & 8)*2 | (self.crctrasm & 0x38 ^ 8)*4)
        return bytedatrasm

    def boardReboot(self, board_id):
        """
        Command to board REBOOT (0 for all board in the BUS)
        """
        return [self.BOARD_ADDRESS, self.code['CR_REBOOT'], board_id] # Fa reboor scheda

    def getTypeBoard(self, board_id):
        """
        Ritorna: Tipo Board, Versione board, Versione software
        """
        return [self.BOARD_ADDRESS, self.code['CR_GET_TIPO_BOARD'], board_id] # Get board type

    def readEE(self, board_id, startaddressLs, startaddressMs, nbyte):
        """
        Read bytes of EEPROM
        """
        return [self.BOARD_ADDRESS, self.code['CR_RD_EE'], board_id, startaddressLs, startaddressMs, nbyte] # Read EE

    def writeEE(self, board_id, startaddressLs, startaddressMs, data):
        """
        Write EEPROM bytes
        """
        msg = [self.BOARD_ADDRESS, self.code['CR_WR_EE'], board_id, startaddressLs, startaddressMs] + data # Read EE
        return msg

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

        data = [self.BOARD_ADDRESS, self.CR_WR_OUT, board_id, io_logic, byteopzioni] + data
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

        data = [self.BOARD_ADDRESS, self.CR_RD_IN, board_id, io_logic, byteopzioni] + data
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
        data = [self.BOARD_ADDRESS, self.CR_WR_OUT, board_id, io_logic, byteopzioni] + data
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
        data = [self.BOARD_ADDRESS, self.CR_RD_IN, board_id, io_logic, byteopzioni] + data
        # print("WriteI2C:", data)
        return data

    def readIO(self, board_id, io_logic):
        """
        Read IO status
        """
        data = [self.BOARD_ADDRESS, self.CR_RD_IN, board_id, io_logic, 0]
        # print("ReadIO:", data)
        return data # Read EE

    def initIO(self, board_id, io_logic):
        """
        Init IO of board (read configuration in EEPROM)
        """
        data = [self.BOARD_ADDRESS, self.code['CR_INIT_SINGOLO_IO'], board_id, io_logic]
        return data

    def enableSerial(self, board_id, speed):
        """
        ????
        """
        # Abilita la seriale RS232
        # Byte4
        # b0: (1) Trasmissione su RS232 di cosa il nodo trasmette sul BUS
        # b1: (1) Trasmissione su RS232 di cosa il nodo riceve sul BUS
        # b2: (1) Trasmissione su RS232 dei PING
        data = [self.BOARD_ADDRESS, self.CR_WR_EE, board_id, 4, 0, speed]
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
        data = [self.BOARD_ADDRESS, self.CR_WR_EE, board_id, 3, 0, speed[baudrate]]
        return data

    def setBusBaudrate(self, board_id, baudrate):
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
        data = [self.BOARD_ADDRESS, self.CR_WR_EE, board_id, 2, 0, speed[baudrate]]
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
        From bytes to value Temp, Hum, Press
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

    def resetEE(self, board_id, io_logic=0):
        """
        Mette a 0 gli enable dei vari IO logici.
        Se io_logic=0, disabilita gli i dispositivi da 1 a 24
        """
        TXtrama = []
        if io_logic == 0:
            for x in range(1, 25):
                eels = (x * 32) & 127  # Indirizzo EE ls
                eems = (x * 32) >> 7  # Indirizzo EE ms
                msg = self.writeEE(board_id, eels, eems, [0,0])
                TXtrama.append(msg)
                TXtrama.append(self.initIO(board_id, io_logic))

        else:
            eels = (io_logic * 32) & 127  # Indirizzo EE ls
            eems = (io_logic * 32) >> 7  # Indirizzo EE ms
            msg = self.writeEE(board_id, eels, eems, [0, 0])
            # print(msg)
            TXtrama.append(msg)
            TXtrama.append(self.initIO(board_id, io_logic))
        TXtrama.append(self.boardReboot(board_id))
        return(TXtrama)

    def sendConfiguration(self):
        """
        Make configuration to send to boards
        """

        msg = []
        for bb in self.config:
            print("BB", bb)
            if "BOARD" in bb:  # Seleziona le BOARD
                # print(bb, self.config[bb])
                board = self.config.get(bb)
                idbus = int(bb[5:])
                for b in board:
                    # pprint(board[b])
                    # print("b", b)
                    # if "GENERAL" in b:
                    boardenable = int(board.get('GENERAL')['enable'])
                    boardtype = int(board.get('GENERAL')['boardtype'])
                    boardname = board.get('GENERAL')['name']

                    # print("BOARD", idbus, "ENABLE:", boardenable)
                    if boardenable == 0:
                        print("Configurazione board: BOARD DISABILITATA: %s" %boardname)
                        continue

                    if  not 'GENERAL' in b:
                        message_conf_app = []

                        io_logic = int(board[b]['io_logic'])


                        enable = 0 if not 'enable' in board[b] else int(board.get(b)['enable'])  # Enable
                        print("IO ABILITATI %s: %s" %(enable, io_logic))

                        if not enable:  # Non fa configurazione se enable = 0
                            # print("IO disabilitati:",io_logic)
                            continue



                        if io_logic >= 30:
                            print("Configurazione board ERROR: io_logic non può essere superiore a 29. IO_logic=%s", io_logic)
                            continue

                        pin = 0 if not b in self.iomap[boardtype] else self.iomap[boardtype][b]['pin']
                        if pin:
                            byte0 = self.mapmicro.get(pin)['iomicro']
                        else:
                            byte0 = 0

                        eels = (io_logic * 32) & 127  # Indirizzo EE ls
                        eems = (io_logic * 32) >> 7  # Indirizzo EE ms
                        byte1 = 1 if board.get(b).get('direction') == 'output' else 0

                        io_type = board.get(b).get('io_type')
                        if io_type == 'analog' or io_type == 'temp_atmega':
                            byte1 |= 0b10
                        elif io_type == 'digital':
                            byte1 |= 0b00
                        elif io_type == 'i2c':
                            byte1 |= 0b1000
                            enable = 0 if not 'enable' in board[b] else int(board.get(b)['enable'])  # Enable
                            if enable == 0:
                                byte1 = 0
                        elif io_type == 'onewire':
                            byte1 |= 0b00100
                        elif io_type == 'disable':
                            byte1 |= 0b00100
                        else:
                            print("Configurazione board: ERROR: io_type non riconosciuto. IO: %s" %b, io_type, bb)
                            continue

                        enable = 0 if not 'enable' in board[b] else int(board.get(b)['enable'])  # Enable
                        if enable == 0:
                            byte1 = 0
                        # print("Configurazione board: board:%s, io_logic:%s" %(boardname, io_logic))
                        byte1 |= 0x40 if int(board.get(b)['enable']) == 1 else 0  # Settimo BIT

                        direction = board.get(b).get('direction', 0)


                        if direction == 'input':
                            byte2 = 0 if not 'pullup' in board.get(b) else int(board.get(b)['pullup'])
                            byte3 = 0
                        elif direction == 'output':
                            default_startup_value = int(board.get(b)['default_startup_value'])
                            inverted = 0 if 'inverted' not in board.get(b) else int(board.get(b)['inverted'])
                            byte2 = 127 & (default_startup_value ^ inverted)  # Byte 2: valore default ls
                            byte3 = int(board.get(b)['default_startup_value']) >> 7  # Byte 2: valore default ms
                        elif io_type == 'i2c' or io_type == 'onewire':
                            byte2 = 0
                            byte3 = 0
                        else:
                            byte2 = 0
                            byte3 = 0
                            print("ERROR: DIRECTION su configurazione non riconosciuto. IO: %s" %b)
                            # continue



                        if io_type == 'analog' or io_type == 'digital':
                            byte4 = 0 if not 'n_refresh_on' in board.get(b) else int(board.get(b)['n_refresh_on'])  # Byte 4: rinfreschi rete sui fronti ON
                            byte4 |= 0 if not 'n_refresh_off' in board.get(b) else int(board.get(b)['n_refresh_off']) << 3  # Byte 4: rinfreschi rete sui fronti OFF
                        else:
                            byte4 = 0

                        byte5 = int(board.get(b)['time_refresh']) & 127  # Byte 5: rinfresco periodico ls in decimi di secondo
                        byte6 = int(board.get(b)['time_refresh']) >> 7  # Byte 6: rinfresco periodico ms (14 bit = 16383) (0=sempre, 16383=mai)
                        # print("RINGRESCHI", byte5, byte6)

                        if io_type == 'analog' or io_type == 'digital':
                            byte7 = 0 if not 'filter' in board.get(b) else int(board.get(b)['filter'])
                        else:
                            byte7 = 0

                        message_conf_app.append(self.BOARD_ADDRESS)  # Mio indirizzo IDBUS
                        message_conf_app.append(self.code['CR_WR_EE'])  # Comando scrittura EEPROM, 4 per leggere
                        message_conf_app.append(idbus)  # IDBUS Board destinazione
                        message_conf_app.append(eels)  # Indorizzo scrittura EE ls
                        message_conf_app.append(eems)  # Indorizzo scrittura EE ms
                        message_conf_app.append(byte0)  # Port fisico
                        message_conf_app.append(byte1)  # Definizione input / output
                        message_conf_app.append(byte2)  # Valore default LS
                        message_conf_app.append(byte3)  # Valore default MS
                        message_conf_app.append(byte4)  # rinfreschi rete sui fronti ON / OFF
                        message_conf_app.append(byte5)  # Byte 5: rinfresco periodico ls
                        message_conf_app.append(byte6)  # Byte 6: rinfresco periodico ms
                        message_conf_app.append(byte7)  # Byte 7:  Filtro
                        
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
                        # OR 128 = uscita negata
                        
                        # Ogni uscita con funzione associata ad ingressi digitali puo' avere al massimo 8 ingressi
                        # Ogni uscita con funzione associata ad ingressi analogici puo' avere al massimo 2 ingressi
                        
                        """
                        OFFSET 8: codice funzione
                        """
                        byte8 = 0 if not 'plc_function' in board.get(b) or board.get(b)['plc_function'] == 'disable' else int(board.get(b)['plc_function'])
                        plc = []
                        if byte8:
                                message_conf_app.append(byte8)  # Byte 8:  PLC
                        
                                # OFFSET 31: BYTE con NEGAZIONE ingressi
                                plc.append(0)
                        
                                # OFFSET 30: BYTE PRESET valore default prima che arrivino i dati dalla rete
                                plc.append(0)
                        
                                # OFFSET 29: Numero ingressi per la funzione PLC
                                plc.append(1)
                        
                                linked_board_id_io_logic = [] if not 'linked_board_id_io_logic' in board.get(b) else board.get(b)['linked_board_id_io_logic']
                                if linked_board_id_io_logic:
                                    for plc_bio in linked_board_id_io_logic:
                                        plc_bio = plc_bio.split("-")
                                        # OFFSET 28: BOARD_ID
                                        plc.append(int(plc_bio[0]))
                                        # OFFSET 27: IO_LOGICO
                                        plc.append(int(plc_bio[1]))
                                        print("====>>>>PLB BIO:", plc_bio)
                                        
                                else:
                                    print("BOARD_ID and IO_LOGIC not defined on CONFIGURATION File")
                                        
                                
                        
                                #.....
                                # Se timer, dopo elenco di BOARD_ID e IO_LOGIC, seguono questi parametri:
                                # Modo TIMER:   b0: innesca su fronte ON
                                #               b1: innesca su fronte OFF
                                #               b2: innesco permanente con ingresso a 1
                                #               b3: innesco permanente con ingresso a 0
                                #               b4: innesco se timer già innescato
                                #               b5: somma tempo a timer ad ogni innesco sui fronti
                                #               b6 e b7: 0 0 centesimi di secondo
                                #               b6 e b7: 1 0 decimi di secondo
                                #               b6 e b7: 0 1 secondi
                                #               b6 e b7: 1 1 2.5 secondi a unità
                                # Byte: numero massimo di commutazioni. 0=infinito
                                # Byte: Tempo ON LS
                                # Byte: Tempo ON MS
                                # Byte: Tempo OFF LS
                                # Byte: Tempo OFF MS
                                
                                plclen = len(plc)
                                plc.reverse()
                                
                                plc_EE_start = (io_logic * 32) + 32 - plclen 
                                
                                plc_eels = plc_EE_start & 127  # Indirizzo EE ls
                                plc_eems = plc_EE_start >> 7  # Indirizzo EE ms
                                
                                
                                print("PLC_EE:", idbus, plc_eels, plc_eems, plc)
                                plc_data = self.writeEE(idbus, plc_eels, plc_eems, plc)
                                print("PLC_DATA:", plc_data)
                                msg.append(plc_data)
                                
                        
                        # print("TRAMA CONFIGURAZIONE:             ", message_conf_app)
                        msg.append(message_conf_app)
                        # msg.append(self.initIO(idbus, io_logic))  # iNIt io

                        # Configurazione relativa ai sensori I2C e OneWire
                        if io_type == 'i2c':
                            if b == 'PCA9535':
                                print("==>> Inserisce trama di confgurazione I2C per PCA9535")
                                # msg.append(self.writeEE(idbus, eels + 10, eems, [5, 3, 0x4e, 2, 0x0a, 0xa0]))
                                # msg.append(self.writeEE(idbus, eels + 16, eems, [5, 3, 0x4e, 6, 0, 0])) # Impostare direzione OUT (inizializzazione)
                                # msg.append(self.writeEE(idbus, eels + 22, eems, [5, 3, 0x4e, 2, 0xa0, 0x0a]))
                            elif b == 'BME280':
                                msg.append(self.writeEE(idbus, eels + 10, eems, [3 | self.i2c_const['CONCATENA'], 1 | 8, 0xec, 0xf7]))  # 3|128: 128 per concatenare con prg. successivo), 32 reset +
                                msg.append(self.writeEE(idbus, eels + 14, eems, [2 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 3 | 64, 0xec | 1]))  # 2|64: lettura I2C. 3+64: 64 byte da leggere

                                msg.append(self.writeEE(idbus, eels + 17, eems, [4 | self.i2c_const['CONCATENA'], 3 | 32, 0xec, 0xf2, 0x03]))  # Inizializzazione BME e Oversampling umidità
                                msg.append(self.writeEE(idbus, eels + 22, eems, [4 | self.i2c_const['NON_CONCATENA'], 3, 0xec, 0xf4, 0x8f]))  # Inizializzazione BME temperatura + pressione  (Oversampling)

                            elif b == 'AM2320':
                                print("CONFIGURAZIONE AM2320")
                                msg.append(self.writeEE(idbus, eels + 10, eems, [2 | self.i2c_const['CONCATENA'] | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 3, 0xb8]))  # 3|128: 128 per concatenare con prg. successivo), 32 reset +
                                msg.append(self.writeEE(idbus, eels + 13, eems, [5 | self.i2c_const['CONCATENA'] | self.i2c_const['BYTE_OPZIONI_SCRITTURA'],  3, 0xb8, 0x03, 0x00, 0x04]))
                                # FLAG PAUSA: aggiungere prima del byte opzioni 1 byte (potrebbe essere anche 2 byte a 7 bit) che indica la pausa in decine di uS
                                msg.append(self.writeEE(idbus, eels + 19, eems, [3 | self.i2c_const['FLAG_PAUSA'] | self.i2c_const['BYTE_OPZIONI_LETTURA'], 100, 3 | 64, 0xb9, 0 ]))

                        elif io_type == 'onewire':
                            msg.append(self.writeEE(idbus, eels + 10, eems, [3 | self.i2c_const['CONCATENA'] | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 1, 0xcc, 0x44]))  # num. byte, byte opzioni, campionamento di tutte le sonde, leggi temp.

                            address = board.get(b).get('address')
                            address = [int(x, 16) for x in address]
                            print("ADDRESS ID ONE WIRE:", address)

                            msg.append(self.writeEE(idbus, eels + 14, eems, [11 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 1+72, 0x55] + address +  [0xbe, 0]))  # num. byte, byte opzioni, S/N sonda, ID, 0xbe leggi temp
                        else:
                            # If not I2C or OneWire, set 0, 0 at address 10 and 11.
                            msg.append(self.writeEE(idbus, eels + 10, eems, [0,0]))
                                

                # print("ADD REBOOT")
                # msg.append(self.boardReboot(idbus))
        # msg.append(self.getTypeBoard(5))
        # print("RESET TOTALE")
        msg.append(self.boardReboot(0))
        return msg
# END BUS Class


if __name__ == '__main__':
    print("*" * 20, "START DL485 program", "*" * 20)
    if len(sys.argv) > 1:
        # print(sys.argv)
        if sys.argv[1] == 'w':
            logstate = 1
        elif sys.argv[1] == 'p':
            logstate = 2
        elif sys.argv[1] == 'wp':
            logstate = 3
        else:
            logstate = 0
            print("LOG: w=write to file, p=print, wp=write+print")
            sys.exit()
    else:
        logstate = 0
        print("Nessun argomento specificato all'esecuzione del file. Possibili w, p, wp", end="\n\n")

    b = Bus()  # Istanza la classe P
    log = Log('log.txt', logstate)
    config_file_name = "./config.json"
    b.getJsonConfig(config_file_name)

    bus_baudrate = b.config.get('GENERAL')['bus_baudrate']  # Legge la velocità del BUS
    bus_port = b.config.get('GENERAL')['bus_port']  # Legge la porta del BUS di Raspberry PI
    b.BOARD_ADDRESS = int(b.config.get('GENERAL')['board_address'])  # Legge la porta del BUS di Raspberry PI
    print("BUS_BAUDRATE:%s, BUS_PORT:%s, BOARD_ADDRESS:%s" %(bus_baudrate, bus_port, b.BOARD_ADDRESS))

    ser = b.ser(bus_port, bus_baudrate)  # Setup serial
    TXmsg = []  # Vengono inserite le trame da trasmettere
    b.dictBoardIo()  # Crea il DICT con i valori IO basato sul file di configurazione (solo board attive)
    board_ready = {}

    """ Reset parametri SCHEDE """
    msg = b.resetEE(2, 0)  # Board_id, io_logic. Se io_logic=0, resetta tutti gli IO
    print("CONFIGURATION TRAMA:", msg)
    TXmsg = msg

    """ Configurazione SCHEDE """
    message_conf_app = b.sendConfiguration()  # Set configuration of boards
    TXmsg = message_conf_app  # Configurazione

    """ LOOP """
    oldtime = time.time() - 10  # init oldtime per stampe dizionario con i/o per stampa subito al primo loop

    ping = 0
    while 1:
        nowtime = int(time.time())
        RXbyte = ser.read()
        # print(RXbyte)
        if not RXbyte:  # Monitor serial
            # time.sleep(0.001)
            continue

        for d in RXbyte:
            # print(d)
            RXtrama = b.readSerial(d)
            # print(RXtrama)

            if RXtrama:  # Se arrivata una trama copleta
                now = time.time()
                if len(RXtrama) == 1:
                    pass
                    # print(RXtrama)

                if RXtrama[0] == b.BOARD_ADDRESS - 1:  # E' ora di trasmettere
                    # print("TXmsg", TXmsg)
                    if len(TXmsg):
                        # print("Trama to TX: ", len(TXmsg))
                        msg = TXmsg.pop(0)
                        # print("Trasmetto:", msg)
                        msg = b.eight2seven(msg)
                        # print("MSG:", msg)
                        # print("{:<11} ==>>{:<15}".format('MSG 8 to 7', msg))
                        msg = b.calcCrcTx(msg)
                        # print("MSG:", msg)
                        ser.write(bytes(msg))

                b.labinitric()  # Resetta la coda per nuova ricezione alla fine dei calcoli
                board_ready[RXtrama[0]] = nowtime  # Aggiorna la data di quando è stato ricevuto la trama del nodo

                if len(RXtrama) > 1:  # Mosra solo comunicazioni valide (senza PING)
                    # print(RXtrama)  # Visualizza trama
                    # print(b.code)
                    if RXtrama[1] in b.code:
                        log.write("{:<12} TX {:<18} {} ".format(nowtime, b.code[RXtrama[1]], b.int2hex(RXtrama)))
                        value = b.checkIO(RXtrama[0], RXtrama[2], RXtrama[3:])
                        # print(value)
                        try:
                            # b.status[RXtrama[0]]['io'][RXtrama[2] - 1] = value
                            self.updateIO(self.RXtrama[0], self.RXtrama[2], self.RXtrama[3:])  # Aggiorna DOMOTICZ
                        except:
                            pass

                    elif (RXtrama[1] - 32) in b.code:
                        err = ''
                        if RXtrama[1] == 29:
                            # log.write("EEEEEEEEEEEEEEEEEEEEEEERRROR", RXtrama)
                            err = b.error[RXtrama[2]] if RXtrama[2] in b.error else 'ERRORE NON DEFINITO'
                        log.write("{:<12} RX {:<18} {} {}".format(nowtime, b.code[RXtrama[1] - 32], b.int2hex(RXtrama), err))

            if nowtime - oldtime > 2:
                oldtime = nowtime

                # TXmsg.append(b.readEE(3, 32, 0, 5))  # Read EEPROM
                # TXmsg.append(b.getTypeBoard(5))  # Read Board Type
                # TXmsg.append(b.boardReboot(0))  # Reboot board

                # TXmsg.append(b.writeIO(1, 11, [0]))  # Write IO
                # TXmsg.append(b.writeIO(1, 11, [1]))  # Write IO
                # TXmsg.append(b.writeIO(1, 12, [1]))  # Write IO

                # TXmsg.append(pingCrc)  # Trasmissione PING



                # ********************* I2C comandi su EEPROM **********************
                # --------------------- INIZIO COMANDI PCA9535 --------------------
                # TXmsg.append(b.writeEE(4, 10, 5, [5, 3, 0x4e, 2, 0x0a, 0xa0]))
                # TXmsg.append(b.writeIO(4, 1, [10 | 128]))
                # TXmsg.append(b.writeIO(4, 1, [22 | 128]))

                # TXmsg.append(b.writeEE(4, 16, 5, [5, 3, 0x4e, 2, 0x00, 0xff]))
                # TXmsg.append(b.writeEE(4, 46, 5, [3 + 0x80, 0b01001 + 32, 0xec, 0xfa]))
                # TXmsg.append(b.writeIO(4, 20, [16]))
                # ------------------------- FINE PCA9535 -----------------------------

                # -------------------- INIZIO COMANDI BME 280 --------------------------
                # TXmsg.append(b.writeI2C(2, 7, 3 + 32, [0xec, 0xf2, 0x03]))  # Oversamplig umidità
                # TXmsg.append(b.writeI2C(2, 7, 3, [0xec, 0xf4, 0x8f]))  # Oversampling, normal mode pressione e temperatura
                # TXmsg.append(b.writeI2C(2, 7, 1 | 8, [0xec, 0xf7]))  # Indirizzo del primo indirizzo da leggere. Start senza stop
                # TXmsg.append(b.readI2C(2, 7, 3 | 64, [0xec | 1]))  # Lettura 8 byte
                # -------------------- FINE BME 280 --------------------------

                # -------------------- INIZIO COMANDI AM2320 --------------------------
                # TXmsg.append(b.writeI2C(2, 7, 3 + 32, [0xec, 0xf2, 0x03]))  # Oversamplig umidità
                # TXmsg.append(b.writeI2C(2, 7, 3, [0xec, 0xf4, 0x8f]))  # Oversampling, normal mode pressione e temperatura
                # TXmsg.append(b.writeI2C(2, 7, 1 | 8, [0xec, 0xf7]))  # Indirizzo del primo indirizzo da leggere. Start senza stop
                # TXmsg.append(b.readI2C(2, 7, 3 | 64, [0xec | 1]))  # Lettura 8 byte
                # -------------------- FINE BME 280 --------------------------


                # ------------------------- INIZIO COMANDI DS18B20 -----------------------------
                # TXmsg.append(b.writeOneWire(2, 6, 32))  # Reset Multitask OneWire
                # TXmsg.append(b.readOneWire(2, 6, 1))  # Reset OneWire
                # TXmsg.append(b.readOneWire(2, 6, 1+64, [0x33]))  # Richiesta codice ID OneWire per singola sonda collegata
                # TXmsg.append(b.writeOneWire(2, 6, 1, [0xcc, 0x44]))  # Campionamento temperatura SENZA CODICE
                # TXmsg.append(b.readOneWire(2, 6, 1+16, [0xcc, 0xbe]))  # Richiesta temperatura sonda senza ID (solo una sonda collegata). # Temperatura = (Secondo Byte H * 256 + Primo Byte L) * 0.0625


                # TXmsg.append(b.writeOneWire(2, 6, 1, [0x55, 0x28, 0xff, 0x87, 0x6a, 0xa1, 0x16, 0x04, 0x23, 0x44]))  # Campionamento temperatura sonda con codice ID<
                # TXmsg.append(b.readOneWire(2, 6, 1+16, [0x55, 0x28, 0xff, 0x87, 0x6a, 0xa1, 0x16, 0x04, 0x23, 0xbe]))  # Lettura temperatura senza ID sonda: Reset OneWire + numero byte da leggere

                # TXmsg.append(b.readOneWire(2, 6, 1+16, [0xcc, 0xbe]))  # Richiesta temperatura sonda senza ID (solo una sonda collegata). # Temperatura = (Secondo Byte H * 256 + Primo Byte L) * 0.0625
                # TXmsg.append(b.writeOneWire(2, 6, 1, [0x55, 0x28, 0xff, 0x5f, 0x6b, 0xa1, 0x16, 0x04, 0xcc, 0x44]))  # Campionamento temperatura sonda con codice ID
                # TXmsg.append(b.readOneWire(2, 6, 1+16, [0x55, 0x28, 0xff, 0x5f, 0x6b, 0xa1, 0x16, 0x04, 0xcc, 0xbe]))  # Lettura temperatura senza ID sonda: Reset OneWire + numero byte da leggere

                # Formula per la temperatura: ((secondo byte << 8) + primo byte) * 0.0625
                # ------------------------- FINE DS18B20 -----------------------------



                """
                4 = board id
                52 = indirizzo EE LS IO logico dove scrivere la EE + 10 (offset)
                5 = indirizzo EE MS IO logico
                3 = numero byte dati: b7: 1=concatena con prg. successivo; b6:comando I2C lettura
                3 = byte opzioni
                0xec = indirizzo dispostivo I2C
                0xf4, 0x83 comando oversampling BME280
                """

                #------------------- TSL2561 -----------------------
                # TXmsg.append(b.writeI2C(4, 1, 0b0011, [0x4e, 6, 0, 0])) # Impostare direzione OUT


                # Routine che aggiorna le BOARD presenti sul BUS
                board_to_remove = []
                for k, v in board_ready.items():
                    # log.write(v, nowtime-v, v)
                    if (nowtime - v) > 5:
                        board_to_remove.append(k)
                for k in board_to_remove:
                    del board_ready[k]
                # b.BOARD_ADDRESS = max(list(board_ready.keys())) + 1
                log.write("{:<12} BOARD_READY           {:<18} ".format(int(nowtime), str(list(board_ready.keys()))))
                # log.write("{:<12} BOARD_READY           {:<18},   lenTx:{}, lenTxCrc:{}, ".format(int(nowtime), str(list(board_ready.keys())), len(TXmsg), len(TXmsgCrc) ))
                # log.write("TXcount:",TXcount, "indiceTXtrasm:", indiceTXtrasm, "TXboard:", TXboard, "TXtimeout:", TXtimeout, "TXcode:", TXcode)

                # Stampa i valore di tutti gli IO
                # pprint(b.status)
                b.printStatus()  # Print status of IO

            # log.write("T", nowtime)
            # try:
                # conn, addr = sock.accept()
                # log.write("AA")
            # except:
                # pass

            # try:  # Routine per la Ricezione comandi da django e altro via UDP
                # conn.setblocking(0)
                # data = conn.recv(BUFFER_SIZE)
                # log.write("X", nowtime)
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

            RXtrama = []  # Azzera trama ricezione
            time.sleep(0.0005)  # Delay per non occupare tutta la CPU

    log.write("FINE SCRIPT")
