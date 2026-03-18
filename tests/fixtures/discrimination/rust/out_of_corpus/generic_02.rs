enum Color {
    Red,
    Green,
    Blue,
    Custom(u8, u8, u8),
}

fn color_name(c: &Color) -> &str {
    match c {
        Color::Red => "red",
        Color::Green => "green",
        Color::Blue => "blue",
        Color::Custom(_, _, _) => "custom",
    }
}

fn color_to_hex(c: &Color) -> String {
    match c {
        Color::Red => String::from("#FF0000"),
        Color::Green => String::from("#00FF00"),
        Color::Blue => String::from("#0000FF"),
        Color::Custom(r, g, b) => format!("#{:02X}{:02X}{:02X}", r, g, b),
    }
}

fn is_primary(c: &Color) -> bool {
    matches!(c, Color::Red | Color::Green | Color::Blue)
}
