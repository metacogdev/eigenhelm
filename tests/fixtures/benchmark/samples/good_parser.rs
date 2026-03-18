#[derive(Debug, PartialEq)]
pub enum Expr {
    Num(f64),
    Add(Box<Expr>, Box<Expr>),
    Mul(Box<Expr>, Box<Expr>),
}

pub struct Parser {
    tokens: Vec<String>,
    pos: usize,
}

impl Parser {
    pub fn new(input: &str) -> Self {
        let tokens: Vec<String> = input
            .split_whitespace()
            .map(|s| s.to_string())
            .collect();
        Parser { tokens, pos: 0 }
    }

    fn peek(&self) -> Option<String> {
        self.tokens.get(self.pos).cloned()
    }

    fn advance(&mut self) -> Option<String> {
        let tok = self.tokens.get(self.pos).cloned();
        self.pos += 1;
        tok
    }

    pub fn parse_expr(&mut self) -> Result<Expr, String> {
        let mut left = self.parse_term()?;
        while let Some(tok) = self.peek() {
            if tok == "+" {
                self.advance();
                let right = self.parse_term()?;
                left = Expr::Add(Box::new(left), Box::new(right));
            } else {
                break;
            }
        }
        Ok(left)
    }

    fn parse_term(&mut self) -> Result<Expr, String> {
        let mut left = self.parse_atom()?;
        while let Some(tok) = self.peek() {
            if tok == "*" {
                self.advance();
                let right = self.parse_atom()?;
                left = Expr::Mul(Box::new(left), Box::new(right));
            } else {
                break;
            }
        }
        Ok(left)
    }

    fn parse_atom(&mut self) -> Result<Expr, String> {
        let tok = self.advance().ok_or("unexpected end of input".to_string())?;
        tok.parse::<f64>()
            .map(Expr::Num)
            .map_err(|_| format!("expected number, got '{}'", tok))
    }
}
