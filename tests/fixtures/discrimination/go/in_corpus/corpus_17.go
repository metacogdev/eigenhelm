			}
		}
	} else {
		for ; i < len(json); i++ {
			if json[i] == vc {
				i++
				break
			}
			if json[i] > ' ' {
				goto end
			}
		}
		r.vc = vc
	}
	if r.vc == '{' {
		if valueize {
			r.oi = make(map[string]interface{})
		} else {
			r.o = make(map[string]Result)
		}
	} else {
		if valueize {
			r.ai = make([]interface{}, 0)
		} else {
			r.a = make([]Result, 0)
		}
	}
	for ; i < len(json); i++ {
		if json[i] <= ' ' {
			continue
		}
		// get next value
		if json[i] == ']' || json[i] == '}' {
			break
		}
		switch json[i] {
		default:
			if (json[i] >= '0' && json[i] <= '9') || json[i] == '-' {
				value.Type = Number
				value.Raw, value.Num = tonum(json[i:])
				value.Str = ""
			} else {
				continue
			}
		case '{', '[':
			value.Type = JSON
			value.Raw = squash(json[i:])
			value.Str, value.Num = "", 0
		case 'n':
			value.Type = Null
			value.Raw = tolit(json[i:])
			value.Str, value.Num = "", 0
		case 't':
			value.Type = True
			value.Raw = tolit(json[i:])
			value.Str, value.Num = "", 0
		case 'f':
			value.Type = False
			value.Raw = tolit(json[i:])
			value.Str, value.Num = "", 0
		case '"':
			value.Type = String
			value.Raw, value.Str = tostr(json[i:])
			value.Num = 0
		}
		value.Index = i + t.Index

		i += len(value.Raw) - 1

		if r.vc == '{' {
			if count%2 == 0 {
				key = value
			} else {
				if valueize {
					if _, ok := r.oi[key.Str]; !ok {
						r.oi[key.Str] = value.Value()
					}
				} else {
					if _, ok := r.o[key.Str]; !ok {
						r.o[key.Str] = value
					}
				}
			}
			count++
		} else {
			if valueize {
				r.ai = append(r.ai, value.Value())
			} else {
				r.a = append(r.a, value)
			}
		}
	}
end:
	if t.Indexes != nil {
		if len(t.Indexes) != len(r.a) {
			for i := 0; i < len(r.a); i++ {
				r.a[i].Index = 0
			}
		} else {
			for i := 0; i < len(r.a); i++ {
				r.a[i].Index = t.Indexes[i]
			}
		}
	}
	return
}

// Parse parses the json and returns a result.
//
// This function expects that the json is well-formed, and does not validate.
// Invalid json will not panic, but it may return back unexpected results.
// If you are consuming JSON from an unpredictable source then you may want to
// use the Valid function first.
func Parse(json string) Result {
	var value Result
	i := 0
	for ; i < len(json); i++ {
		if json[i] == '{' || json[i] == '[' {
			value.Type = JSON
			value.Raw = json[i:] // just take the entire raw
			break
		}
		if json[i] <= ' ' {
			continue
		}
		switch json[i] {
		case '+', '-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
			'i', 'I', 'N':
			value.Type = Number
			value.Raw, value.Num = tonum(json[i:])
		case 'n':
			if i+1 < len(json) && json[i+1] != 'u' {
				// nan
				value.Type = Number
				value.Raw, value.Num = tonum(json[i:])
			} else {
				// null
				value.Type = Null
				value.Raw = tolit(json[i:])
			}
		case 't':
			value.Type = True
			value.Raw = tolit(json[i:])
		case 'f':
			value.Type = False
			value.Raw = tolit(json[i:])
		case '"':
			value.Type = String
			value.Raw, value.Str = tostr(json[i:])
		default:
			return Result{}
		}
		break
	}
	if value.Exists() {
		value.Index = i
	}
	return value
}

// ParseBytes parses the json and returns a result.
// If working with bytes, this method preferred over Parse(string(data))
func ParseBytes(json []byte) Result {
	return Parse(string(json))
}

func squash(json string) string {
	// expects that the lead character is a '[' or '{' or '(' or '"'
	// squash the value, ignoring all nested arrays and objects.
	var i, depth int
	if json[0] != '"' {
		i, depth = 1, 1
	}
	for ; i < len(json); i++ {
		if json[i] >= '"' && json[i] <= '}' {
			switch json[i] {
			case '"':
				i++
				s2 := i
				for ; i < len(json); i++ {
					if json[i] > '\\' {
						continue
					}
					if json[i] == '"' {
						// look for an escaped slash
						if json[i-1] == '\\' {
							n := 0
							for j := i - 2; j > s2-1; j-- {
								if json[j] != '\\' {
									break
								}
								n++
							}
							if n%2 == 0 {
								continue
							}
						}
						break
					}
				}
