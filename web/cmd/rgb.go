package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	mqtt "github.com/eclipse/paho.mqtt.golang"
	"github.com/labstack/echo/v4"
	"golang.org/x/net/websocket"
	"log"
	"sync"
	"time"
)

type RGBState struct {
	R     string
	G     string
	B     string
	Mutex *sync.Mutex
}

func (rgb *RGBState) RGBStatus(c echo.Context) error {
	websocket.Handler(func(ws *websocket.Conn) {
		defer ws.Close() // TODO: safe to defer when used in goroutine?
		for {
			rgb.Mutex.Lock()
			err := websocket.Message.Send(ws, fmt.Sprintf(
				`<script id="rgb-editor" hx-swap-oob="outerHTML">
						document.getElementById('r').checked = '%s';
						document.getElementById('g').checked = '%s';
						document.getElementById('b').checked = '%s';
						</script>`, rgb.R, rgb.G, rgb.B))
			rgb.Mutex.Unlock()
			if err != nil {
				c.Logger().Error(err)
				return
			}
			time.Sleep(1 * time.Second) // TODO: do it better instead of sending every second
		}
	}).ServeHTTP(c.Response(), c.Request())
	return nil
}

func (rgb *RGBState) handleRGBInfo(_ mqtt.Client, msg mqtt.Message) {
	decoder := json.NewDecoder(bytes.NewReader(msg.Payload()))
	var rgbColor int
	err := decoder.Decode(&rgbColor)
	if err != nil {
		log.Fatalln(err) // TODO: maybe not fatal here
	}
	fmt.Print("Unmarshalled: ")
	fmt.Println(rgbColor)
	rgb.Mutex.Lock()
	defer rgb.Mutex.Unlock()
	rgb.R = ""
	rgb.G = ""
	rgb.B = ""
	if (rgbColor>>2)%2 == 1 {
		rgb.R = "checked"
	}
	if (rgbColor>>1)%2 == 1 {
		rgb.G = "checked"
	}
	if rgbColor%2 == 1 {
		rgb.B = "checked"
	}
}

func (rgb *RGBState) subscribeToRGB(client mqtt.Client) {
	topics := []string{
		"RGBColor",
	}
	// TODO: check what qos means in subscribe
	for _, topic := range topics {
		if token := client.Subscribe(topic, 0, rgb.handleRGBInfo); token.Wait() && token.Error() != nil {
			log.Fatalln(token.Error())
		}
	}
}
