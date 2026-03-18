package sample

import "fmt"

func GetDaysInMonth(m int, y int) int {
	if m == 1 { return 31 }
	if m == 2 {
		if y%4 == 0 {
			if y%100 == 0 {
				if y%400 == 0 { return 29 }
				return 28
			}
			return 29
		}
		return 28
	}
	if m == 3 { return 31 }
	if m == 4 { return 30 }
	if m == 5 { return 31 }
	if m == 6 { return 30 }
	if m == 7 { return 31 }
	if m == 8 { return 31 }
	if m == 9 { return 30 }
	if m == 10 { return 31 }
	if m == 11 { return 30 }
	if m == 12 { return 31 }
	return -1
}

func DaysBetween(m1 int, d1 int, y1 int, m2 int, d2 int, y2 int) int {
	total := 0
	cm := m1
	cd := d1
	cy := y1
	for cy < y2 || (cy == y2 && cm < m2) || (cy == y2 && cm == m2 && cd < d2) {
		cd = cd + 1
		total = total + 1
		if cd > GetDaysInMonth(cm, cy) {
			cd = 1
			cm = cm + 1
			if cm > 12 {
				cm = 1
				cy = cy + 1
			}
		}
	}
	return total
}

func FormatDate(m int, d int, y int) string {
	ms := ""
	if m < 10 { ms = fmt.Sprintf("0%d", m) } else { ms = fmt.Sprintf("%d", m) }
	ds := ""
	if d < 10 { ds = fmt.Sprintf("0%d", d) } else { ds = fmt.Sprintf("%d", d) }
	return fmt.Sprintf("%s/%s/%d", ms, ds, y)
}

func AddDays(m int, d int, y int, n int) string {
	cm := m
	cd := d
	cy := y
	for i := 0; i < n; i++ {
		cd = cd + 1
		if cd > GetDaysInMonth(cm, cy) {
			cd = 1
			cm = cm + 1
			if cm > 12 { cm = 1; cy = cy + 1 }
		}
	}
	return FormatDate(cm, cd, cy)
}
