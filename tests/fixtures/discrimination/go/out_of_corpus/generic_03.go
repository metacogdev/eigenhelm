package sample

func ReverseString(s string) string {
	runes := []rune(s)
	n := len(runes)
	for i := 0; i < n/2; i++ {
		runes[i], runes[n-1-i] = runes[n-1-i], runes[i]
	}
	return string(runes)
}

func IsPalindrome(s string) bool {
	return s == ReverseString(s)
}

func CountChar(s string, ch rune) int {
	count := 0
	for _, c := range s {
		if c == ch {
			count++
		}
	}
	return count
}

func RepeatString(s string, n int) string {
	result := ""
	for i := 0; i < n; i++ {
		result += s
	}
	return result
}
