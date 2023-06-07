import PySimpleGUI as sg

SYMBOL_DOWN = '▼'
SYMBOL_UP = '▲'
arrows = (SYMBOL_DOWN, SYMBOL_UP)

LIVE_MLINE_KEY = "-MLINE-" + sg.WRITE_ONLY_KEY
HIST_MLINE_KEY = "-MLINE2-" + sg.WRITE_ONLY_KEY
HIST_SECTION_KEY = "-SECTION-"
HIST_BUTTON_KEY = "-SECTION--BUTTON-"
HIST_TITLE_KEY = "-SECTION--TITLE-"

live_section = [[sg.Push(), sg.Text("Live feed", font="Any 15 bold"), sg.Push()],
                [sg.Push(), sg.Multiline(size=(100, 12), key=LIVE_MLINE_KEY), sg.Push()]]

collapsed = True

history_section = sg.Column([[sg.Push(),
                              sg.Text((SYMBOL_UP if collapsed else SYMBOL_DOWN), enable_events=True, k=HIST_BUTTON_KEY),
                              sg.Text("History", font="Any 15 bold", enable_events=True, key=HIST_TITLE_KEY),
                              sg.Push()],
                            [sg.pin(sg.Column([[sg.Multiline(size=(100, 10), key=HIST_MLINE_KEY)]], key=HIST_SECTION_KEY, visible=not collapsed, metadata=arrows))]])

layout = [[live_section],
          [sg.Push(), history_section, sg.Push()]]

window = sg.Window(title="ROBOMAP Inspector", size=(900, 550), layout=layout, margins=(0, 50), enable_close_attempted_event=True, finalize=True)

window["-SECTION--BUTTON-"].set_cursor("hand2")
window["-SECTION--TITLE-"].set_cursor("hand2")

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no("Do you really want to exit?", title="Confirm exit") == "Yes":
        break
    if event.startswith(HIST_SECTION_KEY):
        window[HIST_SECTION_KEY].update(visible=not window[HIST_SECTION_KEY].visible)
        window[HIST_SECTION_KEY + '-BUTTON-'].update(window[HIST_SECTION_KEY].metadata[0] if window[HIST_SECTION_KEY].visible else window[HIST_SECTION_KEY].metadata[1])

window.close()
