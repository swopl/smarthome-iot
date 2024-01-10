package handler

import (
	"github.com/jmoiron/sqlx"
	"github.com/labstack/echo/v4"
	"smarthome-back/view"
)

type HomeHandler struct{ DB *sqlx.DB }

func (h *HomeHandler) HandleHomeShow(c echo.Context) error {
	return render(c, view.Home())
}
