package main

import (
	mqtt "github.com/eclipse/paho.mqtt.golang"
	"github.com/jmoiron/sqlx"
	"github.com/joho/godotenv"
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

func main() {
	err := godotenv.Load("./secret.env")
	if err != nil {
		log.Fatalln(err)
	}
	err = os.MkdirAll("./db", 0755)
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
	subscribeToPeopleDetection(client)

	e := echo.New()
	homeHandler := handler.HomeHandler{DB: db}
	e.GET("/", homeHandler.HandleHomeShow)
	e.Logger.Fatal(e.Start(":1323"))
}
