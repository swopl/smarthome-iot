package handler

import (
	"github.com/labstack/echo/v4"
	"smarthome-back/view/pis"
)

func HandlePI1(c echo.Context) error {
	return render(c, pis.PI1())
}
