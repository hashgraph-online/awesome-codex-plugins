## 使用方式

```text
$ gf pack -h
USAGE
    gf pack SRC DST

ARGUMENT
    SRC    source path for packing, which can be multiple source paths.
    DST    destination file path for packed file. if extension of the filename is ".go" and "-n" option is given,
           it enables packing SRC to go file, or else it packs SRC into a binary file.

OPTION
    -n, --name       package name for output go file, it's set as its directory name if no name passed
    -p, --prefix     prefix for each file packed into the resource file
    -k, --keepPath   keep the source path from system to resource file, usually for relative path
    -h, --help       more information about this command

EXAMPLE
    gf pack public data.bin
    gf pack public,template data.bin
    gf pack public,template packed/data.go
    gf pack public,template,config packed/data.go
    gf pack public,template,config packed/data.go -n=packed -p=/var/www/my-app
    gf pack /var/www/public packed/data.go -n=packed
```

该命令用以将任意的文件打包为资源文件或者 `Go` 代码文件，可将任意文件打包后随着可执行文件一同发布。此外，在 `build` 命令中支持打包+编译一步进行，具体请查看 `build` 命令帮助信息。关于资源管理的介绍请参考 [资源管理](../核心组件/资源管理/资源管理.md) 章节。

## 使用示例

```text
$ gf pack public,template packed/data.go
done!
$ ll packed
total 184
-rw-r--r--  1 john  staff    89K Dec 31 00:44 data.go
```

## 延伸阅读

- [资源管理-最佳实践](../核心组件/资源管理/资源管理-最佳实践.md)