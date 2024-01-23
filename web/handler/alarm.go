package handler

import (
	"github.com/labstack/echo/v4"
	"smarthome-back/view"
)

func HandleAlarm(c echo.Context) error {
	return render(c, view.Alarm())
}
