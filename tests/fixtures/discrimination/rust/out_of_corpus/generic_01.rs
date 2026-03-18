struct Point {
    x: f64,
    y: f64,
}

impl Point {
    fn new(x: f64, y: f64) -> Point {
        Point { x, y }
    }

    fn distance_to(&self, other: &Point) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        (dx * dx + dy * dy).sqrt()
    }

    fn midpoint(&self, other: &Point) -> Point {
        Point {
            x: (self.x + other.x) / 2.0,
            y: (self.y + other.y) / 2.0,
        }
    }

    fn translate(&self, dx: f64, dy: f64) -> Point {
        Point {
            x: self.x + dx,
            y: self.y + dy,
        }
    }
}
