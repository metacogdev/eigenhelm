package sample

import "fmt"

func Validate(data map[string]interface{}) map[string]interface{} {
	errors := make([]string, 0)
	if data["name"] != nil {
		n, ok := data["name"].(string)
		if ok {
			if len(n) > 0 {
				if len(n) <= 255 {
					// ok
				} else {
					errors = append(errors, "name too long")
				}
			} else {
				errors = append(errors, "name empty")
			}
		} else {
			errors = append(errors, "name not string")
		}
	} else {
		errors = append(errors, "name missing")
	}
	if data["age"] != nil {
		a, ok := data["age"].(int)
		if ok {
			if a >= 0 {
				if a <= 150 {
					// ok
				} else {
					errors = append(errors, "age too high")
				}
			} else {
				errors = append(errors, "age negative")
			}
		} else {
			errors = append(errors, "age not int")
		}
	} else {
		errors = append(errors, "age missing")
	}
	if data["email"] != nil {
		e, ok := data["email"].(string)
		if ok {
			if len(e) > 0 {
				hasAt := false
				for i := 0; i < len(e); i++ {
					if e[i] == '@' {
						hasAt = true
					}
				}
				if hasAt {
					// ok
				} else {
					errors = append(errors, "email no @")
				}
			} else {
				errors = append(errors, "email empty")
			}
		} else {
			errors = append(errors, "email not string")
		}
	} else {
		errors = append(errors, "email missing")
	}
	r := make(map[string]interface{})
	r["valid"] = len(errors) == 0
	r["errors"] = errors
	_ = fmt.Sprintf("")
	return r
}
