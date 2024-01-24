package handler

import (
	"fmt"
	"github.com/jmoiron/sqlx"
	"github.com/labstack/echo/v4"
	"net/http"
	"smarthome-back/cmd/wakeup"
	"smarthome-back/view"
)

type WakeupHandler struct {
	DB *sqlx.DB
}

func (db *WakeupHandler) HandleWakeupAlert(c echo.Context) error {
	var wa []wakeup.Alert
	// TODO: we only allow one for now...
	err := db.DB.Select(&wa, "SELECT * FROM wakeup_alert LIMIT 1")
	if err != nil {
		return c.String(http.StatusInternalServerError, fmt.Sprint(err))
	}
	if len(wa) == 0 {
		return c.String(http.StatusInternalServerError, "Somehow len is 0 for wakeup...")
	}
	return render(c, view.WakeupAlert(wa[0]))
}
