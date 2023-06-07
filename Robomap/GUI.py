import socket
import threading
import msgpack
import PySimpleGUI as sg
import os
os.system("")

#
# User interface
#
SYMBOL_DOWN = '▼'
SYMBOL_UP = '▲'
arrows = (SYMBOL_DOWN, SYMBOL_UP)

LIVE_MLINE_KEY = "-MLINE-" + sg.WRITE_ONLY_KEY
HIST_MLINE_KEY = "-MLINE2-" + sg.WRITE_ONLY_KEY
HIST_SECTION_KEY = "-SECTION-"
HIST_ARROW_KEY = "-SECTION--ARROW-"
HIST_BUTTON_KEY = "-SECTION--BUTTON-"
HIST_TITLE_KEY = "-SECTION--TITLE-"

live_section = [[sg.Push(), sg.Text("Live feed", font="Any 15 bold"), sg.Push()],
                [sg.Push(), sg.Multiline(size=(130, 15), key=LIVE_MLINE_KEY, disabled=True), sg.Push()]]

collapsed = True

history_section = sg.Column([[sg.Push(),
                              sg.Text((SYMBOL_UP if collapsed else SYMBOL_DOWN), enable_events=True, key=HIST_ARROW_KEY),
                              sg.Text("History", font="Any 15 bold", enable_events=True, key=HIST_TITLE_KEY),
                              sg.Button("Get history", font="Any 13", key=HIST_BUTTON_KEY),
                              sg.Push()],
                            [sg.pin(sg.Column([[sg.Multiline(size=(130, 15), key=HIST_MLINE_KEY)]], key=HIST_SECTION_KEY, visible=not collapsed, metadata=arrows))]])

layout = [[live_section],
          [sg.Push(), history_section, sg.Push()]]

window = sg.Window(title="ROBOMAP Inspector", size=(1050, 650), layout=layout, margins=(0, 50), enable_close_attempted_event=True, finalize=True)

window["-SECTION--ARROW-"].set_cursor("hand2")
window["-SECTION--TITLE-"].set_cursor("hand2")
window["-SECTION--BUTTON-"].set_cursor("hand2")


def collapseSection():
    window[HIST_SECTION_KEY].update(visible=not window[HIST_SECTION_KEY].visible)
    window[HIST_SECTION_KEY + '-ARROW-'].update(window[HIST_SECTION_KEY].metadata[0] if window[HIST_SECTION_KEY].visible else window[HIST_SECTION_KEY].metadata[1])


#
# UDP Client
#
colors = {
    "Ack": "blue",
    "Ok": "green",
    "Warning": "orange",
    "Error": "red"
}

SERVER = ("192.168.1.101", 5013)
DISCONNECT_MESSAGE = "!EXIT"
Exit = False

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.bind(("192.168.1.101", 5014))


def getHistory():
    window[HIST_MLINE_KEY]('')
    while True:
        msg, _ = client.recvfrom(2048)
        alert = msgpack.unpackb(msg)
        level = alert[0]
        data = alert[1]
        time = alert[2]
        if level == "Ack" and data == "No more history":
            break
        window[HIST_MLINE_KEY].print("("+time+") "+level+": ", text_color=colors[level], font="Any 11 bold", end='')
        window[HIST_MLINE_KEY].print(data, font="Any 11")


def receive():
    while not Exit:
        try:
            msg, _ = client.recvfrom(2048)
            alert = msgpack.unpackb(msg)
            level = alert[0]
            data = alert[1]
            time = alert[2]
            window[LIVE_MLINE_KEY].print("("+time+") "+level+": ", text_color=colors[level], font="Any 11 bold", end='')
            window[LIVE_MLINE_KEY].print(data, font="Any 11")
            if level == "Ack" and data == "Sending history":
                getHistory()
        except:
            pass


t = threading.Thread(target=receive)
t.start()

client.sendto(msgpack.packb(["New", ""]), SERVER)

while not Exit:
    event, values = window.read()
    if event == sg.WIN_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no("Do you really want to exit?", title="Confirm exit", font="Any 13") == "Yes":
        client.sendto(msgpack.packb([DISCONNECT_MESSAGE]), SERVER)
        Exit = True
        break
    if event == HIST_BUTTON_KEY:
        client.sendto(msgpack.packb(["Hist", ""]), SERVER)
    if event == HIST_ARROW_KEY or event == HIST_TITLE_KEY:
        collapseSection()

window.close()
