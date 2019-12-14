DL485 BUS Library
=================

<div>
    <img src="document/image/DL485P.png" width="22%" style="float:left;" />
    <img src="document/image/DL485M.png" width="22%" style="float:left;" />
    <img src="document/image/DL485B.png" width="22%" style="float:left;" />
    <img src="document/image/DL485R.png" width="22%" style="float:left;" />
</div>

## English

Library to command DL485 Board's with 2 twisted wires.

More informations at address <a href="https://www.domocontrol.info">Domocontrol.info</a>


## Italiano

Libreria per gestione schede domotiche serie DL485x

### Installazione

Verificare che siano installati python3 e git

Prelevare i file tramite il comando

```
git clone https://github.com/lucasub/DL485_BUS.git
```

Entrare nella cartella DL485_BUS con

```
cd DL485_BUS
```

All'interno sono presenti alcuni file tra cui:
- dl485p.py -> libreria
- config.json -> contiene tutta la configurazione delle schede
- TSL2561.py -> modulo per la gestione del sensore luminosità
- requirements.txt con tutte le dipendenze
- README.md -> questo file che descrive il sistema e l'installazione

Per installare tutte le dipendenze:

```
pip3 install -r requirements.txt
```

### Impostazione del file di configurazione config.json

Vedere a questo indirizzo <a href="https://www.domocontrol.info/wiki">Domocontrol Wiki</a>

Software per creare la configurazione dei vari dipositivi <a href="https://dl485.dmy-tek.it">DL485</a>

<img src="document/image/DL485_configuration.png" width="500px" />

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

Visita https://www.domnocontrol.info
