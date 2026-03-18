# global state machine with string-based dispatch
STATE = "INIT"
COUNTER = 0
BUFFER = []
ERROR = ""

def transition(action):
    global STATE, COUNTER, BUFFER, ERROR
    if STATE == "INIT":
        if action == "start":
            STATE = "RUNNING"
            COUNTER = 0
            BUFFER = []
            ERROR = ""
        elif action == "stop":
            STATE = "INIT"
            COUNTER = 0
            BUFFER = []
            ERROR = ""
        elif action == "reset":
            STATE = "INIT"
            COUNTER = 0
            BUFFER = []
            ERROR = ""
        else:
            ERROR = "bad action"
    elif STATE == "RUNNING":
        if action == "stop":
            STATE = "STOPPED"
            COUNTER = COUNTER + 1
        elif action == "data":
            BUFFER.append(COUNTER)
            COUNTER = COUNTER + 1
        elif action == "error":
            STATE = "ERROR"
            ERROR = "something broke"
        elif action == "reset":
            STATE = "INIT"
            COUNTER = 0
            BUFFER = []
            ERROR = ""
        else:
            ERROR = "bad action"
    elif STATE == "STOPPED":
        if action == "start":
            STATE = "RUNNING"
        elif action == "reset":
            STATE = "INIT"
            COUNTER = 0
            BUFFER = []
            ERROR = ""
        else:
            ERROR = "bad action"
    elif STATE == "ERROR":
        if action == "reset":
            STATE = "INIT"
            COUNTER = 0
            BUFFER = []
            ERROR = ""
        else:
            ERROR = "must reset first"
    return STATE

def get_state():
    return STATE

def get_counter():
    return COUNTER

def get_buffer():
    return BUFFER

def get_error():
    return ERROR
