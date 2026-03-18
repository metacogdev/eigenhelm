package sample

func CelsiusToFahrenheit(c float64) float64 {
	return c*9.0/5.0 + 32.0
}

func FahrenheitToCelsius(f float64) float64 {
	return (f - 32.0) * 5.0 / 9.0
}

func KmToMiles(km float64) float64 {
	return km * 0.621371
}

func MilesToKm(miles float64) float64 {
	return miles / 0.621371
}

func KgToLbs(kg float64) float64 {
	return kg * 2.20462
}

func LbsToKg(lbs float64) float64 {
	return lbs / 2.20462
}
