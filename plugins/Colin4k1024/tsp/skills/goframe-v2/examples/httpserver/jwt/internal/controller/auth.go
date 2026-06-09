package controller

import (
	"context"
	"time"

	v1 "main/api/v1"
	"main/internal/middleware"

	"github.com/gogf/gf/v2/errors/gcode"
	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/util/gconv"
	"github.com/golang-jwt/jwt/v5"
)

// Auth is the controller for handling authentication related requests
type Auth struct{}

// JWTClaims represents the custom claims for the JWT token
type JWTClaims struct {
	Username string `json:"username"`
	jwt.RegisteredClaims
}

// Login processes user login request and generates JWT token
// It validates the credentials (in this demo, against hardcoded values)
// and returns a JWT token if authentication is successful
func (a *Auth) Login(ctx context.Context, req *v1.LoginReq) (res *v1.LoginRes, err error) {
	// In a real application, validate credentials against a database
	// This is just a demo with hardcoded values
	if req.Username != "admin" || req.Password != "password" {
		return nil, gerror.NewCode(gcode.CodeInvalidParameter, "Invalid credentials")
	}

	// Create claims with user information
	claims := &JWTClaims{
		Username: req.Username,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(24 * time.Hour)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			NotBefore: jwt.NewNumericDate(time.Now()),
		},
	}

	// Generate token
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	signedToken, err := token.SignedString([]byte(middleware.JwtSecretKey))
	if err != nil {
		return nil, gerror.NewCode(gcode.CodeInternalError, "Failed to generate token")
	}

	return &v1.LoginRes{
		Token: signedToken,
	}, nil
}

// Protected handles requests to protected endpoints
// It requires a valid JWT token and returns user information along with the current time
func (a *Auth) Protected(ctx context.Context, req *v1.ProtectedReq) (res *v1.ProtectedRes, err error) {
	return &v1.ProtectedRes{
		Username: gconv.String(ctx.Value(middleware.CtxUsername)),
		Time:     time.Now(),
	}, nil
}
