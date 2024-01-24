package wakeup

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/labstack/echo/v4"
	"golang.org/x/net/websocket"
	"log"
	"net/http"
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

func (dba *DBAccessor) PublishDeactivateWakeup(c echo.Context) error {
	fmt.Println("PUBLISH DEACTIVATE")
	dba.Mqtt.publishDeactivateWakeupAlert()
	return c.NoContent(http.StatusOK)
}

func (dba *DBAccessor) Status(c echo.Context) error {
	websocket.Handler(func(ws *websocket.Conn) {
		defer ws.Close() // TODO: safe to defer when used in goroutine?
		for {
			dba.WakeupAlertMutex.Lock()
			text := "INACTIVE"
			if *dba.WakeupAlertActive {
				text = "ACTIVE"
			}
			dba.WakeupAlertMutex.Unlock()
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
