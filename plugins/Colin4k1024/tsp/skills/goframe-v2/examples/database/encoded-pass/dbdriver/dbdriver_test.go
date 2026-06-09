package dbdriver

import (
    `context`
    "testing"

    "github.com/gogf/gf/v2/crypto/gaes"
    "github.com/gogf/gf/v2/encoding/gbase64"
    `github.com/gogf/gf/v2/frame/g`
    "github.com/gogf/gf/v2/test/gtest"
)

// Test_Encode demonstrates the password encryption and decryption process.
// This test function shows how to:
// 1. Take an original password string
// 2. Encode it with Base64
// 3. Encrypt the Base64 string using AES-CBC
// 4. Encode the encrypted binary data with Base64 again (for storage in config)  
// 5. Decrypt the data back to the original password  
//  
// The output of this test can be used to generate encrypted passwords for config.yaml.  
func Test_Encode(t *testing.T) {
    gtest.C(t, func(t *gtest.T) {
        var (
            ctx    = context.Background()
            origin = "12345678"      // Original password
            cipher = gbase64.EncodeString(origin)  // Base64 encoded password
        )
        // Log the original password
        g.Log().Infof(ctx, "origin: %s", origin)
        // Log the Base64 encoded password
        g.Log().Infof(ctx, "cipher: %s", cipher)

        // Encrypt the Base64 encoded password using AES-CBC
        encoded, err := gaes.EncryptCBC([]byte(cipher), []byte(encodeKey))
        t.AssertNil(err)
        // Log the final encrypted password (Base64 encoded again) - use this in config.yaml
        g.Log().Infof(ctx, "encoded: %s", gbase64.Encode(encoded))

        // Decrypt the password to verify the process works
        decoded, err := gaes.DecryptCBC(encoded, []byte(encodeKey))
        t.AssertNil(err)
        // Log the decoded password (should match the original)
        g.Log().Infof(ctx, "decoded: %s", gbase64.MustDecode(decoded))
    })
}
