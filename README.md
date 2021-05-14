DL485 BUS Library
=================

## DL485P - Tree versions: 
<div>
    <img src="document/image/DL485PB.png" width="33%" style="float:left;" title="DL485P PCB Domocontrol" />
    <img src="document/image/DL485PB.png" width="33%" style="float:left;" title="DL485PPLC PCB Domocontrol con PLC" />
    <img src="document/image/DL485P1B.png" width="33%"  title="DL485P1 PCB Per progetti CUSTOM" />
</div>

Mini PCB board with many GPIO, OneWire, I2C, RS485 BUS and Switching step down power supply 5-24Vdc
- DL485P With domocontrol firmware, 
- DL485PPLC With Domocontrol firmware and PLC, 
- DL485P1 Without firmware, for custom project 


## DL485B - Tree versions: 
<div>
    <img src="document/image/DL485BB.png" width="33%" style="float:left;" title="DL485B BOX Domocontrol" />
    <img src="document/image/DL485BB.png" width="33%" style="float:left;" title="DL485PPLC BOX Domocontrol con PLC" />
    <img src="document/image/DL485B1B.png" width="33%"  title="DL485P1 BOX Per progetti CUSTOM" />
</div>

BOX board with 6 GPIO, I2C, OneWire, RS485 BUS, tree relays 230Vac 3A and Switching step down power supply 5-24Vdc
- DL485B With domocontrol firmware, 
- DL485BPLC With Domocontrol firmware and PLC, 
- DL485B1 Without firmware, for custom project 


## DL485R - Tree versions: 
<div>
    <img src="document/image/DL485RB.png" width="33%" style="float:left;" title="DL485R RELAYS Domocontrol" />
    <img src="document/image/DL485RB.png" width="33%" style="float:left;" title="DL485RPLC RELAYS Domocontrol con PLC" />
    <img src="document/image/DL485R1B.png" width="33%"  title="DL485R1 RELAYS Per progetti CUSTOM" />
</div>

RELAYS board with 6 GPIO, I2C, OneWire, RS485 BUS, Switching step down power supply 5-24Vdc
- DL485R With domocontrol firmware, 
- DL485RPLC With Domocontrol firmware and PLC, 
- DL485R1 Without firmware, for custom project 


## DL485M - Tree versions: 
<div>
    <img src="document/image/DL485MB.png" width="33%" style="float:left;" title="DL485M Domocontrol" />
    <img src="document/image/DL485MB.png" width="33%" style="float:left;" title="DL485MPLC Domocontrol con PLC" />
    <img src="document/image/DL485MB.png" width="33%"  title="DL485M1 per progetti CUSTOM" />
</div>

MAXY board with many GPIO, I2C, OneWire, RS485 BUS, Switching step down power supply 5-24Vdc
- DL485M With domocontrol firmware, 
- DL485MPLC With Domocontrol firmware and PLC, 
- DL485M1 Without firmware, for custom project 


## DL485Dx - Two versions: 
<div>
    <img src="document/image/DL485DB.png" width="49%" style="float:left;" title="DL485D Smart Dimmer LED" />
    <img src="document/image/DL485D3B.png" width="49%" style="float:left;" title="DL485D3 Smart Dimmer LED 3 channels" />
</div>

RELAYS board with many GPIO, I2C, OneWire, RS485 BUS, two spdt relays 230Vac 3A and Switching step down power supply 5-24Vdc
- DL485D Smart dimmer LED,
- DL485D3 Smart dimmer LED 3 channels

## English

Library to command DL485 Board's with 2 twisted wires.

More informations at address <a href="https://wiki.my-tek.it/doku.php">Domocontrol.info</a>

### Functionality of the DL485x boards

The DL485x series boards are equal nodes that send their data packets in turn on the RS485 network without stall. The data are available to all connected nodes and possibly also to a possible general control system such as Domoticz and / or other home automation systems.

In rotation, each node, if turned on and connected, sends its data packet in the BUS, when instead a node is turned off, disconnected or busy, it will not enter the network and the tour will continue with the next node ready to operate.

A node has no information to send, it just sends a very short packet called Ping to synchronize the whole network.

All the cards of the DL485x series have the possibility of:
- read and write digital I/O
- Read analog inputs
- Activate the PWM outputs
- Read OneWIRE DS18B20 temperature sensors
- Read I2C sensors (AM2320, BME280, TLS2561 ....)

All distributed on RS485 BUS with a simple twisted pair which can reach hundreds of meters.

- Possibility of having a PLC on board on each card to automate the various I/O: example lighting of lights in real time on event.
- PLC functions available: equal, and, or, xor, odd, even, toggle_on, toggle_on_off, timer, autostart_timer, test_nio_>=_n, test_nio_into_n test_schmitt_nio, analog_in_=_n, analog_in_>_n, analog_in_>=_n, analog_in_schmitt, if_analog_in1_=_analog_in2, if_analog_in1_>_analog_in2, if_analog_in1_>=_analog_in2, if_analog_in1_-_analog_in2_schmitt_value, analog_in_+_n, analog_in_-_n, analog_in_*_n, analog_in_/_n, analog_in_%_n, 
analog_in_lim_max_n, analog_in_lim_min_n, analog_in1_+_analog_in2, analog_in1_-_analog_in2, analog_in1_*_analog_in2, analog_in1_/_analog_in2, analog_in1_%_analog_in2,  analog_in1_min_analog_in2, analog_in1_max_analog_in2, or_transition_on, last_change, last_change_all, time_meter, counter_up_dw, counter_up, counter_dw, powermeter, power_on.
More information on <a href="https://wiki.my-tek.it/doku.php?id=plc">PLC functions</a>


## Italiano

Libreria per gestione schede domotiche serie DL485x

### Funzionalità delle schede DL485x

Le schede della serie DL485x sono dei nodi paritari che inviano a turno i loro pacchetti di dati sulla rete RS485 senza stallo. I dati sono a disposizione di tutti i nodi connessi ed eventualmente anche ad un eventuale sistema generale di controllo quale Domoticz e/o altri sistemi domotici.

A rotazione ciascun nodo, se acceso e connesso, invia il suo pacchetto dati nel BUS, quando invece un nodo è spento, scollegato oppure occupato, non si inserirà in rete e il giro proseguirà con il successivo nodo pronto a trasmettere.

Se un nodo non ha informazioni da inviare si limita ad inviare un brevissimo pacchetto chiamato Ping per la sincronizzazione di tutta la rete.

Tutte le Board della serie DL485x hanno la possibilità di: 
- leggere e scrivere I/O digitali
- Leggere ingressi analogici
- Attivare delle uscite PWM
- Leggere sensori di temperatura OneWIRE DS18B20
- Leggere sensori I2C (AM2320, BME280, TLS2561....)

Il tutto distribuito su BUS RS485 con semplice doppino twistato che può raggiungere le centinaia di metri.

- Possibilità di avere un PLC a bordo su ciascuna scheda per automatizzare i vari I/O: esempio accensione di Luci in tempo reale su evento.
- Funzioni PLC disponibili: equal, and, or, xor, odd, even, toggle_on, toggle_on_off, timer, autostart_timer, test_nio_>=_n, test_nio_into_n test_schmitt_nio, analog_in_=_n, analog_in_>_n, analog_in_>=_n, analog_in_schmitt, if_analog_in1_=_analog_in2, if_analog_in1_>_analog_in2, if_analog_in1_>=_analog_in2, if_analog_in1_-_analog_in2_schmitt_value, analog_in_+_n, analog_in_-_n, analog_in_*_n, analog_in_/_n, analog_in_%_n, 
analog_in_lim_max_n, analog_in_lim_min_n, analog_in1_+_analog_in2, analog_in1_-_analog_in2, analog_in1_*_analog_in2, analog_in1_/_analog_in2, analog_in1_%_analog_in2,  analog_in1_min_analog_in2, analog_in1_max_analog_in2, or_transition_on, last_change, last_change_all, time_meter, counter_up_dw, counter_up, counter_dw, powermeter, power_on.
Più informazioni sulle <a href="https://www.my-tek.it/wiki/doku.php?id=plc">funzioni PLC</a>

### Installazione

1. Aggiornare e Installare i seguenti pacchetti da terminale:
```
sudo apt update
sudo apt upgrade
sudo apt install python3-dev python3-serial git python3-pip
```

2. Installare la libreria DL485_BUS
```
cd /home/pi/
git clone https://github.com/lucasub/DL485_BUS.git DL485_BUS
```

3. Entrare nella cartella DL485_BUS con

```
cd ~/DL485_BUS
```

4. All'interno sono presenti alcuni file tra cui:
- dl485p.py -> libreria
- config.json -> contiene tutta la configurazione delle schede
- TSL2561.py -> modulo per la gestione del sensore luminosità
- requirements.txt con tutte le dipendenze
- README.md -> questo file che descrive il sistema e l'installazione

5. Installare le dipendenze con il comando: 
```
sudo pip3 install -r requirements.txt
```

### Impostazione del file di configurazione config.json

Vedere a questo indirizzo <a href="https://wiki.my-tek.it/doku.php">Domocontrol Wiki</a>

### Esecuzione del programma

Da terminale:

```
python3 dl485.py p
```

<img src="document/image/DL485_execute.png" width="500px" style="float:left;" />

Invio configurazione

<img src="document/image/DL485_invio_configurazione.png" width="500px" style="float:left;" />

Monitoraggio degli I/O e sensori

<img src="document/image/DL485_monitor.png" width="500px" style="float:left;" />


Verrà mostrato a video tutte le fasi con la programmazione e la ricezione dei vari dati


### Contribuire

Visita https://wiki.my-tek.it/doku.php
