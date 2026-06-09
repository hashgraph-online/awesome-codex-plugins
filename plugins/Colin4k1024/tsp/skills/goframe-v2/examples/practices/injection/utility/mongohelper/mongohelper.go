package mongohelper

import (
	"github.com/gogf/gf/v2/errors/gerror"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

// MustObjectIDFromHex converts hex string to ObjectID.
func MustObjectIDFromHex(hex string) primitive.ObjectID {
	id, err := primitive.ObjectIDFromHex(hex)
	if err != nil {
		panic(gerror.Newf("%v %s", err, hex))
	}
	return id
}

// MustObjectIDsFromHexes converts hex strings to ObjectIDs.
func MustObjectIDsFromHexes(hexes []string) []primitive.ObjectID {
	ids := make([]primitive.ObjectID, len(hexes))
	for i, hex := range hexes {
		ids[i] = MustObjectIDFromHex(hex)
	}
	return ids
}
