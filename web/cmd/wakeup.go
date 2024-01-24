package main

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

type WakeupAlert struct {
	Id      int64
	Name    string
	Cron    string
	Enabled bool
}

type WakeupAlertDTO struct {
	Name string
	Cron string
}

type MQTTAccessor struct {
	Client mqtt.Client
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

type DBAccessor struct {
	DB   *sqlx.DB
	Cron *cron.Cron
	Mqtt *MQTTAccessor
}

// TODO: pass into echo instead, but complicated

func (dba *DBAccessor) NewWakeupAlert(c echo.Context) error {
	waDto := new(WakeupAlertDTO)
	if err := c.Bind(waDto); err != nil {
		// TODO: don't send error to client
		return c.String(http.StatusBadRequest, err.Error())
	}
	_, err := dba.Cron.AddFunc(waDto.Cron, dba.Mqtt.publishActivateWakeupAlert)
	if err != nil {
		return c.String(http.StatusInternalServerError, fmt.Sprint(err))
	}
	_, err = dba.DB.Exec("INSERT INTO wakeup_alert (name, cron, enabled) VALUES ($1, $2, $3)",
		waDto.Name, waDto.Cron, true)
	if err != nil {
		return c.String(http.StatusInternalServerError, fmt.Sprint(err))
	}
	return c.NoContent(http.StatusNoContent)
}
