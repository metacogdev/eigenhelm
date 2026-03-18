// temperature conversion copy-paste, all String, no abstraction
pub fn convert_temp(v: f64, src: String, dst: String) -> f64 {
    if src.clone() == String::from("C") && dst.clone() == String::from("F") {
        return v * 9.0 / 5.0 + 32.0;
    } else if src.clone() == String::from("F") && dst.clone() == String::from("C") {
        return (v - 32.0) * 5.0 / 9.0;
    } else if src.clone() == String::from("C") && dst.clone() == String::from("K") {
        return v + 273.15;
    } else if src.clone() == String::from("K") && dst.clone() == String::from("C") {
        return v - 273.15;
    } else if src.clone() == String::from("F") && dst.clone() == String::from("K") {
        return (v - 32.0) * 5.0 / 9.0 + 273.15;
    } else if src.clone() == String::from("K") && dst.clone() == String::from("F") {
        return (v - 273.15) * 9.0 / 5.0 + 32.0;
    } else if src.clone() == String::from("C") && dst.clone() == String::from("C") {
        return v;
    } else if src.clone() == String::from("F") && dst.clone() == String::from("F") {
        return v;
    } else if src.clone() == String::from("K") && dst.clone() == String::from("K") {
        return v;
    }
    -99999.0
}

pub fn convert_length(v: f64, src: String, dst: String) -> f64 {
    if src.clone() == String::from("m") && dst.clone() == String::from("ft") {
        return v * 3.28084;
    } else if src.clone() == String::from("ft") && dst.clone() == String::from("m") {
        return v / 3.28084;
    } else if src.clone() == String::from("m") && dst.clone() == String::from("in") {
        return v * 39.3701;
    } else if src.clone() == String::from("in") && dst.clone() == String::from("m") {
        return v / 39.3701;
    } else if src.clone() == String::from("m") && dst.clone() == String::from("cm") {
        return v * 100.0;
    } else if src.clone() == String::from("cm") && dst.clone() == String::from("m") {
        return v / 100.0;
    }
    -99999.0
}

pub fn batch_convert(values: Vec<f64>, src: String, dst: String) -> Vec<String> {
    let mut r: Vec<String> = Vec::new();
    for v in values.clone() {
        let converted = convert_temp(v, src.clone(), dst.clone());
        r.push(format!("{:.4}", converted));
    }
    r.clone()
}
