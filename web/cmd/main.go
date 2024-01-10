package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	mqtt "github.com/eclipse/paho.mqtt.golang"
	"github.com/jmoiron/sqlx"
	"github.com/labstack/echo/v4"
	_ "github.com/tursodatabase/libsql-client-go/libsql"
	"log"
	_ "modernc.org/sqlite"
	"os"
	"path/filepath"
	"smarthome-back/handler"
)

var schema = `
DROP TABLE IF EXISTS alarm_clock;
CREATE TABLE alarm_clock (
	id integer PRIMARY KEY,
	name text,
	enabled integer
);`

type DeviceData struct {
	Simulated   bool
	Time        string
	Measurement string
	RunsOn      string `json:"runs_on"` // TODO: do i need this json meta?
	Codename    string
	Value       interface{}
}

func handleNewData(client mqtt.Client, msg mqtt.Message) {
	fmt.Printf("\nTOPIC: %s\n", msg.Topic())
	fmt.Printf("MSG: %s\n", msg.Payload())
	decoder := json.NewDecoder(bytes.NewReader(msg.Payload()))
	var data DeviceData
	err := decoder.Decode(&data)
	if err != nil {
		log.Fatalln(err) // TODO: maybe not fatal here
	}
	fmt.Print("Unmarshalled: ")
	fmt.Println(data)
}

func subscribeToAllTopics(client mqtt.Client) {
	topics := []string{
		"Temperature",
		"Humidity",
		"Motion",
		"Keypad",
		"Distance",
		"Button",
		"IRReceiver",
		"Acceleration",
		"Rotation",
	}
	for _, topic := range topics {
		if token := client.Subscribe(topic, 0, handleNewData); token.Wait() && token.Error() != nil {
			log.Fatalln(token.Error())
		}
	}
}

func main() {
	err := os.MkdirAll("./db", 0755)
	if err != nil {
		log.Fatalln(err)
	}
	fname := filepath.Join("./db", "db.db")
	dbUrl := "file:" + fname
	// FIXME: might not work on Windows
	db, err := sqlx.Connect("libsql", dbUrl)
	if err != nil {
		log.Fatalln(err)
	}

	db.MustExec(schema)

	opts := mqtt.NewClientOptions().AddBroker("tcp://localhost:1883").SetClientID("go_mqtt_client")
	client := mqtt.NewClient(opts)
	if token := client.Connect(); token.Wait() && token.Error() != nil {
		log.Fatalln(token.Error())
	}
	subscribeToAllTopics(client)

	e := echo.New()
	homeHandler := handler.HomeHandler{DB: db}
	e.GET("/", homeHandler.HandleHomeShow)
	e.Logger.Fatal(e.Start(":1323"))
}
