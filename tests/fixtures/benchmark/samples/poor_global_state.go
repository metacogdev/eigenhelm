package benchmark

import (
	"fmt"
	"strings"
)

var currentUser string
var isAdmin bool
var requestCount int
var lastError string
var debugMode bool
var appName string
var registry = map[string]string{}

func init() {
	debugMode = true
	appName = "myapp"
	currentUser = "anonymous"
	isAdmin = false
	requestCount = 0
	lastError = ""
}

func SetUser(name string) {
	currentUser = name
	if name == "admin" || name == "root" || name == "superuser" {
		isAdmin = true
	}
}

func HandleRequest(action string, data string) string {
	requestCount++
	if debugMode {
		fmt.Printf("[%s] request #%d: %s\n", appName, requestCount, action)
	}

	if action == "register" {
		parts := strings.SplitN(data, ":", 2)
		registry[parts[0]] = parts[1]
		return "ok"
	}
	if action == "lookup" {
		val := registry[data]
		if val == "" {
			lastError = "not found: " + data
			return ""
		}
		return val
	}
	if action == "delete" {
		if !isAdmin {
			lastError = "permission denied"
			return "error"
		}
		delete(registry, data)
		return "ok"
	}
	if action == "reset" {
		if !isAdmin {
			lastError = "permission denied"
			return "error"
		}
		registry = map[string]string{}
		requestCount = 0
		return "ok"
	}
	lastError = "unknown action: " + action
	return "error"
}

func GetLastError() string {
	return lastError
}
