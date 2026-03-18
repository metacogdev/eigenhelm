package benchmark

import (
	"encoding/json"
	"fmt"
	"os"
	"strconv"
	"strings"
)

func LoadAndProcessData(path string, outputPath string, mode string) map[string]interface{} {
	result := map[string]interface{}{}

	raw, err := os.ReadFile(path)
	if err != nil {
		panic("failed to read: " + err.Error())
	}

	var records []map[string]interface{}
	json.Unmarshal(raw, &records)

	var totals float64
	var count int
	var labels []string

	for _, rec := range records {
		val, ok := rec["amount"]
		if !ok {
			continue
		}
		var num float64
		switch v := val.(type) {
		case float64:
			num = v
		case string:
			num, _ = strconv.ParseFloat(v, 64)
		default:
			num = 0
		}
		totals += num
		count++

		if label, ok := rec["label"]; ok {
			labels = append(labels, fmt.Sprintf("%v", label))
		}

		if mode == "verbose" {
			fmt.Printf("processing record: %v\n", rec)
		}
	}

	result["total"] = totals
	result["count"] = count
	result["average"] = totals / float64(count)
	result["labels"] = strings.Join(labels, ",")

	if outputPath != "" {
		out, _ := json.Marshal(result)
		os.WriteFile(outputPath, out, 0644)
	}

	if mode == "strict" {
		if count == 0 {
			panic("no records processed")
		}
		if totals < 0 {
			panic("negative total")
		}
	}

	return result
}
