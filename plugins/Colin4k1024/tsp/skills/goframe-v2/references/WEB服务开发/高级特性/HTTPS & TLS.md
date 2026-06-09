## HTTPS服务

建立 `HTTPS` 服务非常简单，使用框架WebServer提供的 `EnableHTTPS(certFile, keyFile string) error` 方法即可。很显然，该方法中需要提供两个参数，即两个用于 `HTTPS` 非对称加密的证书文件以及对应的秘钥文件。

### 准备工作

在本地演示的需要，我们可以使用 `openssl` 命令生成本地用于测试的证书和对应的秘钥文件。命令如下：

1. 使用常用的 `RSA` 算法生成秘钥文件

    ```shell
    openssl genrsa -out server.key 2048
    ```

    （可选）或者，我们也可以使用 `ECDSA` 算法来生成秘钥文件：

    ```shell
    openssl ecparam -genkey -name secp384r1 -out server.key
    ```

2. 根据秘钥文件生成证书文件

    ```shell
    openssl req -new -x509 -key server.key -out server.crt -days 365
    ```

3. （可选）根据秘钥生成公钥文件，该文件用于客户端与服务端通信

    ```shell
    openssl rsa -in server.key -out server.key.public
    ```

`openssl` 支持的算法以及命令参数比较多，如果想要深入了解请使用 `man openssl` 命令进行查看。本次示例中，本地环境（`Ubuntu`）使用命令生成相关秘钥、公钥、证书文件的流程如下：

```bash
$ openssl genrsa -out server.key 2048
Generating RSA private key, 2048 bit long modulus
.........................+++
.....................................................................+++
unable to write 'random state'
e is 65537 (0x10001)

$ openssl req -new -x509 -key server.key -out server.crt -days 365
You are about to be asked to enter information that will be incorporated
into your certificate request.
What you are about to enter is what is called a Distinguished Name or a DN.
There are quite a few fields but you can leave some blank
For some fields there will be a default value,
If you enter '.', the field will be left blank.
-----
Country Name (2 letter code) [AU]:CH
State or Province Name (full name) [Some-State]:SiChuan
Locality Name (eg, city) []:Chengdu
Organization Name (eg, company) [Internet Widgits Pty Ltd]:John.cn
Organizational Unit Name (eg, section) []:Dev
Common Name (e.g. server FQDN or YOUR name) []:John
Email Address []:john@johng.cn

$ openssl rsa -in server.key -out server.key.public
writing RSA key

$ ll
total 20
drwxrwxr-x  2 john john 4096 Apr 23 21:26 ./
drwxr-xr-x 90 john john 4096 Apr 23 20:55 ../
-rw-rw-r--  1 john john 1383 Apr 23 21:26 server.crt
-rw-rw-r--  1 john john 1675 Apr 23 21:25 server.key
-rw-rw-r--  1 john john 1675 Apr 23 21:26 server.key.public
```

其中，生成证书的命令提示需要录入一些信息，可以直接回车留空即可，我们这里随便填写了一些。

### 示例代码

根据以上生成的秘钥和证书文件，我们来演示如果使用 `ghttp.Server` 实现一个HTTPS服务。示例代码如下：

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
)

func main() {
    s := g.Server()
    s.BindHandler("/", func(r *ghttp.Request) {
        r.Response.Writeln("来自于HTTPS的：哈喽世界！")
    })
    s.EnableHTTPS("server.crt", "server.key")
    s.SetPort(8000)
    s.Run()
}
```

可以看到，我们直接将之前生成的证书和秘钥文件地址传递给 `EnableHTTPS` 即可，通过 `s.SetPort(8199)` 设置HTTPS的服务端口，当然我们也可以通过 `s.SetHTTPSPort(8199)` 来实现，在单一服务下两者没有区别，当 `WebServer` 需要同时支持 `HTTP` 和 `HTTPS` 服务的时候，两者的作用就不同了，这个特性我们会在后面介绍。随后我们访问页面 [https://127.0.0.1:8199/](https://127.0.0.1:8199/) 来看一下效果：

可以看到浏览器有提示信息，主要是因为我们生成的证书为私有的，非第三方授信企业提供的。浏览器大多会自带一些第三方授信的HTTPS证书机构，这些机构提供的HTTPS证书被浏览器认为是权威的、可信的，才不会出现该提示信息。一般这种第三方权威机构授信证书价格在每年几千到几万人民币不等，感兴趣的朋友可在搜索引擎上了解下。

我们这里直接点击 `Advanced`，然后点击 `Proceed to 127.0.0.1 (unsafe)`，最终可以看到页面输出预期的结果：

## `HTTPS` 与 `HTTP` 支持

我们经常会遇到需要通过HTTP和HTTPS来提供同一个服务的情况，即除了端口和访问协议不一样，其他都是相同的。如果按照传统的使用多 `WebServer` 的方式来运行的话会比较繁琐，为轻松地解决开发者的烦恼， `ghttp` 提供了非常方便的特性：支持 “同一个” `WebServer` 同时支持 `HTTPS` 及 `HTTP` 访问协议。我们先来看一个例子：

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
)

func main() {
    s := g.Server()
    s.BindHandler("/", func(r *ghttp.Request) {
        r.Response.Writeln("您可以同时通过HTTP和HTTPS方式看到该内容！")
    })
    s.EnableHTTPS("server.crt", "server.key")
    s.SetHTTPSPort(443)
    s.SetPort(80)
    s.Run()
}
```

执行后，通过本地浏览器访问这两个地址 [http://127.0.0.1/](http://127.0.0.1/) 和 [https://127.0.0.1/](https://127.0.0.1/) 都会看到同样的内容（需要注意的是，由于部分系统对于权限的限制，WebServer绑定 `80` 和 `443` 端口需要 `root/管理员` 权限，如果启动报错，可以更改端口号后重新执行即可）。

在本示例中，我们使用了两个方法来开启HTTPS特性：

```go
func (s *Server) EnableHTTPS(certFile, keyFile string) error
func (s *Server) SetHTTPSPort(port ...int) error
```

一个是添加证书及密钥文件，一个是设置HTTPS协议的监听端口，一旦这两个属性被设置了，那么WebServer就会启用HTTPS特性。并且，在示例中也通过 `SetPort` 方法来设置了HTTP服务的监听端口，因此该WebServer将会同时监听指定的HTTPS和HTTP服务端口。

## 使用 `Let’s Encrypt` 免费证书

`SSL免费证书` 机构比较多，如：

1. `Let’s Encrypt`: [https://letsencrypt.org/](https://letsencrypt.org/)
2. `腾讯云DV SSL 证书`: [https://cloud.tencent.com/product/ssl](https://cloud.tencent.com/product/ssl)
3. `CloudFlare SSL`: [https://www.cloudflare.com/](https://www.cloudflare.com/)
4. `StartSSL`: [https://www.startcomca.com/](https://www.startcomca.com/)
5. `Wosign沃通SSL`: [https://www.wosign.com/](https://www.wosign.com/)
6. `
               loovit.net AlphaSSL`: [https://www.lowendtalk.com/entry/register?Target=discussion%2Fcomment%2F2306096](https://www.lowendtalk.com/entry/register?Target=discussion%2Fcomment%2F2306096)

以下以 `Let's Encrypt` 为例，介绍如何申请、使用、续期免费证书。

`Let’s Encrypt` 官网地址： [https://letsencrypt.org/](https://letsencrypt.org/)

以下以 `Ubuntu` 系统为例，如何申请 `Let's Encrypt` 免费证书及在 `GoFrame` 框架下对证书的使用。

### 安装 `Certbot`

`Certbot` 官网地址： [https://certbot.eff.org/](https://certbot.eff.org/)

申请 `Let’s Encrypt` 免费证书需要使用到 `certbot` 工具：

```
sudo apt-get update
sudo apt-get install software-properties-common
sudo add-apt-repository ppa:certbot/certbot
sudo apt-get update
sudo apt-get install certbot
```

### 申请证书

使用以下命令：

```
certbot certonly --standalone -d 申请域名 --staple-ocsp -m 邮箱地址 --agree-tos
```

例如：

```
root@ip-172-31-41-204:~# certbot certonly --standalone -d goframe.org --staple-ocsp -m john@goframe.org --agree-tos
Saving debug log to /var/log/letsencrypt/letsencrypt.log
Plugins selected: Authenticator standalone, Installer None
Starting new HTTPS connection (1): acme-v02.api.letsencrypt.org
Obtaining a new certificate
Performing the following challenges:
http-01 challenge for goframe.org
Waiting for verification...
Cleaning up challenges

IMPORTANT NOTES:
 - Congratulations! Your certificate and chain have been saved at:
   /etc/letsencrypt/live/goframe.org/fullchain.pem
   Your key file has been saved at:
   /etc/letsencrypt/live/goframe.org/privkey.pem
   Your cert will expire on 2019-01-25. To obtain a new or tweaked
   version of this certificate in the future, simply run certbot
   again. To non-interactively renew *all* of your certificates, run
   "certbot renew"
 - If you like Certbot, please consider supporting our work by:

   Donating to ISRG / Let's Encrypt:   https://letsencrypt.org/donate
   Donating to EFF:                    https://eff.org/donate-le
```

默认情况下，证书会被安装到 `/etc/letsencrypt/`，证书和私钥文件分别为：

```
/etc/letsencrypt/live/goframe.org/fullchain.pem
/etc/letsencrypt/live/goframe.org/privkey.pem
```

### 使用证书

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
)

func main() {
    s := g.Server()
    s.BindHandler("/", func(r *ghttp.Request) {
        r.Response.Writeln("来自于HTTPS的：哈喽世界！")
    })
    s.EnableHTTPS(
        "/etc/letsencrypt/live/goframe.org/fullchain.pem",
        "/etc/letsencrypt/live/goframe.org/privkey.pem",
    )
    s.Run()
}
```

### 证书续期

证书默认有效期为 `3个月`，到期后需要手动续期，使用以下命令：

```
certbot renew
```

示例1，我们可以使用 `crontab` 定时任务来实现自动续期：

```
# 每天尝试续期一次，成功后重启`GoFrame`框架运行的WebServer
0 3 * * * certbot renew --quiet --renew-hook "kill -SIGUSR1 $(pidof 进程名称)"
```

示例2，如果我们通过 `nginx` 管理证书，那么我们可以这样来设置定时任务：

```
# 每天尝试续期一次，证书续期需要先关闭80端口的WebServer监听
0 3 * * * service nginx stop && certbot renew --quiet --renew-hook "service nginx start"
```

为了防止 `certbot renew` 命令可能的失败导致 `nginx` 无法重新启动，为保证稳定性，可以这样：

```
# 每天尝试续期一次，证书续期需要先关闭80端口的WebServer监听
0 3 * * * service nginx stop && certbot renew --quiet --renew-hook "service nginx start"
5 3 * * * service nginx start
```