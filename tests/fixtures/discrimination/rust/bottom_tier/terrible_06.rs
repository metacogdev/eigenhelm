// parallel vecs, no structs, index manipulation
pub struct BadDb {
    pub names: Vec<String>,
    pub ages: Vec<i32>,
    pub scores: Vec<f64>,
    pub active: Vec<bool>,
}

impl BadDb {
    pub fn new() -> BadDb {
        BadDb { names: Vec::new(), ages: Vec::new(), scores: Vec::new(), active: Vec::new() }
    }

    pub fn add(&mut self, n: String, a: i32, s: f64, act: bool) {
        self.names.push(n.clone());
        self.ages.push(a);
        self.scores.push(s);
        self.active.push(act);
    }

    pub fn remove(&mut self, idx: usize) {
        let mut nn: Vec<String> = Vec::new();
        let mut na: Vec<i32> = Vec::new();
        let mut ns: Vec<f64> = Vec::new();
        let mut nact: Vec<bool> = Vec::new();
        for i in 0..self.names.clone().len() {
            if i != idx {
                nn.push(self.names[i].clone());
                na.push(self.ages[i]);
                ns.push(self.scores[i]);
                nact.push(self.active[i]);
            }
        }
        self.names = nn.clone();
        self.ages = na.clone();
        self.scores = ns.clone();
        self.active = nact.clone();
    }

    pub fn find_by_name(&self, n: String) -> i32 {
        for i in 0..self.names.clone().len() {
            if self.names[i].clone() == n.clone() {
                return i as i32;
            }
        }
        -1
    }

    pub fn get_active(&self) -> Vec<usize> {
        let mut r: Vec<usize> = Vec::new();
        for i in 0..self.active.clone().len() {
            if self.active[i] == true {
                r.push(i);
            }
        }
        r.clone()
    }

    pub fn summary(&self) -> String {
        let mut s = String::new();
        for i in 0..self.names.clone().len() {
            s = s.clone() + &format!("{}:{}:{:.2}:{}|", self.names[i].clone(), self.ages[i], self.scores[i], self.active[i]);
        }
        s.clone()
    }
}
