package benchmark

import (
	"fmt"
	"os"
	"strconv"
	"strings"
)

func ProcessCSV(inputPath string, outputPath string, filterCol int, filterVal string) (int, error) {
	data, err := os.ReadFile(inputPath)
	if err != nil {
		return 0, err
	}

	lines := strings.Split(string(data), "\n")
	var results []string
	count := 0

	for i, line := range lines {
		if i == 0 {
			results = append(results, line)
		} else {
			if strings.TrimSpace(line) != "" {
				fields := strings.Split(line, ",")
				if filterCol >= 0 && filterCol < len(fields) {
					if strings.TrimSpace(fields[filterCol]) == filterVal {
						for j := range fields {
							fields[j] = strings.TrimSpace(fields[j])
							if v, err := strconv.ParseFloat(fields[j], 64); err == nil {
								fields[j] = fmt.Sprintf("%.2f", v)
							}
						}
						results = append(results, strings.Join(fields, ","))
						count++
					}
				} else {
					for j := range fields {
						fields[j] = strings.TrimSpace(fields[j])
						if v, err := strconv.ParseFloat(fields[j], 64); err == nil {
							fields[j] = fmt.Sprintf("%.2f", v)
						}
					}
					results = append(results, strings.Join(fields, ","))
					count++
				}
			}
		}
	}

	output := strings.Join(results, "\n")
	err = os.WriteFile(outputPath, []byte(output), 0644)
	if err != nil {
		return count, err
	}

	return count, nil
}
