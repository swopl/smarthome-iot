package main

import (
	mqtt "github.com/eclipse/paho.mqtt.golang"
	"github.com/jmoiron/sqlx"
	"github.com/joho/godotenv"
	"github.com/labstack/echo/v4"
	"github.com/robfig/cron/v3"
	_ "github.com/tursodatabase/libsql-client-go/libsql"
	"log"
	_ "modernc.org/sqlite"
	"os"
	"path/filepath"
	"smarthome-back/cmd/wakeup"
	"smarthome-back/handler"
)

var schema = `
DROP TABLE IF EXISTS wakeup_alert;
CREATE TABLE wakeup_alert (
	id integer PRIMARY KEY,
	name text,
	cron text,
	enabled boolean
);

INSERT INTO wakeup_alert (name, cron, enabled) VALUES ('MyAlert', '*/15 * * * *', true);`

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
	subscribeToAlarmInfo(client)

	e := echo.New()
	homeHandler := handler.HomeHandler{DB: db}
	cr := cron.New()
	dbAccessor := wakeup.DBAccessor{
		DB:   db,
		Cron: cr,
		Mqtt: &wakeup.MQTTAccessor{Client: client},
	}
	wakeupAlertHandler := handler.WakeupHandler{DB: db}
	cr.Start()
	dbAccessor.ActivateAllCronWakeupAlerts()
	e.GET("/", homeHandler.HandleHomeShow)
	e.GET("/pi1", handler.HandlePI1)
	e.GET("/alarm", handler.HandleAlarm)
	e.POST("/wakeup", dbAccessor.NewWakeupAlert)
	e.GET("/wakeup", wakeupAlertHandler.HandleWakeupAlert)
	e.GET("/socket/wakeup", dbAccessor.Status)
	e.Logger.Fatal(e.Start(":1323"))
}
