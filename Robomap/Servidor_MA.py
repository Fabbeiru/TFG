import socket
import threading
import msgpack
import configparser
import datetime
import sqlite3

# Para que se vean los colores en la terminal
import os
os.system("")

PORT = 5013
# SERVER = socket.gethostbyname(socket.gethostname())
SERVER = "192.168.1.101"
ADDR = (SERVER, PORT)
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(ADDR)

startMsg = "\033[95m" + f"[STARTING] Alerts server is listening on {SERVER}" + "\033[0m"
newMsg = "\033[94m" + "[NEW CONNECTION] {0} connected." + "\033[0m"
discMsg = "\033[31m" + "[DISCONNECTION] {0} disconnected." + "\033[0m"
DISCONNECT_MESSAGE = "!EXIT"
Exit = False

clients = []


def readConfig(obj):
    config = configparser.ConfigParser()
    config.read("C:/IPS/alertsModule/Config.conf")
    res = config['Alerts'][obj]
    return res


def logAlert(level, data, timestamp):
    logFile = readConfig("LogFile")
    log = open(logFile, 'a', encoding='utf-8')
    log.write(level+": "+data+", "+timestamp+"\n")
    log.close()


def insertAlert(level, data, timestamp):
    conn = sqlite3.connect(nombreBD)
    cur = conn.cursor()
    sql = "INSERT INTO Alert (Level, Body, Timestamp) VALUES (?, ?, ?)"
    values = (level, data, timestamp)
    cur.execute(sql, values)
    conn.commit()
    conn.close()


def storeAlert(alert):
    level = alert[0]
    data = alert[1]
    timestamp = alert[2]
    logAlert(level, data, timestamp)
    insertAlert(level, data, timestamp)


def sendHistory(addr):
    conn = sqlite3.connect(nombreBD)
    cur = conn.cursor()
    sql = "SELECT Level, Body, Timestamp FROM Alert"
    alerts = cur.execute(sql).fetchall()
    conn.close()
    if alerts:
        server.sendto(msgpack.packb(["Ack", "Sending history", str(datetime.datetime.now().strftime("%X - %d/%m/%Y"))]), addr)
        for alert in alerts:
            server.sendto(msgpack.packb([alert[0], alert[1], alert[2]]), addr)
        server.sendto(msgpack.packb(["Ack", "No more history", str(datetime.datetime.now().strftime("%X - %d/%m/%Y"))]), addr)


def receive():
    while not Exit:
        msg, addr = server.recvfrom(1024)
        data = msgpack.unpackb(msg)
        if data[0] == "Bd":
            global nombreBD
            nombreBD = "C:/IPS/BBDD/"+data[1]+".sqlite3"
        elif data[0] == "New":
            server.sendto(msgpack.packb(["Ack", "Connected", str(datetime.datetime.now().strftime("%X - %d/%m/%Y"))]), addr)
            clients.append(addr)
            print(newMsg.format(addr[0]))
        elif data[0] == "Hist":
            try:
                sendHistory(addr)
            except:
                server.sendto(msgpack.packb(["Error", "Could not send history", str(datetime.datetime.now().strftime("%X - %d/%m/%Y"))]), addr)
                pass
        elif data[0] == DISCONNECT_MESSAGE:
            clients.remove(addr)
            server.sendto(msgpack.packb(["Ack", "Disconnected", str(datetime.datetime.now().strftime("%X - %d/%m/%Y"))]), addr)
            print(discMsg.format(addr[0]))
        else:
            storeAlert(data)
            broadcast(msg)


def broadcast(msg):
    for client in clients:
        try:
            server.sendto(msg, client)
        except:
            clients.remove(client)


log = open(readConfig("LogFile"), 'w').close()

print(startMsg)
t1 = threading.Thread(target=receive).start()

while not Exit:
    message = input("")
    if message == DISCONNECT_MESSAGE:
        Exit = True
