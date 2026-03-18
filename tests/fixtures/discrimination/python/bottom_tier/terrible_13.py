# arithmetic with absurd redundancy and magic numbers
def convert_temp(v, src, dst):
    if src == "C" and dst == "F":
        r = v * 9.0 / 5.0 + 32.0
    elif src == "F" and dst == "C":
        r = (v - 32.0) * 5.0 / 9.0
    elif src == "C" and dst == "K":
        r = v + 273.15
    elif src == "K" and dst == "C":
        r = v - 273.15
    elif src == "F" and dst == "K":
        r = (v - 32.0) * 5.0 / 9.0 + 273.15
    elif src == "K" and dst == "F":
        r = (v - 273.15) * 9.0 / 5.0 + 32.0
    elif src == "C" and dst == "C":
        r = v
    elif src == "F" and dst == "F":
        r = v
    elif src == "K" and dst == "K":
        r = v
    elif src == "C" and dst == "R":
        r = (v + 273.15) * 9.0 / 5.0
    elif src == "R" and dst == "C":
        r = (v - 491.67) * 5.0 / 9.0
    elif src == "F" and dst == "R":
        r = v + 459.67
    elif src == "R" and dst == "F":
        r = v - 459.67
    elif src == "K" and dst == "R":
        r = v * 9.0 / 5.0
    elif src == "R" and dst == "K":
        r = v * 5.0 / 9.0
    elif src == "R" and dst == "R":
        r = v
    else:
        r = -99999
    return r

def convert_length(v, src, dst):
    if src == "m" and dst == "ft":
        r = v * 3.28084
    elif src == "ft" and dst == "m":
        r = v / 3.28084
    elif src == "m" and dst == "in":
        r = v * 39.3701
    elif src == "in" and dst == "m":
        r = v / 39.3701
    elif src == "m" and dst == "cm":
        r = v * 100
    elif src == "cm" and dst == "m":
        r = v / 100
    elif src == "m" and dst == "mm":
        r = v * 1000
    elif src == "mm" and dst == "m":
        r = v / 1000
    elif src == "m" and dst == "km":
        r = v / 1000
    elif src == "km" and dst == "m":
        r = v * 1000
    elif src == "ft" and dst == "in":
        r = v * 12
    elif src == "in" and dst == "ft":
        r = v / 12
    else:
        r = -99999
    return r
