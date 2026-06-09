package main

import (
    `context`

    // Import the custom database driver which will handle password decryption
    _ "main/dbdriver"

    `github.com/gogf/gf/v2/frame/g`
)

func main() {
    // Create a background context for database operations
    var ctx = context.Background()
    
    // Execute a simple query to test the database connection
    // The password in config.yaml is encrypted and will be automatically decrypted
    // by our custom database driver
    all, err := g.DB().GetAll(ctx, "SELECT 1")
    
    // Log any errors that occurred during the database connection
    g.Log().Info(ctx, err)
    
    // Log the query results
    g.Log().Info(ctx, all)
}
