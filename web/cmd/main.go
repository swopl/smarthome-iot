package main

import (
	"github.com/jmoiron/sqlx"
	"log"
	"os"
	"path/filepath"
	"smarthome-back/handler"

	"github.com/labstack/echo/v4"
	_ "github.com/tursodatabase/libsql-client-go/libsql"
	_ "modernc.org/sqlite"
)

var schema = `
DROP TABLE IF EXISTS alarm_clock;
CREATE TABLE alarm_clock (
	id integer PRIMARY KEY,
	name text,
	enabled integer
);`

func main() {
	err := os.MkdirAll("./db", 0755)
	if err != nil {
		log.Fatalln(err)
	}
	fname := filepath.Join("./db", "db.db")
	dbUrl := "file:" + fname
	// FIXME: might not work on Windows
	db, err := sqlx.Connect("libsql", dbUrl)
	if err != nil {
		log.Fatalln(err)
	}

	db.MustExec(schema)

	e := echo.New()
	homeHandler := handler.HomeHandler{DB: db}
	e.GET("/", homeHandler.HandleHomeShow)
	e.Logger.Fatal(e.Start(":1323"))
}
