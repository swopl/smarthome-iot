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
	"sync"
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
	as := AlarmState{Active: new(bool), Mutex: new(sync.Mutex)}
	alarmMqtt := MQTTAccessor{Client: &client}
	as.subscribeToAlarmInfo(client)

	homeHandler := handler.HomeHandler{DB: db}
	cr := cron.New()
	waa := false
	dbAccessor := wakeup.DBAccessor{
		DB:                db,
		Cron:              cr,
		Mqtt:              &wakeup.MQTTAccessor{Client: client},
		WakeupAlertActive: &waa,
		WakeupAlertMutex:  &sync.Mutex{},
	}
	dbAccessor.SubscribeToWakeupAlert(client)
	wakeupAlertHandler := handler.WakeupHandler{DB: db}
	cr.Start()
	dbAccessor.ActivateAllCronWakeupAlerts()

	ds := AlarmState{Active: new(bool), Mutex: new(sync.Mutex)}
	ds.subscribeToDoorSecuritySystem(client)

	rgb := RGBState{
		R:      "",
		G:      "",
		B:      "",
		Mutex:  new(sync.Mutex),
		Client: client,
	}
	rgb.subscribeToRGB(client)

	e := echo.New()
	e.GET("/", homeHandler.HandleHomeShow)
	e.GET("/pi1", handler.HandlePI1)
	e.GET("/pi2", handler.HandlePI2)
	e.GET("/pi3", handler.HandlePI3)
	e.GET("/alarm", handler.HandleAlarm)
	e.POST("/wakeup", dbAccessor.NewWakeupAlert)
	e.GET("/wakeup", wakeupAlertHandler.HandleWakeupAlert)
	e.GET("/socket/wakeup", dbAccessor.Status)
	e.POST("/wakeup/deactivate", dbAccessor.PublishDeactivateWakeup)
	e.POST("/alarm/deactivate", alarmMqtt.PublishDeactivateAlarm)
	e.GET("/socket/alarm", as.AlarmStatus)
	e.GET("/socket/door", ds.DoorStatus)
	e.GET("/socket/rgb", rgb.RGBStatus)
	e.GET("/rgb", handler.HandleRGB)
	e.PUT("/rgb/r", rgb.PublishNewColorR)
	e.PUT("/rgb/g", rgb.PublishNewColorG)
	e.PUT("/rgb/b", rgb.PublishNewColorB)
	e.Logger.Fatal(e.Start(":1323"))
}
