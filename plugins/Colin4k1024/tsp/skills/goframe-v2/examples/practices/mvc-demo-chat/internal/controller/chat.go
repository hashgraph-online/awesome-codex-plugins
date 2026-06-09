package controller

import (
	"context"
	"fmt"

	"practices/mvc-demo-chat/api/v1"
	"practices/mvc-demo-chat/internal/consts"
	"practices/mvc-demo-chat/internal/model"

	"github.com/gogf/gf/v2/container/garray"
	"github.com/gogf/gf/v2/container/gmap"
	"github.com/gogf/gf/v2/container/gset"
	"github.com/gogf/gf/v2/encoding/ghtml"
	"github.com/gogf/gf/v2/encoding/gjson"
	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
	"github.com/gogf/gf/v2/os/gcache"
	"github.com/gogf/gf/v2/util/gconv"
)

var Chat = hChat{
	Users: gmap.New(true),
	Names: gset.NewStrSet(true),
}

type hChat struct {
	Users *gmap.Map    // All users in chat.
	Names *gset.StrSet // All names in chat for unique name validation.
}

func (h *hChat) Index(ctx context.Context, req *v1.ChatIndexReq) (res *v1.ChatIndexRes, err error) {
	var (
		r = g.RequestFromCtx(ctx)
	)
	view := r.GetView()
	if r.Session.MustContains(consts.ChatSessionName) {
		view.Assign("tplMain", "chat/include/chat.html")
	} else {
		view.Assign("tplMain", "chat/include/main.html")
	}
	_ = r.Response.WriteTpl("chat/index.html")
	return
}

func (h *hChat) Name(ctx context.Context, req *v1.ChatNameReq) (res *v1.ChatNameRes, err error) {
	var (
		session = g.RequestFromCtx(ctx).Session
	)
	// Create name in session.
	req.Name = ghtml.Entities(req.Name)
	session.MustSet(consts.ChatSessionNameTemp, req.Name)
	if h.Names.Contains(req.Name) {
		return nil, gerror.Newf(`Nickname "%s" is already token by others`, req.Name)
	} else {
		session.MustSet(consts.ChatSessionName, req.Name)
		session.MustRemove(
			consts.ChatSessionNameTemp,
			consts.ChatSessionNameError,
		)
	}
	return
}

func (h *hChat) Websocket(ctx context.Context, req *v1.ChatWebsocketReq) (res *v1.ChatWebsocketRes, err error) {
	var (
		r       = g.RequestFromCtx(ctx)
		ws      *ghttp.WebSocket
		msg     model.ChatMsg
		name    string
		msgByte []byte
	)
	if ws, err = r.WebSocket(); err != nil {
		g.Log().Error(ctx, err)
		return
	}
	// Chat name retrieving.
	if name = r.Session.MustGet(consts.ChatSessionName).String(); name == "" {
		name = r.Request.RemoteAddr
	}

	// Create session data for current websocket.
	h.Names.Add(name)
	h.Users.Set(ws, name)

	// It notifies all clients that this websocket is online.
	if err = h.writeGroupWithTypeList(); err != nil {
		return nil, err
	}

	for {
		// Blocking reading message from current websocket.
		_, msgByte, err = ws.ReadMessage()
		if err != nil {
			// Remove session info.
			h.Names.Remove(name)
			h.Users.Remove(ws)
			// It notifies all clients that this websocket is offline.
			_ = h.writeGroupWithTypeList()
			return nil, nil
		}
		// Message decoding.
		if err = gjson.DecodeTo(msgByte, &msg); err != nil {
			_ = h.write(ws, model.ChatMsg{
				Type: consts.ChatTypeError,
				Data: fmt.Sprintf(`invalid message: %s`, err.Error()),
				From: "",
			})
			continue
		}
		msg.From = name

		g.Log().Print(ctx, msg)

		switch msg.Type {
		case consts.ChatTypeSend:
			// Checks sending interval limit.
			var (
				cacheKey = fmt.Sprintf("ChatWebSocket:%p", ws)
			)
			if ok, _ := gcache.SetIfNotExist(ctx, cacheKey, struct{}{}, consts.ChatIntervalLimit); !ok {
				_ = h.write(ws, model.ChatMsg{
					Type: consts.ChatTypeError,
					Data: `Message sending too frequently, why not a rest first`,
					From: "",
				})
				continue
			}
			// When new message retrieved, it notifies all clients.
			if msg.Data != nil {
				if err = h.writeGroup(model.ChatMsg{
					Type: consts.ChatTypeSend,
					Data: ghtml.SpecialChars(gconv.String(msg.Data)),
					From: ghtml.SpecialChars(msg.From),
				}); err != nil {
					g.Log().Error(ctx, err)
				}
			}
		}
	}
}

// write sends message to current client.
func (h *hChat) write(ws *ghttp.WebSocket, msg model.ChatMsg) error {
	msgBytes, err := gjson.Encode(msg)
	if err != nil {
		return err
	}
	return ws.WriteMessage(ghttp.WsMsgText, msgBytes)
}

// writeGroup sends message to all clients.
func (h *hChat) writeGroup(msg model.ChatMsg) error {
	b, err := gjson.Encode(msg)
	if err != nil {
		return err
	}
	h.Users.RLockFunc(func(m map[interface{}]interface{}) {
		for user := range m {
			_ = user.(*ghttp.WebSocket).WriteMessage(ghttp.WsMsgText, []byte(b))
		}
	})

	return nil
}

// writeGroupWithTypeList sends "list" type message to all clients that can update users list in each client.
func (h *hChat) writeGroupWithTypeList() error {
	array := garray.NewSortedStrArray()
	h.Names.Iterator(func(v string) bool {
		array.Add(v)
		return true
	})
	if err := h.writeGroup(model.ChatMsg{
		Type: consts.ChatTypeList,
		Data: array.Slice(),
		From: "",
	}); err != nil {
		return err
	}
	return nil
}
