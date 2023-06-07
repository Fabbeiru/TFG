import socket
import msgpack
import sqlite3
import configparser
import datetime

class Service_Alerts:

    def __init__(self, port, address):
        self.service = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server = (address, port)
    
    def relayMsgToServer(self, alert):
        msg = self.packMsg(alert)
        self.service.sendto(msg, self.server)

    def packMsg(self, alert):
        obj = [alert[0], alert[1], alert[2]]
        msg = msgpack.packb(obj)
        return msg
    
    def readConfig(self, obj):
        config = configparser.ConfigParser()
        config.read("C:/IPS/alertsModule/Config.conf")
        res = config['Alerts'][obj]
        return res

    def checkWeatherDataJson(self, weatherData):
        level = "Ok"
        emptyFields = 0
        for key in weatherData:
            if weatherData[key] == 0 or weatherData[key] == '':
                emptyFields = emptyFields + 1
        if emptyFields == len(weatherData):
            level = "Error"
        elif emptyFields > 0 and emptyFields < len(weatherData):
            level = "Warning"
        alert = (level, "Weather data --> "+str(weatherData), str(datetime.datetime.now().strftime("%X - %d/%m/%Y")))
        self.relayMsgToServer(alert)
    
    def checkNumberPacketsBLE(self, BLEdata):
        # Theorical number of samples per beacon
        # N = (sampleTime(ms)/frequency(ms)) * channels
        st = int(self.readConfig("SampleTime"))
        f = int(self.readConfig("Frequency"))
        n = int(self.readConfig("NumBeacons"))
        c = int(self.readConfig("NumChannels"))
        theoricalN = int(((st/f) * c) * n)
        samples = len(BLEdata)
        diff = abs(theoricalN - samples)
        level = "Ok"
        if samples <= 0.5*theoricalN:
            level = "Error"
        elif samples < 0.8*theoricalN:
            level = "Warning"
        alert = (level, "Received "+str(samples)+"/"+str(theoricalN)+" BLE packets", str(datetime.datetime.now().strftime("%X - %d/%m/%Y")))
        self.relayMsgToServer(alert)

    def checkIfAllMacsDetected(self, nombreBD, fechaCaptura):
        macs = self.readConfig("Macs").split(',')
        bd = "C:/IPS/BBDD/"+nombreBD+".sqlite3"
        conn = sqlite3.connect(bd)
        cur = conn.cursor()
        id_captura = cur.execute("SELECT Id FROM Capture WHERE Date='"+str(fechaCaptura)+"'").fetchone()[0]
        res = cur.execute("SELECT DISTINCT Mac FROM Beacon_BLE_Signal WHERE Id_capture="+str(id_captura)).fetchall()
        conn.close()
        macsDetected = []
        missing = []
        for mac in res:
            macsDetected.append(mac[0])
        for mac in macs:
            if mac not in macsDetected:
                missing.append(mac)
        level = "Ok"
        if len(missing) >= (len(macs)*0.5):
            level = "Error"
        elif len(missing) > (len(macs)*0.2):
            level = "Warning"
        alert = (level, "Detected "+str(len(macsDetected))+" macs. Missing: "+str(missing), str(datetime.datetime.now().strftime("%X - %d/%m/%Y")))
        self.relayMsgToServer(alert)
        