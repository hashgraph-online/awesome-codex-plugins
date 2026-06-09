## Go实现枚举值

`Go` 语言并没有提供 `enum` 的定义，我们可以使用 `const` 来模拟枚举类型，这也是 `Go` 语言中约定俗成的方式。

例如，在 `Kubernetes` 项目中，有大量的以常量形式定义的"枚举值"：

```go
// PodPhase is a label for the condition of a pod at the current time.
type PodPhase string

// These are the valid statuses of pods.
const (
    // PodPending means the pod has been accepted by the system, but one or more of the containers
    // has not been started. This includes time before being bound to a node, as well as time spent
    // pulling images onto the host.
    PodPending PodPhase = "Pending"
    // PodRunning means the pod has been bound to a node and all of the containers have been started.
    // At least one container is still running or is in the process of being restarted.
    PodRunning PodPhase = "Running"
    // PodSucceeded means that all containers in the pod have voluntarily terminated
    // with a container exit code of 0, and the system is not going to restart any of these containers.
    PodSucceeded PodPhase = "Succeeded"
    // PodFailed means that all containers in the pod have terminated, and at least one container has
    // terminated in a failure (exited with a non-zero exit code or was stopped by the system).
    PodFailed PodPhase = "Failed"
    // PodUnknown means that for some reason the state of the pod could not be obtained, typically due
    // to an error in communicating with the host of the pod.
    PodUnknown PodPhase = "Unknown"
)
```

## 如何跨服务高效维护枚举值

如果只是项目内部使用枚举值比较简单，定义完了内部使用即可，但涉及到跨服务之间调用，或者前后端协作时，效率就比较低了。当服务需要给外部调用者展示接口能力时，往往需要生成 `API` 接口文档（或者接口定义文件，例如 `proto`），往往也需要根据接口文档（文件）生成调用的客户端 `SDK`。

如果是接口定义文件，例如 `proto`，往往可以直接查看源码来解决这个问题，问题不大。我们这里主要讨论的是接口文档维护枚举值的问题，特别是前后端协作时通过 `OpenAPI` 标准协议来维护枚举值的问题。这里我们提供了专门的工具来维护这些枚举值，具体请参考章节： [枚举维护-gen enums](../开发工具/代码生成-gen/枚举维护-gen%20enums.md)