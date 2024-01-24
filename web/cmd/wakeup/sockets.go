package wakeup

import (
	"fmt"
	"github.com/labstack/echo/v4"
	"golang.org/x/net/websocket"
	"log"
	"time"
)

func (mqtt *MQTTAccessor) publishDeactivateWakeupAlert() {
	log.Println("Deactivating wakeup")
	mqtt.Client.Publish("WakeupAlert", 2, true, DoorSecurityInfo{
		Time:   time.Now().UTC(),
		RunsOn: "SERVER",
		State:  "disabled",
	})
}

func (dba *DBAccessor) Status(c echo.Context) error {
	websocket.Handler(func(ws *websocket.Conn) {
		defer ws.Close()
		for {
			err := websocket.Message.Send(ws, "<span id=\"status\" hx-swap-oob=\"outerHTML\">hereiam</span>")
			if err != nil {
				c.Logger().Error(err)
			}
			msg := ""
			err = websocket.Message.Receive(ws, &msg)
			if err != nil {
				c.Logger().Error(err)
				return
			}
			dba.Mqtt.publishDeactivateWakeupAlert()
			fmt.Printf("%s\n", msg)
		}
	}).ServeHTTP(c.Response(), c.Request())
	return nil
}
