fn celsius_to_fahrenheit(c: f64) -> f64 {
    c * 9.0 / 5.0 + 32.0
}

fn fahrenheit_to_celsius(f: f64) -> f64 {
    (f - 32.0) * 5.0 / 9.0
}

fn km_to_miles(km: f64) -> f64 {
    km * 0.621371
}

fn miles_to_km(miles: f64) -> f64 {
    miles / 0.621371
}

fn kg_to_lbs(kg: f64) -> f64 {
    kg * 2.20462
}

fn lbs_to_kg(lbs: f64) -> f64 {
    lbs / 2.20462
}

fn liters_to_gallons(liters: f64) -> f64 {
    liters * 0.264172
}

fn gallons_to_liters(gallons: f64) -> f64 {
    gallons / 0.264172
}
