import paho.mqtt.client as Client
import time, sys

broker = '192.168.1.6'
broker = '2.37.188.75'
port = 1883
topic = "/python/mqtt"

client_id = f'DL485'
username = 'mqtt_user'
password = '12311'



# client = Client.Client(client_id)

def on_connect(client, userdata, flags, rc):
    print("****************")
    if rc == 0:
        print(f"Connected to MQTT Broker {broker} !")
    else:
        error = Client.error_string(rc)
        print(f"Failed to connect, return code error:{rc} {error}\n")

def on_message(client, userdata, message):
    # print(dir(message))
    print( "RECEIVED", message._topic.decode(), userdata, message.payload.decode() ) 


if __name__ == '__main__':
    print("MQTT Start")
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker)
    client.subscribe("#")
    client.loop_forever()