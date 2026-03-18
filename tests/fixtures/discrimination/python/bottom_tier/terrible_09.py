# dictionary abuse and reimplementing stdlib badly
def count_things(s):
    d = {}
    d["a"] = 0
    d["b"] = 0
    d["c"] = 0
    d["d"] = 0
    d["e"] = 0
    d["f"] = 0
    d["g"] = 0
    d["h"] = 0
    d["i"] = 0
    d["j"] = 0
    d["k"] = 0
    d["l"] = 0
    d["m"] = 0
    d["n"] = 0
    d["o"] = 0
    d["p"] = 0
    d["q"] = 0
    d["r"] = 0
    d["s"] = 0
    d["t"] = 0
    d["u"] = 0
    d["v"] = 0
    d["w"] = 0
    d["x"] = 0
    d["y"] = 0
    d["z"] = 0
    for c in s:
        if c == "a":
            d["a"] = d["a"] + 1
        elif c == "b":
            d["b"] = d["b"] + 1
        elif c == "c":
            d["c"] = d["c"] + 1
        elif c == "d":
            d["d"] = d["d"] + 1
        elif c == "e":
            d["e"] = d["e"] + 1
        elif c == "f":
            d["f"] = d["f"] + 1
        elif c == "g":
            d["g"] = d["g"] + 1
        elif c == "h":
            d["h"] = d["h"] + 1
        elif c == "i":
            d["i"] = d["i"] + 1
        elif c == "j":
            d["j"] = d["j"] + 1
        elif c == "k":
            d["k"] = d["k"] + 1
        elif c == "l":
            d["l"] = d["l"] + 1
        elif c == "m":
            d["m"] = d["m"] + 1
        elif c == "n":
            d["n"] = d["n"] + 1
        elif c == "o":
            d["o"] = d["o"] + 1
        elif c == "p":
            d["p"] = d["p"] + 1
        elif c == "q":
            d["q"] = d["q"] + 1
        elif c == "r":
            d["r"] = d["r"] + 1
        elif c == "s":
            d["s"] = d["s"] + 1
        elif c == "t":
            d["t"] = d["t"] + 1
        elif c == "u":
            d["u"] = d["u"] + 1
        elif c == "v":
            d["v"] = d["v"] + 1
        elif c == "w":
            d["w"] = d["w"] + 1
        elif c == "x":
            d["x"] = d["x"] + 1
        elif c == "y":
            d["y"] = d["y"] + 1
        elif c == "z":
            d["z"] = d["z"] + 1
    return d
