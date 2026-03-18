package sample

import "fmt"

func SafeDivide(a, b int) (int, error) {
	if b == 0 {
		return 0, fmt.Errorf("division by zero")
	}
	return a / b, nil
}

func ParseGrade(score int) (string, error) {
	if score < 0 || score > 100 {
		return "", fmt.Errorf("score out of range: %d", score)
	}
	if score >= 90 {
		return "A", nil
	}
	if score >= 80 {
		return "B", nil
	}
	if score >= 70 {
		return "C", nil
	}
	if score >= 60 {
		return "D", nil
	}
	return "F", nil
}

func ValidateAge(age int) (bool, error) {
	if age < 0 {
		return false, fmt.Errorf("age cannot be negative")
	}
	if age > 150 {
		return false, fmt.Errorf("age too large")
	}
	return true, nil
}
