package benchmark

import (
	"os"
	"strconv"
	"strings"
)

type Config struct {
	Host    string
	Port    int
	Debug   bool
	Timeout int
	LogFile string
}

func ParseConfig(path string) Config {
	cfg := Config{Host: "localhost", Port: 8080, Debug: false, Timeout: 30, LogFile: ""}

	data, _ := os.ReadFile(path)
	lines := strings.Split(string(data), "\n")

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		if strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}
		key := strings.TrimSpace(parts[0])
		val := strings.TrimSpace(parts[1])

		if key == "host" {
			cfg.Host = val
		} else if key == "port" {
			p, _ := strconv.Atoi(val)
			cfg.Port = p
		} else if key == "debug" {
			if val == "true" {
				cfg.Debug = true
			} else if val == "false" {
				cfg.Debug = false
			}
		} else if key == "timeout" {
			t, _ := strconv.Atoi(val)
			cfg.Timeout = t
		} else if key == "logfile" {
			cfg.LogFile = val
		}
	}

	envHost := os.Getenv("APP_HOST")
	if envHost != "" {
		cfg.Host = envHost
	}
	envPort := os.Getenv("APP_PORT")
	if envPort != "" {
		p, _ := strconv.Atoi(envPort)
		cfg.Port = p
	}

	return cfg
}
