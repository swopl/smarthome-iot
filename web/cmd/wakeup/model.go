package wakeup

import (
	"fmt"
	mqtt "github.com/eclipse/paho.mqtt.golang"
	"github.com/jmoiron/sqlx"
	"github.com/labstack/echo/v4"
	"github.com/robfig/cron/v3"
	"log"
	"net/http"
	"time"
)

type Alert struct {
	Id      int64
	Name    string
	Cron    string
	Enabled bool
}

type MQTTAccessor struct {
	Client mqtt.Client
}

type DBAccessor struct {
	DB   *sqlx.DB
	Cron *cron.Cron
	Mqtt *MQTTAccessor
}

type AlertDTO struct {
	Name string `form:"name"`
	Cron string `form:"cron"`
}

type DoorSecurityInfo struct {
	Time   time.Time
	RunsOn string `json:"runs_on"` // TODO: do i need this json meta?
	State  string
}

func (mqtt *MQTTAccessor) publishActivateWakeupAlert() {
	log.Println("Activating wakeup")
	mqtt.Client.Publish("DoorSecuritySystem", 2, true, DoorSecurityInfo{
		Time:   time.Now().UTC(),
		RunsOn: "SERVER",
		State:  "enabled",
	})
}

func (mqtt *MQTTAccessor) publishDeactivateWakeupAlert() {
	log.Println("Deactivating wakeup")
	mqtt.Client.Publish("DoorSecuritySystem", 2, true, DoorSecurityInfo{
		Time:   time.Now().UTC(),
		RunsOn: "SERVER",
		State:  "disabled",
	})
}

// TODO: pass into echo instead, but complicated

func (dba *DBAccessor) NewWakeupAlert(c echo.Context) error {
	// FIXME: !!!! this function, if sometimes errors, will require restart to start cron again...
	// TODO: don't also delete here...
	waDto := new(AlertDTO)
	if err := c.Bind(waDto); err != nil {
		// TODO: don't send error to client
		return c.String(http.StatusBadRequest, err.Error())
	}
	dba.Cron.Stop() // FIXME: is this thread safe?
	entries := dba.Cron.Entries()
	for _, entry := range entries {
		dba.Cron.Remove(entry.ID)
		log.Printf("CronRemoved %d", entry.ID)
	}
	_, err := dba.Cron.AddFunc(waDto.Cron, dba.Mqtt.publishActivateWakeupAlert)
	if err != nil {
		dba.Cron.Start()
		return c.String(http.StatusInternalServerError, fmt.Sprint(err))
	}
	tx, err := dba.DB.Begin()
	if err != nil {
		return c.String(http.StatusInternalServerError, fmt.Sprint(err))
	}
	_, err = tx.Exec("DELETE FROM wakeup_alert") // this is intentional for now!
	if err != nil {
		err = tx.Rollback()
		if err != nil {
			return c.String(http.StatusInternalServerError, fmt.Sprint(err))
		}
		return c.String(http.StatusInternalServerError, fmt.Sprint(err))
	}
	_, err = tx.Exec("INSERT INTO wakeup_alert (name, cron, enabled) VALUES ($1, $2, $3)",
		waDto.Name, waDto.Cron, true)
	if err != nil {
		err = tx.Rollback()
		if err != nil {
			return c.String(http.StatusInternalServerError, fmt.Sprint(err))
		}
		return c.String(http.StatusInternalServerError, fmt.Sprint(err))
	}
	err = tx.Commit()
	if err != nil {
		return c.String(http.StatusInternalServerError, fmt.Sprint(err))
	}
	dba.Cron.Start()
	return c.NoContent(http.StatusNoContent)
}

func (dba *DBAccessor) ActivateAllCronWakeupAlerts() {
	var wakeupAlerts []Alert
	err := dba.DB.Select(&wakeupAlerts, "SELECT * FROM wakeup_alert")
	if err != nil {
		log.Fatalln(err)
	}
	for _, alert := range wakeupAlerts {
		_, err := dba.Cron.AddFunc(alert.Cron, dba.Mqtt.publishActivateWakeupAlert)
		if err != nil {
			log.Fatalln(err)
		}
	}
}
