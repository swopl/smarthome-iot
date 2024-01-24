package main

import (
	"fmt"
	"github.com/jmoiron/sqlx"
	"github.com/labstack/echo/v4"
	"net/http"
)

type WakeupAlert struct {
	Id      int64
	Name    string
	Cron    string
	Enabled bool
}

type WakeupAlertDTO struct {
	Name string
	Cron string
}

type DBAccessor struct{ DB *sqlx.DB }

// TODO: pass into echo instead, but complicated

func (dba *DBAccessor) NewWakeupAlert(c echo.Context) error {
	waDto := new(WakeupAlertDTO)
	if err := c.Bind(waDto); err != nil {
		// TODO: don't send error to client
		return c.String(http.StatusBadRequest, err.Error())
	}
	_, err := dba.DB.Exec("INSERT INTO wakeup_alert (name, cron, enabled) VALUES ($1, $2, $3)",
		waDto.Name, waDto.Cron, true)
	if err != nil {
		return c.String(http.StatusInternalServerError, fmt.Sprint(err))
	}
	return c.NoContent(http.StatusNoContent)
}
