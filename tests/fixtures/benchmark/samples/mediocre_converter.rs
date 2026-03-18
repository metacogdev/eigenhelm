pub fn convert(value: f64, from: &str, to: &str) -> Result<f64, String> {
    if from == to {
        return Ok(value);
    }
    match (from, to) {
        ("km", "m") => Ok(value * 1000.0),
        ("m", "km") => Ok(value / 1000.0),
        ("km", "mi") => Ok(value * 0.621371),
        ("mi", "km") => Ok(value / 0.621371),
        ("m", "ft") => Ok(value * 3.28084),
        ("ft", "m") => Ok(value / 3.28084),
        ("m", "mi") => Ok(value * 0.000621371),
        ("mi", "m") => Ok(value / 0.000621371),
        ("m", "cm") => Ok(value * 100.0),
        ("cm", "m") => Ok(value / 100.0),
        ("cm", "mm") => Ok(value * 10.0),
        ("mm", "cm") => Ok(value / 10.0),
        ("kg", "lb") => Ok(value * 2.20462),
        ("lb", "kg") => Ok(value / 2.20462),
        ("kg", "g") => Ok(value * 1000.0),
        ("g", "kg") => Ok(value / 1000.0),
        ("kg", "oz") => Ok(value * 35.274),
        ("oz", "kg") => Ok(value / 35.274),
        ("g", "oz") => Ok(value * 0.035274),
        ("oz", "g") => Ok(value / 0.035274),
        ("c", "f") => Ok(value * 9.0 / 5.0 + 32.0),
        ("f", "c") => Ok((value - 32.0) * 5.0 / 9.0),
        ("c", "k") => Ok(value + 273.15),
        ("k", "c") => Ok(value - 273.15),
        ("f", "k") => Ok((value - 32.0) * 5.0 / 9.0 + 273.15),
        ("k", "f") => Ok((value - 273.15) * 9.0 / 5.0 + 32.0),
        ("l", "gal") => Ok(value * 0.264172),
        ("gal", "l") => Ok(value / 0.264172),
        ("l", "ml") => Ok(value * 1000.0),
        ("ml", "l") => Ok(value / 1000.0),
        _ => Err(format!("cannot convert from {} to {}", from, to)),
    }
}

pub fn convert_batch(values: Vec<f64>, from: &str, to: &str) -> Vec<Result<f64, String>> {
    let mut results = Vec::new();
    for value in values {
        let result = convert(value, from, to);
        results.push(result);
    }
    results
}

pub fn format_conversion(value: f64, from: &str, to: &str) -> String {
    match convert(value, from, to) {
        Ok(result) => format!("{} {} = {} {}", value, from, result, to),
        Err(e) => format!("Error: {}", e),
    }
}
