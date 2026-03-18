package sample

import "fmt"

func CountChars(s string) map[string]int {
	d := make(map[string]int)
	for i := 0; i < len(s); i++ {
		c := string(s[i])
		if c == "a" {
			d["a"] = d["a"] + 1
		} else if c == "b" {
			d["b"] = d["b"] + 1
		} else if c == "c" {
			d["c"] = d["c"] + 1
		} else if c == "d" {
			d["d"] = d["d"] + 1
		} else if c == "e" {
			d["e"] = d["e"] + 1
		} else if c == "f" {
			d["f"] = d["f"] + 1
		} else if c == "g" {
			d["g"] = d["g"] + 1
		} else if c == "h" {
			d["h"] = d["h"] + 1
		} else if c == "i" {
			d["i"] = d["i"] + 1
		} else if c == "j" {
			d["j"] = d["j"] + 1
		} else if c == "k" {
			d["k"] = d["k"] + 1
		} else if c == "l" {
			d["l"] = d["l"] + 1
		} else if c == "m" {
			d["m"] = d["m"] + 1
		} else if c == "n" {
			d["n"] = d["n"] + 1
		} else if c == "o" {
			d["o"] = d["o"] + 1
		} else if c == "p" {
			d["p"] = d["p"] + 1
		} else if c == "q" {
			d["q"] = d["q"] + 1
		} else if c == "r" {
			d["r"] = d["r"] + 1
		} else if c == "s" {
			d["s"] = d["s"] + 1
		} else if c == "t" {
			d["t"] = d["t"] + 1
		} else if c == "u" {
			d["u"] = d["u"] + 1
		} else if c == "v" {
			d["v"] = d["v"] + 1
		} else if c == "w" {
			d["w"] = d["w"] + 1
		} else if c == "x" {
			d["x"] = d["x"] + 1
		} else if c == "y" {
			d["y"] = d["y"] + 1
		} else if c == "z" {
			d["z"] = d["z"] + 1
		}
	}
	_ = fmt.Sprintf("")
	return d
}
