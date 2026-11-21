# 微服务技术栈

> 📚 课程：[黑马程序员 2026 微服务技术栈（BV1S142197x7）](https://www.bilibili.com/video/BV1S142197x7)
> 定位：Java 工程落地主线。AI 板块用 Python 学原理，这里用 Java/Spring 做生产级实现。

---

## 模块进度

| 模块 | 集数 | 状态 |
|------|------|------|
| MyBatis-Plus | 20 | ✅ 完成（01 总览 + 02 Wrapper 精讲） |
| Docker | 14 | ✅ 完成（03 基础与实战） |
| 微服务（服务拆分/网关/Nacos/OpenFeign） | ~40 | ⏳ 未开始 |
| 服务保护（Sentinel/雪崩/Seata） | ~25 | ⏳ 未开始 |
| 消息队列（RabbitMQ） | ~30 | ⏳ 未开始 |
| Elasticsearch | ~25 | ⏳ 未开始 |
| 面试篇 | ~17 | ⏳ 未开始 |

---

## 笔记目录

| 序号 | 内容 | 完成时间 |
|------|------|----------|
| [01 - MyBatis-Plus](./01-MyBatisPlus.md) | MP 是 MyBatis 增强非替代、BaseMapper 17 方法、IService 体系、Wrapper 条件构造器（Lambda 首选·`or` 必配 `and` 包裹）、常用注解与主键策略（雪花算法）、`@TableLogic` 逻辑删除、MetaObjectHandler 自动填充、`@Version` 乐观锁、分页拦截器与拦截链、代码生成器、选型与 12 条踩坑 | 2026-11-17 |
| [02 - LambdaQueryWrapper 与 LambdaUpdateWrapper](./02-LambdaQuery与LambdaUpdate.md) | 二者继承自 `AbstractWrapper` 故条件能力完全一致（Update 只是多 `set` 系列）；`SerializedLambda` 把 `User::getAge` 反射成列名（**必须有 getter**）；**每个条件方法都有 `boolean condition` 首参** = 动态 SQL 的唯一正确姿势；`or()` 破坏优先级必须 `and/or/nested(Consumer)` 包括号（`nested` 不带连接词·`not` 取反）；`set`/`setSql`/**3.5.x 新增 `setIncrBy`/`setDecrBy`** 原子自增；`update(null, uw)` 与 `update(entity, uw)` 的 SET 合并语义；`BlockAttackInnerInterceptor` 防无 WHERE 全表（在 `mybatis-plus-jsqlparser` 包里）；`IService.lambdaQuery()/lambdaUpdate()` 链式终结方法 vs Wrapper 可复用；12 条踩坑（空 `in` 集合·wrapper 复用状态错位·`likeRight` 能走索引·幂等 CAS 写法） | 2026-11-18 |
| [03 - Docker 基础与实战](./03-Docker.md) | **Docker = 镜像(类) / 容器(对象) / 仓库(中央仓库) 一物三态**，不是 VM（共享内核·7.8MB vs GB 级）；镜像**只读分层 + CoW**（`docker history` 实测 RUN/COPY/ADD 生成真实层、ENV/WORKDIR/CMD 只是元数据层）；**`CMD` 会被 `run` 后参数整条替换**（实测报 `exec: "a": not found`）→ 传参必须 `ENTRYPOINT`；分层缓存「某层变则其下全失效」→ 越稳定越靠前、多阶段构建砍体积；**数据卷三选**（bind/volume/tmpfs）——**容器删了可写层就没了**，数据库一律挂卷；**🔴 UID 权限坑实测**：容器内 UID = 宿主 UID（无 userns-remap），root 容器写出的文件属主是 root → 后续非 root 读写 Permission denied；网络四模式 + `-p 宿主:容器` + 自定义网络**容器名即 DNS**（服务发现原型）；Compose 声明式编排（`depends_on` 只保证启动顺序不等于就绪）；**国内镜像源实测**（老 registry-mirrors 全废、`dockerproxy.net` 可用）；**排障实录：下载插件「退出码 0 但文件是假的」**；12 条踩坑 + 速查表 | 2026-11-21 |

---

## 学习笔记说明

- 单表 CRUD 用 MP（Wrapper），多表 JOIN 用 XML，两者同一个 Mapper 共存
- 所有增强（分页 / 逻辑删除 / 乐观锁 / 多租户 / 字段填充）本质上都是 **MyBatis 拦截器 + 注解**
- 这个「横切逻辑统一插桩」的思路，和 Redis 的多级缓存、后面的网关/Sentinel 是同一个套路
- Docker 是**微服务的地基不是微服务本身**：后面 Nacos/Sentinel/RabbitMQ/ES 全都以容器方式起，学它是为了统一环境，不是学架构
- 容器化的三个正交视角：**Namespace 管「看到什么」 · Cgroups 管「能用多少」 · UnionFS 管「文件从哪来」**
