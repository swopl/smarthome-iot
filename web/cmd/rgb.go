package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	mqtt "github.com/eclipse/paho.mqtt.golang"
	"github.com/labstack/echo/v4"
	"golang.org/x/net/websocket"
	"log"
	"net/http"
	"sync"
	"time"
)

type RGBState struct {
	R      string
	G      string
	B      string
	Mutex  *sync.Mutex
	Client mqtt.Client
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

type RGBDto struct {
	R string `form:"r"`
	G string `form:"g"`
	B string `form:"b"`
}

func (rgb *RGBState) PublishNewColorR(c echo.Context) error {
	fmt.Println("PUBLISH COLOR")
	rgbDto := new(RGBDto)
	if err := c.Bind(rgbDto); err != nil {
		// TODO: don't send error to client
		return c.String(http.StatusBadRequest, err.Error())
	}
	rgb.Mutex.Lock()
	if rgbDto.R != "" {
		rgb.R = "checked"
	} else {
		rgb.R = ""
	}
	rgb.Mutex.Unlock()
	rgb.publishColor()
	return c.NoContent(http.StatusOK)
}

func (rgb *RGBState) PublishNewColorG(c echo.Context) error {
	fmt.Println("PUBLISH COLOR")
	rgbDto := new(RGBDto)
	if err := c.Bind(rgbDto); err != nil {
		// TODO: don't send error to client
		return c.String(http.StatusBadRequest, err.Error())
	}
	rgb.Mutex.Lock()
	if rgbDto.G != "" {
		rgb.G = "checked"
	} else {
		rgb.G = ""
	}
	rgb.Mutex.Unlock()
	rgb.publishColor()
	return c.NoContent(http.StatusOK)
}

func (rgb *RGBState) PublishNewColorB(c echo.Context) error {
	fmt.Println("PUBLISH COLOR")
	rgbDto := new(RGBDto)
	if err := c.Bind(rgbDto); err != nil {
		// TODO: don't send error to client
		return c.String(http.StatusBadRequest, err.Error())
	}
	rgb.Mutex.Lock()
	if rgbDto.B != "" {
		rgb.B = "checked"
	} else {
		rgb.B = ""
	}
	rgb.Mutex.Unlock()
	rgb.publishColor()
	return c.NoContent(http.StatusOK)
}

func (rgb *RGBState) publishColor() {
	// TODO: take bool instead of string
	var buf bytes.Buffer
	encoder := json.NewEncoder(&buf)
	output := 0
	if rgb.R != "" {
		output++
	}
	output <<= 1
	if rgb.G != "" {
		output++
	}
	output <<= 1
	if rgb.B != "" {
		output++
	}
	err := encoder.Encode(output)
	if err != nil {
		log.Println("Error unmarshal pub Alarm:", err)
	}
	log.Println("Color publishing:", output)
	token := rgb.Client.Publish("RGBColor", 2, true, buf)
	if token.Wait() && token.Error() != nil {
		log.Println("Error publishing WA:", token.Error())
	}
}
