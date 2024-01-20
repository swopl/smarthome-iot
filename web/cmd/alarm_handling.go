package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	mqtt "github.com/eclipse/paho.mqtt.golang"
	influxdb2 "github.com/influxdata/influxdb-client-go"
	"log"
	"os"
	"sync/atomic"
	"time"
)

type PersonData struct {
	Time     time.Time
	Entering bool
	Leaving  bool
}

type PersonCounter struct {
	// TODO: maybe not the most go-like way to use atomic counter?
	Present atomic.Int32
}

func (pc *PersonCounter) handleNewPerson(client mqtt.Client, msg mqtt.Message) {
	fmt.Printf("\nTOPIC: %s\n", msg.Topic())
	fmt.Printf("MSG: %s\n", msg.Payload())
	decoder := json.NewDecoder(bytes.NewReader(msg.Payload()))
	var data PersonData
	err := decoder.Decode(&data)
	if err != nil {
		log.Fatalln(err) // TODO: maybe not fatal here
	}
	fmt.Print("Unmarshalled: ")
	fmt.Println(data)
	if data.Entering {
		pc.Present.Add(1)
	} else if data.Leaving {
		pc.Present.Add(-1)
	}
	go publishPeopleCount(client, pc.Present.Load())
	fmt.Println("Present:", pc.Present.Load())
}

func publishPeopleCount(client mqtt.Client, count int32) {
	// TODO: check if this works, sending only i32...
	client.Publish("PeopleCount", 2, true, count)
}

func subscribeToPeopleDetection(client mqtt.Client) {
	topics := []string{
		"PeopleDetection",
	}
	var pa PersonCounter
	for _, topic := range topics {
		if token := client.Subscribe(topic, 0, pa.handleNewPerson); token.Wait() && token.Error() != nil {
			log.Fatalln(token.Error())
		}
	}
}

type AlarmCreation struct {
	Time   time.Time
	RunsOn string `json:"runs_on"` // TODO: do i need this json meta?
	Reason string
	Extra  string
}

func handleNewAlarm(client mqtt.Client, msg mqtt.Message) {
	fmt.Printf("\nTOPIC: %s\n", msg.Topic())
	fmt.Printf("MSG: %s\n", msg.Payload())
	decoder := json.NewDecoder(bytes.NewReader(msg.Payload()))
	var alarm AlarmCreation
	err := decoder.Decode(&alarm)
	if err != nil {
		log.Fatalln(err) // TODO: maybe not fatal here
	}
	fmt.Print("Unmarshalled: ")
	fmt.Println(alarm)

	org := "FTN"
	bucket := "example_db"
	token := os.Getenv("INFLUX_TOKEN")
	url := "http://localhost:8086"

	// FIXME: !! Grafana showing old because of tags 'true' and 'True' difference!!
	// TODO: optimize using async? Then must use different for alarm and regular data
	influxClient := influxdb2.NewClient(url, token)
	writeAPI := influxClient.WriteAPIBlocking(org, bucket)
	p := influxdb2.NewPointWithMeasurement("Alarm").
		SetTime(alarm.Time).
		AddTag("runs_on", alarm.RunsOn).
		AddTag("state", "enabled").
		AddField("reason", alarm.Reason).
		AddField("extra", alarm.Extra)
	err = writeAPI.WritePoint(context.Background(), p)
	if err != nil {
		log.Fatalln(err) // TODO: maybe not fatal here
	}
	influxClient.Close()
}

func subscribeToAlarmCreated(client mqtt.Client) {
	topics := []string{
		"AlarmCreated",
	}
	// TODO: check what qos means in subscribe
	for _, topic := range topics {
		if token := client.Subscribe(topic, 0, handleNewAlarm); token.Wait() && token.Error() != nil {
			log.Fatalln(token.Error())
		}
	}
}

type AlarmOver struct {
	Time   time.Time
	RunsOn string `json:"runs_on"` // TODO: do i need this json meta?
}

func handleAlarmEnded(client mqtt.Client, msg mqtt.Message) {
	fmt.Printf("\nTOPIC: %s\n", msg.Topic())
	fmt.Printf("MSG: %s\n", msg.Payload())
	decoder := json.NewDecoder(bytes.NewReader(msg.Payload()))
	var alarm AlarmOver
	err := decoder.Decode(&alarm)
	if err != nil {
		log.Fatalln(err) // TODO: maybe not fatal here
	}
	fmt.Print("Unmarshalled: ")
	fmt.Println(alarm)

	org := "FTN"
	bucket := "example_db"
	token := os.Getenv("INFLUX_TOKEN")
	url := "http://localhost:8086"

	influxClient := influxdb2.NewClient(url, token)
	writeAPI := influxClient.WriteAPIBlocking(org, bucket)
	p := influxdb2.NewPointWithMeasurement("Alarm").
		SetTime(alarm.Time).
		AddTag("runs_on", alarm.RunsOn).
		AddTag("state", "disabled")
	err = writeAPI.WritePoint(context.Background(), p)
	if err != nil {
		log.Fatalln(err) // TODO: maybe not fatal here
	}
	influxClient.Close()
}

func subscribeToAlarmEnded(client mqtt.Client) {
	topics := []string{
		"AlarmEnded",
	}
	for _, topic := range topics {
		if token := client.Subscribe(topic, 0, handleAlarmEnded); token.Wait() && token.Error() != nil {
			log.Fatalln(token.Error())
		}
	}
}
