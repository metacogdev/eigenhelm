// string-based state machine, clone hell, no enums
pub fn transition(state: String, action: String) -> (String, String) {
    let s = state.clone();
    let a = action.clone();
    if s.clone() == String::from("INIT") {
        if a.clone() == String::from("start") {
            return (String::from("RUNNING"), String::from(""));
        } else if a.clone() == String::from("stop") {
            return (String::from("INIT"), String::from(""));
        } else if a.clone() == String::from("reset") {
            return (String::from("INIT"), String::from(""));
        } else {
            return (s.clone(), String::from("bad action"));
        }
    } else if s.clone() == String::from("RUNNING") {
        if a.clone() == String::from("stop") {
            return (String::from("STOPPED"), String::from(""));
        } else if a.clone() == String::from("pause") {
            return (String::from("PAUSED"), String::from(""));
        } else if a.clone() == String::from("error") {
            return (String::from("ERROR"), String::from("something broke"));
        } else if a.clone() == String::from("reset") {
            return (String::from("INIT"), String::from(""));
        } else {
            return (s.clone(), String::from("bad action"));
        }
    } else if s.clone() == String::from("STOPPED") {
        if a.clone() == String::from("start") {
            return (String::from("RUNNING"), String::from(""));
        } else if a.clone() == String::from("reset") {
            return (String::from("INIT"), String::from(""));
        } else {
            return (s.clone(), String::from("bad action"));
        }
    } else if s.clone() == String::from("PAUSED") {
        if a.clone() == String::from("start") {
            return (String::from("RUNNING"), String::from(""));
        } else if a.clone() == String::from("stop") {
            return (String::from("STOPPED"), String::from(""));
        } else if a.clone() == String::from("reset") {
            return (String::from("INIT"), String::from(""));
        } else {
            return (s.clone(), String::from("bad action"));
        }
    } else if s.clone() == String::from("ERROR") {
        if a.clone() == String::from("reset") {
            return (String::from("INIT"), String::from(""));
        } else {
            return (s.clone(), String::from("must reset"));
        }
    } else {
        return (String::from("UNKNOWN"), String::from("unknown state"));
    }
}

pub fn run_sequence(actions: Vec<String>) -> Vec<String> {
    let mut state = String::from("INIT");
    let mut log: Vec<String> = Vec::new();
    for a in actions.clone() {
        let (new_state, err) = transition(state.clone(), a.clone());
        log.push(format!("{}->{}: {}", state.clone(), new_state.clone(), err.clone()));
        state = new_state.clone();
    }
    log.clone()
}
