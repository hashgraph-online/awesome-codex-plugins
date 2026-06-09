package middleware

import (
	"github.com/gogf/gf/v2/errors/gcode"
	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/net/ghttp"
	"github.com/gogf/gf/v2/os/gctx"
	"github.com/golang-jwt/jwt/v5"
)

// JWTClaims represents the custom claims for the JWT token
type JWTClaims struct {
	Username string `json:"username"`
	jwt.RegisteredClaims
}

const (
	// CtxUsername is the context key for storing the username
	CtxUsername gctx.StrKey = "username"
	// JwtSecretKey is the secret key for JWT signing and validation
	// Note: In production, this should be replaced with a secure key
	JwtSecretKey = "your-secret-key-here"
)

// JWTAuth is a middleware that validates JWT tokens in the request header
// It checks for the presence and validity of the token, and sets the username
// in the context for downstream handlers
func JWTAuth(r *ghttp.Request) {
	// Get token from Authorization header
	tokenString := r.Header.Get("Authorization")
	if tokenString == "" {
		r.SetError(gerror.NewCode(gcode.CodeNotAuthorized, "No token provided"))
		return
	}

	// Remove 'Bearer ' prefix if present
	if len(tokenString) > 7 && tokenString[:7] == "Bearer " {
		tokenString = tokenString[7:]
	}

	// Parse and validate the token
	claims := &JWTClaims{}
	token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
		return []byte(JwtSecretKey), nil
	})

	if err != nil || !token.Valid {
		r.SetError(gerror.NewCode(gcode.CodeNotAuthorized, "Invalid token"))
		return
	}

	// Store username in context for later use
	r.SetCtxVar(CtxUsername, claims.Username)
	r.Middleware.Next()
}
