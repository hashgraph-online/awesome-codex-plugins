package main

import (
	_ "github.com/gogf/gf/contrib/drivers/mysql/v2"

	"github.com/gogf/gf/v2/os/gctx"

	"practices/user-grpc-service/internal/cmd"
)

func main() {
	cmd.Main.Run(gctx.New())
}
