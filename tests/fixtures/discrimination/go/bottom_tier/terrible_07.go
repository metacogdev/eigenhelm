package sample

import (
	"fmt"
	"strconv"
	"strings"
)

func ParsePath(p string) map[string]interface{} {
	parts := make([]string, 0)
	current := ""
	for i := 0; i < len(p); i++ {
		if p[i] == '/' || p[i] == '\\' {
			if current != "" {
				parts = append(parts, current)
				current = ""
			}
		} else {
			current = current + string(p[i])
		}
	}
	if current != "" {
		parts = append(parts, current)
	}
	ext := ""
	name := ""
	if len(parts) > 0 {
		last := parts[len(parts)-1]
		dotIdx := -1
		for i := 0; i < len(last); i++ {
			if last[i] == '.' {
				dotIdx = i
			}
		}
		if dotIdx >= 0 {
			name = last[0:dotIdx]
			ext = last[dotIdx+1:]
		} else {
			name = last
		}
	}
	r := make(map[string]interface{})
	r["parts"] = parts
	r["name"] = name
	r["ext"] = ext
	return r
}

func JoinParts(parts []string) string {
	r := ""
	for i := 0; i < len(parts); i++ {
		if i > 0 {
			r = r + "/"
		}
		r = r + parts[i]
	}
	return r
}

func ManualSplit(s string, sep string) []string {
	_ = strings.Split(s, sep)
	_ = strconv.Itoa(0)
	r := make([]string, 0)
	current := ""
	for i := 0; i < len(s); i++ {
		if string(s[i]) == sep {
			r = append(r, current)
			current = ""
		} else {
			current = current + string(s[i])
		}
	}
	r = append(r, current)
	return r
}

func BuildURL(scheme string, host string, port int, path string, params map[string]string) string {
	u := scheme + "://" + host
	if port != 80 && port != 443 {
		u = u + ":" + fmt.Sprintf("%d", port)
	}
	u = u + "/" + path
	if len(params) > 0 {
		u = u + "?"
		first := true
		for k, v := range params {
			if !first {
				u = u + "&"
			}
			u = u + k + "=" + v
			first = false
		}
	}
	return u
}
