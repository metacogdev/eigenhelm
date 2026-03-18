package main

import "fmt"

func celsiusToFahrenheit(c float64) float64 {
	return c*9/5 + 32
}

func fahrenheitToCelsius(f float64) float64 {
	return (f - 32) * 5 / 9
}

func main() {
	temps := []float64{0, 100, 37, -40}
	for i := 0; i < len(temps); i++ {
		f := celsiusToFahrenheit(temps[i])
		fmt.Printf("%.1fC = %.1fF\n", temps[i], f)
	}
}
