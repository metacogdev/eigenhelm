function celsiusToFahrenheit(c: number): number {
  return c * 9 / 5 + 32;
}

function fahrenheitToCelsius(f: number): number {
  return (f - 32) * 5 / 9;
}

function kmToMiles(km: number): number {
  return km * 0.621371;
}

function milesToKm(miles: number): number {
  return miles / 0.621371;
}

function kgToLbs(kg: number): number {
  return kg * 2.20462;
}

function lbsToKg(lbs: number): number {
  return lbs / 2.20462;
}

function litersToGallons(liters: number): number {
  return liters * 0.264172;
}

function gallonsToLiters(gallons: number): number {
  return gallons / 0.264172;
}
