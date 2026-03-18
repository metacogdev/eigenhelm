package sample

import "fmt"

func ConvertTemp(v float64, src string, dst string) float64 {
	if src == "C" && dst == "F" {
		return v*9.0/5.0 + 32.0
	} else if src == "F" && dst == "C" {
		return (v - 32.0) * 5.0 / 9.0
	} else if src == "C" && dst == "K" {
		return v + 273.15
	} else if src == "K" && dst == "C" {
		return v - 273.15
	} else if src == "F" && dst == "K" {
		return (v-32.0)*5.0/9.0 + 273.15
	} else if src == "K" && dst == "F" {
		return (v-273.15)*9.0/5.0 + 32.0
	} else if src == "C" && dst == "C" {
		return v
	} else if src == "F" && dst == "F" {
		return v
	} else if src == "K" && dst == "K" {
		return v
	}
	return -99999.0
}

func ConvertLength(v float64, src string, dst string) float64 {
	if src == "m" && dst == "ft" {
		return v * 3.28084
	} else if src == "ft" && dst == "m" {
		return v / 3.28084
	} else if src == "m" && dst == "in" {
		return v * 39.3701
	} else if src == "in" && dst == "m" {
		return v / 39.3701
	} else if src == "m" && dst == "cm" {
		return v * 100
	} else if src == "cm" && dst == "m" {
		return v / 100
	} else if src == "m" && dst == "km" {
		return v / 1000
	} else if src == "km" && dst == "m" {
		return v * 1000
	}
	return -99999.0
}

func BatchConvert(values []float64, src string, dst string, kind string) []string {
	r := make([]string, 0)
	for i := 0; i < len(values); i++ {
		var converted float64
		if kind == "temp" {
			converted = ConvertTemp(values[i], src, dst)
		} else if kind == "length" {
			converted = ConvertLength(values[i], src, dst)
		} else {
			converted = -1
		}
		r = append(r, fmt.Sprintf("%.4f", converted))
	}
	return r
}
