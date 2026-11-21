# Docker 基础与实战（微服务第二模块）

> 学习日期：2026-11-21
> 课程：[黑马 2026 微服务技术栈 BV1S142197x7](https://www.bilibili.com/video/BV1S142197x7) · Docker 模块（14 集）
> 环境：本机 **Docker Engine 24.0.9 / API 1.43 / containerd 1.7.29 / overlay2 / cgroup v2**
> 说明：本文所有「实测」结论都来自本机 terminal 真跑，不是抄博客。实验素材放在 `~/docker_lab/`。

---

## 一句话

**Docker = 把「应用 + 依赖 + 运行时」打成一个可搬运的镜像，用内核的 Namespace 做隔离、用 Cgroups 做限额、用 UnionFS 分层做存储。**
镜像管「交付」，容器管「运行」，仓库管「分发」——三者是同一个东西的三个状态，就像**类 / 对象 / Maven 中央仓库**。

---

## 一、为什么需要 Docker（先讲清它解决什么，再讲怎么用）

### 1.1 三个老问题

| 问题 | 传统做法 | Docker 做法 |
|------|----------|-------------|
| **环境不一致** | 开发机 JDK8、服务器 JDK11，`在我电脑上能跑` | 镜像里连 OS 用户态一起打包，跑起来的东西字节级一致 |
| **依赖冲突** | 一台机器只能装一个 MySQL 5.7 | 每个容器有自己的文件系统，两个 MySQL 版本同时跑 |
| **部署慢、扩容难** | 手动装环境、改配置、拷 jar | `docker run` 一条命令；配合编排可秒级横向扩容 |

### 1.2 Docker 不是什么

- ❌ **不是虚拟机**。VM 虚拟化的是**硬件**（Hypervisor + 完整 Guest OS，启动几十秒、占用 GB 级）；容器虚拟化的是**操作系统**（共享宿主内核，只隔离进程视角，启动毫秒级、占用 MB 级）。
- 实测：本机 `alpine:3.20` 镜像 **7.8 MB**，一个 `lab:v2` 业务镜像 **7.81 MB**（因为就基于 alpine）。同样的 VM 起步几个 GB。
- 代价：**容器跑不了别的内核**（Linux 容器不能跑 Windows），且**隔离性弱于 VM**（内核共享，逃逸风险更高）。

### 1.3 Docker 的地位

> **Docker 是微服务的地基，不是微服务本身。**

后面课程的 Nacos、Sentinel、RabbitMQ、Elasticsearch 全部以容器方式启动。所以它是**环境工具**，学它是为了以后少配置环境，而不是为了学微服务架构本身。（这也是我之前说的：学 Docker 不违背「放弃 SpringCloud」的决定。）

---

## 二、核心概念三件套

```
          docker build                docker run              docker push
Dockerfile ──────────> 镜像(Image) ──────────> 容器(Container) ──────────> 仓库(Registry)
(菜谱)                  (类/安装包)             (对象/进程)              (Maven 中央仓库)
                       静态、只读、分层         动态、可写层、有生命周期   分发与版本管理
```

### 2.1 镜像 = 只读分层文件系统

镜像是**一层层叠加的**，每层是只读的，只有最上面一层容器可写（写时复制 Copy-on-Write）。

实测 `docker history lab:v2`，从上到下（顶层在上）：

```
/bin/sh -c #(nop)  ENTRYPOINT ["/app/start.sh"]     ← 元数据层，几乎不占空间
/bin/sh -c #(nop)  USER appuser
/bin/sh -c echo '#!/bin/sh' > /app/start.sh ...      ← 真正写文件的层
/bin/sh -c #(nop)  WORKDIR /app
/bin/sh -c #(nop)  ENV APP_ENV=dev
CMD ["/bin/sh"]
ADD alpine-minirootfs-3.20.10-x86_64.tar.gz /        ← 基础镜像层
```

**关键认知：`RUN / COPY / ADD` 会生成真实文件层；`ENV / WORKDIR / USER / CMD / ENTRYPOINT / EXPOSE` 只是元数据层。**

### 2.2 容器 = 镜像 + 一个可写层 + 一个进程

**容器不是一个"轻量虚拟机"，而是被隔离的普通进程。** 实测：

```bash
$ docker run -d --name ex_test alpine:3.20 sh -c 'while true; do sleep 1; done'
$ docker exec ex_test sh -c 'pwd; head -2 /etc/os-release'
/
NAME="Alpine Linux"
ID=alpine
```

`pwd` 返回 `/`（不是宿主的 `/`），`/etc/os-release` 是 Alpine 的——这就是 **Mount Namespace**：容器看到的根目录是镜像的根目录。

### 2.3 仓库 = 镜像的分发中心

默认 Docker Hub。国内实测：

```bash
$ docker run --rm hello-world
docker: Error response from daemon: Get "https://registry-1.docker.io/v2/": context deadline exceeded.
```

即使 `/etc/docker/daemon.json` 里配了 `registry-mirrors`（`registry.docker-cn.com`、`docker.mirrors.ustc.edu.cn`），**这两个老镜像源早都失效了**，照样超时。

**2026 年可用的做法：显式带镜像源前缀拉取**

```bash
docker pull dockerproxy.net/library/alpine:3.20     # ✅ 实测成功
docker tag dockerproxy.net/library/alpine:3.20 alpine:3.20
```

避坑：`docker.m.daocloud.io` 实测 `TLS handshake timeout`、`docker.1ms.run` / `hub.rat.dev` 拉取卡住不动——**多备几个源轮着试比死磕一个可靠**。

---

## 三、命令地图（按使用频率排）

### 3.1 镜像相关

```bash
docker pull <image>:<tag>      # 拉取
docker images                  # 本地镜像列表
docker rmi <image>             # 删镜像（有容器引用会失败，先删容器）
docker tag <src> <dst>         # 打标签（实测用它把 dockerproxy.net/... 改成短名）
docker history <image>         # 看分层 —— 排查"镜像怎么这么大"的第一招
docker save / docker load      # 导出/导入 tar（离线部署）
```

### 3.2 容器生命周期

```bash
docker run [选项] <image> [命令]     # 创建 + 启动
docker ps                            # 运行中
docker ps -a                         # 含已退出
docker start / stop / restart <c>    # 生命周期
docker rm <c>                        # 删容器（-f 强制）
docker logs -f <c>                   # 看日志（stdout/stderr）
docker exec -it <c> sh               # 进容器（开新进程，不影响主进程）
```

**`run` 的常用选项，按重要性：**

| 选项 | 作用 | 备注 |
|------|------|------|
| `-d` | 后台运行 | 不加就是前台，Ctrl+C 即停 |
| `--name` | 命名 | 不命名会随机给个 `nervous_turing` 这种 |
| `-p 宿主:容器` | 端口映射 | **左边宿主、右边容器**，反过来是最常见写错 |
| `-e KEY=VALUE` | 环境变量 | 实测 `-e APP_ENV=prod` 覆盖了 Dockerfile 里的 `dev` |
| `-v 宿主:容器` | 挂载 | 见第五节 |
| `--rm` | 退出即删 | 一次性任务用 |
| `-it` | 交互式终端 | 调试用 |
| `--network host` | 用宿主网络 | 实测可用，跳过 NAT |
| `--memory` | 内存限额 | 实测 `--memory 64m` 后 `docker stats` 显示 `/ 64MiB` |
| `--restart` | 重启策略 | `no` / `on-failure` / `always` / `unless-stopped` |

### 3.3 观察与排障

```bash
docker inspect <c>                       # 完整 JSON，排障源头
docker inspect <c> --format '{{.State.ExitCode}}'   # 实测退出码 3 → exitcode=3
docker stats [--no-stream]               # 实测输出 cpu=0.12% mem=368KiB / 64MiB
docker top <c>                           # 容器内进程
docker port <c>                          # 实测 8080/tcp -> 0.0.0.0:18099
docker diff <c>                          # 可写层相对镜像改了什么（找"它到底改了哪个文件"）
docker cp <c>:<path> ./                  # 拷文件出来
```

**`inspect` 是最重要的排障命令**，模板取字段比 `docker ps` 信息全得多：

```bash
$ docker inspect stat_test --format '{{.State.Status}} mem={{.HostConfig.Memory}} ip={{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
running mem=67108864 ip=10.255.0.2
```

---

## 四、Dockerfile：把部署过程写成代码

### 4.1 全量指令表

| 指令 | 作用 | 要点 |
|------|------|------|
| `FROM` | 基础镜像 | 必须第一条（`ARG` 除外）；`FROM scratch` 表示空镜像 |
| `RUN` | 构建时执行 | **每条 RUN 生成一层**，多个命令用 `&&` 合并 |
| `COPY` | 复制文件 | 推荐用它不用 `ADD` |
| `ADD` | 复制 + 自动解压 tar + 支持 URL | 行为隐式，容易踩坑 |
| `WORKDIR` | 设工作目录 | 后续指令的相对基准；目录不存在会自动建 |
| `ENV` | 环境变量 | 构建+运行期都生效 |
| `ARG` | 构建参数 | **只在构建期有效**，运行时拿不到 |
| `EXPOSE` | 声明端口 | **纯文档性质，不会真的映射** |
| `VOLUME` | 声明匿名卷 | 该目录写入会落到卷而不是可写层 |
| `USER` | 切用户 | 安全底线，别用 root 跑业务 |
| `CMD` | 默认命令 | **可被 `docker run` 后面的命令整体替换** |
| `ENTRYPOINT` | 入口命令 | **不被替换，run 的参数追加在后面** |
| `.dockerignore` | 排除构建上下文 | 类比 `.gitignore`，能显著加快 build |

### 4.2 `CMD` vs `ENTRYPOINT` —— 实测踩坑

**同一个 Dockerfile，只把最后一行从 `CMD` 改成 `ENTRYPOINT`，行为完全不同。**

先用 `CMD`：

```bash
$ docker run --rm lab:v1 a b
docker: Error response from daemon: failed to create task for container:
  runc create failed: exec: "a": executable file not found in $PATH: unknown.
```

**为什么？** `CMD ["/app/start.sh"]` 被 `run` 后面的 `a b` **整条替换**了，等价于执行 `a b`——`a` 不是可执行文件，直接崩。

改成 `ENTRYPOINT ["/app/start.sh"]`：

```bash
$ docker run --rm lab:v2 a b
hello from container, env=dev, args=a b        ← 参数真的传进去了

$ docker run --rm -e APP_ENV=prod lab:v2
hello from container, env=prod, args=         ← 环境变量覆盖生效
```

**心智模型：**

```
最终执行命令 = ENTRYPOINT + (run 后面给的东西 | CMD 的默认值)
               ↑ 不可替换        ↑ 有就给，没有用 CMD
```

所以生产写法几乎都是：**`ENTRYPOINT` 放固定的启动器，`CMD` 放可变的默认参数**。

### 4.3 分层缓存 —— 为什么顺序决定构建速度

实测：重复 `docker build` 同一份 Dockerfile，输出全是 `---> Using cache`：

```
---> bf8527eb54c3
 ---> Using cache
 ---> d3675905f03a
 ---> Using cache
 ...
```

**规则：某一层的内容变了，它和它下面所有层全部失效。**

所以「改一次代码，所有依赖重装一遍」的经典事故是这样产生的：

```dockerfile
# ❌ 慢：任何源码改动都让 npm install 重跑
COPY . .
RUN npm install
```

```dockerfile
# ✅ 快：依赖清单不变就永远命中缓存
COPY package.json package-lock.json ./
RUN npm install
COPY . .
```

**口诀：越稳定的指令越往前放，越易变的越往后放。** `FROM → ENV → 装依赖 → 拷源码`。

### 4.4 多阶段构建

编译器和产物不该进生产镜像。Java 场景：

```dockerfile
# 阶段一：构建（镜像里带 Maven + JDK，很大）
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /src
COPY pom.xml .
RUN mvn -q dependency:go-offline        # 和 4.3 同一个套路：先拷 pom 吃缓存
COPY src ./src
RUN mvn -q package -DskipTests

# 阶段二：运行（只要 JRE，体积砍一大半）
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=build /src/target/app.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

`COPY --from=build` 只搬产物，构建工具的几百 MB 全留在上一阶段。

### 4.5 安全基线

实测容器内的用户确认：

```bash
$ docker run --rm --entrypoint sh lab:v2 -c 'id; ls -l /app'
uid=1000(appuser) gid=1000(appuser) groups=1000(appuser)
total 4
-rwxr-xr-x    1 appuser  root            61 Nov 21 13:15 start.sh
```

文件属主是 `appuser`，进程也以 `appuser` 跑——这就是 `USER appuser` 的效果。

- 别用 `root` 跑业务进程（容器逃逸时 root 危害最大）
- 别把密钥写进 `ENV`（`docker history` 能看到，见 2.1）
- 基础镜像用 `-slim` / `-alpine`，定期重建

---

## 五、数据卷：容器的"可写层"不可信

### 5.1 为什么必须挂卷

容器**删掉，可写层一起消失**。下面两段实测对比得很清楚：

```bash
# 绑定挂载（宿主目录）——容器删了文件还在
$ docker run --rm -v /home/admin/docker_lab/data:/data alpine:3.20 \
    sh -c 'echo from-container > /data/a.txt'
$ ls -l data/a.txt
-rw-r--r-- 1 root root 15 a.txt            ← 落在宿主磁盘上了

# 数据卷（Docker 托管）——容器删了卷还在
$ docker run -d --name vol_test -v labvol:/data alpine:3.20 sh -c 'echo named > /data/x; sleep 60'
$ docker rm -f vol_test
$ docker run --rm -v labvol:/data alpine:3.20 cat /data/x
named                                       ← 卷里的数据活着
```

### 5.2 三种挂载对比

| 类型 | 写法 | 存放位置 | 适用场景 |
|------|------|----------|----------|
| **bind mount** | `-v /宿主/绝对路径:/容器路径` | 你指定的宿主目录 | 开发时改代码即时生效、配置文件 |
| **volume** | `-v 卷名:/容器路径` | `/var/lib/docker/volumes/` | 数据库数据、生产持久化（**首选**） |
| **tmpfs** | `--tmpfs /容器路径` | 内存 | 临时缓存、敏感数据不落盘 |

**volume vs bind mount 的取舍：** bind mount 依赖宿主机路径（换机器就得改），volume 由 Docker 管理、可移植、可备份（`docker volume ls / inspect / prune`），**生产用 volume**。

### 5.3 🔴 权限坑：非 root 容器挂宿主目录会写不进去

这是一个极常见的生产事故。本机实测复现（先用 root 拥有、755 的宿主目录）：

```bash
# 1) 宿主目录属主是 root，用容器内的非 root 用户（uid 1000）去写
$ ls -ld rootdir
755  rootdir/                                   # owner=root
$ docker run --rm --user 1000:1000 -v /home/admin/docker_lab/rootdir:/data alpine:3.20 \
    sh -c 'echo ok > /data/b.txt'
sh: can't create /data/b.txt: Permission denied  ← 写不进去

# 2) 把宿主目录属主改成 1000 再跑，立刻好了
$ sudo chown -R 1000:1000 data2 && ls -ld data2
755  data2/
$ docker run --rm --user 1000:1000 -v /home/admin/docker_lab/data2:/data alpine:3.20 \
    sh -c 'echo ok > /data/b.txt && cat /data/b.txt'
ok                                               ← 成功
```

**另外注意：用 root 跑容器（默认）时写宿主目录是成功的，但生成的文件属主是 `root`：**

```bash
$ docker run --rm -v /home/admin/docker_lab/data:/data alpine:3.20 \
    sh -c 'echo from-container > /data/a.txt'
$ ls -l data/a.txt
-rw-r--r-- 1 root root 15        ← 容器里的 root = 宿主的 root
```

于是这里埋了第二个雷：**root 容器写出来的文件，之后非 root 容器（或宿主的普通用户）改不动**，会出现「第一次能跑，第二次启动就 Permission denied」的诡异现象。

**根因：容器内的 UID 和宿主的 UID 是同一套数字，Docker 默认不做映射（`docker info` 里没有 userns 相关的 Security Option，说明未开启 user namespace remapping）。** 容器里 `root`（uid 0）→ 宿主也是 `root`；容器里 `appuser`（uid 1000）→ 宿主也是 1000。

**三种解法：**

1. 宿主目录 `chown` 成容器内用户对应的 UID（最简单，但耦合）
2. `docker run --user 1000:1000` 显式指定（要保证目录可写）
3. 开启 **user namespace remapping**（`/etc/docker/daemon.json` 加 `"userns-remap": "default"`，把容器 root 映射成宿主的高位 UID，最安全但配置复杂、需要重建镜像、且改了之后**旧镜像/卷都要重新生成**）

> 这条和第六节的「容器内是哪个用户」是同一个知识点：**`USER` 指令决定了进程身份，但挂载目录的权限由宿主的 UID 数字决定。**

---

## 六、网络

### 6.1 四种模式

| 模式 | 写法 | 特点 |
|------|------|------|
| **bridge**（默认） | `-p 8080:80` | 容器有独立虚拟网卡 + 私有 IP，靠端口映射对外 |
| **host** | `--network host` | 直接用宿主网络栈，无 NAT，端口不能重复 |
| **none** | `--network none` | 只有 lo，完全隔离（安全计算） |
| **container** | `--network container:<c>` | 共享另一个容器的网络栈（k8s 的 Pod 就是这个思路） |

实测 bridge 模式下容器有自己的网段：

```bash
$ docker run --rm alpine:3.20 ip route
default via 10.255.0.1 dev eth0
10.255.0.0/24 dev eth0 scope link  src 10.255.0.2      ← 容器私有 IP
```

### 6.2 端口映射实测

```bash
$ docker run -d --name port_test -p 18099:8080 alpine:3.20 sh -c '<一个监听 8080 的小服务>'
$ docker port port_test
8080/tcp -> 0.0.0.0:18099
8080/tcp -> [::]:18099
$ curl http://127.0.0.1:18099
hello-docker                                          ← 外部能访问到容器的 8080
```

**`-p 宿主端口:容器端口`，左边是宿主。** 容器内服务监听 `8080`，宿主访问 `18099`。

### 6.3 自定义网络 + 容器名互访（微服务的前提）

默认 bridge 网络**不支持用容器名做 DNS 解析**，只能靠不稳定的 IP。自定义网络则可以：

```bash
docker network create msa
docker run -d --name redis --network msa redis:7
docker run -d --name app   --network msa myapp
docker exec app ping -c1 redis        # ✅ 能用名字 ping 通
```

这就是后面 Nacos / Eureka 之前，最朴素的「服务发现」原型。

---

## 七、Docker Compose：多容器编排

### 7.1 一个服务一个 `docker run` 是不可维护的

启动 MySQL + Redis + 应用 = 三条 `docker run`，参数记不住、顺序要注意、删起来要一个个删。Compose 用一个 YAML 描述全部。

```yaml
# docker-compose.yml（现代写法：不需要 version 顶层字段）
services:
  web:
    build: .
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=prod
    depends_on:
      - redis
    volumes:
      - ./logs:/app/logs
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
volumes:
  redis-data:
```

```bash
docker compose up -d          # 全部起来
docker compose ps             # 状态
docker compose logs -f web    # 看某个服务日志
docker compose down           # 全部停止并删除（-v 连卷一起删）
```

### 7.2 必须知道的三个点

1. **`depends_on` 只保证启动顺序，不保证服务就绪**。MySQL 端口起来了但还没初始化完，应用照样连不上 → 用 `healthcheck` + `depends_on: condition: service_healthy`。
2. **Compose 默认给项目建一个网络，服务名就是主机名**。`web` 里连 `redis` 直接写 `redis:6379`，不用 IP。
3. **`down` 默认不删 volume**（数据安全），要删加 `-v`。

### 7.3 🚨 本机踩到的真实故障：`docker compose` 命令不存在

本机是单机装的 Docker Engine，**没有 Compose 插件**：

```bash
$ docker compose version
docker: 'compose' is not a docker command.

$ docker-compose version        # 也不存在
```

尝试的修复路径与结果（**这是一份真实的排障记录，不是教程里的理想流程**）：

| 尝试 | 结果 |
|------|------|
| `pip install docker-compose` | ❌ `Failed to build 'PyYAML'`（Python 3.x 新版编译不过） |
| `curl github.com/docker/compose/releases/...` | ❌ 下载不到（GitHub release 直连超时） |
| `get.daocloud.io` 镜像下载 | ❌ `Couldn't connect to server` |
| `mirror.ghproxy.com` | ❌ 连接被拒 |
| `gh-proxy.com` | ⚠️ **返回了 2.5 MB 的文件、退出码 0，但内容不是可执行文件**（`md5sum` 有值、`strings` 无内容），执行时静默无输出 |
| 放到 `~/.docker/cli-plugins/docker-compose` | ❌ 仍报 `'compose' is not a docker command`（插件是坏的） |

**结论与教训：**
- **"下载成功、退出码 0" ≠ "拿到了正确文件"**。必须验证：`file` 类型、可执行、`--version` 有输出。gh-proxy 返回的假文件是这次最大的坑。
- 生产/学习环境推荐直接就着装 **Docker Desktop** 或 `dnf install docker-compose-plugin`（走官方仓库，不用折腾代理）。
- Compose 是**语法层**的知识，本文的 7.1 那份 YAML 结构是准确的；本机只是跑不起来，等装上插件即可验证。

---

## 八、把 Java 应用装进容器（微服务真正要用的场景）

### 8.1 标准 Dockerfile

```dockerfile
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
# 时区 + 语言（Dockerfile 里做，别等运行时 set）
ENV TZ=Asia/Shanghai LANG=C.UTF-8
# 先拷产物（单模块；多模块用 4.4 的多阶段）
COPY target/app.jar app.jar
EXPOSE 8080
# 容器限额与 JVM 对齐：容器看到多少内存，JVM 就用多少
# JDK 10+ 默认 -XX:UseContainerSupport 已开，但 -Xmx 仍建议显式给
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar /app/app.jar"]
```

### 8.2 三个必须对齐的点

1. **JVM 内存 vs 容器限额**。JDK 8u191+ 前 JVM 看不到 `--memory` 限额，会按宿主机的内存算默认堆——容器被 OOM Kill。现代 JDK 已默认 `UseContainerSupport`，但仍建议显式 `-Xmx`（一般为限额的 60~70%，剩余给元空间/线程栈/直接内存）。
2. **时区**。容器默认 UTC，日志时间比北京时间少 8 小时。`ENV TZ=Asia/Shanghai` 或挂 `/etc/localtime`。
3. **启动顺序**。应用先于 MySQL 启动 → 连接失败。用 Compose 的 `healthcheck` 或应用侧重试（Spring 的 `spring.datasource.hikari.initialization-fail-timeout` / 重连）。

### 8.3 容器里排障常用

```bash
docker exec -it <c> sh                      # alpine 只有 sh，没有 bash
docker exec <c> jcmd 1 VM.flags             # 看 JVM 实际参数（确认容器感知生效）
docker logs <c> --tail 200
docker inspect <c> --format '{{.State.OOMKilled}}'   # 是否被 OOM 杀
```

---

## 九、原理补充：隔离靠什么

| 机制 | Linux 能力 | 作用 |
|------|-----------|------|
| **Namespace** | PID / Mount / Network / UTS / IPC / User / Cgroup | 让进程"看不见"别人（实测容器里 `pwd` 是 `/`、`/etc/os-release` 是 Alpine 的） |
| **Cgroups** | cgroup v1 / **v2**（本机实测 `Cgroup Version: 2`） | 限制 CPU / 内存 / IO（实测 `--memory 64m` 后 `docker stats` 显示 `/ 64MiB`） |
| **UnionFS** | overlay2（本机实测 `Storage Driver: overlay2`） | 多个只读层 + 一个可写层合并成一个视图 |
| **Seccomp/Capabilities** | 实测 `Security Options: seccomp (builtin)` | 限制系统调用与内核能力 |

**一句话串起来：Namespace 管"看到什么"、Cgroups 管"能用多少"、UnionFS 管"文件从哪来"。** 三者合用 = 容器。因为共享内核，所以快；因为共享内核，所以隔离不如 VM。

---

## 十、踩坑清单（都是本机实测踩出来的）

1. **`CMD` 被 `docker run` 后面的参数整条替换** → 报 `exec: "a": executable file not found`。要传参用 `ENTRYPOINT`（4.2 实测）。
2. **`-p` 左右写反**。`-p 宿主:容器`，服务监听的是右边那个。
3. **`EXPOSE` 不会真的映射端口**，它只是文档。必须 `-p`。
4. **`registry-mirrors` 里的老源全废**，`docker pull` 静默超时。显式带前缀 `dockerproxy.net/library/xxx` 更可靠（2.3）。
5. **`docker build` 上下文包含巨大目录**（本机踩到 `can't stat '/tmp/snap-private-tmp'`）→ 换个干净目录，并写 `.dockerignore`。
6. **`docker compose` 命令不存在**，且下载的插件可能是假文件（7.3，**退出码 0 也要验证内容**）。
7. **非 root 用户挂宿主目录 Permission denied** → 宿主 UID 与容器 UID 是同一套数字（5.3）。反之 **root 容器写出的文件属主是 root**，后续非 root 读写会失败。
7b. 想 `chown` 改成 root 属主时如果在普通用户下会报 `chown: changing ownership ... Operation not permitted`——改属主要 `sudo`。
8. **容器可写层不可持久**，删容器数据就没了 → 数据库一律 `-v` 卷（5.1 实测）。
9. **`depends_on` 不等于服务就绪** → 必须 `healthcheck`。
10. **容器内 UID 1000 与宿主 UID 1000 同名不同人**，别以为改个用户名就隔离了。
11. **不带 `--rm` 的临时容器会堆积**，磁盘被可写层和悬空镜像吃满（`docker system df` 看，`docker system prune` 清）。
12. **每次 `RUN` 一层**，`RUN apt install && rm -rf /var/cache` 必须写成一条，否则删掉的文件还在上一层里占空间。

---

## 十一、速查表

```bash
# —— 镜像 ——
docker pull <img>:<tag>              docker images            docker rmi <img>
docker history <img>                 docker tag a b           docker save/load

# —— 容器 ——
docker run -d --name c -p 宿主:容器 -e K=V -v 宿主:容器 --memory 512m --rm <img>
docker ps / ps -a                    docker start|stop|restart|rm <c>
docker logs -f <c>                   docker exec -it <c> sh
docker inspect <c> [--format '{{.State.ExitCode}}']
docker stats --no-stream             docker top <c>           docker diff <c>
docker cp <c>:<path> ./

# —— 网络 ——
docker network ls / create <name>    docker network inspect <name>
-p 8080:80     --network host     --network msa

# —— 卷 ——
docker volume ls / inspect / prune    -v name:/path    -v /abs:/path

# —— 构建 ——
docker build -t name:tag .           # 越靠前的层越稳定
docker build --no-cache -t name:tag . # 强制重建

# —— Compose ——
docker compose up -d / ps / logs -f / down [-v] / build --no-cache

# —— 清理 ——
docker system df                     # 空间占用总览
docker system prune -a               # ⚠️ 删所有未使用镜像/容器/网络
```

---

## 十二、和前后的连接

- **往前接 MyBatis-Plus**：MP 管「数据怎么访问」，Docker 管「应用怎么交付」。两件事正交——MP 让代码变少，Docker 让环境变一致。
- **往后接微服务**：Nacos / Sentinel / RabbitMQ / Elasticsearch 全部容器起；Compose 的「服务名即主机名」是服务发现的最小原型；容器化之后的部署才是 K8s / 云原生的起点。
- **与 AI 主线的类比**（顺手打通）：Compose 的声明式 YAML ≈ LangGraph 的声明式建图——**都是「描述目标状态」而不是「写步骤」**；`healthcheck` 等待就绪 ≈ Agent 里工具调用的重试与超时策略；`--memory` 限额 ≈ 上下文预算（**都是给资源划死上限，逼系统在约束内工作**）。

---

## 附：本次实验素材

```
~/docker_lab/
├── Dockerfile              # ENTRYPOINT 版本（lab:v2）
├── docker-compose.yml      # 双服务编排示例（本机缺插件，未实跑）
├── data/a.txt              # bind mount 产物（root 拥有）
└── data2/b.txt             # chown 1000 后 bind mount 成功
```
