package sample

import (
	"bufio"
	"strings"
)

func CountLines(text string) int {
	if text == "" {
		return 0
	}
	count := 0
	scanner := bufio.NewScanner(strings.NewReader(text))
	for scanner.Scan() {
		count++
	}
	return count
}

func CountNonEmptyLines(text string) int {
	count := 0
	scanner := bufio.NewScanner(strings.NewReader(text))
	for scanner.Scan() {
		if strings.TrimSpace(scanner.Text()) != "" {
			count++
		}
	}
	return count
}

func GetLine(text string, lineNum int) string {
	scanner := bufio.NewScanner(strings.NewReader(text))
	current := 0
	for scanner.Scan() {
		if current == lineNum {
			return scanner.Text()
		}
		current++
	}
	return ""
}
