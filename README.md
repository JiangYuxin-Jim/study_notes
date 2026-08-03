# 学习笔记

> 📚 基于黑马程序员课程，按知识板块整理的学习笔记。
> 内容使用 AI 辅助生成和润色。

---

## 📂 目录

### Java SE

| 序号 | 内容 | 完成时间 |
|------|------|----------|
| [01 - Java 初入门](./JavaSE/01-Java初入门.md) | JDK/JRE/JVM、环境搭建、HelloWorld、注释、关键字与标识符 | 2026-07-09 |
| [02 - 变量与运算符](./JavaSE/02-变量与运算符.md) | 8 种基本类型、类型转换、算术/比较/逻辑/三元运算符、Scanner | 2026-07-09 |
| [03 - 流程控制语句](./JavaSE/03-流程控制语句.md) | if/switch、for/while/do-while、break/continue | 2026-07-09 |
| [04 - 数组](./JavaSE/04-数组.md) | 数组初始化、遍历、常见操作、冒泡排序、二维数组 | 2026-07-09 |
| [05 - 方法](./JavaSE/05-方法.md) | 方法定义/调用、重载、参数传递（值传递）、递归 | 2026-07-09 |
| [06 - Java 运行原理](./JavaSE/06-Java运行原理.md) | 编译与运行、JVM 内存模型、类加载（双亲委派）、GC 简介 | 2026-07-09 |
| [07 - 面向对象编程](./JavaSE/07-面向对象编程.md) | 类与对象、封装、this、构造方法、标准 JavaBean、ArrayList、学生管理系统 | 2026-07-16 |
| [08 - 字符串(String)](./JavaSE/08-字符串(String).md) | String 创建/比较/API、不可变性、StringBuilder、StringJoiner | 2026-07-16 |
| [09 - 常用 API](./JavaSE/09-常用API.md) | Math/System/Runtime/Object、BigInteger/BigDecimal | 2026-07-16 |
| [10 - 对象克隆与深浅拷贝](./JavaSE/10-对象克隆与深浅拷贝.md) | Object.clone()、Cloneable、浅拷贝/深拷贝、序列化深拷贝 | 2026-07-19 |
| [11 - 正则表达式](./JavaSE/11-正则表达式.md) | 正则规则、Pattern/Matcher、分组、爬虫匹配 | 2026-07-19 |
| [12 - 时间日期类](./JavaSE/12-时间日期类.md) | Date/Calendar、SimpleDateFormat、JDK8 新日期 API(LocalDate/LocalDateTime) | 2026-07-19 |
| [13 - 泛型与集合框架(List)](./JavaSE/13-泛型与集合框架(List).md) | 泛型(类/方法/接口/通配符/擦除)、数据结构(栈/队列/数组/链表)、ArrayList源码、LinkedList源码、迭代器 | 2026-07-21 |
| [14 - 集合进阶（一）](./JavaSE/14-集合进阶（一）.md) | Collection/List 体系、ArrayList/LinkedList 源码、泛型、三种遍历方式 | 2026-07-20 |
| [15 - 集合进阶（二）](./JavaSE/15-集合进阶（二）-数据结构与Set集合.md) | 数据结构(二叉树/平衡二叉树/红黑树)、HashSet/LinkedHashSet/TreeSet | 2026-07-22 |
| [16 - Map 集合体系](./JavaSE/16-Map集合体系.md) | Map API、三种遍历方式、HashMap/TreeMap/LinkedHashMap 源码解析 | 2026-07-23 |
| [17 - 集合工具类与综合练习](./JavaSE/17-集合工具类与综合练习.md) | 可变参数、Collections、随机点名器、加权随机算法、集合嵌套 | 2026-07-24 |
| [18 - 斗地主阶段项目](./JavaSE/18-斗地主阶段项目.md) | 生成牌、洗牌、发牌、排序、面向对象设计 (Poker/Player)、游戏完善 | 2026-07-24 |
| [19 - 不可变集合与 Stream 流基础](./JavaSE/19-不可变集合与Stream流基础.md) | 不可变集合 (of/copyOf)、Stream 流概述、四种获取方式、流水线模式 | 2026-07-24 |
| [20 - Stream 流进阶与方法引用](./JavaSE/20-Stream流与方法引用.md) | Stream 流中间/终结操作、collect 收集方法、方法引用 6 种形式 | 2026-07-25 |
| [21 - 异常体系](./JavaSE/21-异常体系.md) | 异常体系、编译时/运行时异常、try-catch、throws、自定义异常 | 2026-07-26 |
| [22 - File 类](./JavaSE/22-File类.md) | File 构造/判断/获取/创建/删除/遍历、递归遍历、文件过滤器 | 2026-07-26 |
| [23 - IO 流基础（字节流与字符流）](./JavaSE/23-IO流基础（字节流与字符流）.md) | 字节流/字符流、文件拷贝、read() vs read(byte[])、编码解码 | 2026-07-26 |
| [24 - IO 流进阶（整合篇）](./JavaSE/24-IO流进阶（缓冲流·转换流·序列化流）.md) | 缓冲流原理、readLine()、转换流解决乱码、序列化/transient/serialVersionUID、FileWriter 底层缓冲区 | 2026-07-26 |
| [25 - IO 流进阶（一）· 缓冲流概述与字节缓冲流](./JavaSE/25-IO流进阶（一）-缓冲流概述与字节缓冲流.md) | 缓冲流四大金刚、内部缓冲区原理、性能对比、flush 机制 | 2026-07-27 |
| [26 - IO 流进阶（二）· 字符缓冲流](./JavaSE/26-IO流进阶（二）-字符缓冲流.md) | BufferedReader(readLine) / BufferedWriter(newLine)、按行读写、排序练习 | 2026-07-27 |
| [27 - IO 流进阶（三）· 转换流与序列化流](./JavaSE/27-IO流进阶（三）-转换流与序列化流.md) | InputStreamReader/OutputStreamWriter、ObjectInputStream/ObjectOutputStream、Serializable、serialVersionUID、transient | 2026-07-27 |
| [28 - IO 流进阶（四）· 打印流与 Commons-IO](./JavaSE/28-IO流进阶（四）-打印流与Commons-IO.md) | PrintStream/PrintWriter、System.out、自动刷新、Commons-IO(FileUtils/IOUtils)、压缩流 | 2026-07-27 |
| [29 - IO 流进阶（五）· Properties 与压缩流](./JavaSE/29-IO流进阶（五）-Properties与压缩流.md) | Properties 配置文件读写、ZipOutputStream/ZipInputStream 压缩解压、IO 流全体系总结 | 2026-07-28 |
| [30 - 多线程基础](./JavaSE/30-多线程基础（创建与线程安全）.md) | 三种创建方式（Thread/Runnable/Callable）、线程安全、synchronized/Lock、死锁、等待唤醒、volatile、Atomic | 2026-07-28 |
| [31 - 多线程进阶](./JavaSE/31-多线程进阶（并发工具与线程池）.md) | 线程池（Executor/ThreadPoolExecutor）、CountDownLatch、CyclicBarrier、Semaphore、阻塞队列、并发集合、ForkJoin | 2026-07-28 |
| [32 - 网络编程](./JavaSE/32-网络编程（UDP-TCP）.md) | UDP（DatagramSocket）、TCP（Socket/ServerSocket）、三次握手/四次挥手、BS 架构 | 2026-07-30 |
| [33 - 反射（Reflection）](./JavaSE/33-反射（Reflection）.md) | Class 对象获取、构造器/字段/方法反射、暴力反射、框架应用 | 2026-07-30 |
| [34 - 动态代理（Proxy）](./JavaSE/34-动态代理（Proxy）.md) | JDK 动态代理（Proxy + InvocationHandler）、AOP 底层、Spring 应用场景 | 2026-07-30 |

### JavaWeb

| 序号 | 内容 | 完成时间 |
|------|------|----------|
| [01 - 前端基础(HTML+CSS)](./javaweb/01-前端基础(HTML+CSS).md) | HTML 常用标签、CSS 选择器、盒子模型、Flexbox 布局 | 2026-07-09 |
| [02 - 前端基础(JS+Vue+Ajax)](./javaweb/02-前端基础(JS+Vue+Ajax).md) | JS 核心语法、DOM 操作、Vue 指令、Axios 异步请求 | 2026-07-09 |
| [03 - Maven 基础与高级](./javaweb/03-Maven基础与高级.md) | 坐标/依赖/生命周期、JUnit、分模块、继承/聚合、私服 | 2026-07-09 |
| [04 - SpringBoot 入门与 HTTP 协议](./javaweb/04-SpringBoot入门与HTTP协议.md) | SpringBoot 初体验、HTTP 请求/响应、三层架构、IOC/DI | 2026-07-09 |
| [05 - MySQL 数据库与多表查询](./javaweb/05-MySQL数据库与多表查询.md) | DDL/DML/DQL、多表关系、内连接/外连接、子查询 | 2026-07-09 |
| [06 - JDBC 与 MyBatis](./javaweb/06-JDBC与MyBatis.md) | JDBC 流程、MyBatis 注解/XML、动态 SQL、多环境配置 | 2026-07-09 |
| [07 - 部门管理 CRUD 实战](./javaweb/07-部门管理CRUD实战.md) | 前后端分离、统一响应格式、日志技术(Logback) | 2026-07-09 |
| [08 - 员工管理实战(上)](./javaweb/08-员工管理实战(上).md) | 新增员工、事务管理(ACID/@Transactional)、文件上传(OSS) | 2026-07-09 |
| [09 - 员工管理实战(下)](./javaweb/09-员工管理实战(下).md) | 分页查询(PageHelper)、批量删除、修改回显、全局异常处理 | 2026-07-09 |
| [10 - 登录认证与 JWT](./javaweb/10-登录认证与JWT.md) | Cookie/Session 演进、JWT 令牌、Filter/Interceptor、ThreadLocal | 2026-07-09 |
| [11 - AOP 面向切面编程](./javaweb/11-AOP面向切面编程.md) | AOP 概念、通知类型、切入点表达式、操作日志案例 | 2026-07-09 |
| [12 - SpringBoot 原理](./javaweb/12-SpringBoot原理.md) | 自动配置、@Conditional、Starter 起步依赖、启动流程 | 2026-07-09 |
| [13 - Vue 工程化与 ElementPlus](./javaweb/13-Vue工程化与ElementPlus.md) | Vite 工程、.vue 组件、Vue Router、Element Plus 常用组件 | 2026-07-09 |
| [14 - 前端 Tlias 案例实战](./javaweb/14-前端Tlias案例实战.md) | 部门/员工 CRUD 页面、登录页、路由守卫、前后端联调 | 2026-07-09 |
| [15 - 项目部署(Linux+Docker)](./javaweb/15-项目部署(Linux+Docker).md) | Linux 常用命令、Jar 包部署、Nginx 代理、Docker/Docker Compose | 2026-07-09 |

### Redis 缓存

| 序号 | 内容 | 完成时间 |
|------|------|----------|
| [01 - 认识 Redis](./redis/01-认识Redis.md) | Redis 介绍、数据类型、常用命令 | 2026-07-05 |
| [02 - 缓存穿透/雪崩/击穿](./redis/02-缓存穿透雪崩击穿.md) | 三大缓存问题及解决方案 | 2026-07-05 |
| [03 - 优惠券秒杀](./redis/03-优惠券秒杀.md) | 全局唯一ID、RedisIdWorker、超卖问题、乐观锁/悲观锁、一人一单 | 2026-07-07 |
| [04 - 分布式锁](./redis/04-分布式锁.md) | SETNX 演进路线、UUID + Lua 原子解锁、Redisson（WatchDog/可重入/RedLock） | 2026-07-07 |
| [05 - 秒杀优化与消息队列](./redis/05-秒杀优化与消息队列.md) | Lua 脚本前置判断、异步下单、Redis 消息队列（List/PubSub/Stream）、消费者组 | 2026-07-08 |
| [06 - 达人探店](./redis/06-达人探店.md) | 发布探店笔记、图片上传、点赞/取消点赞、SortedSet 点赞排行榜 | 2026-07-09 |
| [07 - 短信登录](./redis/07-短信登录.md) | 短信验证码、Token 机制、Redis 替代 Session、ThreadLocal、双重拦截器 | 2026-07-29 |
| [08 - 好友关注](./redis/08-好友关注.md) | 共同关注（Set 交集）、Feed 流推送（SortedSet）、滚动分页 | 2026-07-30 |
| [09 - 附近商铺](./redis/09-附近商铺.md) | GEO 空间索引、按距离排序、GEOSEARCH 实现 LBS | 2026-07-30 |
| [10 - 用户签到](./redis/10-用户签到.md) | BitMap 位图签到、BITFIELD 批量读取、连续签到位运算 | 2026-07-30 |
| [11 - UV 统计](./redis/11-UV统计.md) | HyperLogLog 概率算法、12KB 固定内存、PFADD/PFCOUNT/PFMERGE | 2026-07-30 |
| [12 - 持久化（RDB 与 AOF）](./redis/12-持久化(RDB与AOF).md) | RDB 快照、AOF 追加日志、刷盘策略、AOF 重写、RDB/AOF 对比 | 2026-08-02 |
| [13 - 主从复制](./redis/13-主从复制.md) | 一主多从、读写分离、全量/增量同步、replid 与 offset | 2026-08-02 |
| [14 - 哨兵与分片集群](./redis/14-哨兵与分片集群.md) | 哨兵高可用、自动故障转移、Cluster 槽位分片、MOVED/ASK、多级缓存 | 2026-08-03 |

---

## 📊 学习历程时间线

> 从上到下按时间排列，每天学什么一目了然。

<img alt="学习历程时间线" src="./images/learning-timeline.svg" width="100%">

---

## 📌 学习进度

- ✅ JavaSE（完整 34 篇笔记）— 全部完结 🎉（补写网络编程·反射·动态代理）
- ✅ JavaWeb（15 篇笔记）— 已完成
- 🔄 Redis（基础 + 实战 + 高级篇进行中）— 实战篇已完结，高级篇从持久化·主从复制·哨兵·分片集群（11+3 篇）
- ⏳ 下一阶段：SpringCloud 微服务（紧跟高级篇之后） 🎯
