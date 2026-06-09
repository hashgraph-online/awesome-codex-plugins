:::tip
从`v2`版本开始，项目的创建不再依赖远端获取，仓库模板已经通过 [资源管理](../核心组件/资源管理/资源管理.md) 的方式内置到了工具二进制文件中，因此项目创建速度非常迅速，无需网络访问。
:::

## 使用方式

```bash
$ gf init -h
USAGE
    gf init ARGUMENT [OPTION]

ARGUMENT
    NAME    name for the project. It will create a folder with NAME in current directory.
            The NAME will also be the module name for the project.

OPTION
    -m, --mono          initialize a mono-repo instead a single-repo
    -a, --monoApp       initialize a mono-repo-app instead a single-repo
    -u, --update        update to the latest goframe version
    -g, --module        custom go module
    -r, --repo          remote repository URL for template download
    -s, --select        enable interactive version selection for remote template
    -i, --interactive   enable interactive mode to select template
    -h, --help          more information about this command

EXAMPLE
    gf init my-project
    gf init my-mono-repo -m
    gf init my-mono-repo -a
    gf init my-project -u
    gf init my-project -g "github.com/myorg/myproject"
    gf init -r github.com/gogf/template-single my-project
    gf init -r github.com/gogf/examples/httpserver/jwt my-jwt
    gf init -r github.com/gogf/gf/cmd/gf/v2@v2.9.7 mygf
    gf init -r github.com/gogf/gf/cmd/gf/v2 mygf -s
    gf init -i
```

我们可以使用`init`命令在当前目录生成一个示例的`GoFrame`空框架项目，并可给定项目名称参数。生成的项目目录结构根据业务项目具体情况可自行调整。生成的目录结构详细介绍请参考 [工程目录设计](../框架设计/工程开发设计/工程目录设计.md) 章节。

:::tip 提示
- `GoFrame`框架开发推荐统一使用官方的`go module`特性进行依赖包管理，因此空项目根目录下也有一个`go.mod`文件。

- 工程目录采用了通用化的设计，实际项目中可以根据项目需要适当增减模板给定的目录。例如，没有`kubernetes`部署需求的场景，直接删除对应`deploy`目录即可。
:::

## 选项说明

| 选项 | 缩写 | 说明 |
|---|---|---|
| `--mono` | `-m` | 创建`MonoRepo`（大仓）项目，而非默认的`SingleRepo`项目 |
| `--monoApp` | `-a` | 在`MonoRepo`大仓中创建一个子应用项目 |
| `--update` | `-u` | 项目创建后自动升级`GoFrame`依赖到最新版本 |
| `--module` | `-g` | 自定义`Go`模块路径，不指定时默认使用项目名称 |
| `--repo` | `-r` | 指定远程仓库`URL`作为项目模板来源 |
| `--select` | `-s` | 配合`-r`使用，启用交互式版本选择 |
| `--interactive` | `-i` | 启用完整的交互式引导模式创建项目 |

## 模板类型

`gf init`命令支持三种内置项目模板：

| 模板类型 | 选项 | 说明 |
|---|---|---|
| `SingleRepo` | 默认 | 单仓项目，适用于大多数独立项目开发场景 |
| `MonoRepo` | `-m` | 大仓项目，适用于微服务架构的统一仓库管理 |
| `MonoRepoApp` | `-a` | 大仓子应用，在已有`MonoRepo`仓库中创建新的子服务 |

## 使用示例

### 在当前目录下初始化项目

使用`.`作为项目名称，直接在当前目录下初始化项目，模块名称默认使用当前目录名称。

```bash
$ gf init .
initializing...
initialization done!
you can now run 'gf run main.go' to start your journey, enjoy!
```

### 创建一个指定名称的项目

指定项目名称后，会在当前目录下创建一个同名文件夹，模块名称默认与项目名称一致。

```bash
$ gf init myapp
initializing...
initialization done!
you can now run 'cd myapp && gf run main.go' to start your journey, enjoy!
```

### 创建一个`MonoRepo`项目

默认情况下创建的是`SingleRepo`项目，若有需要也可以创建一个`MonoRepo`（大仓）项目，通过使用`-m`选项即可。

```bash
$ gf init mymono -m
initializing...
initialization done!
```

关于大仓的介绍请参考章节： [微服务大仓管理模式](../框架设计/工程开发设计/微服务大仓管理模式.md)

### 创建一个`MonoRepoApp`项目

若需要在`MonoRepo`（大仓）下创建一个子应用，在大仓项目根目录下，给定需要生成的项目路径，并使用`-a`选项即可。

```bash
$ gf init app/user -a
initializing...
initialization done!
```

### 自定义`Go`模块路径

默认情况下项目的`go.mod`中的模块名称(`module`)与项目文件夹名称一致。如果需要自定义`Go`模块路径（例如使用完整的仓库地址），可以通过`-g`选项指定。

```bash
$ gf init myapp -g "github.com/myorg/myproject"
initializing...
initialization done!
you can now run 'cd myapp && gf run main.go' to start your journey, enjoy!
```

执行后生成的`go.mod`文件中模块路径为`github.com/myorg/myproject`，项目中所有相关的`import`路径也会自动替换为该模块路径。

### 创建项目并升级`GoFrame`版本

使用`-u`选项可以在项目创建完成后自动将`GoFrame`依赖升级到**最新版本**，并执行`go mod tidy`。

```bash
$ gf init myapp -u
initializing...
initialization done!
you can now run 'cd myapp && gf run main.go' to start your journey, enjoy!
```

## 远程模板

除了使用内置模板外，`gf init`还支持从远程仓库拉取模板来创建项目，通过`-r`选项指定远程仓库地址。远程模板支持以下两种来源：

- **`Go`模块**：通过`Go`模块代理下载，支持使用`@version`语法指定版本。
- **`Git`仓库子目录**：通过`git sparse checkout`下载指定子目录，适合从示例仓库中提取特定项目。

:::tip 注意
使用远程模板时需要确保本地已安装`Go`环境。如果使用`Git`仓库子目录方式，还需要安装`git`工具。远程模板模式下，目标目录必须为空，否则会返回错误。
:::

### 使用远程`Go`模块模板

```bash
$ gf init -r github.com/gogf/template-single my-project
```

### 使用远程仓库子目录模板

可以从一个`Git`仓库的子目录中提取模板，适合从示例仓库中获取特定类型的项目模板。

```bash
$ gf init -r github.com/gogf/examples/httpserver/jwt my-jwt
```

### 指定模板版本

可以通过`@version`语法指定模板的版本号。

```bash
$ gf init -r github.com/gogf/gf/cmd/gf/v2@v2.9.7 mygf
```

### 交互式选择模板版本

使用`-s`选项配合`-r`选项，可以在命令执行时列出可用版本供用户选择。工具会展示最新的版本列表（按版本号倒序排列），用户可以通过编号选择或直接输入版本号。

```bash
$ gf init -r github.com/gogf/gf/cmd/gf/v2 mygf -s
```

## 交互式模式

使用`-i`选项可以启用完整的交互式引导模式，工具会分步引导用户完成项目创建的所有配置。

```bash
$ gf init -i
```

交互式模式分为两个阶段：

**第一步：选择初始化方式**

- **内置模板**（默认）：使用工具内置的模板快速创建项目，无需网络访问。
- **远程模板**：从远程仓库拉取模板创建项目。

**第二步（内置模板方式）：**

- 选择项目类型：`SingleRepo`/`MonoRepo`/`MonoRepoApp`
- 输入项目名称
- 输入`Go`模块路径（可选，默认使用项目名称）
- 选择是否升级到最新`GoFrame`版本

**第二步（远程模板方式）：**

- 选择预设模板（`template-single`、`template-mono`）或输入自定义仓库`URL`
- 输入项目名称
- 输入`Go`模块路径（可选）
- 选择是否升级依赖

:::info
交互式模式对新手用户非常友好，如果不确定各参数的用法，推荐使用该模式完成项目创建。
:::

## 注意事项

- 当目标目录已存在且非空时，使用内置模板会提示是否覆盖；使用远程模板则会直接报错，要求目标目录为空。
- 使用`.`作为项目名称时，会直接在当前目录下初始化项目，模块名默认取当前目录名称。
- `-u`选项在内置模板模式下会升级`GoFrame`相关依赖；在远程模板模式下会升级所有依赖并执行`go mod tidy`。
- 项目创建完成后，所有生成的`.go`文件中的`import`路径会自动替换为实际的模块路径。