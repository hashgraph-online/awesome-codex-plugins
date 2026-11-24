---
case: api-A7
description: Use when you call a gRPC service and want the call kept as a request the user can send again.
---

# gRPC

Shapes: api.

```sh
stickypane note write users-grpc.http <<'EOF'
### Get user
# @grpc users.v1.Users/Get
# @grpc-plaintext true
GRPC localhost:50051

{"id": 7}
# @assert response.grpc.status == "OK"
EOF
stickypane api users-grpc "Get user"
```

The message types come from `# @grpc-descriptor file.protoset`, else
from the server's reflection, else fields go by number (`{"1": 7}`).
There is no listing of services: you need the service and method names.
Unary and server-streaming calls only.

Done when: the last line ends in ✔ with the status you expected.
