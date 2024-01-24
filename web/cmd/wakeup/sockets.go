package wakeup

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/labstack/echo/v4"
	"golang.org/x/net/websocket"
	"log"
	"sync"
	"time"
)

func (mqtt *MQTTAccessor) publishDeactivateWakeupAlert() {
	log.Println("Deactivating wakeup")
	var output bytes.Buffer
	encoder := json.NewEncoder(&output)
	err := encoder.Encode(DoorSecurityInfo{
		Time:   time.Now().UTC(),
		RunsOn: "SERVER",
		State:  "disabled",
	})
	if err != nil {
		log.Println("Error unmarshal pub WA:", err)
	}
	token := mqtt.Client.Publish("WakeupAlert", 2, true, output)
	if token.Wait() && token.Error() != nil {
		log.Println("Error publishing WA:", token.Error())
	}
}

func sendStatus(c echo.Context, ws *websocket.Conn, waActive <-chan bool, group *sync.WaitGroup) {
	group.Add(1)
	for {
		alertActive := <-waActive
		text := "INACTIVE"
		if alertActive {
			text = "ACTIVE"
		}
		err := websocket.Message.Send(ws, fmt.Sprintf(
			"<span id=\"status\" hx-swap-oob=\"outerHTML\">%s</span>", text))
		if err != nil {
			c.Logger().Error(err)
			break
		}
	}
	group.Done()
}

func (dba *DBAccessor) Status(c echo.Context) error {
	websocket.Handler(func(ws *websocket.Conn) {
		defer ws.Close() // TODO: safe to defer when used in goroutine?
		var group sync.WaitGroup
		go sendStatus(c, ws, dba.WakeupAlertActive, &group)
		group.Add(1)
		for {
			msg := ""
			err := websocket.Message.Receive(ws, &msg)
			if err != nil {
				c.Logger().Error(err)
				break
			}
			dba.Mqtt.publishDeactivateWakeupAlert()
			fmt.Printf("%s\n", msg)
		}
		group.Done()
		group.Wait()
	}).ServeHTTP(c.Response(), c.Request())
	return nil
}
