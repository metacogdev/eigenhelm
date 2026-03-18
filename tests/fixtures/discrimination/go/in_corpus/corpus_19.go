	path    string
	pipe    string
	piped   bool
	more    bool
	alogok  bool
	arrch   bool
	alogkey string
	query   struct {
		on    bool
		all   bool
		path  string
		op    string
		value string
	}
}

func parseArrayPath(path string) (r arrayPathResult) {
	for i := 0; i < len(path); i++ {
		if path[i] == '|' {
			r.part = path[:i]
			r.pipe = path[i+1:]
			r.piped = true
			return
		}
		if path[i] == '.' {
			r.part = path[:i]
			if !r.arrch && i < len(path)-1 && isDotPiperChar(path[i+1:]) {
				r.pipe = path[i+1:]
				r.piped = true
			} else {
				r.path = path[i+1:]
				r.more = true
			}
			return
		}
		if path[i] == '#' {
			r.arrch = true
			if i == 0 && len(path) > 1 {
				if path[1] == '.' {
					r.alogok = true
					r.alogkey = path[2:]
					r.path = path[:1]
				} else if path[1] == '[' || path[1] == '(' {
					// query
					r.query.on = true
					qpath, op, value, _, fi, vesc, ok :=
						parseQuery(path[i:])
					if !ok {
						// bad query, end now
						break
					}
					if len(value) >= 2 && value[0] == '"' &&
						value[len(value)-1] == '"' {
						value = value[1 : len(value)-1]
						if vesc {
							value = unescape(value)
						}
					}
					r.query.path = qpath
					r.query.op = op
					r.query.value = value

					i = fi - 1
					if i+1 < len(path) && path[i+1] == '#' {
						r.query.all = true
					}
				}
			}
			continue
		}
	}
	r.part = path
	r.path = ""
	return
}

// splitQuery takes a query and splits it into three parts:
//
//	path, op, middle, and right.
//
// So for this query:
//
//	#(first_name=="Murphy").last
//
// Becomes
//
//	first_name   # path
//	=="Murphy"   # middle
//	.last        # right
//
// Or,
//
//	#(service_roles.#(=="one")).cap
//
// Becomes
//
//	service_roles.#(=="one")   # path
//	                           # middle
//	.cap                       # right
func parseQuery(query string) (
	path, op, value, remain string, i int, vesc, ok bool,
) {
	if len(query) < 2 || query[0] != '#' ||
		(query[1] != '(' && query[1] != '[') {
		return "", "", "", "", i, false, false
	}
	i = 2
	j := 0 // start of value part
	depth := 1
	for ; i < len(query); i++ {
		if depth == 1 && j == 0 {
			switch query[i] {
			case '!', '=', '<', '>', '%':
				// start of the value part
				j = i
				continue
			}
		}
		if query[i] == '\\' {
			i++
		} else if query[i] == '[' || query[i] == '(' {
			depth++
		} else if query[i] == ']' || query[i] == ')' {
			depth--
			if depth == 0 {
				break
			}
		} else if query[i] == '"' {
			// inside selector string, balance quotes
			i++
			for ; i < len(query); i++ {
				if query[i] == '\\' {
					vesc = true
					i++
				} else if query[i] == '"' {
					break
				}
			}
		}
	}
	if depth > 0 {
		return "", "", "", "", i, false, false
	}
	if j > 0 {
		path = trim(query[2:j])
		value = trim(query[j:i])
		remain = query[i+1:]
		// parse the compare op from the value
		var opsz int
		switch {
		case len(value) == 1:
			opsz = 1
		case value[0] == '!' && value[1] == '=':
			opsz = 2
		case value[0] == '!' && value[1] == '%':
			opsz = 2
		case value[0] == '<' && value[1] == '=':
			opsz = 2
		case value[0] == '>' && value[1] == '=':
			opsz = 2
		case value[0] == '=' && value[1] == '=':
			value = value[1:]
			opsz = 1
		case value[0] == '<':
			opsz = 1
		case value[0] == '>':
			opsz = 1
		case value[0] == '=':
			opsz = 1
		case value[0] == '%':
			opsz = 1
		}
		op = value[:opsz]
		value = trim(value[opsz:])
	} else {
		path = trim(query[2:i])
		remain = query[i+1:]
	}
	return path, op, value, remain, i + 1, vesc, true
}

func trim(s string) string {
left:
	if len(s) > 0 && s[0] <= ' ' {
		s = s[1:]
		goto left
	}
right:
	if len(s) > 0 && s[len(s)-1] <= ' ' {
		s = s[:len(s)-1]
		goto right
	}
	return s
}

// peek at the next byte and see if it's a '@', '[', or '{'.
func isDotPiperChar(s string) bool {
	if DisableModifiers {
		return false
	}
