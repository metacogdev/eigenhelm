package sample

import (
	"fmt"
	"strings"
)

func FormatThing(t int, a string, b string, c string) string {
	switch t {
	case 1:
		return fmt.Sprintf("<div class='t1'><span>%s</span><span>%s</span></div>", a, b)
	case 2:
		return fmt.Sprintf("<div class='t2'><span>%s</span><span>%s</span></div>", a, b)
	case 3:
		return fmt.Sprintf("<div class='t3'><span>%s</span><span>%s</span></div>", a, b)
	case 4:
		return fmt.Sprintf("<div class='t4'><span>%s</span><span>%s</span></div>", a, c)
	case 5:
		return fmt.Sprintf("<div class='t5'><span>%s</span><span>%s</span></div>", a, c)
	case 6:
		return fmt.Sprintf("<div class='t6'><span>%s</span><span>%s</span></div>", b, c)
	case 7:
		return fmt.Sprintf("<div class='t7'><span>%s</span><span>%s</span></div>", b, c)
	case 8:
		return fmt.Sprintf("<div class='t8'><span>%s</span><span>%s</span><span>%s</span></div>", a, b, c)
	case 9:
		return fmt.Sprintf("<div class='t9'><span>%s</span><span>%s</span><span>%s</span></div>", a, b, c)
	case 10:
		return fmt.Sprintf("<div class='t10'><span>%s</span><span>%s</span><span>%s</span></div>", a, b, c)
	default:
		return fmt.Sprintf("<div class='unknown'>%s</div>", a)
	}
}

func BuildPage(items [][]string) string {
	var b strings.Builder
	b.WriteString("<html><body>")
	for i := 0; i < len(items); i++ {
		if len(items[i]) >= 3 {
			b.WriteString(FormatThing(i%10+1, items[i][0], items[i][1], items[i][2]))
		}
	}
	b.WriteString("</body></html>")
	return b.String()
}
