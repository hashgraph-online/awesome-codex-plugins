// Package dbdriver implements a custom MySQL driver with password decryption capabilities.
// It extends the standard GoFrame MySQL driver to handle encrypted database passwords.
package dbdriver

import (
    "database/sql"

    "github.com/gogf/gf/contrib/drivers/mysql/v2"
    `github.com/gogf/gf/v2/crypto/gaes`
    "github.com/gogf/gf/v2/database/gdb"
    `github.com/gogf/gf/v2/encoding/gbase64`
)

// Driver is a custom database driver that extends the standard MySQL driver
// to support encrypted passwords in database connection strings.
type Driver struct {
    mysql.Driver
}

const (
    // encodeKey is the encryption key used for AES encryption/decryption of passwords.
    // In production environments, this should be securely managed and not hardcoded.
    encodeKey = "key for encoding"
)

func init() {
    // Register our custom driver to replace the standard MySQL driver.
    // This ensures all MySQL connections will use our password decryption logic.
    err := gdb.Register("mysql", &Driver{})
    if err != nil {
        panic(err)
    }
}

// New creates and returns a database object for MySQL.
// It implements the interface of gdb.Driver for custom database driver installation.
// This method creates a new instance of our custom driver with the provided core.
func (d *Driver) New(core *gdb.Core, node *gdb.ConfigNode) (gdb.DB, error) {
    return &Driver{
        mysql.Driver{
            Core: core,
        },
    }, nil
}

// Open creates and returns an underlying sql.DB object for MySQL.
// This method overrides the standard driver's Open method to handle password decryption.
// The password decryption process follows these steps:
// 1. Base64 decode the encrypted password string to binary
// 2. Decrypt the binary data using AES-CBC with the encodeKey
// 3. Base64 decode the decrypted data to get the original password
// 4. Use the original password to establish the database connection
func (d *Driver) Open(config *gdb.ConfigNode) (db *sql.DB, err error) {
    // Convert Base64 encoded password to binary
    passBytes, err := gbase64.DecodeString(config.Pass)
    if err != nil {
        return nil, err
    }
    
    // Decrypt the binary data using AES-CBC
    decodedPass, err := gaes.DecryptCBC(passBytes, []byte(encodeKey))
    if err != nil {
        return nil, err
    }
    
    // Convert the decrypted binary data to original password string
    originPass, err := gbase64.Decode(decodedPass)
    if err != nil {
        return nil, err
    }
    
    // Replace the encrypted password with the original password
    config.Pass = string(originPass)
    
    // Call the parent driver's Open method with the decrypted password
    return d.Driver.Open(config)
}
