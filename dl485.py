#!/usr/bin/python3.4
# -*- coding: utf-8 -*-
"""
Class protocol DL485
"""
import sys
import os
print("Working PATH:", os.getcwd())
import serial
from pprint import pprint
import time
import logging
import math
import json
import re
import curses
from struct import unpack, unpack_from
# from TSL2561 import tsl2561_calculate
from TSL2561 import tsl2561_calculate

class Log:
    def __init__(self, file='log.txt', logstate=0):
        self.logstate = logstate
        if self.logstate & 1:
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
         4: "Ricevuto pacchetto nullo",
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
        23: "Indirizzo ricevuto uguale a se stesso",
        24: "OneWire Occupata",
        25: "Lettura numero ingreso fuori range",
        26: "Dimensione pacchetto non conforme",
        27: "Accesso EE oltre limite indirizzo",
        28: "Scrittura numero uscita fuori range",
        29: "Numero parametro fuori range",
        30: "Nodo occupato da ordine precedente",
        31: "Accesso EE sotto spazio EE IO",
        32: "Errore secondo crc",
        33: "1W Timeout"
    }

    device_type_dict = {
        'DS18B20':              {'type_io':'onewire',       'direction':'input',    'dtype':'Temperature',      'pullup':1},
        'AM2320':               {'type_io':'i2c',           'direction':'input',    'dtype':'Temp+Hum',         'pullup':0},
        'BME280':               {'type_io':'i2c',           'direction':'input',    'dtype':'Temp+Hum+Baro',    'pullup':1},
        'BME280_CALIB':         {'type_io':'i2c',           'direction':'input',    'dtype':'Temp+Hum+Baro',    'pullup':1},
        'TSL2561':              {'type_io':'i2c',           'direction':'input',    'dtype':'Illumination',     'pullup':0},
        'VINR1R2':              {'type_io':'analog',        'direction':'input',    'dtype':'Voltage',          'pullup':0},
        'VINKMKA':              {'type_io':'analog',        'direction':'input',    'dtype':'Voltage',          'pullup':0},
        'DIGITAL_OUT':          {'type_io':'digital',       'direction':'output',   'dtype':'Switch',           'pullup':0},
        'DIGITAL_OUT_PWM':      {'type_io':'analog',        'direction':'output',   'dtype':'Voltage',          'pullup':0},
        'DIGITAL_IN':           {'type_io':'digital',       'direction':'input',    'dtype':'Switch',           'pullup':0},
        'DIGITAL_IN_PULLUP':    {'type_io':'digital',       'direction':'input',    'dtype':'Switch',           'pullup':1},
        'ANALOG_IN':            {'type_io':'analog',        'direction':'input',    'dtype':'Switch',           'pullup':0},
        'PSYCHROMETER':         {'type_io':'',              'direction':'input',    'dtype':'Humidity',         'pullup':0},
        'TEMP_ATMEGA':          {'type_io':'temp_atmega',   'direction':'input',    'dtype':'Temperature',      'pullup':0},
        'VIRTUAL':              {'type_io':'discrete',      'direction':'output',   'dtype':'Temperature',      'pullup':0},
    }

    i2c_const = {  # Const I2C
        'CONCATENA': 128,
        'NON_CONCATENA': 0,
        'BYTE_OPZIONI_LETTURA': 64,
        'BYTE_OPZIONI_SCRITTURA': 0,
        # 'BYTE_OPZIONI_RESET_I2C': ???? ,
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
         1: {'name': 'PD3',         'fisic_io':    3,    'function': ['I', 'O', 'P']},
         2: {'name': 'PD4',         'fisic_io':    4,    'function': ['I', 'O']},
         3: {'name': 'PE0',         'fisic_io':   21,    'function': ['I', 'O', 'SDA']},
         4: {'name': 'VCC',         'fisic_io':   99,    'function': ['VCC']},
         5: {'name': 'GND',         'fisic_io':   99,    'function': ['GND']},
         6: {'name': 'PE1',         'fisic_io':   22,    'function': ['I', 'O', 'A']},
         7: {'name': 'XTAL1',       'fisic_io':   99,    'function': ['X']},
         8: {'name': 'XTAL2',       'fisic_io':   99,    'function': ['X']},
         9: {'name': 'PD5',         'fisic_io':    5,    'function': ['PROG']},
        10: {'name': 'PD6',         'fisic_io':    6,    'function': ['LED_TX']},
        11: {'name': 'PD7',         'fisic_io':    7,    'function': ['LR']},
        12: {'name': 'PB0',         'fisic_io':    8,    'function': ['I', 'O']},
        13: {'name': 'PB1',         'fisic_io':    9,    'function': ['I', 'O', 'P']},
        14: {'name': 'PB2',         'fisic_io':   10,    'function': ['I', 'O', 'P']},
        15: {'name': 'PB3',         'fisic_io':   11,    'function': ['I', 'O', 'MO']},
        16: {'name': 'PB4',         'fisic_io':   12,    'function': ['I', 'O', 'MI']},
        17: {'name': 'PB5',         'fisic_io':   13,    'function': ['I', 'O', 'SC']},
        18: {'name': 'AVCC',        'fisic_io':   99,    'function': ['VCC']},
        19: {'name': 'ADC6 PE2',    'fisic_io':   23,    'function': []},
        20: {'name': 'AREF',        'fisic_io':   99,    'function': []},
        21: {'name': 'GND',         'fisic_io':   99,    'function': []},
        22: {'name': 'ADC7 PE3',    'fisic_io':   24,    'function': []},
        23: {'name': 'PC0',         'fisic_io':   14,    'function': []},
        24: {'name': 'PC1',         'fisic_io':   15,    'function': []},
        25: {'name': 'PC2',         'fisic_io':   16,    'function': []},
        26: {'name': 'PC3',         'fisic_io':   17,    'function': []},
        27: {'name': 'PC4',         'fisic_io':   18,    'function': []},
        28: {'name': 'PC5',         'fisic_io':   19,    'function': []},
        29: {'name': 'RST',         'fisic_io':   99,    'function': []},
        30: {'name': 'PD0',         'fisic_io':    0,    'function': []},
        31: {'name': 'PD1',         'fisic_io':    1,    'function': ['TX_BUS']},
        32: {'name': 'PD2',         'fisic_io':    2,    'function': ['']},
        33: {'name': 'BME280',      'fisic_io':   18,    'function': []},
        34: {'name': 'BME280',      'fisic_io':   18,    'function': []},
        35: {'name': 'DS18B20',     'fisic_io':    3,    'function': []},
        37: {'name': 'TEMP_ATMEGA', 'fisic_io':   25,    'function': ['AT']},
        38: {'name': 'AM2320',      'fisic_io':   18,    'function': ['AM2320']},
        39: {'name': 'BME280_CALIB','fisic_io':   18,    'function': []},
        41: {'name': 'VIRT1',       'fisic_io':   40,    'function': ['VIRTUAL1']},
    }

    iomap = { # MAP IO of board in base al tipoboard 1,2,3,4,5
        1: {  # DL485M
            'PB0':          {'pin':   12,  'name':     'IO4'},
            'PB1':          {'pin':   13,  'name':     'IO5'},
            'PB2':          {'pin':   14,  'name':     'IO8'},
            'PB3':          {'pin':   15,  'name':     'IO15'},
            'PB4':          {'pin':   16,  'name':     'IO13'},
            'PB5':          {'pin':   17,  'name':     'IO14'},
            'PD3':          {'pin':    1,  'name':     'IO6'},
            'PD4':          {'pin':    2,  'name':     'IO7'},
            'PC0':          {'pin':   23,  'name':     'IO9'},
            'PC1':          {'pin':   24,  'name':     'IO10'},
            'PC2':          {'pin':   25,  'name':     'IO11'},
            'PC3':          {'pin':   26,  'name':     'IO12'},
            'PC4':          {'pin':   27,  'name':     'IO11'},
            'PC5':          {'pin':   28,  'name':     'IO12'},
            'PE0':          {'pin':    3,  'name':     'SDA'},
            'PE1':          {'pin':    6,  'name':     ''},
            'PE2':          {'pin':   19,  'name':     ''},
            'VIN':          {'pin':   22,  'name':     'VIN'},
            'PCA9535':      {'pin':   27,  'name':     'PCA9535'},
            'BME280':       {'pin':   27,  'name':     'BME280'},
            'BME280_CALIB': {'pin':   27,  'name':     'BME280_CALIB'},
            'BME280B':      {'pin':   27,  'name':     'BME280'},
            'AM2320':       {'pin':   27,  'name':     'AM2320'},
            'TSL2561':      {'pin':   27,  'name':     'TSL2561'},
            'DS18B20-1':    {'pin':   35,  'name':     'DS18B20'},
            'DS18B20-2':    {'pin':   35,  'name':     'DS18B20'},
            'DS18B20-3':    {'pin':   35,  'name':     'DS18B20'},
            'DS18B20-4':    {'pin':   35,  'name':     'DS18B20'},
            'DS18B20-5':    {'pin':   35,  'name':     'DS18B20'},
            'DS18B20-6':    {'pin':   35,  'name':     'DS18B20'},
            'DS18B20-7':    {'pin':   35,  'name':     'DS18B20'},
            'TEMP_ATMEGA':  {'pin':   37,  'name':     'TEMP_ATMEGA'},
            'DS18B20-6':    {'pin':   35,  'name':     'DS18B20'},
            'VIRT1':        {'pin':   41,  'name':     'VIRT1'},
            'VIRT2':        {'pin':   41,  'name':     'VIRT2'},
            'VIRT3':        {'pin':   41,  'name':     'VIRT3'},
            'VIRT4':        {'pin':   41,  'name':     'VIRT4'},
            'VIRT5':        {'pin':   41,  'name':     'VIRT5'},
            'VIRT6':        {'pin':   41,  'name':     'VIRT6'},
            'VIRT7':        {'pin':   41,  'name':     'VIRT7'},
            'VIRT8':        {'pin':   41,  'name':     'VIRT8'},
            'VIRT9':        {'pin':   41,  'name':     'VIRT9'},
            'I2C1':         {'pin':   27,  'name':     'I2C1'},
            'I2C2':         {'pin':   27,  'name':     'I2C2'},
            'I2C3':         {'pin':   27,  'name':     'I2C3'},
            'I2C4':         {'pin':   27,  'name':     'I2C4'},
            'I2C5':         {'pin':   27,  'name':     'I2C5'},
            'I2C6':         {'pin':   27,  'name':     'I2C6'},
            'I2C7':         {'pin':   27,  'name':     'I2C7'},
            'I2C8':         {'pin':   27,  'name':     'I2C8'},
            'I2C9':         {'pin':   27,  'name':     'I2C9'},            
        },

        2: {  # DL485B
            'IO1':          {'pin':   23,  'name':     'IO1'},
            'IO2':          {'pin':   24,  'name':     'IO2'},
            'IO3':          {'pin':   25,  'name':     'IO3'},
            'IO4':          {'pin':   26,  'name':     'IO4'},
            'OUT1':         {'pin':    3,  'name':     'RELE1'},
            'OUT2':         {'pin':    2,  'name':     'RELE2'},
            'OUT3':         {'pin':    1,  'name':     'RELE3'},
            'VIN':          {'pin':   22,  'name':     'VIN'},
            'SDA':          {'pin':   27,  'name':     'SDA'},
            'SCL':          {'pin':   28,  'name':     'SCL'},
            'PCA9535':      {'pin':    0,  'name':     'PCA9535'},
            'BME280A':      {'pin':    0,  'name':     'BME280'},
            'BME280B':      {'pin':    0,  'name':     'BME280'},
            'BME280_CALIB': {'pin':   27,  'name':     'BME280_CALIB'},
            'TSL2561':      {'pin':    0,  'name':     'TSL2561'},
            'DS18B20':      {'pin':   35,  'name':     'DS18B20'},
            'TEMP_ATMEGA':  {'pin':   37,  'name':     'TEMP_ATMEGA'},
            'VIRT1':        {'pin':   41,  'name':     'VIRT1'},
            'VIRT2':        {'pin':   41,  'name':     'VIRT2'},
            'VIRT3':        {'pin':   41,  'name':     'VIRT3'},
            'VIRT4':        {'pin':   41,  'name':     'VIRT4'},
            'VIRT5':        {'pin':   41,  'name':     'VIRT5'},
            'VIRT6':        {'pin':   41,  'name':     'VIRT6'},
            'VIRT7':        {'pin':   41,  'name':     'VIRT7'},
            'VIRT8':        {'pin':   41,  'name':     'VIRT8'},
            'VIRT9':        {'pin':   41,  'name':     'VIRT9'},
            'I2C1':         {'pin':   27,  'name':     'I2C1'},
            'I2C2':         {'pin':   27,  'name':     'I2C2'},
            'I2C3':         {'pin':   27,  'name':     'I2C3'},
            'I2C4':         {'pin':   27,  'name':     'I2C4'},
            'I2C5':         {'pin':   27,  'name':     'I2C5'},
            'I2C6':         {'pin':   27,  'name':     'I2C6'},
            'I2C7':         {'pin':   27,  'name':     'I2C7'},
            'I2C8':         {'pin':   27,  'name':     'I2C8'},
            'I2C9':         {'pin':   27,  'name':     'I2C9'},
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
            'BME280':       {'pin':   27},
            'BME280B':      {'pin':   0},
            'BME280_CALIB': {'pin':  27,  'name':      'BME280_CALIB'},
            'AM2320':       {'pin':   0},
            'TSL2561':      {'pin':   27},
            'VIRT1':        {'pin':   41,  'name':     'VIRT1'},
            'VIRT2':        {'pin':   41,  'name':     'VIRT2'},
            'VIRT3':        {'pin':   41,  'name':     'VIRT3'},
            'VIRT4':        {'pin':   41,  'name':     'VIRT4'},
            'VIRT5':        {'pin':   41,  'name':     'VIRT5'},
            'VIRT6':        {'pin':   41,  'name':     'VIRT6'},
            'VIRT7':        {'pin':   41,  'name':     'VIRT7'},
            'VIRT8':        {'pin':   41,  'name':     'VIRT8'},
            'VIRT9':        {'pin':   41,  'name':     'VIRT9'},
            'I2C1':         {'pin':   27,  'name':     'I2C1'},
            'I2C2':         {'pin':   27,  'name':     'I2C2'},
            'I2C3':         {'pin':   27,  'name':     'I2C3'},
            'I2C4':         {'pin':   27,  'name':     'I2C4'},
            'I2C5':         {'pin':   27,  'name':     'I2C5'},
            'I2C6':         {'pin':   27,  'name':     'I2C6'},
            'I2C7':         {'pin':   27,  'name':     'I2C7'},
            'I2C8':         {'pin':   27,  'name':     'I2C8'},
            'I2C9':         {'pin':   27,  'name':     'I2C9'},
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
            'BME280':       {'pin':  27,  'name':      'BME280'},
            'BME280_CALIB': {'pin':  27,  'name':      'BME280_CALIB'},
            'BME280A':      {'pin':   0,  'name':      'BME280A'},
            'TSL2561':      {'pin':  27,  'name':      'TSL2561'},
            'DS18B20':      {'pin':  35,  'name':      'DS18B20'},
            'TEMP_ATMEGA':  {'pin':  37,  'name':      'VIRT1'},
            'VIRT1':        {'pin':  41,  'name':      'VIRT1'},
            'VIRT2':        {'pin':  41,  'name':      'VIRT2'},
            'VIRT3':        {'pin':  41,  'name':      'VIRT3'},
            'VIRT4':        {'pin':  41,  'name':      'VIRT4'},
            'VIRT5':        {'pin':  41,  'name':      'VIRT5'},
            'VIRT6':        {'pin':  41,  'name':      'VIRT6'},
            'VIRT7':        {'pin':  41,  'name':      'VIRT7'},
            'VIRT8':        {'pin':  41,  'name':      'VIRT8'},
            'VIRT9':        {'pin':  41,  'name':      'VIRT9'},
            'I2C1':         {'pin':  27,  'name':      'I2C1'},
            'I2C2':         {'pin':  27,  'name':      'I2C2'},
            'I2C3':         {'pin':  27,  'name':      'I2C3'},
            'I2C4':         {'pin':  27,  'name':      'I2C4'},
            'I2C5':         {'pin':  27,  'name':      'I2C5'},
            'I2C6':         {'pin':  27,  'name':      'I2C6'},
            'I2C7':         {'pin':  27,  'name':      'I2C7'},
            'I2C8':         {'pin':  27,  'name':      'I2C8'},
            'I2C9':         {'pin':  27,  'name':      'I2C9'},
        },
    }

    def __init__(self, config_file_name, logstate=0):
        self.buffricnlung = 0  # Lenght RX buffer
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
        self.poweroff_voltage_setup = 10  # Time to make shutdown for unvervoltage limit
        self.poweroff_voltage_counter = self.poweroff_voltage_setup
        self.poweron_linked = 0
        self.getJsonConfig(config_file_name)
        self.BOARD_ADDRESS = int(self.config['GENERAL_NET']['board_address'])  # Legge ID assegnato a Raspberry PI per accedere al Bus
        self.MAX_BOARD_ADDRESS = int(self.config['GENERAL_NET']['max_board_address'])  # Legge ID assegnato a Raspberry PI per accedere al Bus
        self.dictBoardIo()  # Crea il DICT con i valori IO basato sul file di configurazione (solo boards attive)
        self.bus_baudrate = int(self.config['GENERAL_NET']['bus_baudrate'])  # Legge la velocità del BUS
        self.bus_port = self.config['GENERAL_NET']['bus_port']  # Legge la porta del BUS di Raspberry PI
        self.TIME_PRINT_LOG = 6  # intervallo di tempo in secondi per la stampa periodica del log a schermo
        self.nowtime = self.oldtime = 0
        self.RXtrama = []
        self.TXmsg = []  # Lista che contiene le liste da trasmettere sul BUS
        self.board_ready = {}
        self.BUFF_MSG_TX = {} # dizionario dei messaggi trasmessi indicizzato secondo indirizzo destinatario
        self.NLOOPTIMEOUT = 4  # numero di giri del loop dopo i quali si ritrasmettera il messaggio
        self.log = Log('log.txt', logstate)  # Instazia la classe Log
        self.Connection = self.ser(self.bus_port, self.bus_baudrate)  # Setup serial
        self.ping = self.ping()  # init variabile di appoggio con ping di questo nodo
        self.BME = {}


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
                board_id = int(b[5:])
                board_type = int(self.config[b]['GENERAL_BOARD']['board_type'])
                name = self.config[b]['GENERAL_BOARD']['name']
                self.status[board_id] = {}
                self.status[board_id]['board_type'] = board_type
                self.status[board_id]['name'] = name
                try:
                    self.status[board_id]['io'] = [0] * len(self.iomap[board_type])
                    self.status[board_id]['boardtypename'] = self.config['TYPEB']["%s" %board_type]
                except:
                    print("BOARD TYPE %s non esistente" %board_type)
                    sys.exit()

                board_enable = 0
                for bb in self.config[b]:
                    if 'GENERAL_BOARD' in bb:
                        board_enable = self.config[b][bb]['enable']  # Board enable
                        board_type = self.config[b][bb]['board_type']
                        overwrite_text = self.config[b][bb].get('overwrite_text', 0) # Overtwrite Name and Description of Domoticz device with config.json
                        # pprint(self.config[b][bb])
                        if not board_enable:
                            print("BOARD DISABILItata", b)


                for bb in self.config[b]:
                    #print(bb)
                    # sys.exit()
                    if not 'GENERAL_BOARD' in bb:
                        enable = self.config[b][bb].get('enable', 0)
                        if not enable:
                            print("IO DISABILITATO", self.config[b][bb].get('logic_io', 0))
                            continue

                        logic_io = int(self.config[b][bb].get('logic_io', 0))
                        if not logic_io:
                            print("LOGIC_IO non impostato, boardid=",b, bb)
                            sys.exit()

                        if not board_id in self.mapiotype: self.mapiotype[board_id] = {}

                        inverted = int(self.config[b][bb].get('inverted', 0))
                        default_startup_value = self.config[b][bb].get('default_startup_value', 0)

                        if 'device_type' in self.config[b][bb]:
                            device_type = self.config[b][bb]['device_type']
                        else:
                            print("DEVICE_TYPE NON DEFINITO IN FILE JSON: board_id: %s - logic_io: %s - io_name: %s" %(b, logic_io, bb))
                            print("----------------------------\nVALORI AMMESSI PER device_type su FILE JSON.\nValori validi:\n")
                            for k in self.device_type_dict.keys():
                                print(k)
                            sys.exit()

                        try:
                            pin = self.iomap[board_type][bb]['pin']
                        except:
                            print("NOME LABEL {} NON TROVATO NELLA DEFINIZIONE DELLA BOARD TIPO: {}:".format(bb, board_type), self.iomap[board_type])
                            pin = 0

                        if pin>0:
                            try:
                                fisic_io = self.mapmicro[self.iomap[board_type][bb]['pin']]['fisic_io']
                            except:
                                
                                fisic_io = 99
                        else:
                            fisic_io = 99


                        direction = self.device_type_dict[device_type].get('direction')
                        if not direction:
                            print("VALORI AMMESSI: ", self.device_type_dict[device_type])
                            raise("ERROR: direcrtion NOT DEFINE!!!")

                        self.mapiotype[board_id][logic_io] = {
                            'board_enable': board_enable, # Abilitazione scheda
                            'board_type': board_type, # Tipo scheda
                            'default_startup_filter_value': int(self.config[b][bb].get('default_startup_filter_value', 0)), # 0 o 1
                            'default_startup_value': default_startup_value,  # Valore di default allo startup
                            'description': self.config[b][bb].get('description', 'NO description'),  # Descrizione IO
                            'device_address': self.config[b][bb].get('address', []),  # Address of I2C / Onewire (serial number for DS18B20)
                            'device_type': device_type, # Tipo di device collegato al PIN del micro
                            'direction': direction,  # Input / Output
                            'direction_val': 1 if direction == 'output' else 0,  # 1=Output, 0=Input (how arduino)
                            'dtype': self.config[b][bb].get('dtype', self.device_type_dict[device_type].get('dtype', 'Switch')),  # Domoticz Device
                            'enable': enable,
                            'filter': int(self.config[b][bb].get('filter', 20)),  # For digital input (Anti-bounce filter)
                            'fisic_io': fisic_io,  # PIN address od micro
                            'inverted': inverted,  # Logic Invert of IO
                            'kadd': self.config[b][bb].get('kadd', 0),
                            'kmul': self.config[b][bb].get('kmul', 1),
                            'logic_io': logic_io,
                            'n_refresh_off': int(self.config[b][bb].get('n_refresh_off', 1)),
                            'n_refresh_on': int(self.config[b][bb].get('n_refresh_on', 1)),
                            'name': self.config[b][bb].get('name', 'NO Name'),
                            'logic_io_calibration': self.config[b][bb].get('logic_io_calibration', 0),
                            'altitude': int(self.config[b][bb].get('altitude', 0)),  # OFFSET altitudine
                            'offset_pression': int(self.config[b][bb].get('offset_pression', 0)),  # OFFSET pression
                            'round_pression': int(self.config[b][bb].get('round_pression', 0)),
                            'offset_temperature': int(self.config[b][bb].get('offset_temperature', 0)),  # OFFSET temperature
                            'round_temperature': int(self.config[b][bb].get('round_temperature', 1)),
                            'offset_humidity': int(self.config[b][bb].get('offset_humidity', 0)),  # OFFSET temperature
                            'round_humidity': int(self.config[b][bb].get('round_humidity', 0)),
                            'lux_gain': int(self.config[b][bb].get('lux_gain', 0)),
                            'lux_integration': int(self.config[b][bb].get('lux_integration', 0)),
                            'only_fronte_off': int(self.config[b][bb].get('only_fronte_off', 0)),
                            'only_fronte_on': int(self.config[b][bb].get('only_fronte_on', 0)),
                            'overwrite_text': overwrite_text,
                            'pin_label': bb,
                            'pin': pin,
                            'plc_counter_timeout': int(self.config[b][bb].get('plc_counter_timeout', 0)),
                            'plc_delay_off_on': int(self.config[b][bb].get('plc_delay_off_on', 0)),
                            'plc_delay_on_off': int(self.config[b][bb].get('plc_delay_on_off', 0)),
                            'plc_function': self.config[b][bb].get('plc_function', 'disable'),
                            'plc_linked_board_id_logic_io': self.config[b][bb].get('plc_linked_board_id_logic_io', []),
                            'plc_byte_list_io': [],
                            'plc_params': self.config[b][bb].get('plc_params', 0),
                            'plc_time_off': int(self.config[b][bb].get('plc_time_off', 0)),
                            'plc_time_on': int(self.config[b][bb].get('plc_time_on', 0)),
                            'plc_tmax_on': int(self.config[b][bb].get('plc_tmax_on', 65535)),
                            'plc_counter_filter': self.config[b][bb].get('plc_counter_filter', 0),
                            'plc_counter_min_period_time': int(self.config[b][bb].get('plc_counter_min_period_time', 0)),
                            'plc_counter_mode': int(self.config[b][bb].get('plc_counter_mode', 0)),
                            'plc_time_unit': float(self.config[b][bb].get('plc_time_unit', 1)), # default 1 secondo
                            'plc_timer_n_transitions': int(self.config[b][bb].get('plc_timer_n_transitions', 0)),
                            'plc_preset_input': int(self.config[b][bb].get('plc_preset_input', 0)),
                            'plc_mode_timer': int(self.config[b][bb].get('plc_mode_timer', 0)),
                            'plc_xor_input': 0,
                            'power_on_timeout' : int(self.config[b][bb].get('power_on_timeout',0)) ,
                            'power_on_tmin_off' : int(self.config[b][bb].get('power_on_tmin_off', 0)),
                            'power_on_voltage_off' : float(self.config[b][bb].get('power_on_voltage_off', 0)),
                            'power_on_voltage_on' : float(self.config[b][bb].get('power_on_voltage_on', 0)),
                            'powermeter_k': int(self.config[b][bb].get('powermeter_k', 0)),
                            'pullup': self.config[b][bb].get('pullup', self.device_type_dict[device_type].get('pullup', 0)),
                            'rgnd': int(self.config[b][bb].get('rgnd', 100000)),
                            'rvcc': int(self.config[b][bb].get('rvcc', 1)),
                            'time_refresh': int(self.config[b][bb].get('time_refresh', 3000)),
                            'type_io': self.device_type_dict[device_type].get('type_io'),
                            'write_ee': self.config[b][bb].get('write_ee', []),

                        }

                        # print(self.mapiotype[board_id][logic_io]['plc_linked_board_id_logic_io'])
                        app=[]
                        plc_xor_input = 0
                        plc_byte_list_io = []
                        for x in self.mapiotype[board_id][logic_io]['plc_linked_board_id_logic_io']:
                            xx=x.split("-")
                            if xx[0][0] == '!':  # sistema la negazione degli ingressi
                                xx[0] = xx[0][1:]
                                plc_xor_input = plc_xor_input * 2 + 1
                            else:
                                plc_xor_input = plc_xor_input * 2

                            if "*" in xx[0]:
                                xx[0] = board_id
                            plc_byte_list_io.append(int(xx[0]))
                            plc_byte_list_io.append(int(xx[1]))
                            app1 = '%s-%s' %(xx[0], xx[1])
                            app.append(app1)
                            if app1 not in self.mapproc: #
                                self.mapproc[app1] = {}
                            self.mapproc[app1] = {'board_id': board_id, 'logic_io': logic_io}
                        self.mapiotype[board_id][logic_io]['plc_linked_board_id_logic_io'] = app
                        self.mapiotype[board_id][logic_io]['plc_xor_input'] = plc_xor_input
                        self.mapiotype[board_id][logic_io]['plc_byte_list_io'] = plc_byte_list_io

                        # print(self.mapiotype[board_id][logic_io]['plc_linked_board_id_logic_io'],self.mapiotype[board_id][logic_io]['plc_xor_input'])

        # pprint(self.mapproc)

    def make_inverted(self, board_id, logic_io, value):
        """
        Invert IO value. To use if not PLC function on board
        """
        if not board_id in self.mapiotype or not logic_io in self.mapiotype[board_id]:
            return 0
        inverted = self.mapiotype[board_id][logic_io]['inverted']
        if inverted:
            value = 1 - value & 1
            self.status[board_id]['io'][logic_io - 1] = value  # Valore corrente IO
        # print("value2", value)
        return value

    def calcCrcDS(self, b, crc):
        """
        Calc CRC of DS18xxx
        """
        a = 0xff00 | b
        while 1:
            crc = ((((crc ^ a) & 1) * 280) ^ crc) // 2
            a = a // 2
            if (a <= 255):
                return crc

    def ADC_value(self, VIN, rvcc, rgnd):
        """
        Dato il valore della tensione e le resistenze del partitore, ricavo la tensione in ingresso ADC del micro
        """
        try:
            value = VIN / (rvcc + rgnd) * rgnd * 930.0
            return round(value)
        except:
            print("ERROR ADC_value", VIN, rvcc, rgnd)
            return 0

    def byteLSMS2uint(self, byteLS, byteMS):
        return byteLS + (byteMS * 256)

    def byteLSMS2int(self, byteLS, byteMS):
        if byteMS > 127:
            return -32768 + (byteLS + ((byteMS - 128) * 256))
        return byteLS + (byteMS * 256)

    def byte2signed(self, byte):
        if byte > 127:
            return -128 + byte

        return byte

    def calculate(self, board_id, logic_io, value):
        """
        Ritorna il valore calcolato a seconda del tipo e del dispositivo connesso:
            Temperature:
                DS18B20         -> Temp
                BME280          -> Temp + Hum + Bar
                BME280_CALIB    -> Calibrazione BME280
                ATMEGA CHIP     -> Temp
                AM2320          -> Temp + Hum
                TSL2561         -> Light
            Voltage:
                VINR1R2
                VINKMKA
                Power_on
            Digital:
                Digital input
            PowerMeter
        """
        # print("CALCULATE: board_id: %s, logic_io: %s, value: %s" %(board_id, logic_io, value))

        if board_id in self.mapiotype and logic_io in self.mapiotype[board_id]:
            kmul = self.mapiotype[board_id][logic_io]['kmul']
            kadd = self.mapiotype[board_id][logic_io]['kadd']

            adjust = lambda value : (value * kmul) + kadd # Funzione che aggiusta il risultato

            type_io = self.mapiotype[board_id][logic_io]['type_io']
            device_type = self.mapiotype[board_id][logic_io]['device_type']
            plc_function = self.mapiotype[board_id][logic_io]['plc_function']

            # print("board_id: {:<5} logic_io: {:<5} device_type: {:<25} type_io: {:<25} kmul: {:<10} kadd: {:<10} plc_function: {:<10}"
            #     .format(board_id, logic_io, device_type, type_io, kmul, kadd, plc_function))

            if device_type == 'DS18B20':
                # print(">>>>>>>>>>>>>>>>>>>>>>>>><<DS18B20", value)
                if len(value) < 9:
                    return None
                crc = 0
                for x in value[0:8]:
                    crc = self.calcCrcDS(x, crc)
                if crc == value[8]:
                    value = ((value[1] << 8) + value[0]) * 0.0625
                    if value == 85: return None

                        # print("****************",value);
                    #print(value)


                    bio = '%s-%s' %(board_id, logic_io)
                    if bio in self.mapproc:
                        # print("DS18B20 LINKED BOARD", bio, self.mapproc[bio])
                        board_id_linked = self.mapproc[bio]["board_id"]
                        logic_io_linked = self.mapproc[bio]["logic_io"]
                        device_type_linked = self.mapiotype[board_id_linked][logic_io_linked]['device_type']
                        if device_type_linked =="PSYCHROMETER":
                            print("PSYCHROMETER",self.mapiotype[board_id_linked][logic_io_linked]["plc_linked_board_id_logic_io"])
                            io_linked = self.mapiotype[board_id_linked][logic_io_linked]["plc_linked_board_id_logic_io"]
                            t1 = io_linked[0].split("-")
                            t2 = io_linked[1].split("-")
                            temp_umido = self.status[int(t1[0])]['io'][int(t1[1])-1]
                            temp_secco = self.status[int(t2[0])]['io'][int(t2[1])-1]
                            if temp_umido and temp_secco:
                                # print(device_type_linked,io_linked,temp_umido,temp_secco)

                                pressione_vapore_saturo_temperatura_sensore_asciutto = 6.11 * 10 ** ((7.5 * temp_secco)/(237.7 + temp_secco))
                                pressione_vapore_saturo_temperatura_sensore_umido = 6.11 * 10 ** ((7.5 * temp_umido)/(237.7 + temp_umido))
                                altezza = 100
                                pressione_approssimata_all_altezza = (0.9877 ** (altezza/100)) * 1013.25

                                pressione_vapore_aria_umida =  pressione_vapore_saturo_temperatura_sensore_umido - (1005/(2.5*0.622*10**6))*pressione_approssimata_all_altezza*(temp_secco-temp_umido)

                                correzione_strumentale = pressione_vapore_aria_umida*(1-(temp_secco-temp_umido)/(temp_secco+50/(temp_secco+10**-10)))
                                umidita_relativa_percentuale = (correzione_strumentale / pressione_vapore_saturo_temperatura_sensore_asciutto) * 100
                                if umidita_relativa_percentuale > 100:
                                    print("PSYCHROMETER WARNING: T_umido > T_secco. Set umidità=100")
                                    umidita_relativa_percentuale = 100
                                elif umidita_relativa_percentuale < 0:
                                    print("PSYCHROMETER WARNING: Umidità < 0,  Set umidità=0")
                                    umidita_relativa_percentuale = 0
                                umidita_specifica_alla_saturazione = 0.622 * pressione_vapore_saturo_temperatura_sensore_asciutto / pressione_approssimata_all_altezza
                                # umidita_specifica = umidita_relativa_percentuale*umidita_specifica_alla_saturazione / 100
                                print("PSYCHROMETER HUMIDITY: {}".format(round(umidita_relativa_percentuale, 1)))
                                self.status[board_id_linked]['io'][logic_io_linked - 1] = round(umidita_relativa_percentuale, 1)
                            else:
                                print('PSYCHROMETER ERROR: Temp1 or Temp2 have None value')
                    value = round((((value * kmul) + kadd)+ self.mapiotype[board_id][logic_io]['offset_temperature']), self.mapiotype[board_id][logic_io]['round_temperature'])
                    if self.mapiotype[board_id][logic_io]['round_temperature'] == 0:
                        return int(value)
                    return value
                else:
                    # print("=====>>>>> Errore CRC DS", ((value[1] << 8) + value[0]) * 0.0625)
                    return None

            elif plc_function == 'powermeter' :
                # print(plc_function, value)
                value = value[0] + (value[1] * 256)
                # return (value * kmul) + kadd
                return adjust(value)

            elif type_io == 'digital' and plc_function == 'time_meter' :
                # print(plc_function, value)
                return value[0] + (value[1] * 256)      

            elif plc_function in ['counter_up', 'counter_dw', 'counter_up_dw'] :
                # print(plc_function, value)
                flag_signed = self.mapiotype[board_id][logic_io]['plc_counter_mode'] & 2
                value = value[0] + (value[1] * 256)
                if flag_signed:
                    if value >= 32768:
                        value -= 65536 
                return value

            elif type_io == 'analog' and device_type == 'ANALOG_IN':
                if len(value) >= 2: # Attenzione: lasciare  altrimenti se si passa dalla configurazione DIGITAL_IN in ANALOG_IN, puo' dare errore
                    return value[0] + (value[1] * 256)
                return 0

            elif device_type == 'BME280_CALIB':
                bme_key = '{}-{}'.format(board_id, logic_io)

                if bme_key not in self.BME:
                    self.BME[bme_key] = {}

                if len(value) == 26: # value from 0x88 to 0xA1
                    # print("CALIBRAZIONE BME--->>>>>", value)
                    # [101, 109, 65, 103, 50, 0, 54, 146, 12, 214, 208, 11, 9, 32, 56, 255, 249, 255, 172, 38, 10, 216, 189, 16, 0, 75]
                    
                    flag_ok=True

                    if self.BME[bme_key].get('dig_T1') != self.byteLSMS2uint(value[0], value[1]): 
                        flag_ok = False
                        self.BME[bme_key]['dig_T1'] = self.byteLSMS2uint(value[0], value[1]) #  0x88
                    
                    if self.BME[bme_key].get('dig_T2') != self.byteLSMS2int(value[2], value[3]): 
                        flag_ok = False
                        self.BME[bme_key]['dig_T2'] = self.byteLSMS2int(value[2], value[3]) #  0x8A

                    if self.BME[bme_key].get('dig_T3') != self.byteLSMS2int(value[4], value[5]): 
                        flag_ok = False
                        self.BME[bme_key]['dig_T3'] = self.byteLSMS2int(value[4], value[5]) #  0x8C

                    if self.BME[bme_key].get('dig_P1') != self.byteLSMS2uint(value[6], value[7]): #  0x8E: 
                        flag_ok = False
                        self.BME[bme_key]['dig_P1'] = self.byteLSMS2uint(value[6], value[7]) #  0x8E
                    
                    if self.BME[bme_key].get('dig_P2') != self.byteLSMS2int(value[8], value[9]): #  0x90 
                        flag_ok = False                    
                        self.BME[bme_key]['dig_P2'] = self.byteLSMS2int(value[8], value[9]) #  0x90
                    
                    if self.BME[bme_key].get('dig_P3') != self.byteLSMS2int(value[10], value[11]): #  0x92
                        flag_ok = False                    
                        self.BME[bme_key]['dig_P3'] = self.byteLSMS2int(value[10], value[11]) #  0x92
                    
                    if self.BME[bme_key].get('dig_P4') != self.byteLSMS2int(value[12], value[13]): #  0x94
                        flag_ok = False                    
                        self.BME[bme_key]['dig_P4'] = self.byteLSMS2int(value[12], value[13]) #  0x94
                    
                    if self.BME[bme_key].get('dig_P5') != self.byteLSMS2int(value[14], value[15]): #  0x96
                        flag_ok = False                    
                        self.BME[bme_key]['dig_P5'] = self.byteLSMS2int(value[14], value[15]) #  0x96

                    if self.BME[bme_key].get('dig_P6') != self.byteLSMS2int(value[16], value[17]): #  0x98
                        flag_ok = False                                        
                        self.BME[bme_key]['dig_P6'] = self.byteLSMS2int(value[16], value[17]) #  0x98
                        
                    if self.BME[bme_key].get('dig_P7') != self.byteLSMS2int(value[18], value[19]): #  0x9A
                        flag_ok = False                    
                        self.BME[bme_key]['dig_P7'] = self.byteLSMS2int(value[18], value[19]) #  0x9A
                    
                    if self.BME[bme_key].get('dig_P8') != self.byteLSMS2int(value[20], value[21]): #  0x9C
                        flag_ok = False                    
                        self.BME[bme_key]['dig_P8'] = self.byteLSMS2int(value[20], value[21]) #  0x9C
                        
                    if self.BME[bme_key].get('dig_P9') != self.byteLSMS2int(value[22], value[23]): #  0x9E
                        flag_ok = False                        
                        self.BME[bme_key]['dig_P9'] = self.byteLSMS2int(value[22], value[23]) #  0x9E
                        
                    if self.BME[bme_key].get('dig_H1') != value[25]: #  0xA1
                        flag_ok = False                        
                        self.BME[bme_key]['dig_H1'] = value[25] #  0xA1
                    
                    self.BME[bme_key]['flag26'] = flag_ok

                if len(value) == 7: # value from 0xE1 to 0xE7
                    # print("CALIBRAZIONE BME--->>>>>", value)
                    
                    flag_ok=True
                    if self.BME[bme_key].get('dig_H2') !=  self.byteLSMS2int(value[0], value[1]): #  0xE1:
                        flag_ok = False 
                        self.BME[bme_key]['dig_H2'] =  self.byteLSMS2int(value[0], value[1]) #  0xE1
                    
                    if self.BME[bme_key].get('dig_H3') != value[2]: # 0xE3:
                        flag_ok = False 
                        self.BME[bme_key]['dig_H3'] = value[2] # 0xE3

                    h4 = self.byte2signed(value[3])
                    h4 = h4 << 4
                    
                    if self.BME[bme_key].get('dig_H4') != h4 | (value[4] & 0x0f):
                        flag_ok = False 
                        self.BME[bme_key]['dig_H4'] = h4 | (value[4] & 0x0f)
                    h5 = self.byte2signed(value[5]) # 0xE6
                    
                    if self.BME[bme_key].get('dig_H5') != (h5 << 4) | ((value[4] >> 4) & 0x0f):
                        flag_ok = False 
                        self.BME[bme_key]['dig_H5'] = (h5 << 4) | ((value[4] >> 4) & 0x0f)
                    
                    if self.BME[bme_key].get('dig_H5') != ((value[4] >> 4) & 0x0F) | (value[5] << 4):
                        flag_ok = False 
                        self.BME[bme_key]['dig_H5'] = ((value[4] >> 4) & 0x0F) | (value[5] << 4)
                    
                    if self.BME[bme_key].get('dig_H6') !=  self.byte2signed(value[6]): # 0xE7
                        flag_ok = False 
                        self.BME[bme_key]['dig_H6'] =  self.byte2signed(value[6]) # 0xE7
                    
                    self.BME[bme_key]['flag7'] = flag_ok
                # pprint(self.BME)

            elif device_type == 'BME280':
                # print(self.mapiotype[board_id][logic_io]['type_io'], self.mapiotype[board_id][logic_io]['device_type'] )

                T_Raw,H_Raw,P_Raw = self.getBME280(board_id, logic_io, value, )
                # print("UNCOMPENSATE:", T_Raw, H_Raw, P_Raw)
                logic_io_calibration = self.mapiotype[board_id][logic_io]['logic_io_calibration']
                bme_key = '{}-{}'.format(board_id, logic_io_calibration)
                # print("bme_key:", bme_key)
                if (bme_key in self.BME) and self.BME[bme_key].get('flag26') and self.BME[bme_key].get('flag7'):
                    # pprint(self.BME[bme_key])

                    v1 = (T_Raw / 16384.0 - self.BME[bme_key]['dig_T1'] / 1024.0) * self.BME[bme_key]['dig_T2']
                    v2 = ((T_Raw / 131072.0 - self.BME[bme_key]['dig_T1'] / 8192.0) ** 2) * self.BME[bme_key]['dig_T3']
                    T_fine = (v1 + v2)
                    T = T_fine / 5120.0

                    # print("TEMERATURE:", T_Raw, T)

                    H = T_fine - 76800.0
                    H = (H_Raw - (self.BME[bme_key]['dig_H4'] * 64.0 + self.BME[bme_key]['dig_H5'] / 16384.0 * H)) * \
                            (self.BME[bme_key]['dig_H2'] / 65536.0 * (1.0 + self.BME[bme_key]['dig_H6'] / 67108864.0 * H * \
                            (1.0 + self.BME[bme_key]['dig_H3'] / 67108864.0 * H)))
                    H = H * (1.0 - (self.BME[bme_key]['dig_H1'] * H / 524288.0))
                    # print("HUMIDITY:", H_Raw, H)

                    v1 = T_fine / 2.0 - 64000.0
                    v2 = v1 * v1 * self.BME[bme_key]['dig_P6'] / 32768.0
                    v2 = v2 + v1 * self.BME[bme_key]['dig_P5'] * 2.0
                    v2 = v2 / 4.0 + self.BME[bme_key]['dig_P4'] * 65536.0
                    v1 = (self.BME[bme_key]['dig_P3'] * v1 * v1 / 524288.0 + self.BME[bme_key]['dig_P2'] * v1) / 524288.0
                    v1 = (1.0 + v1 / 32768.0) * self.BME[bme_key]['dig_P1']

                    # Prevent divide by zero
                    if v1 == 0:
                        P = 0

                    res = 1048576.0 - P_Raw
                    res = ((res - v2 / 4096.0) * 6250.0) / v1
                    v1 = self.BME[bme_key]['dig_P9'] * res * res / 2147483648.0
                    v2 = res * self.BME[bme_key]['dig_P8'] / 32768.0
                    P = (res + (v1 + v2 + self.BME[bme_key]['dig_P7']) / 16.0) / 100

                    # print("PRESSURE:", P_Raw, P)
                else:
                    return None

                P /= (0.9877**(self.mapiotype[board_id][logic_io]['altitude'] / 100)) # Compensazione altitudine
                P += self.mapiotype[board_id][logic_io]['offset_pression'] # Offset pressione
                P = round(P, self.mapiotype[board_id][logic_io]['round_pression'])
                if self.mapiotype[board_id][logic_io]['round_pression'] == 0:
                    P = int(P)
                T += self.mapiotype[board_id][logic_io]['offset_temperature']
                T = round(T, self.mapiotype[board_id][logic_io]['round_temperature'])
                if self.mapiotype[board_id][logic_io]['round_temperature'] == 0:
                    T = int(T)
                H += self.mapiotype[board_id][logic_io]['offset_humidity']
                H = round(H, self.mapiotype[board_id][logic_io]['round_humidity'])
                if self.mapiotype[board_id][logic_io]['round_humidity'] == 0:
                    H = int(H)

                print(T,H,P, self.mapiotype[board_id][logic_io]['round_humidity'])

                return [T,H,P]

            elif device_type == 'AM2320':
                # print ("VALUE=",value)

                hum = ((value[1] * 256 + value[2]) / 10.0) + self.mapiotype[board_id][logic_io]['offset_humidity']

                temp = (((value[3] & 0x7F) * 256 + value[4]) / 10.0) + self.mapiotype[board_id][logic_io]['offset_temperature']
                if value[3] & 0x80 == 0x80: temp = -temp
                # print("AM2320", hum, temp)
                return [temp, hum]

            elif device_type == 'TSL2561':
                # print("TSL2561 Data:", value)
                ch0 = value[0] + (value[1] * 256)
                ch1 = value[2] + (value[3] * 256)

                lux_gain = self.mapiotype[board_id][logic_io]['lux_gain']
                lux_integration = self.mapiotype[board_id][logic_io]['lux_integration']

                # value = self.calculateLux(iGain, tInt, ch0, ch1, IC_Package)
                lux = tsl2561_calculate(lux_gain, lux_integration, ch0, ch1, 'T')
                return round(adjust(lux), 0)

            elif device_type == 'TEMP_ATMEGA':
                value = (value[0] + (value[1] * 256)) - 270 + 25
                return round(value + self.mapiotype[board_id][logic_io]['offset_temperature'], 1)
                # return round(value, 1)

            elif device_type == 'VINR1R2' or device_type == 'VINKMKA' or type_io == 'analog' or type_io == 'virtual':

                rvcc =  self.mapiotype[board_id][logic_io]['rvcc']
                rgnd =  self.mapiotype[board_id][logic_io]['rgnd']
                #print("rvcc:%s - rgnd:%s - kmul:%s - kadd:%s value:%s" %(rvcc, rgnd, kmul, kadd, value))

                if device_type == 'VINR1R2':
                    value = round((value[0] + (value[1] * 256)) * (rvcc + rgnd) / (rgnd * 930.0), 1)
                else:
                    # print("----------------------", value)
                    value = round((value[0] + (value[1] * 256)) * kmul + kadd, 1)

                bio = '%s-%s' %(board_id, logic_io)
                if bio in self.mapproc:
                    #print (self.mapproc['%s-%s' %(board_id, logic_io)])
                    board_id_linked = self.mapproc['%s-%s' %(board_id, logic_io)]['board_id']
                    logic_io_linked = self.mapproc['%s-%s' %(board_id, logic_io)]['logic_io']

                    appfuncplc = self.mapiotype[board_id_linked][logic_io_linked]['plc_function']
                    #print("appfuncplc:", appfuncplc)
                    if appfuncplc == 'power_on':
                        appboardid = self.mapproc['%s-%s' %(board_id,logic_io)]['board_id']
                        appiologic = self.mapproc['%s-%s' %(board_id,logic_io)]['logic_io']
                        vmin = self.mapiotype[appboardid][appiologic]['power_on_voltage_off']
                        # print(appboardid, appiologic, vmin, value)
                        if value >= vmin:
                            self.poweroff_voltage_counter = self.poweroff_voltage_setup
                        elif self.poweroff_voltage_counter > 1:
                            self.poweroff_voltage_counter -= 1
                        else:
                            # print("SPENTO")
                            """ Abilitare per spegnere RAPSBERRY PI """
                            #self.shutdownRequest()
                        print("count = ", self.poweroff_voltage_counter)

                #print("ANALOG VALUE:", value)
                return value

            elif device_type in ['DIGITAL_IN', 'DIGITAL_IN_PULLUP', 'DIGITAL_OUT'] :
                # b0: dato filtrato
                # b1: dato istantaneo
                # b2: fronte OFF
                # b3: fronte ON
                # b4: fronte OFF da trasmettere
                # b5: fronte ON da trasmettere
                # value = value[0]
                # value_io = value & 1
                value = value[0]
                return value

            elif device_type == 'PSICROMETRO':
                print("PSICROMETRO")

            else:
                # print("calculate ERROR: Tipo dispositivo NON trovato:", board_id, logic_io)
                return value
        else:
            # print("calculate ERROR: Board o logic_io non presenti sul file di configurazione. Comunica IO ignorato. board_id:%s, logic_io:%s" % (board_id,  logic_io))
            # pprint(self.mapiotype)
            # pprint(self.mapiotype[board_id])
            return 0

    def printStatus(self):
        """
        Show to screen the IO status
        """

        print("\n", "-" * 83, "STATUS IO", "-" * 83)
        print(" ID Name        board_type  IO: ", end='')
        for i in range(1, 20):  # estremo superiore viene escluso
            print("{:>6} ".format(i), end='')
        print()
        for b in self.status:
            print("{:>3} {:<11} {} {:>6}     ".format(b, self.status[b]['name'][:11], self.status[b]['board_type'], self.status[b]['boardtypename'])," ", end='')

            for i in self.status[b]['io'][:20]:
                print(" {:>6}".format(str(i)), end='')
            print()
        print("-" * 83, "END STATUS", "-" * 83, "\n")


    def int2hex(self, msg):
        """
        Convert list data from INT to HEX
        """
        return ['{:02X}'.format(a) for a in msg]

    # def serold(self, port='/dev/ttyAMA0', baudrate=9600):
    #     """
    #     Instance of serial
    #     """
    #     return arduinoserial.SerialPort(port, baudrate)

    def ser(self, port='/dev/ttyAMA0', baudrate=19200):
        """
        Instance of serial
        """
        return serial.Serial(port, baudrate)

    def send_data_serial(self, Connection, databyte):
        Connection.write(bytes(databyte))  # invia alla seriale

    def calccrc(self, b, crc):
        """
        Calc CRC of trama
        """
        a = 0xff00 | b
        # while 1:
            # crc = ((((crc ^ a) & 1) * 280) ^ crc) // 2
            # a = a // 2
            # if (a <= 255):
                # return crc
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

    crcdoppio = 1   # se 0 sistema vecchio con CRC e fine pacchetto insieme null'ultimo byte
                    # se 1 sistema nuovo con, oltre al sistema vecchio, viene trasmesso un ulteriore byte CRC calcolato passando come dato l'ultimo CRC negato
    lastfinepacc = False

    def readSerial(self, inSerial):
        """
        Calculate trama and return list with right values
        """
        app = inSerial

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
#            print("ric=",ric)
            if (auscrc ^ self.crcric) & 0x7f == 0:  # crc corretto e fine pacchetto veramente
                #print("Secondo crc OK")
                self.labinitric()
                return(ric)
            else:
                print("ERRORE secondo CRC, calcolato - Ricevuto", hex(self.crcric), hex(auscrc), ", len buffricn=",len(self.buffricn),self.buffricnlung)
                self.labinitric()
                return []

        if (inSerial & 0x38) == 0x18 or (inSerial & 0x38) == 0x20:  # Fine pacchetto
            # print("---------", inSerial)
#            print("Ricevuto fine pacchetto",hex(inSerial))
            inSerial = (inSerial & 0x0f) | ((inSerial & 0xc0) // 4)
#            print("fine pacchetto decodificato:", hex(inSerial),", 6bit==>",hex(inSerial&0x3F), "confrontare con:", hex(self.crcric & 0x3F) )
#            print("confrontare con:            ", hex(self.crcric),", 6bit==>",hex(self.crcric & 0x3F), end="" )
            if (inSerial ^ self.crcric) & 0x3F == 0:  # crc corretto
                # print(" CRC OK",end="")
                # print(inSerial)

                appn = len(self.buffricn) + len(self.buffricnapp)
                if appn>2:  # non è un ping
                    if self.buffricnapp:
#                        print("sistema ultimi residui")
                        self.seven2eight()  # sistema gli ultimi residui
                    ric = self.buffricn
                else:
                    ric=self.buffricnapp

                if len(self.buffricn) > 1:  # Non è un PING
                    if self.crcdoppio == 1:
                        #print("Aspetto secondo CRC")
                        self.lastfinepacc = True
                        return []

                    self.labinitric()
                    return(ric)

                else: # è un PING
                    #print("ping")
                    self.labinitric()
                    return(ric)

            else:
                print(self.buffricn," * ",self.buffricnapp)
                print(" PRIMO CRC ERRATO, calcolato - ricevuto",self.crcric, inSerial, ", len buffricn=",len(self.buffricn),self.buffricnlung)
                self.labinitric()
                return []

        elif inSerial == 0:  # Errore 1
            print("ERR 1: Tre 0 ricevuti, byte=", hex(inSerial))
            self.labinitric()
            return []

        elif inSerial == 0x38:  # Errore 2
            print("ERR 2: Tre 1 ricevuti, byte=", hex(inSerial))
            self.labinitric()
            return []

        else:  # carattere normale
            self.crcric = self.calccrc(inSerial, self.crcric)  # aggiorna crc
            self.buffricnapp.insert(self.buffricnlung, ((inSerial & 0x0f) | ((inSerial & 0xE0)//2)))  # inserisce carattere decodificato
#            print("CAR PRIMA E DOPO DECODIFICA",inSerial,((inSerial & 0x0f) | ((inSerial & 0xE0)//2)))
            if len(self.buffricnapp)==8:  # E' arrivato il byte con i bit residui
                # print("+++++++++++++++++", self.buffricn, self.buffricnapp)
                self.seven2eight()
            self.buffricnlung += 1
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
        Setta il numero massimo di board presenti nella rete. Serve per velocizzare il loop
        """
        return [self.BOARD_ADDRESS, self.code['CR_WR_EE'], 0, 6, 0, max_board_address] # Max Board Address

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

    def readEEnIOoffset(self, board_id, logic_io, offset, nbyte):
        """
        Read EEPROM bytes + offset
        """
        address = (logic_io * 32) + offset
        return self.readEEadd(board_id, address, nbyte)

    def writeEEadd(self, board_id, address, data):
        """
        Write EEPROM bytes
        """
        LS, MS = self.calcAddressLsMs8(address)
        msg = [self.BOARD_ADDRESS, self.code['CR_WR_EE'], board_id, LS, MS] + data # Read EE
        return msg

    def writeEEnIOoffset(self, board_id, logic_io, offset, data):
        """
        Write EEPROM bytes
        """
        address = (logic_io * 32) + offset
        return self.writeEEadd(board_id, address, data)


    def readIO(self, board_id, logic_io):
        """
        Read IO status
        """
        data = [self.BOARD_ADDRESS, self.code['CR_RD_IN'], board_id, logic_io, 0]
        # print("ReadIO:", data)
        return data # Read EE

    def writeIO(self, board_id, logic_io, data, ms=0):
        """
        Write IO
        """
        # Su analogico è necessario inviare anche un MS byte per andare fino al valore 1023 (7 bit LS + 3 bit MS)
        data = [self.BOARD_ADDRESS, self.code['CR_WR_OUT'], board_id, logic_io, ] + data + [ms]
        return data # Read EE

    def writeOneWire(self, board_id, logic_io, byteopzioni, data=[]):
        """
        Write One Wire command
        """
        # Su analogico è necessario inviare anche un MS byte per andare fino al valore 1023 (7 bit LS + 3 bit MS)
        # Byteopzioni:
        # b0: reset iniziali
        # b1: 1 bit a 1 su OneWire
        # b2: scrive BIT a ZERO
        # b3: Occupa BUS

        data = [self.BOARD_ADDRESS, self.code['CR_WR_OUT'], board_id, logic_io, byteopzioni] + data
        return data # Read EE

    def readOneWire(self, board_id, logic_io, byteopzioni, data=[]):
        """
        Read OneWire data
        """
        # Su analogico è necessario inviare anche un MS byte per andare fino al valore 1023 (7 bit LS + 3 bit MS)
        # Byteopzioni:
        # b0: reset iniziali
        # b1: 1 bit a 1 su OneWire
        # b2: scrive BIT a ZERO
        # b3: Occupa BUS

        data = [self.BOARD_ADDRESS, self.code['CR_RD_IN'], board_id, logic_io, byteopzioni] + data
        return data # Read EE

    def writeI2C(self, board_id, logic_io, byteopzioni, data):
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

        # print(board_id, logic_io, byteopzioni, data)
        # data = self.get8to7(data)
        data = [self.BOARD_ADDRESS, self.code['CR_WR_OUT'], board_id, logic_io, byteopzioni] + data
        # print("WriteI2C:", data)
        return data

    def readI2C(self, board_id, logic_io, byteopzioni, data):
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

        # print(board_id, logic_io, byteopzioni, data)
        # data = self.get8to7(data)
        data = [self.BOARD_ADDRESS, self.code['CR_RD_IN'], board_id, logic_io, byteopzioni] + data
        # print("WriteI2C:", data)
        return data

    def initIO(self, board_id, logic_io):
        """
        Init IO of board (read configuration in EEPROM)
        """
        data = [self.BOARD_ADDRESS, self.code['CR_INIT_SINGOLO_IO'], board_id, logic_io]
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

    def getBME280(self, board_id, logic_io, value):
        """
        From bytes to value Temp, Hum, Press of BME280
        """
        bmeValue = value
        pres_raw = (bmeValue[0] << 12) | (bmeValue[1] << 4) | (bmeValue[2] >> 4)
        temp_raw = (bmeValue[3] << 12) | (bmeValue[4] << 4) | (bmeValue[5] >> 4)
        hum_raw  = (bmeValue[6] << 8)  |  bmeValue[7]
        tot = [temp_raw, hum_raw, pres_raw]
        # print("Termperatura BME280 ==>>", t, pressure, hh, tot)
        return tot

    def resetEE(self, board_id, logic_io):
        """
        Mette a 0 gli enable dei vari IO logici.
        Se logic_io=0, disabilita gli i dispositivi da 1 a 24
        """
        TXtrama = []
        if logic_io == 0:
            for x in range(1, 25):
                msg = self.writeEEnIOoffset(board_id, logic_io, 0, [0,0])
                TXtrama.append(msg)
                TXtrama.append(self.initIO(board_id, logic_io))

        else:
            msg = self.writeEEnIOoffset(board_id, logic_io, 0, [0, 0])
            # print(msg)
            TXtrama.append(msg)
            TXtrama.append(self.initIO(board_id, logic_io))
        TXtrama.append(self.boardReboot(board_id))
        return(TXtrama)

    def getConfiguration(self):
        """
        Make configuration to send to board
        """
        msg = []
        #pprint(self.mapiotype)
        #print("------------------------------------------")
#        pprint(self.config)
        for board_id in self.mapiotype:
            flagreset = True
            #pprint(self.mapiotype[board_id])
            for logic_io in self.mapiotype[board_id]:

                # casi 'board_enable':
                #  0=programmazione disabilitata,
                #  1=cancella tutto e riprogramma,
                #  2=cancella tutto e non riprogramma

                appbe=self.mapiotype[board_id][logic_io]['board_enable']

                if appbe==0:
                    # print("Configurazione board: BOARD DISABILITATA: ", board_id)
                    break

                if appbe==2:
                    msg.append(self.clearIO_boardReboot(board_id))
                    break

                if appbe != 1:
                    print("ERRORE CAMPO board enable, BOARD: ", board_id)
                    break


                print("ABILITATI: BOARD:", board_id, "LOGIC_IO:",logic_io)

                if flagreset:
                    flagreset = False
                    msg.append(self.clearIO_boardReboot(board_id))
                    # msg.append(self.clearIO_boardReboot(board_id))
                    # msg.append(self.clearIO_boardReboot(board_id))

                #print(msg)

                board_type = self.mapiotype[board_id][logic_io]['board_type']
                boardname = self.mapiotype[board_id][logic_io]['name']

                message_conf_app = []
                write_ee = self.mapiotype[board_id][logic_io]['write_ee']

                if logic_io >= 30:
                    print("Configurazione board ERROR: logic_io non può essere superiore a 29. logic_io=%s", logic_io)
                    continue


                byte0 = self.mapiotype[board_id][logic_io]['fisic_io']
                # print("################",board_type,byte0)
                eels, eems = self.calcAddressLsMs8(logic_io * 32)

                byte1 = self.mapiotype[board_id][logic_io]['direction_val']

                type_io = self.mapiotype[board_id][logic_io]['type_io']

                device_type = self.mapiotype[board_id][logic_io]['device_type']

                plc_linked_board_id_logic_io = self.mapiotype[board_id][logic_io]['plc_linked_board_id_logic_io']

                if device_type == "PSYCHROMETER":  # PSYCHROMETER è calcolato da DL485.py in base a 2 temperature. Nessuna configurazione da inviare
                    if len(plc_linked_board_id_logic_io) != 2:
                        print("PSYCHROMETER CONFIGURATION ERROR: Need 2 TEMPERATURE value linked")
                        sys.exit()
                    # print("plc_linked_board_id_logic_io", plc_linked_board_id_logic_io)
                    print("PSYCHROMETER",message_conf_app )
                    continue


                # print("type_io: %s - device_type: %s" %(type_io, device_type))

                #if not enable: type_io = 'disable' # Non fa configurazione se enable = 0
                print("")

                if type_io == 'analog' or type_io == 'temp_atmega':
                    byte1 |= 0b10
                elif type_io == 'digital':
                    byte1 |= 0b00
                elif type_io == 'i2c':
                    byte1 |= 0b1000
                elif type_io == 'onewire' or type_io == 'onewire_test':
                    byte1 |= 0b00100
                elif type_io == 'discrete':
                    byte1 |= 0b1100
                elif type_io == 'disable':
                    byte1 |= 0b00000
                else:
                    print("Configurazione boards: ERROR: type_io non riconosciuto. BOARD_ID:%s - logic_io:%s - type_io:%s" %(board_id, logic_io, type_io))
                    continue

                # print("Configurazione boards: boards:%s, logic_io:%s" %(boardname, logic_io))
                byte1 |= 0x40 #b6

                direction = self.mapiotype[board_id][logic_io]['direction']
                # print("******K*********",direction)
                if type_io == 'i2c' or type_io == 'onewire' or type_io == 'onewire_test':
                    byte2 = self.mapiotype[board_id][logic_io]['pullup']
                    byte3 = 0
                    # print(board_id,"*************** Pullup: ",bin(byte2),bin(byte1))
                elif direction == 'input':
                    byte2 = self.mapiotype[board_id][logic_io]['pullup'] | (self.mapiotype[board_id][logic_io]['default_startup_filter_value']*2)
                    byte3 = 0
                elif direction == 'output':
                    byte1 |= 1
                    # print("OUTPUT")
                    default_startup_value = self.mapiotype[board_id][logic_io]['default_startup_value']
                    default_startup_value = default_startup_value
                    byte2, byte3 = self.calcAddressLsMs8(default_startup_value)
                else:
                    byte2 = byte3 = 0
                    print("ERROR: DIRECTION su configurazione non riconosciuto. IO: %s" %board_id)
                    # continue

                if type_io == 'analog' or type_io == 'digital':
                    byte4 = self.mapiotype[board_id][logic_io]['n_refresh_on']  # Byte 4: rinfreschi rete sui fronti ON
                    # print("----", self.mapiotype[board_id][logic_io]['n_refresh_on'], self.mapiotype[board_id][logic_io]['n_refresh_off'])
                    byte4 |= self.mapiotype[board_id][logic_io]['n_refresh_off'] << 3  # Byte 4: rinfreschi rete sui fronti OFF
                else:
                    byte4 = 0

                if self.mapiotype[board_id][logic_io]['inverted']:  # Invert OUTPUT. Se inverted, lo stato ON in uscita di un rele si ha con lo stato zero.
                    byte4 |= 128

                # byte5 = int(boards.get(board)['time_refresh']) & 255  # Byte 5: rinfresco periodico ls in decimi di secondo
                # byte6 = int(boards.get(board)['time_refresh']) >> 8  # Byte 6: rinfresco periodico ms (14 bit = 16383) (0=sempre, 16383=mai)
                byte5, byte6 = self.calcAddressLsMs8(self.mapiotype[board_id][logic_io]['time_refresh'])# Byte 5: rinfresco periodico ls in decimi di secondo, Byte 6: rinfresco periodico ms (14 bit = 16383) (0=sempre, 16383=mai)
                # print("RINFRESCHI", byte5, byte6)

                if type_io == 'analog' or type_io == 'digital':
                    byte7 = self.mapiotype[board_id][logic_io]['filter']
                else:
                    byte7 = 0

                message_conf_app.append(self.BOARD_ADDRESS)  # Mio indirizzo IDBUS
                message_conf_app.append(self.code['CR_WR_EE'])  # Comando scrittura EEPROM, 4 per leggere
                message_conf_app.append(board_id)  # board_id destinazione
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

                #print("TRAMA CONFIGURAZIONE:             ", message_conf_app)

                msg.append(message_conf_app)
                # msg.append(self.initIO(board_id, logic_io))  # iNIt io

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
                    # 'or_transition_on_single': 15, # Se più di un fronte sullo stesso campionamento o fronti consecutivi, si considera un fronte singolo // non funzionano
                    # 'nor_transition_on_single': 15 | 128, // non funzionano
                    'or_transition_on': 16, # n impulsi separati per ciascun fronte (ex funzione or_transition_on_multi)
                    'nor_transition_on': 16 | 128,
                    # 'or_transition_on_sum': 17, # Uscita allungata finche non sono finiti i fronti // non funzionano
                    # 'nor_transition_on_sum': 17 | 128, // non funzionano
                    'analog_in_=_n': 20,
                    'nanalog_in_=_n': 20 | 128,
                    'analog_in_>_n': 21,
                    'nanalog_in_>_n': 21 | 128,
                    'analog_in_>=_n': 22,
                    'nanalog_in_>=_n': 22 | 128,
                    'analog_in_schmitt': 23,
                    'nanalog_in_schmitt': 23 | 128,
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
                    'analog_in_lim_max_n': 45,
                    'analog_in_lim_min_n': 46,
                    'analog_in1_+_analog_in2': 50,
                    'analog_in1_-_analog_in2': 51,
                    'analog_in1_*_analog_in2': 52,
                    'analog_in1_/_analog_in2': 53,
                    'analog_in1_%_analog_in2': 54,
                    'analog_in1_min_analog_in2': 55,
                    'analog_in1_max_analog_in2': 56,
                    'sampletrigger': 60,
                }

                sbyte8 = self.mapiotype[board_id][logic_io]['plc_function']
                print("PLC_FUNCTION:************************", plc_function[sbyte8], sbyte8)

                if sbyte8 == "disable":
                    # print("PLC DISABILITATO", logic_io, plc_function[sbyte8])
                    message_conf_app.append(0)

                else:  # byte8 != "disable":
                    # if inverted:
                        # plc_function[byte8] ^= 0x80
                    plc_params = self.mapiotype[board_id][logic_io]['plc_params']
                    plc = []

                    message_conf_app.append(plc_function[sbyte8])
                    # print("--------------------->>>>>>>>>>>>>>>>>>>>>>message_conf_app", message_conf_app)

                    # plc_linked_board_id_logic_io = self.mapiotype[board_id][logic_io]['plc_linked_board_id_logic_io'] # già calcolato sopra

                    plc_time_unit = self.mapiotype[board_id][logic_io]['plc_time_unit']
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


                    if sbyte8 == 'power_on':
                        appboardid = self.mapiotype[board_id][logic_io]['plc_byte_list_io'][0]
                        applogicio = self.mapiotype[board_id][logic_io]['plc_byte_list_io'][1]

                        rgnd = self.mapiotype[appboardid][applogicio]['rgnd']
                        rvcc = self.mapiotype[appboardid][applogicio]['rvcc']
                        power_on_voltage_on = self.mapiotype[board_id][logic_io]['power_on_voltage_on']

                        value_dac_in = self.ADC_value(float(power_on_voltage_on), rvcc, rgnd)
                        # self.poweron_linked=1111
                        # print(self.mapproc)
                        # print("valuedacin:",value_dac_in,power_on_voltage_on, rvcc, rgnd)
                        plc += [self.mapiotype[board_id][logic_io]['plc_byte_list_io'][1]]
                        # print(self.mapiotype[board_id][logic_io]['power_on_timin_off'])
                        plc += list(self.calcAddressLsMs8(int(self.mapiotype[board_id][logic_io]['power_on_timeout']))) + list(self.calcAddressLsMs8(int(self.mapiotype[board_id][logic_io]['power_on_tmin_off']))) + list(self.calcAddressLsMs8(value_dac_in))
                        # print("POWER_ON data:", sbyte8, value_dac_in, plc)


                    else:  # Funzione PLC
                        plc.append(self.mapiotype[board_id][logic_io]['plc_xor_input'])  # OFFSET 31: BYTE con NEGAZIONE ingressi. Mettere davanti a plc_linked_board_id_logic_io il carattere ! per negare gli ingresso

                        plc_preset_input =  self.mapiotype[board_id][logic_io]['plc_preset_input']
                        plc.append(plc_preset_input)  # OFFSET 30: BYTE PRESET valore default prima che arrivino i dati dalla rete

                        plc.append(len(plc_linked_board_id_logic_io))  # OFFSET 29: Numero ingressi per la funzione PLC

                        # print("list_plc_linked_board_id_logic_io", list_plc_linked_board_id_logic_io)
                        # print(plc_linked_board_id_logic_io)

                        plc += self.mapiotype[board_id][logic_io]['plc_byte_list_io']
                        # print(plc)
                        # sys.exit()

                        # if plc_linked_board_id_logic_io:
                        #     for plc_bio in plc_linked_board_id_logic_io:
                        #         plc_bio = plc_bio.split("-")
                        #         plc.append(int(plc_bio[0]))  # OFFSET 28: BOARD_ID
                        #         plc.append(int(plc_bio[1]))  # OFFSET 27: logic_ioO
                        # else:
                        #     print("BOARD_ID and logic_io not defined on CONFIGURATION File")

                        # print("Funzione PLC:", sbyte8)
                        if sbyte8 in ["timer", "ntimer", "autostart_timer", "nautostart_timer"]:
                            # Se timer, dopo elenco di BOARD_ID e logic_io, seguono questi parametri:
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

                            plc_mode_timer = self.mapiotype[board_id][logic_io]['plc_mode_timer']

                            plc.append((plc_mode_timer & 0x3F) | plc_time_unit_app)

                            plc_timer_n_transitions = self.mapiotype[board_id][logic_io]['plc_timer_n_transitions']
                            if plc_timer_n_transitions > 255:
                                print("ERRORE CONFIGURATION: plc_timer_n_transitions 0...255")
                                sys.exit()
                            plc.append(plc_timer_n_transitions)

                            plc_time_on = self.mapiotype[board_id][logic_io]['plc_time_on']
                            # plc.append(plc_time_on & 255)
                            # plc.append(plc_time_on >> 8)
                            plc += list(self.calcAddressLsMs8(plc_time_on))

                            plc_time_off = self.mapiotype[board_id][logic_io]['plc_time_off']
                            # plc.append(plc_time_off & 255)
                            # plc.append(plc_time_off >> 8)
                            plc += list(self.calcAddressLsMs8(plc_time_off))

                        elif sbyte8 in ["equal", "nequal"]:

                            plc.append(plc_time_unit_app)
                            plc.append(0) # Numero massimo di commutazioni (ignorato)

                            plc_delay_on_off = self.mapiotype[board_id][logic_io]['plc_delay_on_off']
                            plc += list(self.calcAddressLsMs8(plc_delay_on_off))

                            plc_delay_off_on = self.mapiotype[board_id][logic_io]['plc_delay_off_on']
                            plc += list(self.calcAddressLsMs8(plc_delay_off_on))

                            plc_tmax_on = self.mapiotype[board_id][logic_io]['plc_tmax_on']
                            plc += list(self.calcAddressLsMs8(plc_tmax_on))

                        elif sbyte8 in ['test_nio_>_n', 'ntest_nio_>_n', 'test_nio_>=_n', 'ntest_nio_>=_n']:
                            plc_params_val = int(plc_params)
                            plc.append(plc_params_val)

                        elif sbyte8 in ['test_nio_into_n', 'ntest_nio_into_n', 'test_schmitt_nio', 'ntest_schmitt_nio']:
                            plc_params_val = list(plc_params)
                            plc.append(plc_params_val[1] * 16 | plc_params[0])

                        elif sbyte8 in ['analog_in_=_n', 'nanalog_in_=_n', 'analog_in_>_n', 'nanalog_in_>_n', 'analog_in_>=_n', 'nanalog_in_>=_n']:
                            plc_params_val = int(plc_params)
                            plc += list(self.calcAddressLsMs8(plc_params_val))

                        elif sbyte8 in ['analog_in_schmitt', 'nanalog_in_schmitt']:
                            plc_params_val = list(plc_params)
                            plc += list(self.calcAddressLsMs8(plc_params_val[1]))
                            plc += list(self.calcAddressLsMs8(plc_params_val[0]))

                        elif sbyte8 in ['if_analog_in1_=_analog_in2', 'nif_analog_in1_=_analog_in2', 'if_analog_in1_>_analog_in2', 'nif_analog_in1_>_analog_in2', 'if_analog_in1_>=_analog_in2', 'nif_analog_in1_>=_analog_in2']:
                            """ non serve passare alcun parametro """
                            pass

                        elif sbyte8 in ['if_analog_in1_-_analog_in2_schmitt_value', 'nif_analog_in1_-_analog_in2_schmitt_value']:
                            plc_params_val = list(plc_params)
                            plc += list(self.calcAddressLsMs8(plc_params_val[1]))
                            plc += list(self.calcAddressLsMs8(plc_params_val[0]))

                        elif sbyte8 in ['last_change', 'nlast_change', 'last_change_all', 'nlast_change_all']:
                            pass


                        elif sbyte8 in ['analog_in_+_n', 'analog_in_-_n', 'analog_in_*_n', 'analog_in_/_n', 'analog_in_%_n', 'analog_in_lim_min_n', 'analog_in_lim_max_n']:

                            plc_params_val = int(plc_params)
                            # plc.append(plc_params_val & 255)
                            # plc.append(plc_params_val >> 8)
                            plc += list(self.calcAddressLsMs8(plc_params_val))

                        elif sbyte8 in ['analog_in1_+_analog_in2', 'analog_in1_-_analog_in2', 'analog_in1_*_analog_in2', 'analog_in1_/_analog_in2', \
                                        'analog_in1_/_analog_in2', 'analog_in1_%_analog_in2', 'analog_in1_min_analog_in2', 'analog_in1_max_analog_in2']:
                            pass

                        elif sbyte8 in ['counter_up', 'counter_dw']:
                            plc_counter_mode = self.mapiotype[board_id][logic_io]['plc_counter_mode']
                            plc.append(plc_counter_mode)
                            plc_counter_filter = self.mapiotype[board_id][logic_io]['plc_counter_filter']
                            plc.append(plc_counter_filter)
                            plc_counter_timeout = self.mapiotype[board_id][logic_io]['plc_counter_timeout']
                            plc += list(self.calcAddressLsMs8(plc_counter_timeout))
                            
                        elif sbyte8 in ['counter_up_dw']:
                            """ ingresso dispari incrementa - ingresso pari decrementa """
                            plc_counter_mode = self.mapiotype[board_id][logic_io]['plc_counter_mode']
                            plc.append(plc_counter_mode)
                            plc_counter_filter = self.mapiotype[board_id][logic_io]['plc_counter_filter']
                            plc.append(plc_counter_filter)
                            plc_counter_timeout = self.mapiotype[board_id][logic_io]['plc_counter_timeout']
                            plc += list(self.calcAddressLsMs8(plc_counter_timeout))

                        elif sbyte8 == 'time_meter':
                            plc_counter_mode = self.mapiotype[board_id][logic_io]['plc_counter_mode']
                            plc.append(plc_counter_mode)
                            plc_counter_filter = self.mapiotype[board_id][logic_io]['plc_counter_filter']
                            plc.append(plc_counter_filter)
                            plc_counter_timeout = self.mapiotype[board_id][logic_io]['plc_counter_timeout']
                            plc += list(self.calcAddressLsMs8(plc_counter_timeout))

                        elif sbyte8 == 'powermeter':
                            plc_counter_mode = self.mapiotype[board_id][logic_io]['plc_counter_mode']
                            plc.append(plc_counter_mode)
                            plc_counter_filter = self.mapiotype[board_id][logic_io]['plc_counter_filter']
                            plc.append(plc_counter_filter)
                            plc_counter_timeout = self.mapiotype[board_id][logic_io]['plc_counter_timeout']
                            plc += list(self.calcAddressLsMs8(plc_counter_timeout))
                            plc_counter_min_period_time = self.mapiotype[board_id][logic_io]['plc_counter_min_period_time']
                            plc.append(plc_counter_min_period_time)
                            powermeter_k = self.mapiotype[board_id][logic_io]['powermeter_k']
                            plc += list(self.calcAddressLsMs8(powermeter_k))

                        elif sbyte8 in  ['and', 'nand',   'or', 'nor', 'xor', 'nxor', 'odd', 'even', 'toggle_off', 'toggle_on', 'toggle_on_off']:
                            plc.append(plc_time_unit_app)
                            plc.append(0) # Numero massimo di commutazioni (ignorato)
                            plc_tmax_on = self.mapiotype[board_id][logic_io]['plc_tmax_on']
                            plc += list(self.calcAddressLsMs8(plc_tmax_on))

                        elif sbyte8 in  ['or_transition_on', 'nor_transition_on', 'or_transition_on_single', 'nor_transition_on_single', 'or_transition_on_multi', 'nor_transition_on_multi', 'or_transition_on_sum', 'nor_transition_on_sum' ]:
                            pass

                        else:
                            self.log.write('FUNZIONE PLC NON TROVATA: %s' %sbyte8)
                            sys.exit()

                    plclen = len(plc)
                    # print("CONFIGURAZIONE PLC =======>>>>>: ", sbyte8, plc)
                    plc.reverse()

                    plc_EE_start = (logic_io * 32) + 32 - plclen
                    plc_data = self.writeEEadd(board_id, plc_EE_start, plc)
                    # print("<<<<<<<<<<<<<<<<<<<============PLC_DATA:", sbyte8, plc_function[sbyte8], plc_data)
                    msg.append(plc_data)

                # Configurazione relativa ai sensori I2C e OneWire

                #if type_io == 'i2c':
                if device_type == 'PCA9535':
                    print("==>> Inserisce trama di confgurazione I2C per PCA9535")
                    # msg.append(self.writeEE(board_id, eels + 10, eems, [5, 3, 0x4e, 2, 0x0a, 0xa0]))
                    # msg.append(self.writeEE(board_id, eels + 16, eems, [5, 3, 0x4e, 6, 0, 0])) # Impostare direzione OUT (inizializzazione)
                    # msg.append(self.writeEE(board_id, eels + 22, eems, [5, 3, 0x4e, 2, 0xa0, 0x0a]))
                elif device_type == 'BME280':
                    if self.EEPROM_LANGUAGE == 0:
                        print("EEPROM_LANGUAGE OLD")
                        msg.append(self.writeEEnIOoffset(board_id, logic_io, 10, [3 | self.i2c_const['CONCATENA'], 1 | 8, 0xec, 0xf7]))  # 3|128: 128 per concatenare con prg. successivo), 32 reset +
                        msg.append(self.writeEEnIOoffset(board_id, logic_io, 14, [2 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 3 | 64, 0xec | 1]))  # 2|64: lettura I2C. 3+64: 8 byte da leggere

                        msg.append(self.writeEEnIOoffset(board_id, logic_io, 17, [4 | self.i2c_const['CONCATENA'], 3 | 32, 0xec, 0xf2, 0x03]))  # Inizializzazione BME e Oversampling umidità
                        msg.append(self.writeEEnIOoffset(board_id, logic_io, 22, [4 | self.i2c_const['NON_CONCATENA'], 3, 0xec, 0xf4, 0x8f]))  # Inizializzazione BME temperatura + pressione  (Oversampling)
                    elif self.EEPROM_LANGUAGE == 1:
                        # print("EEPROM_LANGUAGE NEW")
                        # msg.append(self.writeEEnIOoffset(board_id, logic_io, 10, [3, 1 | 8, 0xec, 0xf7]))  # F7 indirizzo di inizio lettura
                        # msg.append(self.writeEEnIOoffset(board_id, logic_io, 14, [2 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 3 | 64, 0xec | 1, 0]))  # 64 = 8 byte da leggere, 0=fine programma

                        # msg.append(self.writeEEnIOoffset(board_id, logic_io, 18, [4, 3 | 32, 0xec, 0xf2, 0x03]))  # Inizializzazione BME e Oversampling umidità
                        # msg.append(self.writeEEnIOoffset(board_id, logic_io, 23, [4, 3, 0xec, 0xf4, 0x8f, 0]))  # Inizializzazione BME temperatura + pressione  (Oversampling)

                        msg.append(self.writeEEnIOoffset(board_id, logic_io, 10, [4, 3 | 32, 0xec, 0xf2, 0x03]))  # Inizializzazione BME e Oversampling umidità
                        msg.append(self.writeEEnIOoffset(board_id, logic_io, 15, [4, 3, 0xec, 0xf4, 0x8f]))  # Inizializzazione BME temperatura + pressione  (Oversampling)
                        msg.append(self.writeEEnIOoffset(board_id, logic_io, 20, [3, 1 | 8, 0xec, 0xf7]))  # F7 indirizzo di inizio lettura
                        msg.append(self.writeEEnIOoffset(board_id, logic_io, 24, [2 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 3|64, 0xec | 1, 0, 0]))  # 64 = 8 byte da leggere, 0=fine programma


                elif device_type == 'BME280_CALIB':
                    if self.EEPROM_LANGUAGE == 0:
                        print("ERRORE - MANCA DEFINIZIONE LINGUAGGIO VECCHIO")
                    elif self.EEPROM_LANGUAGE == 1:
                        msg.append(self.writeEEnIOoffset(board_id, logic_io, 10, [3 | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 1|8|32, 0xec, 0x88]))  # 1=start iniziale | termina per dare start senza stop | reset I2C prima di iniziare
                        msg.append(self.writeEEnIOoffset(board_id, logic_io, 14, [2 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 3|208, 0xec | 1]))  # 208: lettura I2C. 26 byte da leggere da indirizzo 0x88
                        msg.append(self.writeEEnIOoffset(board_id, logic_io, 17, [3 | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 1|8, 0xec, 0xE1]))
                        msg.append(self.writeEEnIOoffset(board_id, logic_io, 21, [2 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 3|56, 0xec | 1, 0]))  # 56: lettura I2C. 7 byte da indirizzo E1

                elif device_type == 'AM2320':
                    print("CONFIGURAZIONE AM2320")
                    if self.EEPROM_LANGUAGE == 0:  # vecchio linguaggio
                        i2cconf = []
                        i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 10, [2 | self.i2c_const['CONCATENA'] | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 3, 0xb8]))  # 3|128: 128 per concatenare con prg. successivo), 32 reset +
                        i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 13, [5 | self.i2c_const['CONCATENA'] | self.i2c_const['BYTE_OPZIONI_SCRITTURA'],  3, 0xb8, 0x03, 0x00, 0x04]))
                        i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 19, [3 | self.i2c_const['FLAG_PAUSA'] | self.i2c_const['BYTE_OPZIONI_LETTURA'], 100, 3 | 64, 0xb9, 0 ]))
                    elif self.EEPROM_LANGUAGE == 1:  # nuovo linguaggio
                        i2cconf = []
                        #i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 13, [0]))
                        #i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 12, [0]))

                        i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 10, [2 | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 3, 0xb8]))  #3=start+stop, 0xb8=indirizzo dispositivo*2 serve per risveglio dispositivo
                        i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 13, [5 | self.i2c_const['BYTE_OPZIONI_SCRITTURA'],  3, 0xb8, 0x03, 0x00, 0x04]))  #3=start+stop, 0xb8=indirizzo dispositivo*2,03=?, 00=indirizzo primo byte da leggere, 4=numero byte da leggere
                        i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 19, [1 | self.i2c_const['FLAG_PAUSA'] , 100 ])) #100=decine di microsecondi di pausa, totale 1 ms
                        i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 21, [3 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 3|40 , 0xb9, 0, 0])) #3=start+stop|40=numero byte da leggere*8=5*8, 5 perchè servono 4 byte e inizia col numero di byte (4)+b,b,b,b, 0xb9=indirizzo dispositivo+flag lettura, 0=nessun programma seguente, 0=nessun programma setup
                    msg.extend(i2cconf)

                elif device_type == 'TSL2561':
                    # print("CONFIGURAZIONE TSL2561")
                    lux_gain = self.mapiotype[board_id][logic_io]['lux_gain']
                    lux_integration = self.mapiotype[board_id][logic_io]['lux_integration']
                    if lux_gain not in [0, 1]:
                        print("ERROR TSL2561 lux_gain={}. Deve essere 0 o 1 ".format(lux_gain))
                        sys.exit()
                    if lux_integration not in [0, 1, 2]:
                        print("ERROR TSL2561 lux_integration={}. Deve essere 0, 1, 2 ".format(lux_integration))
                        sys.exit()


                    if self.EEPROM_LANGUAGE == 0:
                        i2cconf = []
                        i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 10, [3 | self.i2c_const['CONCATENA'] | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 1, 0x72, 0xAC])) #0x72 address dispositivo
                        i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 14, [2 | self.i2c_const['CONCATENA'] | self.i2c_const['BYTE_OPZIONI_LETTURA'], 3 | 32, 0x72 | 1  ]))

                        i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 17, [3 | self.i2c_const['CONCATENA'] | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 1, 0x72, 0x80])) #scrive registro 0
                        i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 21, [3 | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 3, 0x72, 0x03])) #alimenta tsl2561

                    elif self.EEPROM_LANGUAGE == 1:
                        i2cconf = []
                        # i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 10, [3 | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 1, 0x72, 0xAC])) #0x72 address dispositivo poi legge a Word (A) partendo da indirizzo (C)
                        # i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 14, [2 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 3 | 32, 0x72 | 1  ,0]))#legge 4 byte

                        # i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 18, [3 | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 1, 0x72, 0xA0])) #scrive registro 0
                        # i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 22, [4 | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 3, 0x72, 0x03, (lux_gain*16)|lux_integration, 0,0]) )#alimenta tsl2561

                        i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 10, [3 | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 1, 0x72, 0xA0])) #scrive registro 0
                        i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 14, [4 | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 3, 0x72, 0x03, (lux_gain*16)|lux_integration]) )#alimenta tsl2561
                        i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 19, [3 | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 1, 0x72, 0xAC])) #0x72 address dispositivo poi legge a Word (A) partendo da indirizzo (C)
                        i2cconf.append(self.writeEEnIOoffset(board_id, logic_io, 23, [2 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 3|32, 0x72|1 , 0, 0]))#legge 4 byte

                        

                    msg.extend(i2cconf)
                    # print("CONFIGURAZIONE I2C:", i2cconf)

                #elif type_io == 'onewire':
                elif device_type == 'DS18B20':
                    if self.EEPROM_LANGUAGE == 0:
                        msg.append(self.writeEEnIOoffset(board_id, logic_io, 10, [3 | self.i2c_const['CONCATENA'] | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 1, 0xcc, 0x44]))  # num. byte, byte opzioni, campionamento di tutte le sonde, campiona temperatura
                        device_address = self.mapiotype[board_id][logic_io]['device_address']
                        # print("ADDRESS ID ONE WIRE:", device_address)
                        if device_address:
                            device_address = [int(x, 16) for x in device_address]
                            msg.append(self.writeEEnIOoffset(board_id, logic_io, 14, [11 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 1+72, 0x55] + device_address +  [0xbe, 0]))  # num. byte, byte opzioni, S/N sonda, ID, 0xbe leggi temp
                        else:
                            msg.append(self.writeEEnIOoffset(board_id, logic_io, 14, [3 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 1+72, 0xCC] + [0xbe, 0]))  # num. byte, byte opzioni, S/N sonda, ID, 0xbe leggi temp

                    elif  self.EEPROM_LANGUAGE == 1:
                        msg.append(self.writeEEnIOoffset(board_id, logic_io, 10, [3 | self.i2c_const['BYTE_OPZIONI_SCRITTURA'], 1, 0xcc, 0x44]))  # num. byte, byte opzioni, campionamento di tutte le sonde, campiona temperatura
                        device_address = self.mapiotype[board_id][logic_io]['device_address']
                        # print("ADDRESS ID ONE WIRE:", device_address)
                        if device_address:
                            device_address = [int(x, 16) for x in device_address]
                            msg.append(self.writeEEnIOoffset(board_id, logic_io, 14, [11 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 1+72, 0x55] + device_address +  [0xbe, 0]))  # num. byte, byte opzioni, S/N sonda, ID, 0xbe leggi temp
                        else:
                            msg.append(self.writeEEnIOoffset(board_id, logic_io, 14, [3 | self.i2c_const['BYTE_OPZIONI_LETTURA'], 1+72, 0xCC] + [0xbe, 0, 0]))  # num. byte, byte opzioni, S/N sonda, ID, 0xbe leggi temp

                elif device_type == 'GENERIC':
                    # Go To programma di altro IO logico
                    # print("WRITE_EE", write_ee, board_id, eels + 10, eems, [32 | 3, 0, 0])
                    if write_ee:
                        msg.append(self.writeEEnIOoffset(board_id, logic_io, 10, [32 | 3, 0, 0]))  # [32: Go_TO | 3: IO logico, 0: offset (0=10), 0=non ci sono altri programmi da eseguire ]
                    else:
                        print("********************")
                        msg.append(self.writeEEnIOoffset(board_id, logic_io, 10, [32 | 3, 0, 0]))  # [32: Go_TO | 3: IO logico, 0: offset (0=10), 0=non ci sono altri programmi da eseguire ]

                else:
                    # If not I2C or OneWire, set 0, 0 at address 10 and 11.
                    msg.append(self.writeEEnIOoffset(board_id, logic_io, 10, [0,0]))  # 0 = lunghezza programma periodico, 0 = lunghezza prg. inizializzazione

        if msg:
            msg.append(self.boardReboot(0))
            # msg.append(self.boardReboot(0))
        else:
            print("NESSUNA CONFIGURAZIONE BOARD DA INVIARE")
        #pprint(msg)

        return msg

    def arrivatatrama(self):
        # arrivata una trama completa (PING e trame piu lunghe)
        self.nowtime = int(time.time())  # seleziona la parte intera dei secondi
        #print(b.RXtrama)
        self.board_ready[self.RXtrama[0]] = self.nowtime  # Aggiorna la data di quando è stato ricevuto la trama del nodo, serve per dizionario delle boards rilevate sul bus

        if self.RXtrama[0] + 1 == self.BOARD_ADDRESS:  # test su address ricevuto, e' ora di trasmettere

            for x in self.BUFF_MSG_TX:  ## aggiornamento timeout
                ##print(b.BUFF_MSG_TX[x][1])
                if self.BUFF_MSG_TX[x][1]: self.BUFF_MSG_TX[x][1] -= 1

            for x in self.BUFF_MSG_TX: ##cerca msg in timeout, fatto in un secondo ciclo for perchè questa modifica il dizionario e crea un errore se si continua la ricerca dopo la modifica
                if not self.BUFF_MSG_TX[x][1]:  ## trovato messaggio in timeout
                    # print("TIMEOUT MSG:",b.BUFF_MSG_TX[x][0])
                    self.log.write("{:<11} {}    {:<18}".format(self.nowtime, 'CONFIG. TIMEOUT MSG', str(self.int2hex(self.BUFF_MSG_TX[x][0]))))

                    self.TXmsg.insert(0,self.BUFF_MSG_TX[x][0])  ## lo mette al primo posto nella lista di trasmissione
                    del self.BUFF_MSG_TX[x] ## lo cancella per poterlo reinserire tutto perche non c'è il goto
                    break  ## esce dal for

            if len(self.TXmsg): #se qualcosa da trasmettere
                #print("TXmsg to send:", len(self.TXmsg))
                msg = self.TXmsg.pop(0)  # prende dalla lista la prima trama da trasmettere (msg piu vecchio)
                ##print(msg, msg[2], b.BUFF_MSG_TX)
                #if (len(msg)>1): print("****FORSE TRASMETTE: %s            %s" %(len(self.TXmsg), self.int2hex(msg)))
                if (len(msg)>1) and (msg[1]==self.code['CR_REBOOT']):  # il comando reboot va trasmesso alla fine della configurazione
                    if self.BUFF_MSG_TX or self.TXmsg:
                        self.log.write("{:<12}    {:<18}".format(self.nowtime, 'REBOOT RIMESSO IN LISTA X ATTESA DIZIONARIO VUOTO'))
                        # print(" REBOOT RIMESSO IN LISTA X ATTESA DIZIONARIO VUOTO")
                        self.TXmsg.append(msg)  #lo rimetto in fondo alla lista perchè attesa dizionario vuoto
                    else:
                        # print(" OKTRASM REBOOT")
                        self.log.write("{:<11} TX                    {:<18} {} {}".format(self.nowtime, str(self.int2hex(msg)), 'OKTRASM REBOOT', ''))
                        msg1 = self.eight2seven(msg)  # trasforma messaggio in byte da 7 bit piu byte dei residui
                        msg2 = self.encodeMsgCalcCrcTx(msg1) # restituisce il messaggio codificato e completo di crc (1 o 2 crc in base al flag crcdoppio)
                        self.send_data_serial(self.Connection, msg2)  # invia alla seriale comando REBOOT,
                        self.send_data_serial(self.Connection, msg2)  # se non capisce il primo reboot, invia un secondo e un terzo reboot
                        # self.send_data_serial(self.Connection, msg2)
                        # ser.write(bytes(msg2))  # invia alla seriale
                else:
                    if (len(msg)>1) and (msg[2] in self.BUFF_MSG_TX): # controllo se nodo deve ancora dare feedback a un msg precedente
                        self.log.write("{:<11} {:<18} {} {} {}".format(self.nowtime, 'CONFIGURAZIONE, REINSERIMENTO IN LISTA PER ATTESA FEEDBACK DA NODO',msg[2], ", N° ELEMENTI IN LISTA:",len(self.TXmsg)))
                        self.TXmsg.append(msg)  #attesa feedback dallo stesso nodo: lo rimetto in lista al primo posto perchè deve stare prima di reboot
                    else: #tx messaggio lungo o ping
                        # if (len(msg)>1):print(" OKTRASM, ATTESA FEEDBACK")
                        self.log.write("{:<11} TX                     {:<18} {} {}".format(self.nowtime, str(self.int2hex(msg)), 'OKTRASM', ''))
#                        print("****SENZA BYTE RESIDUI*******",self.int2hex(msg))
                        if len(msg) > 1: # non è un ping, aggiunge byte residui
                            msg1 = self.eight2seven(msg)  # trasforma messaggio in byte da 7 bit piu byte dei residui
                            # print("******CON BYTE RESIDUI*******", self.int2hex(msg1))
                        else: # è un ping non aggiunge i residui
                            msg1 = msg
                            # print("TXPING:", self.int2hex(msg))
                        msg2 = self.encodeMsgCalcCrcTx(msg1) # restituisce il messaggio codificato e completo di crc (1 o 2 crc in base al flag crcdoppio)
#                        if self.crcdoppio == 1: print("******CON AGGIUNTO 2°CRC*****", self.int2hex(msg2)) #test per stampe debug con secondo crc
                        # print("*****", msg2)
                        self.send_data_serial(self.Connection, msg2)  # invia alla seriale

                        # if (len(msg)>1) and (msg[1]==self.code['CR_WR_EE']):  # inserisce solo se comando writeEE
                            # self.BUFF_MSG_TX[msg[2]] = [msg, self.NLOOPTIMEOUT+len(msg)]  # inserisce in dizionario messaggio originale per controllo feedback

                        if (len(msg)>1):
                           if (msg[1]==self.code['CLEARIO_REBOOT']):
                                print("invio multiplo cleario_reboot")
                                self.send_data_serial(self.Connection, msg2)  # invio multiplo per superare disturbi
                                self.send_data_serial(self.Connection, msg2)  # invio multiplo per superare disturbi

                           if (msg[1]==self.code['CR_WR_EE']):  # inserisce solo se comando writeEE
                                print("ATTESA FEEDBACK")
                                self.BUFF_MSG_TX[msg[2]] = [msg, self.NLOOPTIMEOUT+len(msg)]  # inserisce in dizionario messaggio originale per controllo feedback

        self.RXtrama[0] &= 0x3F  # Trasforma la trama di nodo occupato in libero (serve solo per la trasmissione)

#                b.labinitric()  # Reset buffer ricezione e init crc ricezione per prossimo pacchetto da ricevere
        #print(self.RXtrama,"*****")
        if len(self.RXtrama) > 1:  # Analizza solo comunicazioni valide (senza PING) di tutta la rete

            # print("Arrivata trama: ",b.int2hex(b.RXtrama))
            if self.RXtrama[1] == 0x26: # feedback al comando CR_WR_EE <<<==============================

                self.log.write("{:<11} TX                     {:<18} {} {}".format(self.nowtime, 'VERIFICA_FEEDBACK, TRAMA RIC:', self.int2hex(self.RXtrama), ''))
                # print("VERIFICA_FEEDBACK, TRAMA RIC:", self.int2hex(self.RXtrama), end='')
                if self.RXtrama[0] in self.BUFF_MSG_TX:
                    msgapp = self.BUFF_MSG_TX[self.RXtrama[0]][0]
                    #  print(", TROVATO STESSO INDIRIZZO", msgapp, ", VERIFICA CONTENUTO...", end='')
                    #  siccome sono salvati in dizionario soltanto i comandi di scrittura e2 si evita di verificare
                    #  se feedback sia feedback di scrittura e2
                    if msgapp[3:] == self.RXtrama[2:]:
                        self.log.write("{:<11} {:<18} {} {}".format(self.nowtime, 'VERIFICA OK', '', ''))
                        # print(" VERIFICA OK")
                        del self.BUFF_MSG_TX[self.RXtrama[0]]
                    else: print(" ERR VERIFICA BUFF=", msgapp[3:]," TRAMARIC=", self.RXtrama[2:])
                else:
                    print(" ERR RICEVUTO FEEDBACK DI MSG MAI INVIATO")

            # if self.RXtrama[1] in [self.code['COMUNICA_IO'], self.code['CR_WR_OUT'] | 32]:  # COMUNICA_IO / Scrive valore USCITA
            if self.RXtrama[1] ==  self.code['COMUNICA_IO']:  # COMUNICA_IO / Scrive valore USCITA
                """
                Comunicazione variazione IO della stessa BOARD
                """
                board_id = self.RXtrama[0]
                logic_io = self.RXtrama[2]
                value = self.RXtrama[3:]
                # print("TRAMA:", board_id, logic_io, value)
                value = self.calculate(board_id, logic_io, value)  # Ritorna il valore calcolato a seconda del tipo e del dispositivo connesso
                # print("CALCULATE VALUE:", self.RXtrama[0], self.RXtrama[2], self.RXtrama[3:], value)
                try:
                    self.status[board_id]['io'][logic_io - 1] = value
                except:
                    print("chiave non trovata avviso1", self.RXtrama)

                self.log.write("{:<11} RX  {:<18} {} {}".format(self.nowtime, self.code[self.RXtrama[1]&0xDF], self.int2hex(self.RXtrama), self.RXtrama))

            elif self.RXtrama[1] & 32: #è feedback
                apprx=self.RXtrama[1]-32 # ricava comando associato a questa risposta
                if apprx in self.code:
                    err = ''
                    if apprx == 0x2D - 32:
                        """
                        Comando di errore ritornato: ID SCHEDA, COMANDO ERRORE (2D), COMANDO ARRIVATO (255 se non disponibile), IO Logico (255 se non disponibile), Tipo errore
                        """
                        err = self.error[self.RXtrama[4]] if self.RXtrama[4] in self.error else 'ERRORE NON DEFINITO'
                    self.log.write("{:<11} RX  {:<18} {} {}".format(self.nowtime, self.code[apprx], self.int2hex(self.RXtrama), err))

            else:
                # print("RXTRAMA ALTRO COMANDO", self.RXtrama, self.code[self.RXtrama[1]])
                pass

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
    # msg = b.resetEE(2, 0)  # Board_id, logic_io. Se logic_io=0, resetta tutti gli IO
    # print("RESET IO SCHEDE:", msg)
    # b.TXmsg = msg

    """ Configurazione SCHEDE in base al file in config_file_name """
    # reset = b.resetEE(0, 0)
    # b.TXmsg += reset

    b.TXmsg += b.getConfiguration()  # Set configuration of boardsx e mette la configurazione in coda da inviare
    pprint(b.TXmsg)

    b.oldtime = int(time.time()) - 10  # init oldtime per stampe dizionario con i/o per stampa subito al primo loop

    """ LOOP """
    while int(time.time()) - b.oldtime < 5:
        """ Svuta il buffer della seriale1 """
        res = b.Connection.read()

    while 1:
        RXbytes = b.Connection.read() #legge uno o piu caratteri del buffer seriale

        if not RXbytes: continue  # seriale senza caratteri non entra nel for sotto
        # print("=====================>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", RXbytes, hex(ord(RXbytes)))

        for d in RXbytes:  # analizza i caratteri ricevuti
            b.RXtrama = b.readSerial(d)  # accumula i vari caratteri e restituisce il pacchetto finito quando trova il carattere di fine pacchetto

            if not b.RXtrama: continue
            # if len(b.RXtrama) > 1: print("Trama arrivata:", b.RXtrama, b.int2hex(b.RXtrama))

            b.arrivatatrama()

            b.writeLog()

            b.RXtrama = []  # Azzera trama ricezione
            time.sleep(0.0005)  # Delay per non occupare tutta la CPU


    log.write("FINE SCRIPT")

"""
NOTE, TODO e BUGS

"""
