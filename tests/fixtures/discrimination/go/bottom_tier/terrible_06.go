package sample

import "fmt"

var stateGlobal string = "INIT"
var counterGlobal int = 0
var bufferGlobal []int
var errorGlobal string = ""

func Transition(action string) string {
	if stateGlobal == "INIT" {
		if action == "start" {
			stateGlobal = "RUNNING"
			counterGlobal = 0
			bufferGlobal = nil
			errorGlobal = ""
		} else if action == "stop" {
			stateGlobal = "INIT"
			counterGlobal = 0
			bufferGlobal = nil
			errorGlobal = ""
		} else if action == "reset" {
			stateGlobal = "INIT"
			counterGlobal = 0
			bufferGlobal = nil
			errorGlobal = ""
		} else {
			errorGlobal = fmt.Sprintf("bad action: %s", action)
		}
	} else if stateGlobal == "RUNNING" {
		if action == "stop" {
			stateGlobal = "STOPPED"
			counterGlobal = counterGlobal + 1
		} else if action == "data" {
			bufferGlobal = append(bufferGlobal, counterGlobal)
			counterGlobal = counterGlobal + 1
		} else if action == "error" {
			stateGlobal = "ERROR"
			errorGlobal = "something broke"
		} else if action == "reset" {
			stateGlobal = "INIT"
			counterGlobal = 0
			bufferGlobal = nil
			errorGlobal = ""
		} else {
			errorGlobal = fmt.Sprintf("bad action: %s", action)
		}
	} else if stateGlobal == "STOPPED" {
		if action == "start" {
			stateGlobal = "RUNNING"
		} else if action == "reset" {
			stateGlobal = "INIT"
			counterGlobal = 0
			bufferGlobal = nil
			errorGlobal = ""
		} else {
			errorGlobal = fmt.Sprintf("bad action: %s", action)
		}
	} else if stateGlobal == "ERROR" {
		if action == "reset" {
			stateGlobal = "INIT"
			counterGlobal = 0
			bufferGlobal = nil
			errorGlobal = ""
		} else {
			errorGlobal = "must reset"
		}
	}
	return stateGlobal
}

func GetState() string   { return stateGlobal }
func GetCounter() int    { return counterGlobal }
func GetBuffer() []int   { return bufferGlobal }
func GetError() string   { return errorGlobal }
