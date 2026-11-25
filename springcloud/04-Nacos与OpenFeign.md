# Nacos 注册中心与 OpenFeign 远程调用（微服务第三模块 · 上）

> 学习日期：2026-11-25
> 课程：[黑马 2026 微服务技术栈 BV1S142197x7](https://www.bilibili.com/video/BV1S142197x7) · Nacos + OpenFeign 模块
> 环境：本机 **Nacos 2.3.2 standalone（Docker `nacos/nacos-server:v2.3.2`，8848 HTTP + 9848 gRPC）** · **JDK 17（Dragonwell）** · **Spring Boot 3.2.5 / Spring Cloud 2023.0.1 / Spring Cloud Alibaba 2023.0.1.0** · Maven 3.9.6
> 说明：**本文的重点不是「Nacos 怎么装、Feign 怎么写」这种教程步骤，而是「注册中心到底靠什么机制工作」** —— 下面每条「实测」都来自本机真跑：curl 直打 Nacos OpenAPI、两个 user-service 实例 + 一个 order-service 组成的真实调用链、以及针对注册/心跳/摘除/负载均衡的对照实验。代码在这：`~/nacos_lab/cloud-demo/`。

---

## 一句话

**Nacos = 让服务「自己报名字」的电话簿；OpenFeign = 让你「照名字打电话」的声明式拨号器。**
二者缺一不可：注册中心解决「**别人的地址是什么**」，Feign 解决「**知道了地址之后怎么优雅地发起 HTTP 调用**」。
再往下一层：**Nacos 的本质不是一张表，而是「一张表 + 一套让表永远接近真相的更新机制」**——注册、心跳、推送、摘除，四件事合起来才叫注册中心。

---

## 一、没有注册中心的世界长什么样（先讲清它治什么病）

服务拆开后，order-service 需要调用 user-service。课程里的演进路径是：

| 阶段 | 做法 | 病在哪 |
|------|------|--------|
| ① 硬编码 | `RestTemplate` 写死 `http://localhost:8081/user/1` | 换机器/换端口要改代码重新发版 |
| ② 配置文件 | 把地址抽到 `application.yml` | 改配置要重启；**多实例时根本写不下** |
| ③ 手工维护列表 | 配置文件里放一个地址数组，自己的 `LoadBalancer` 轮询 | 实例上下线全靠人工同步 → 必然滞后 |

关键的第三点就是注册中心存在的全部理由：**服务实例是动态的**（扩缩容、发版、宕机、迁移），而「人工维护的地址列表」永远是**一个正在腐烂的快照**。

> **注册中心解决的从来不是「存地址」，而是「让地址集合自动保持新鲜」。**

---

## 二、Nacos 两个身份要对齐：注册中心 + 配置中心

课程里 Nacos 同时干两件事，初学者容易混：

| 能力 | 干什么 | 端口/协议 | 本文实测到的 OpenAPI |
|------|--------|-----------|---------------------|
| **注册中心（Naming）** | 服务实例登记与发现 | 8848 HTTP + **9848 gRPC**（2.x 客户端走 gRPC 长连接） | `/nacos/v1/ns/instance`（注册）、`/nacos/v1/ns/instance/list`（查询）、`/nacos/v1/ns/instance/beat`（心跳） |
| **配置中心（Config）** | 配置集中管理与热更新 | 8848 HTTP + 9849 gRPC | `/nacos/v1/cs/configs`（发布/读取）、`/nacos/v1/cs/configs/listener`（长轮询监听）、`/nacos/v1/cs/history`（历史版本） |

实测：`nc -z 127.0.0.1 9848` 通，说明客户端注册成功后其实**还靠 gRPC 长连接**在收推送——这一点非常关键，后面摘除实验会用到。

启动方式（standalone 单机，仅学习用）：

```bash
docker run -d --name nacos-standalone \
  -e MODE=standalone -e NACOS_AUTH_ENABLE=false \
  -p 8848:8848 -p 9848:9848 \
  nacos/nacos-server:v2.3.2
# 就绪探针
curl "http://127.0.0.1:8848/nacos/v1/console/health/readiness"   # OK
curl "http://127.0.0.1:8848/nacos/v1/ns/operator/metrics"        # {"status":"UP"}
```

> 生产环境不要 standalone：集群模式 + 外置 MySQL（Nacos 默认用内嵌 Derby，重启/多节点会丢数据），并且**必须开鉴权**（`NACOS_AUTH_ENABLE=true` + 改默认 `nacos/nacos` 密码）。本文为了做实验关掉了鉴权，`/nacos/v1/auth/users/login` 返回 `"accessToken":"AUTH_DISABLED"`——**这就是它没开鉴权的证据**。

---

## 三、服务的分级模型：Namespace → Group → Service → Cluster → Instance

这是 Nacos 最容易被当成「概念背诵」的部分，但要理解它只需要一个视角：**这五层是「隔离/分组」的五个正交维度，越往下越细**。

```
Namespace（环境/租户，隔离最强，默认 public）
└── Group（业务分组，默认 DEFAULT_GROUP）
    └── Service（服务名，如 user-service）
        └── Cluster（机房/同地域，默认 DEFAULT）
            └── Instance（ip:port + weight + metadata + healthy/ephemeral）
```

实测命名空间创建：

```bash
curl -X POST "http://127.0.0.1:8848/nacos/v1/console/namespaces" \
  -d "customNamespaceId=dev&namespaceName=dev&namespaceDesc=开发环境"
# 返回 true；再查 /nacos/v1/console/namespaces 可见 public + dev 两条
```

**踩到的第一个真实坑**：我发布了一条配置到默认命名空间，但用 `?dataId=...&group=...` 读回来是 `config data not exist`——差点以为是写入失败。其实**发布和读取必须在同一个 namespace**，读取时显式带 `&tenant=`（空串即 public）才能命中。**「查不到」很多时候不是没写进去，是查错了分区**。

> 记忆锚点：`Namespace = 哪套环境`、`Group = 哪个团队/业务线`、`Service = 哪个服务`、`Cluster = 哪个机房`、`Instance = 哪台机器`。跨 Namespace **默认互不可见**，跨 Group 可发现但需指定 group。

---

## 四、实例的两个「生死方式」：临时实例 vs 持久实例（这是理解 Nacos 的主线）

课程里会讲 `ephemeral`，但很少讲透为什么需要两种。实测对照如下：

### 4.1 临时实例（ephemeral=true，**Spring Cloud 默认就是它**）

- 存活依赖**客户端主动心跳**（默认每 5s 一次，`instanceHeartBeatInterval: 5000`）
- 超过 **15s** 无心跳 → 标记 `healthy=false`（不再被路由，但还留在列表中）
- 超过 **30s** 无心跳 → **直接从列表摘除**（`ipDeleteTimeout: 30000`）
- 适合：**无状态应用、随时扩缩容的 Pod/进程**——机器没了实例就该消失

实测（手打 OpenAPI 注册一个不心跳的实例）：

```
t=0s   注册 192.168.1.10:8081 ephemeral=true   → ok，hosts 里 healthy=true
t=16s  不心跳                                  → healthy=false（但仍在列表中）
t=40s  仍不心跳                                → hosts: []（已摘除）
```

### 4.2 持久实例（ephemeral=false）

- **不依赖客户端心跳**，由服务端主动探活（`tcp/HTTP` 健康检查）
- 客户端进程死了实例也**不会自动消失**，只能手动下线（`enabled=false`）或删除
- 适合：**数据库、中间件、老系统**这类「地址是固定的、不归注册中心管生死」的服务

实测：持久实例注册后（`ephemeral=false`）我人为让它探测不到 → `healthy=false` 但**依然留在列表里**，且尝试手动改健康状态被服务端拒绝：

```
PUT /nacos/v1/ns/health/instance → caused: health check is still working,
service: DEFAULT_GROUP@@order-service, cluster: DEFAULT;
```

> **这句话是本节最有价值的一条**：持久实例的健康状态**由服务端探活决定，客户端说了不算**。所以生产上「注册中心里显示健康但业务实际出问题」的经典事故，多半就是探活只看 TCP 端口通不通（端口活着、业务已死）。

### 4.3 ★ 一个非常容易撞上的真实报错（我实测撞上了）

我在实验里先手工注册了两个 `order-service` 的**持久实例**做对照，之后启动真实的 Spring Boot order-service（默认临时实例），启动直接**失败**：

```
errCode: 400, errMsg: Current service DEFAULT_GROUP@@order-service is persistent service,
can't register ephemeral instance.
  → nacos registry, order-service register failed...
  → ApplicationContextException: Failed to start bean 'webServerStartStop'
```

**机制**：一个 Service 下**不能混用两种实例类型**（服务级别有个 `type` 字段，第一个注册的实例类型定死了这个服务）。脏数据一旦存在，正确的 Spring 服务反而起不来，而且**报错是注册失败 → 容器启动失败**，看起来像「Nacos 挂了」或「代码有问题」，排查方向很容易跑偏。

**解法**：`DELETE /nacos/v1/ns/instance?...&ephemeral=false` 删干净（必要时连 Service 一起删 `DELETE /nacos/v1/ns/service?serviceName=xxx`），再重启服务。

> 教训：**注册中心里的脏数据会伪装成你的代码 bug。** 微服务排障第一步永远是「先看注册表长什么样」，而不是先看代码。

---

## 五、注册中心真正的工作原理（本节核心）

大部分人把 Nacos 理解成「一张服务列表的表」，然后就卡在几个经典疑问上：
- 服务下线了，调用方多久知道？
- Nacos 挂了，业务还能不能跑？
- 为什么有的服务端配置改了调用方「立刻就生效」，有的要等半分钟？

答案在于**四条独立的时间线**，必须拆开看：

| 机制 | 方向 | 频率/触发 | 生效效果 |
|------|------|-----------|----------|
| **注册** | 客户端 → 服务端 | 启动时一次 | 实例进表（`REGISTER-SERVICE` 日志） |
| **心跳上报** | 客户端 → 服务端 | 默认 5s | 维持「我还活着」 |
| **服务端推送（push）** | 服务端 → 客户端 | 表变化时立即 | 客户端本地缓存**立刻刷新**（2.x 走 gRPC 长连接） |
| **客户端定时拉取（pull）** | 客户端 → 服务端 | 默认 30s（`watchDelay`） | 兜底：推送丢了也能最终一致 |

实测日志（user-service 启动即注册）：

```
com.alibaba.nacos.client.naming : [REGISTER-SERVICE] public registering service user-service
  with instance Instance{ip='172.24.3.167', port=8081, weight=1.0, healthy=true,
  enabled=true, ephemeral=true, metadata={preserved.register.source=SPRING_CLOUD}}
c.a.c.n.registry.NacosServiceRegistry : nacos registry, DEFAULT_GROUP user-service
  172.24.3.167:8081 register finished
```

**注意两件事**：
1. `metadata` 里有 `preserved.register.source=SPRING_CLOUD` —— 这是 Spring Cloud Alibaba 打的标记（谁注册的）。
2. **注册上去的是宿主机的真实内网 IP**（`172.24.3.167`），不是 127.0.0.1。多网卡/容器环境下取错网卡是经典事故，需要 `spring.cloud.nacos.discovery.ip` / `network-interface` 显式指定。

### 5.1 ★ 摘除到底快不快？我做了精确计时实验

网上说法混乱（「立刻」「30s」「15s」都有人说），实测结果：

```
T0: kill -9 node-B (pid 352473)
t=2s: 注册表 IP 数 = 1，实际路由 = node-A  →  已摘除，请求未失败
```

**结论：Nacos 2.x + gRPC 长连接下，进程被强杀是「秒级」摘除，不是等 15s/30s 心跳超时。** 机制是：进程死亡 → TCP/gRPC 连接断开 → 服务端感知连接断开 → 立即摘除并向订阅者推送。

**但这里有个巨大陷阱，必须记住**：

| 死法 | 服务端能否感知 | 摘除速度 | 真实影响 |
|------|----------------|----------|----------|
| 进程正常退出 / kill -9 | ✅ 连接断开 | **秒级** | 调用方基本无感 |
| 机器断网 / 网络分区 / 容器网络黑洞 | ❌ 连接看似还在（半开） | **要等心跳超时 15s+** | 这段时间流量会打到黑洞实例，**真实超时** |

所以「Nacos 摘除很快」这句话只在**进程级故障**下成立。**网络分区才是真正会让你半夜被告警叫醒的场景**，而它能救你的只有「心跳超时 + 客户端侧的超时/重试/熔断」（后者是 Sentinel 模块的内容）。

### 5.2 新实例上线多久被发现？反方向的实验

我启动 node-C（18082）后，**order-service 在第 1 轮（0~10s 内）就已经把请求分到它了**。原因同上：服务端推送，不等 30s 拉取。

> 把 5.1 和 5.2 放一起看，才能得出正确结论：
> **在「连接正常」的前提下，Nacos 的变更传播是推模式、准实时（秒级）；30s 轮询只是兜底。**
> 一旦连接异常（网络分区），一切都退回到 15s/30s 的**心跳超时**时间尺度。

---

## 六、OpenFeign：声明式远程调用

手写 `RestTemplate` 的三个难受点：URL 拼接、结果反序列化、没有像本地方法一样的抽象。Feign 的思路是**「把 HTTP 调用伪装成本地接口调用」**。

### 6.1 三步走

```java
// 1. 开闸：启动类加注解
@EnableFeignClients
@SpringBootApplication
public class OrderApplication { ... }

// 2. 声明客户端：只写「调谁 + 调哪个路径」，不写 IP 不写端口
@FeignClient(name = "user-service")           // ← name 就是 Nacos 里的服务名
public interface UserClient {
    @GetMapping("/user/{id}")
    String queryUser(@PathVariable("id") Long id);
}

// 3. 像调本地方法一样用
String user = userClient.queryUser(id);
```

**`name = "user-service"` 这一行就是全部魔法**：Feign 把服务名交给 `LoadBalancer`，后者向 Nacos 要实例列表，挑一个，拼出真实 `http://172.24.3.167:8081/user/1` 再发请求。

### 6.2 实测调用结果（这是最直观的证据）

两个 user-service 实例（8081 = node-A、18081 = node-B），一个 order-service：

```
order#1 -> user#1 from 127.0.0.1:8081  tag=node-A cost=224ms
order#2 -> user#2 from 127.0.0.1:18081 tag=node-B cost=190ms
order#3 -> user#3 from 127.0.0.1:8081  tag=node-A cost=17ms
order#4 -> user#4 from 127.0.0.1:18081 tag=node-B cost=20ms
```

**严格交替** —— 默认策略 `RoundRobinLoadBalancer`（Spring Cloud 2023 已无 Ribbon，用的是 `spring-cloud-loadbalancer`，**不引它 Feign 启动直接失败**，这是个高频坑）。

### 6.3 依赖清单（Spring Cloud 2023 版本要对齐）

```xml
<!-- 父 POM 的版本三件套必须配套，错一个都可能启动失败 -->
<spring-boot.version>3.2.5</spring-boot.version>
<spring-cloud.version>2023.0.1</spring-cloud.version>
<spring-cloud-alibaba.version>2023.0.1.0</spring-cloud-alibaba.version>

<!-- 注册/发现 -->
<dependency>
  <groupId>com.alibaba.cloud</groupId>
  <artifactId>spring-cloud-starter-alibaba-nacos-discovery</artifactId>
</dependency>
<!-- Feign 本体 -->
<dependency>
  <groupId>org.springframework.cloud</groupId>
  <artifactId>spring-cloud-starter-openfeign</artifactId>
</dependency>
<!-- ★ 必须显式引：2020 之后 Ribbon 被移除，负载均衡拆成独立 starter -->
<dependency>
  <groupId>org.springframework.cloud</groupId>
  <artifactId>spring-cloud-starter-loadbalancer</artifactId>
</dependency>
```

### 6.4 日志：想看真实的请求/响应要开两处

Feign 默认**不打任何请求日志**。我实测开了两层：

```yaml
spring.cloud.openfeign.client.config.default.logger-level: full   # ① Feign 自己：basic/headers/full
logging.level.cn.itcast.orderservice.UserClient: debug            # ② 该接口包的日志级别降为 debug
```

**两处缺一不可**——这是 Feign 日志最反直觉的地方：`logger-level` 只决定「记录多少」，而 Feign 用 `FULL` 日志时会打 debug 级别，包级别不放行就什么都看不到。

### 6.5 HTTP 客户端选型（性能与连接池）

| 客户端 | 特点 |
|--------|------|
| `HttpURLConnection`（默认） | **不支持连接池**，每次新建连接，高并发下是明显瓶颈 |
| Apache HttpClient 5 / OkHttp | 支持连接池，生产必换 |

Spring Cloud 2023 换用的方式：引 `feign-hc5`（或 `feign-okhttp`）依赖，再 `spring.cloud.openfeign.httpclient.hc5.enabled=true` + `spring.cloud.openfeign.http2client.enabled=true` 之类开关。**默认那个抓一下就知道没连接池**，是「能跑但跑不快」的典型。

### 6.6 性能优化的真正抓手

很多人以为优化 Feign 是「调参数」，其实就四件事，按收益排序：

1. **换连接池客户端**（默认 URLConnection 无池）
2. **开日志有成本**（`full` 会打印 body，只建议在预发开；生产用 `basic`）
3. **合理的超时**（连接超时 / 读超时，默认值往往太长，一个慢依赖会拖住整个线程池）
4. **别把大对象/大量数据一次传**，能批处理就批处理

---

## 七、负载均衡的「可运营」一面：权重与上下线（实测）

这是课程里容易被略过、但生产上极其有用的一块：**不改代码、不发版，直接在注册中心调整流量**。

### 7.1 权重（weight）

给 node-B 设 `weight=0.1`（相当于让它的流量变成 node-A 的十分之一）：

```bash
curl -X PUT "http://127.0.0.1:8848/nacos/v1/ns/instance?serviceName=user-service&ip=172.24.3.167&port=18081&weight=0.1&ephemeral=true"
```

**实测**：改完立刻跑 20 次，结果还是 10:10 均分 —— **权重不是立刻生效的**，客户端要重新拉取到新的实例列表（含 weight）才会按权重加权，所以需要等一个刷新周期。

### 7.2 enabled=false（下线但保留）

```bash
curl -X PUT "http://127.0.0.1:8848/nacos/v1/ns/instance?serviceName=user-service&ip=...&port=18081&enabled=false&ephemeral=true"
```

**实测**：等 35s 后 20 次请求 **全部打到 node-A**，一次都没漏到已下线节点；恢复 `enabled=true&weight=1` 后再等 35s，6 次请求 3:3 恢复均衡。

> 这两条合起来就是**「不发版灰度」**的标准手法：
> - **权重**：按比例切流（10% → 30% → 100%），做金丝雀发布
> - **enabled**：整机摘除（发版前踢出、发版后拉回），做滚动更新
> - 两者都**不需要重启调用方**，但都需要**等一个客户端刷新周期**才生效 —— 这个延迟就是灰度事故（「我刚下线了为什么还有流量」）的常见根因

---

## 八、健康状态 vs 上下线状态：两个独立开关

一个实例的状态由三个字段描述，它们**互不覆盖**：

| 字段 | 含义 | 谁改 |
|------|------|------|
| `healthy` | 实例是否活着（心跳/探活） | 客户端心跳或服务端探活 |
| `enabled` | 是否允许被路由（人工开关） | 运维/接口 |
| `weight` | 被路由到的相对概率 | 运维/接口 |

- `enabled=false` 而 `healthy=true`：机器好的、只是我不想让它接流量（发版中）
- `healthy=false` 而 `enabled=true`：机器可能炸了（等心跳超时/探活失败）
- 调用方**只路由到 `healthy=true && enabled=true`** 的实例

> 这个区分很重要：**「下线」不等于「不健康」，「不健康」也不是「被下线」**。运维事故里很多是「用错了开关」——想让流量走开却把机器标记成不健康，导致依赖它的监控/自动伸缩策略误判。

---

## 九、Nacos 是「无状态」的吗？——它挂了业务还能跑吗

标准答案（也是课程强调的架构原则）：

**注册中心必须是「最终一致 + 客户端本地缓存」的设计，因为它是系统里最不该成为单点的地方。**

- 各服务启动时注册并**把实例列表缓存到本地内存**
- 调用时默认**读本地缓存**，不是每次去问 Nacos
- Nacos 自己用 **Raft（CP）/ Distro（AP）** 两种一致性协议：临时实例走 **Distro（AP）**，优先可用；持久实例走 **Raft（CP）**，优先一致

所以：**Nacos 短暂挂掉，已在运行的服务可以照常互相调用（缓存还在），但新实例注册不上、列表变更不传播。**

> 我实测的一个「间接证据」：把 `user-service` 的注册表改来改去，order-service 的调用始终没崩 —— 因为它工作的是本地缓存，而不是每次 echo 都直连 Nacos。真要把 Nacos 停掉再调，还能调通（因为没有新实例变更的需求）；但一旦有新实例上线就发现不了。

---

## 十、踩坑清单（本次实测真实踩到的）

1. **🔴 服务类型不能混用**：同一服务下先注册过持久实例，临时实例的 Spring Boot 应用会**启动失败**（`can't register ephemeral instance`），报错看起来完全不像配置问题。→ 删干净再启。
2. **🔴 命名空间不匹配 = 「查不到」**：配置/实例都可能是「写了但读写在不同 namespace」，不是丢失。读取时注意 `tenant` 参数。
3. **`spring-cloud-starter-loadbalancer` 必须显式引**：Spring Cloud 2020 起 Ribbon 被移除，只引 `openfeign` 会在运行/启动时报「没有 LoadBalancer」类错误。
4. **Feign 日志要两处齐开**：只配 `logger-level` 不加包级别 debug，什么都看不到。
5. **注册上去的 IP 是宿主内网 IP**，多网卡/容器环境常取错，需要显式指定 `discovery.ip`。
6. **权重/enabled 变更不是秒级生效**：客户端有刷新周期，灰度操作要预留等待窗口。
7. **持久实例的健康状态客户端改不了**（`health check is still working`），由服务端探活决定。
8. **端口被占的坑**：本机 8082/8083 被别的项目（pm2 前端演示）占着，Spring Boot 直接 `Port already in use` 启动失败——**换端口前先 `ss -ltnp` 看**，别靠猜。
9. **Nacos 2.x 客户端的 gRPC 端口 9848 必须一起映射**（`-p 8848:8848 -p 9848:9848`），只映 8848 时老 SDK 能连、新 SDK 注册失败。
10. **standalone 模式用内嵌 Derby**，重启/扩节点会丢数据，生产必须接 MySQL。

---

## 十一、和前后知识的连线

- **和 Docker（模块二）**：这节课的 Nacos 就是用 Docker 起的容器。Docker 笔记里那条「**自定义网络里容器名即 DNS = 最朴素的服务发现**」——Nacos 就是这句话的**工业级版本**：容器名 DNS 只能表达「谁在哪」，Nacos 还表达了「谁活着、谁该接多少流量、变更了通知谁」。
- **和 Redis / MP 的横切思想**：MyBatis-Plus 把「分页/逻辑删除」抽成拦截器，Nacos 把「地址与健康」抽成注册中心，Sentinel（后面）会把「限流/熔断」抽成切面 —— **都是把横切关注点从业务代码里剥出来**，这是微服务整个技术栈的一条主线。
- **和 AI 侧的知识**：Nacos 的 `Namespace/Group/Service/Instance` 分层，和 LangGraph 的 `namespace/key` 长期记忆、hello-agents 的 ContextBuilder 「分区结构」是同一个思路：**先分区，再在分区内检索**。分区决定了「你看得见什么」，比检索算法本身更早决定结果。

---

## 十二、速查表

```bash
# 启 Nacos（学习用 standalone）
docker run -d --name nacos-standalone -e MODE=standalone -e NACOS_AUTH_ENABLE=false \
  -p 8848:8848 -p 9848:9848 nacos/nacos-server:v2.3.2

# 就绪
curl http://127.0.0.1:8848/nacos/v1/console/health/readiness     # OK

# 服务列表 / 实例列表 / 服务清单
curl "http://127.0.0.1:8848/nacos/v1/ns/service/list?pageNo=1&pageSize=20"
curl "http://127.0.0.1:8848/nacos/v1/ns/instance/list?serviceName=user-service"

# 手工注册（临时实例）
curl -X POST "http://127.0.0.1:8848/nacos/v1/ns/instance?serviceName=user-service&ip=1.2.3.4&port=8081&ephemeral=true"
# 下线（保留记录）/ 恢复
curl -X PUT  "http://127.0.0.1:8848/nacos/v1/ns/instance?serviceName=user-service&ip=1.2.3.4&port=8081&enabled=false&ephemeral=true"
# 删除实例 / 删除服务
curl -X DELETE "http://127.0.0.1:8848/nacos/v1/ns/instance?serviceName=user-service&ip=1.2.3.4&port=8081&ephemeral=true"
curl -X DELETE "http://127.0.0.1:8848/nacos/v1/ns/service?serviceName=order-service"

# 配置发布 / 读取 / 历史版本
curl -X POST "http://127.0.0.1:8848/nacos/v1/cs/configs" -d "dataId=a.yaml" -d "group=DEFAULT_GROUP" -d "content=k: v"
curl "http://127.0.0.1:8848/nacos/v1/cs/configs?dataId=a.yaml&group=DEFAULT_GROUP&tenant="
curl "http://127.0.0.1:8848/nacos/v1/cs/history?search=accurate&dataId=a.yaml&group=DEFAULT_GROUP&pageNo=1&pageSize=10"
```

Feign 三件套：`@EnableFeignClients` → `@FeignClient(name="服务名")` → 注入即用。
**记一句：Feign 的接口里永远不出现 IP 和端口，出现了就说明退化成 RestTemplate 了。**

---

## 附：实验素材

```
~/nacos_lab/
├── cloud-demo/                    # 父 POM（Boot 3.2.5 + Cloud 2023.0.1 + Alibaba 2023.0.1.0）
│   ├── user-service/              # /user/{id}，带 app.tag 区分实例
│   └── order-service/             # /order/{id} 经 Feign 调 user-service
└── （Nacos 容器 nacos-standalone，8848/9848）
```

启动：

```bash
java -jar user-service/target/*.jar  --server.port=8081 --app.tag=node-A
java -jar user-service/target/*.jar  --server.port=18081 --app.tag=node-B
java -jar order-service/target/*.jar --server.port=18080
curl http://127.0.0.1:18080/order/1     # → order#1 -> user#1 ... tag=node-A/B
```
