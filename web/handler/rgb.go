package handler

import (
	"github.com/labstack/echo/v4"
	"smarthome-back/view"
)

func HandleRGB(c echo.Context) error {
	return render(c, view.RGB())
}
