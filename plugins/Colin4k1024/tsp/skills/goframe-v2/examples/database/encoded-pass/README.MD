---
title: Encoded Password Database Connection
slug: /examples/database/encoded-pass
keywords: [database, security, encoded password, encryption, goframe]
description: Demonstrates implementation of a custom database driver in GoFrame that handles encrypted database passwords for enhanced security. This example showcases how to create a custom MySQL driver with AES encryption and Base64 encoding, automatic password decryption during connection establishment, secure credential storage in configuration files, transparent database connection handling, and seamless integration with GoFrame's database component. Features include encrypted password storage, custom driver registration, automatic decryption middleware, production-ready security patterns, and zero-impact on existing database operations. Perfect for applications requiring enhanced database security, compliance with security policies, protection of sensitive credentials in version control, and secure configuration management without code changes.
hide_title: true
---

# Encoded Password Database Connection

## Description

This example demonstrates how to implement a custom database driver in GoFrame that can handle encrypted database passwords. The implementation allows you to store encrypted passwords in your configuration files, which are automatically decrypted when establishing database connections.

The example uses AES encryption combined with Base64 encoding to secure the database password, providing an additional layer of security for your application's database credentials.

## Requirements

- [Go](https://golang.org/dl/) `1.18` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- MySQL database

## Structure

```text
.
├── config.yaml           # Configuration file with encrypted database password
├── dbdriver/             # Custom database driver implementation
│   ├── dbdriver.go       # Custom MySQL driver with password decryption
│   └── dbdriver_test.go  # Test for password encryption/decryption
├── go.mod                # Go module file
├── go.sum                # Go module checksums
└── main.go               # Main application entry point
```

## Features

- Custom database driver implementation
- Password encryption using AES-CBC
- Base64 encoding for binary data handling
- Seamless integration with GoFrame's database operations
- Secure storage of database credentials

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/gogf/examples.git
   cd examples/database/encoded-pass
   ```

2. Install the dependencies:
   ```bash
   go mod tidy
   ```

3. Set up a MySQL database:
   ```bash
   docker run --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=12345678 -e MYSQL_DATABASE=test -d mysql:8.0
   ```

4. Update the configuration file with your encrypted database password (see the Password Encryption section below).

5. Run the application:
   ```bash
   go run main.go
   ```

## Password Encryption

To encrypt your database password:

1. Run the test function which demonstrates the encryption process:
   ```bash
   cd dbdriver
   go test -v -run Test_Encode
   ```

2. The test will output:
   - Original password
   - Base64 encoded password
   - AES encrypted and Base64 encoded password (use this in your config.yaml)
   - Decrypted password (for verification)

3. Update the `config.yaml` file with your encrypted password:
   ```yaml
   database:
     default:
       link: "mysql:root:YOUR_ENCRYPTED_PASSWORD@tcp(127.0.0.1:3306)/test?loc=Local&parseTime=true"
   ```

## Implementation Details

The custom database driver extends the standard MySQL driver provided by GoFrame and overrides the `Open` method to handle password decryption:

1. The encrypted password is extracted from the database connection string
2. The password is Base64 decoded to get the binary encrypted data
3. AES-CBC decryption is applied using a predefined encryption key
4. The decrypted data is Base64 decoded again to get the original password
5. The original password is used to establish the database connection

## Notes

- The encryption key is hardcoded in this example (`encodeKey`). In a production environment, you should use a secure method to manage this key.
- This approach can be extended to encrypt other sensitive information in your configuration files.
- The example uses AES-CBC encryption, but you can modify it to use other encryption algorithms provided by GoFrame.
