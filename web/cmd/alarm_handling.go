package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	mqtt "github.com/eclipse/paho.mqtt.golang"
	influxdb2 "github.com/influxdata/influxdb-client-go"
	"github.com/labstack/echo/v4"
	"golang.org/x/net/websocket"
	"log"
	"net/http"
	"os"
	"smarthome-back/cmd/wakeup"
	"sync"
	"sync/atomic"
	"time"
)

type PersonData struct {
	Time         time.Time
	RunsOn       string `json:"runs_on"` // TODO: do i need this json meta?
	Incrementing bool
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
	if data.Incrementing {
		pc.Present.Add(1)
	} else {
		pc.Present.Add(-1)
	}
	go publishPeopleCount(client, pc.Present.Load())
	fmt.Println("Present:", pc.Present.Load())
}

func publishPeopleCount(client mqtt.Client, count int32) {
	// TODO: check if this works, sending only i32...
	if count < 0 {
		log.Println("Negative count for people somehow:", count)
		count = 0
	}
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

type AlarmInfo struct {
	Time   time.Time
	RunsOn string `json:"runs_on"` // TODO: do i need this json meta?
	Reason string
	Extra  string
	State  string
}

type AlarmState struct {
	Active *bool
	Mutex  *sync.Mutex
}

func (as *AlarmState) handleNewAlarmInfo(_ mqtt.Client, msg mqtt.Message) {
	fmt.Printf("\nTOPIC: %s\n", msg.Topic())
	fmt.Printf("MSG: %s\n", msg.Payload())
	decoder := json.NewDecoder(bytes.NewReader(msg.Payload()))
	var alarm AlarmInfo
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
		AddTag("state", alarm.State).
		AddTag("reason", alarm.Reason).
		AddField("extra", alarm.Extra)
	err = writeAPI.WritePoint(context.Background(), p)
	if err != nil {
		log.Fatalln(err) // TODO: maybe not fatal here
	}
	influxClient.Close()
	as.Mutex.Lock()
	defer as.Mutex.Unlock()
	*as.Active = alarm.State == "enabled"
}

func (as *AlarmState) subscribeToAlarmInfo(client mqtt.Client) {
	topics := []string{
		"AlarmInfo",
	}
	// TODO: check what qos means in subscribe
	for _, topic := range topics {
		if token := client.Subscribe(topic, 0, as.handleNewAlarmInfo); token.Wait() && token.Error() != nil {
			log.Fatalln(token.Error())
		}
	}
}

type MQTTAccessor struct {
	Client *mqtt.Client
}

func (mqtt *MQTTAccessor) PublishDeactivateAlarm(c echo.Context) error {
	fmt.Println("PUBLISH DEACTIVATE ALARM")
	publishDeactivateAlarm(*mqtt.Client)
	return c.NoContent(http.StatusOK)
}

func publishDeactivateAlarm(client mqtt.Client) {
	var output bytes.Buffer
	encoder := json.NewEncoder(&output)
	err := encoder.Encode(AlarmInfo{
		Time:   time.Now().UTC(),
		RunsOn: "SERVER",
		Reason: "SERVER",
		Extra:  "SERVER btn pressed",
		State:  "disabled",
	})
	if err != nil {
		log.Println("Error unmarshal pub Alarm:", err)
	}
	token := client.Publish("AlarmInfo", 2, true, output)
	if token.Wait() && token.Error() != nil {
		log.Println("Error publishing WA:", token.Error())
	}
}

func (as *AlarmState) AlarmStatus(c echo.Context) error {
	websocket.Handler(func(ws *websocket.Conn) {
		defer ws.Close() // TODO: safe to defer when used in goroutine?
		for {
			as.Mutex.Lock()
			text := "INACTIVE"
			if *as.Active {
				text = "ACTIVE"
			}
			as.Mutex.Unlock()
			err := websocket.Message.Send(ws, fmt.Sprintf(
				"<span id=\"status\" hx-swap-oob=\"outerHTML\">%s</span>", text))
			if err != nil {
				c.Logger().Error(err)
				return
			}
			time.Sleep(5 * time.Second) // TODO: do it better instead of sending every second
		}
	}).ServeHTTP(c.Response(), c.Request())
	return nil
}

func (as *AlarmState) handleDoorSecuritySystemInfo(_ mqtt.Client, msg mqtt.Message) {
	decoder := json.NewDecoder(bytes.NewReader(msg.Payload()))
	var doorInfo wakeup.DoorSecurityInfo
	err := decoder.Decode(&doorInfo)
	if err != nil {
		log.Fatalln(err) // TODO: maybe not fatal here
	}
	fmt.Print("Unmarshalled: ")
	fmt.Println(doorInfo)
	as.Mutex.Lock()
	defer as.Mutex.Unlock()
	*as.Active = doorInfo.State == "enabled"
}

func (as *AlarmState) subscribeToDoorSecuritySystem(client mqtt.Client) {
	topics := []string{
		"DoorSecuritySystem",
	}
	// TODO: check what qos means in subscribe
	for _, topic := range topics {
		if token := client.Subscribe(topic, 0, as.handleDoorSecuritySystemInfo); token.Wait() && token.Error() != nil {
			log.Fatalln(token.Error())
		}
	}
}
