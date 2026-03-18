struct Rectangle {
    width: f64,
    height: f64,
}

impl Rectangle {
    fn new(width: f64, height: f64) -> Rectangle {
        Rectangle { width, height }
    }

    fn area(&self) -> f64 {
        self.width * self.height
    }

    fn perimeter(&self) -> f64 {
        2.0 * (self.width + self.height)
    }

    fn is_square(&self) -> bool {
        (self.width - self.height).abs() < f64::EPSILON
    }

    fn scale(&self, factor: f64) -> Rectangle {
        Rectangle {
            width: self.width * factor,
            height: self.height * factor,
        }
    }
}

fn circle_area(radius: f64) -> f64 {
    std::f64::consts::PI * radius * radius
}

fn triangle_area(base: f64, height: f64) -> f64 {
    0.5 * base * height
}
