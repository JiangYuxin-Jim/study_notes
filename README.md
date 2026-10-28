# 学习笔记

> 📚 基于黑马程序员课程，按知识板块整理的学习笔记。
> 内容使用 AI 辅助生成和润色。

---

## 📂 目录

### Java SE

| 序号 | 内容 | 完成时间 |
|------|------|----------|
| [01 - Java初入门](./JavaSE/01-Java初入门.md) | JDK/JRE/JVM、环境搭建、HelloWorld、注释、关键字与标识符 | 2026-07-09 |
| [02 - 变量与运算符](./JavaSE/02-变量与运算符.md) | 8 种基本类型、类型转换、算术/比较/逻辑/三元运算符、Scanner | 2026-07-09 |
| [03 - 流程控制语句](./JavaSE/03-流程控制语句.md) | if/switch、for/while/do-while、break/continue | 2026-07-09 |
| [04 - 数组](./JavaSE/04-数组.md) | 数组初始化、遍历、常见操作、冒泡排序、二维数组 | 2026-07-09 |
| [05 - 方法](./JavaSE/05-方法.md) | 方法定义/调用、重载、参数传递（值传递）、递归 | 2026-07-09 |
| [06 - Java运行原理](./JavaSE/06-Java运行原理.md) | 编译与运行、JVM 内存模型、类加载（双亲委派）、GC 简介 | 2026-07-09 |
| [07 - 面向对象编程](./JavaSE/07-面向对象编程.md) | 类与对象、封装、this、构造方法、标准 JavaBean、ArrayList、学生管理系统 | 2026-07-16 |
| [08 - 继承（Inheritance）](./JavaSE/08-继承（Inheritance）.md) | extends、super、方法重写 vs 重载、构造流程、final、Object、抽象类、继承 vs 组合 | 2026-08-04 |
| [09 - 字符串(String)](./JavaSE/09-字符串(String).md) | String 创建/比较/API、不可变性、StringBuilder、StringJoiner | 2026-07-16 |
| [10 - 常用API](./JavaSE/10-常用API.md) | Math/System/Runtime/Object、BigInteger/BigDecimal | 2026-07-16 |
| [11 - 对象克隆与深浅拷贝](./JavaSE/11-对象克隆与深浅拷贝.md) | Object.clone()、Cloneable、浅拷贝/深拷贝、序列化深拷贝 | 2026-07-19 |
| [12 - 正则表达式](./JavaSE/12-正则表达式.md) | 正则规则、Pattern/Matcher、分组、爬虫匹配 | 2026-07-19 |
| [13 - 时间日期类](./JavaSE/13-时间日期类.md) | Date/Calendar、SimpleDateFormat、JDK8 新日期 API(LocalDate/LocalDateTime) | 2026-07-19 |
| [14 - Arrays与Lambda表达式](./JavaSE/14-Arrays与Lambda表达式.md) | Arrays 工具类、Lambda 表达式、Comparator 排序 | 2026-07-21 |
| [14 - 泛型与集合框架(List)](./JavaSE/14-泛型与集合框架(List).md) | 泛型(类/方法/接口/通配符/擦除)、数据结构(栈/队列/数组/链表)、ArrayList源码、LinkedList源码、迭代器 | 2026-07-21 |
| [15 - 集合进阶（一）](./JavaSE/15-集合进阶（一）.md) | Collection/List 体系、ArrayList/LinkedList 源码、泛型、三种遍历方式 | 2026-07-20 |
| [16 - 集合进阶（二）-数据结构与Set集合](./JavaSE/16-集合进阶（二）-数据结构与Set集合.md) | 数据结构(二叉树/平衡二叉树/红黑树)、HashSet/LinkedHashSet/TreeSet | 2026-07-22 |
| [17 - Map集合体系](./JavaSE/17-Map集合体系.md) | Map API、三种遍历方式、HashMap/TreeMap/LinkedHashMap 源码解析 | 2026-07-23 |
| [18 - 集合工具类与综合练习](./JavaSE/18-集合工具类与综合练习.md) | 可变参数、Collections、随机点名器、加权随机算法、集合嵌套 | 2026-07-24 |
| [19 - 斗地主阶段项目](./JavaSE/19-斗地主阶段项目.md) | 生成牌、洗牌、发牌、排序、面向对象设计 (Poker/Player)、游戏完善 | 2026-07-24 |
| [20 - 不可变集合与Stream流基础](./JavaSE/20-不可变集合与Stream流基础.md) | 不可变集合 (of/copyOf)、Stream 流概述、四种获取方式、流水线模式 | 2026-07-24 |
| [21 - Stream流与方法引用](./JavaSE/21-Stream流与方法引用.md) | Stream 流中间/终结操作、collect 收集方法、方法引用 6 种形式 | 2026-07-25 |
| [22 - 异常体系](./JavaSE/22-异常体系.md) | 异常体系、编译时/运行时异常、try-catch、throws、自定义异常 | 2026-07-26 |
| [23 - File类](./JavaSE/23-File类.md) | File 构造/判断/获取/创建/删除/遍历、递归遍历、文件过滤器 | 2026-07-26 |
| [24 - IO流基础（字节流与字符流）](./JavaSE/24-IO流基础（字节流与字符流）.md) | 字节流/字符流、文件拷贝、read() vs read(byte[])、编码解码 | 2026-07-26 |
| [25 - IO流进阶（缓冲流·转换流·序列化流）](./JavaSE/25-IO流进阶（缓冲流·转换流·序列化流）.md) | 缓冲流原理、readLine()、转换流解决乱码、序列化/transient/serialVersionUID、FileWriter 底层缓冲区 | 2026-07-26 |
| [26 - IO流进阶（一）-缓冲流概述与字节缓冲流](./JavaSE/26-IO流进阶（一）-缓冲流概述与字节缓冲流.md) | 缓冲流四大金刚、内部缓冲区原理、性能对比、flush 机制 | 2026-07-27 |
| [27 - IO流进阶（二）-字符缓冲流](./JavaSE/27-IO流进阶（二）-字符缓冲流.md) | BufferedReader(readLine) / BufferedWriter(newLine)、按行读写、排序练习 | 2026-07-27 |
| [28 - IO流进阶（三）-转换流与序列化流](./JavaSE/28-IO流进阶（三）-转换流与序列化流.md) | InputStreamReader/OutputStreamWriter、ObjectInputStream/ObjectOutputStream、Serializable、serialVersionUID、transient | 2026-07-27 |
| [29 - IO流进阶（四）-打印流与Commons-IO](./JavaSE/29-IO流进阶（四）-打印流与Commons-IO.md) | PrintStream/PrintWriter、System.out、自动刷新、Commons-IO(FileUtils/IOUtils)、压缩流 | 2026-07-27 |
| [30 - IO流进阶（五）-Properties与压缩流](./JavaSE/30-IO流进阶（五）-Properties与压缩流.md) | Properties 配置文件读写、ZipOutputStream/ZipInputStream 压缩解压、IO 流全体系总结 | 2026-07-28 |
| [31 - 多线程基础（创建与线程安全）](./JavaSE/31-多线程基础（创建与线程安全）.md) | 三种创建方式（Thread/Runnable/Callable）、线程安全、synchronized/Lock、死锁、等待唤醒、volatile、Atomic | 2026-07-28 |
| [32 - 多线程进阶（并发工具与线程池）](./JavaSE/32-多线程进阶（并发工具与线程池）.md) | 线程池（Executor/ThreadPoolExecutor）、CountDownLatch、CyclicBarrier、Semaphore、阻塞队列、并发集合、ForkJoin | 2026-07-28 |
| [33 - 网络编程（UDP-TCP）](./JavaSE/33-网络编程（UDP-TCP）.md) | UDP（DatagramSocket）、TCP（Socket/ServerSocket）、三次握手/四次挥手、BS 架构 | 2026-07-30 |
| [34 - 反射（Reflection）](./JavaSE/34-反射（Reflection）.md) | Class 对象获取、构造器/字段/方法反射、暴力反射、框架应用 | 2026-07-30 |
| [35 - 动态代理（Proxy）](./JavaSE/35-动态代理（Proxy）.md) | JDK 动态代理（Proxy + InvocationHandler）、AOP 底层、Spring 应用场景 | 2026-07-30 |
| [36 - JUC 并发编程三大特性（原子性·可见性·有序性）](./JavaSE/36-JUC并发编程三大特性（原子性·可见性·有序性）.md) | JMM 内存模型、原子性（count++ 非原子/CAS）、可见性（死循环案例）、有序性（指令重排·DCL 半初始化对象）、volatile 三特性语义、happens-before 七大规则 | 2026-10-20 |
| [37 - 原子类与锁机制（CAS·锁升级·AQS入门）](./JavaSE/37-原子类与锁机制（CAS·锁升级·AQS入门）.md) | 原子类家族（AtomicIntegerArray/引用原子类/字段更新器）、LongAdder 分段 CAS、乐观锁 vs 悲观锁、CAS 三大问题（ABA/自旋/单变量）、自旋锁、wait 与 sleep、生产者消费者（wait-notifyAll · Condition 精准唤醒 · 阻塞队列）、synchronized 锁升级（偏向→轻量→重量·Mark Word·JDK15 废弃偏向锁）、可重入原理（AQS state）、ReentrantLock（tryLock/lockInterruptibly/公平锁/排他共享）、Synchronized vs Lock 选型、高并发锁优化最佳实践 | 2026-10-21 |
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
| [15 - 多级缓存](./redis/15-多级缓存.md) | Caffeine 进程缓存、Lua/OpenResty、Nginx 本地缓存、缓存预热、Canal 缓存同步 | 2026-08-04 |
| [16 - Redis 最佳实践](./redis/16-Redis最佳实践.md) | 键值设计、BigKey 问题与治理、数据结构选择 | 2026-08-04 |
| [18 - 最佳实践补充（批处理/服务端/集群）](./redis/18-最佳实践补充(批处理-服务端-集群).md) | Pipeline 批量、慢查询、安全配置、内存划分、集群 vs 主从 | 2026-08-05 |
| [17 - 原理篇·底层数据结构（SDS/intset/Dict/ZipList）](./redis/17-原理篇-底层数据结构(SDS-intset-Dict-ZipList).md) | SDS 动态字符串、IntSet 整数集合、Dict/rehash、ZipList 连锁更新 | 2026-08-05 |
| [19 - 原理篇·网络模型（IO多路复用/事件驱动）](./redis/19-原理篇-网络模型(IO多路复用与事件驱动).md) | 阻塞/非阻塞/多路复用、select/poll/epoll、事件驱动 Reactor、单线程、6.0 多线程 IO | 2026-08-06 |
| [20 - 原理篇·通信协议（RESP）](./redis/20-原理篇-通信协议(RESP).md) | RESP 五种类型、命令/返回编码、手写简易客户端、RESP3 | 2026-08-07 |
| [21 - 原理篇·内存回收](./redis/21-原理篇-内存回收.md) | 惰性/定期删除、maxmemory 淘汰策略、LRU vs LFU、手写 LRU | 2026-08-07 |

### AI 智能体与 RAG

> 详见板块说明：[ai/README.md](./ai/README.md) · 本地项目：`/home/admin/ai_projects/`

| 序号 | 内容 | 完成时间 |
|------|------|----------|
| [模块说明与学习路线](./ai/README.md) | hello-agents（Agent 16章）+ all-in-rag（RAG 9章），Python + Java 双修 | 2026-08-07 |
| [Transformer 实战 · 从零手搓 Transformer 英译中](./ai/transformer/01-从零手搓Transformer英译中实战.md) | **用 PyTorch 亲手写完整 Encoder-Decoder 做机器翻译**（源码仓库 [Transformer-pytorch](https://github.com/JiangYuxin-Jim/Transformer-pytorch)）：数据层（语料合并·对齐校验·中英各训 32k BPE·三种 mask 对照表·Teacher Forcing 错位一格）；模型层（Embedding×√d·PE sin/cos exp 技巧·Scaled Dot-Product 除以√d_k·MHA 形状变化·手写 LayerNorm·**Post-LN 为什么必须 warmup**·Encoder/Decoder 交叉注意力是唯一跨语言通道·Xavier 初始化）；训练（label-wise 交叉熵按 ntokens 归一·Noam warmup=10000 逆平方根衰减·**MultiGPULossCompute 分块过 Generator 只累加标量再拼梯度省显存**·**用 BLEU 不用 loss 选模型**）；推理（**Beam Search 手写全解**：`//` 与 `%` 反推来源 beam 与词 id·Encoder 只跑一次靠 repeat 扇出·**已完成句子提前退出**·回溯重建；训练/推理 mask 差异）；**BLEU 26.30** 结果解读与 paper 差异清单（未用 Label Smoothing·无长度惩罚·无 KV Cache）＋6 条真实踩坑 + 7 项改进方向 | 2026-10-28 |
| [hello-agents 01 · 初识智能体(理论基础)](./ai/hello-agents/01-初识智能体(理论基础).md) | Agent 定义、传统演进、LLM 新范式、分类维度、PEAS、Agent Loop、TAO | 2026-08-07 |
| [hello-agents 02 · 动手实现第一个智能体](./ai/hello-agents/02-动手实现第一个智能体与协作模式.md) | Python 旅行助手（提示词+工具+LLM客户端+主循环）、协作模式 | 2026-08-07 |
| [hello-agents 第二章 · 智能体发展史](./ai/hello-agents/02-智能体发展史.md) | 四代演进：符号主义(物理符号系统·接地难题) → 专家系统(知识获取瓶颈·知识外置) → 强化学习(策略/奖励/探索-利用·样本效率) → LLM 智能体(LLM+工具+循环+记忆)；ReAct/Reflexion/Plan-and-Solve 的范式祖先 | 2026-10-18 |
| [hello-agents 03 · 大语言模型基础](./ai/hello-agents/03-大语言模型基础.md) | N-gram→RNN/LSTM→Transformer→Decoder-Only、采样参数、提示工程、BPE 分词、本地部署 Qwen、模型选型、缩放法则与幻觉 | 2026-08-11 |
| [hello-agents 06 · 框架开发实践](./ai/hello-agents/06-框架开发实践.md) | AutoGen/AgentScope/CAMEL/LangGraph 四大框架：对话驱动·消息驱动/工程化·角色扮演·图式状态机，实战案例 + 选型分析 | 2026-08-13 |
| [hello-agents 07 · 构建你的Agent框架](./ai/hello-agents/07-构建你的Agent框架.md) | 自建框架理念(轻量+万物皆为工具)、HelloAgentsLLM多提供商/本地模型/自动检测、Message·Config·Agent抽象基类、五种范式实现(Simple/ReAct/Reflection/PlanAndSolve/FunctionCall)、统一工具系统 | 2026-08-14 |
| [hello-agents 08 · 记忆与检索](./ai/hello-agents/08-记忆与检索.md) | 四种记忆(工作/情景/语义/感知)+MemoryManager添加·检索·整合·遗忘、RAG"五层七步"架构+Markitdown统一转换+向量库检索增强、智能文档问答助手综合实战 | 2026-08-18 |
| [hello-agents 08 · 8.3.5 高级检索 MQE 与 HyDE](./ai/hello-agents/08-进阶检索-MQE与HyDE.md) | **查询侧改写两大技术**：词汇不匹配→MQE 多查询扩展(LLM 生成 N 个语义等价变体·并行检索·多视角召回)；问句/答句语义鸿沟→HyDE 假设文档嵌入("用答案找答案"·先编一段答案再检索·补术语密度)；统一扩展框架「扩展→检索→合并」三步；**候选池倍率 candidate_pool_multiplier=4**(去重会缩水，宁可多捞)·按 memory_id 去重保留最高分·扩展失败回退原 query·metadata 三层过滤隔离记忆与文档；策略选型(一般用MQE/专业领域同开/延迟敏感基础检索) | 2026-10-25 |
| [hello-agents 09 · 上下文工程](./ai/hello-agents/09-上下文工程.md) | 上下文工程 vs 提示工程、上下文腐蚀与注意力预算、上下文解剖学(系统提示分区·工具 MVTS·示例)、JIT 上下文与渐进式披露、长时程三件套(压缩整合/结构化笔记/子代理)、**ContextBuilder GSSC 流水线**(Gather 多源容错 → Select 相关性×新近性指数衰减+阈值过滤+贪心填充 → Structure 五分区模板 → Compress 分区截断兜底)、NoteTool·TerminalTool | 2026-10-19 |
| [hello-agents 09 · 补充：JIT 上下文与 GSSC 流水线](./ai/hello-agents/09-补充-JIT上下文与GSSC流水线.md) | **JIT 及时上下文**：不预加载数据只放轻量引用(路径/查询/URL)·元数据本身传语义(路径/大小/时间)·渐进式披露·混合策略(前置高价值+工具自主探索)；**GSSC 四步**：Gather 多源容错汇集→Select 先扣系统指令预算+相关性(Jaccard)×新近性(指数衰减[0.1,1])+阈值过滤+贪心填充(break非continue)→Structure 五分区→Compress 按分区截断保结构完整；参数调优表；**Transformer 架构**：Q/K/V+自注意力 softmax(QKᵀ/√d)·多头·位置编码·因果掩码 → **n² 注意力稀释 = 上下文腐蚀的物理根源** | 2026-10-26 |
| [Zotero 文献管理·基础使用](./ai/tools/zotero-基础使用.md) | 文献库/分类集/标签/附件/笔记、网页抓取·DOI导入、PDF阅读高亮、Word插件自动引用与参考文献、引文格式切换、同步备份 | 2026-08-29 |
| [Learn Claude Code · 前三章](./ai/tools/learn-claude-code-前三章.md) | Agent Loop（TAO 循环工程化·终止条件·上下文累加）、工具调用（name/description/schema + 提议→权限→执行→结果回灌）、三层权限隔离（工具白名单→参数级校验→人工确认） | 2026-09-17 |
| [Learn Claude Code · 第四章 钩子函数](./ai/tools/learn-claude-code-04-钩子函数.md) | Hooks 生命周期事件（Session/每轮/每工具调用）、三层配置结构（事件+matcher+handler）、5 种 handler、退出码 0/2 与 JSON 输出、权限接管（PreToolUse 四决策 allow/deny/ask/defer + PermissionRequest 写权限规则）、实战：拦截 rm / 自动 prettier 格式化 | 2026-09-18 |
| [Learn Claude Code · 第五章 TodoWrite](./ai/tools/learn-claude-code-05-todowrite.md) | 任务清单（元工具：只写自身状态不改外部世界，Permission=No）、Agent Loop 中的规划位、四态生命周期（pending/in_progress/completed/deleted）、建清单的四类场景、**提醒机制**（宿主注入系统消息：工具调用后 + 收工前两条触发线，与 Hook 同源；提醒成本计入工具可用性）、SDK 里的 tool_use 流（TaskCreate/TaskUpdate、ID 要靠 tool_result 回带、字段名防御式解析、activeForm vs subject）、模型可用性反直觉事实（新模型默认不提供，能力内化后撤工具省 context）、终端 Ctrl+T / 跨压缩存活 / CLAUDE_CODE_TASK_LIST_ID 跨会话共享 | 2026-09-20 |
| [Learn Claude Code · 第六章 Subagent 与 Skill 加载](./ai/tools/learn-claude-code-06-subagent与skill加载.md) | Subagent（隔离上下文窗口·只回摘要、内置 Explore/Plan/general-purpose、五级作用域、frontmatter 全字段、自动委派与 @提及、前台后台与 fork 模式、启动时加载什么、Resume）、Skill（描述常驻+正文按需、Reference vs Task、frontmatter、内容生命周期与压缩预算、allowed-tools 安全提醒、context: fork、Skill↔Subagent 双向组合）、上下文成本总表与选型 | 2026-09-21 |
| [Learn Claude Code · 第七章 上下文压缩](./ai/tools/learn-claude-code-07-上下文压缩.md) | 四级降级策略（从轻到重）：①工具调用结果压缩（超长直接截断只留前部）②消息数量压缩（超阈值如50条，保留头3条+尾47条、掐中间）③消息内容压缩（老工具结果→文件路径引用化，不够再压新结果）④LLM 摘要兜底（输入按前 1/4 + 后 3/4 裁剪）；核心直觉：头尾优先·能机械别调LLM·缓存降级为外存 | 2026-09-22 |
| [Learn Claude Code · 第八章 记忆系统](./ai/tools/learn-claude-code-08-记忆系统.md) | LLM 无状态→记忆纯属工程问题（上下文内 vs 上下文外）；四层记忆（工作/会话/长期文件/外部知识）；CLAUDE.md 显式长期记忆（常驻订阅制·按轮计费）；自动记忆=把上下文外化成文件；与第七章压缩互补（先落盘再压缩）；设计要点：写什么/何时写/何时读/冲突处理/成本意识 | 2026-10-04 |
| [LangChain · 三 结构化输出](./ai/tools/langchain-03-structured-output.md) | 目标：把自由文本收敛成可校验数据结构（抽取/分类/路由/API填充）；底层仍是 Function Calling——给模型一个「只有 schema 无实现」的虚拟工具，只取 `args`；首选 `with_structured_output(PydanticModel)` 进出皆强类型；Schema 设计（description 写具体·`Literal` 收窄分类·`Optional` 标可缺失·嵌套 ≤3 层）；备用 `bind_tools(tool_choice=...)` 自己解析；失败兜底：校验器+重试+收窄 schema+few-shot | 2026-10-08 |
| [LangChain · 四 Agent](./ai/tools/langchain-04-agents.md) | **Agent = LLM + 工具 + 循环**（区别于 Workflow：下一步由 LLM 自主决定）；ReAct（Thought-Action-Observation）原祖范式 → 现代 = 原生 Function Calling 版 ReAct；`create_agent`（1.x 取代 AgentExecutor，入出参 `{"messages":[...]}`）；内部是一张图：model node → 判断 tool_calls → tools node → 回灌 → 循环 → 终止（= 第二章手动回路的自动化版）；**Middleware** 钩子（上下文压缩/工具审批 HITL/动态工具集 ≈ Claude Code Hook·权限系统）；**checkpointer** 会话记忆（`thread_id` 隔离·生产换持久化后端）；HITL 敏感工具审批四决策 | 2026-10-08 |
| [LangChain · 五 中间件 Middleware](./ai/tools/langchain-05-middleware.md) | **Middleware = Agent 的 AOP**（把日志/压缩/审批/重试/限流/脱敏从 agent 本体剥成可插拔一层）；六大钩子：node-style（`before/after_agent`·`before/after_model`，顺序执行·改 state·可 `jump_to`）vs wrap-style（`wrap_model_call`·`wrap_tool_call`，包住调用·可控制调用 0/1/N 次·直接 `request.override()`）；装饰器 vs 类（类可声明 `state_schema`/`tools`/`transformers`）；state 更新差异（node 直接 return dict，wrap 要 `ExtendedModelResponse`+`Command`）；执行顺序 before 正序·after 逆序·wrap 嵌套；内置库全览（Retry/Fallback·Summarization·HITL·PII·CallLimit·TodoList·SubAgent·Filesystem·LLMToolSelector·ContextEditing）；实战四例：动态 prompt·动态模型·动态工具集·工具监控；**HITL 必须配 checkpointer** | 2026-10-10 |
| [LangChain · 二 工具调用 Tool Use](./ai/tools/langchain-02-tool-use.md) | `@tool` 装饰器（函数名/docstring/类型注解 = name·description·args_schema 三要素）与 `StructuredTool`（Pydantic 精控参数）；**模型只提议不执行**——`bind_tools()` 本质是把工具 JSON Schema 预绑定进每次请求，返回 AIMessage 带 `tool_calls`（可多个·含 id）；手动回路四步（invoke→执行→`ToolMessage(tool_call_id=...)` 回灌→再 invoke）；`create_agent` 封装决策-执行-回灌循环（入出参均为 messages）；工具集臃肿=吃掉上下文预算 → MVTS 最小可行工具集 | 2026-10-08 |
| [LangChain · 一 模型调用与消息体系](./ai/tools/langchain-01-模型调用与消息体系.md) | `init_chat_model()` 统一初始化（provider:model·模型代码解耦）；六种调用 invoke/ainvoke/stream/astream/batch/abatch（batch 更快但同步阻塞·异步需 abatch）；`model_kwargs` vs `extra_body`（模型字段 vs 厂商私有扩展如 DeepSeek thinking）；LangSmith 四大能力（tracing/monitoring/debug/evaluate）；AIMessage 特有 response_metadata·tool_calls（可多个）+ ToolMessage 的 tool_call_id 必须与 tool_calls[].id 配对 | 2026-10-06 |
| [LangGraph · 一 图基础与状态管理](./ai/tools/langgraph-01-图基础与状态管理.md) | **LangGraph = 有向图 + 共享 State**（状态机思维：循环·可控·可观测）；建图五步 State(TypedDict)+Node(返增量)+Edge(START/END/条件边)+compile+invoke；**Reducer 更新语义**（默认覆盖 · `Annotated[T,f]` 声明合并函数 · 消息一律 `add_messages` 按 id 更新）；条件边三要素与反思-修正循环 + `recursion_limit`(=super-step 数·默认10007)；stream_mode updates/values/messages/debug/custom；**checkpointer** super-step 快照 + thread_id 隔离（多轮记忆·线程隔离·get_state_history 时间旅行·HITL 前提·生产换 Postgres/Redis）；对照 `create_agent` 内部图与 Middleware 钩子（本机 langgraph 1.2.16 全部代码实测） | 2026-10-24 |
| [LangGraph · 二 进阶建图：defer·条件边·sequence·Router·Send](./ai/tools/langgraph-02-进阶建图-defer-条件边-sequence-router-send.md) | **五个建图能力实测**(langgraph 1.2.16)：`add_sequence` 批量连链(自动命名+连边·不能连已注册节点·**图构建即代码**·步骤可由配置驱动)；`add_conditional_edges` 三要素补全(`path_map` dict=list 分层业务语义与拓扑·返回 list=固定并行扇出·路由抛异常直接冒泡→必须 try+兜底出口+`Literal` 类型标注)；**Router=纯函数决策层**(执行层 node/决策层 router/结构层 edge 三层分离·纯函数才能重放与单测·对照 `Command(goto)` 隐式跳转)；**`Send` 动态并行扇出**(payload 就是该实例完整 state·worker 返回值经 reducer 汇回·map-reduce·与 MQE「扩展→并行检索→合并」同构)；**`defer=True`** 实测真相(仅同一 super-step 内推迟到末尾·线性链无效·中间节点无效·主链 END **不会**取消它·对照 Middleware `after_agent`)；`interrupt`+`Command(resume)` 三条铁律(必须 checkpointer·节点整段重放→**interrupt 前代码必须幂等**·resume 值需可序列化)；defer/interrupt/Command 三者对照表 + 9 条踩坑清单 | 2026-10-25 |
| [LangChain · 六 RAG 与文档加载](./ai/tools/langchain-06-rag与文档加载.md) | **RAG = 检索增强生成**：解决模型知识过时·幻觉·无私有数据三大短板；微调改「说话方式」vs RAG 改「手边材料」（便宜/快/易更新/可溯源）；两阶段——**离线索引**（加载→切分→向量化→入库）+ **在线检索生成**（检索→拼 Prompt→生成）；第一步 Load：一切资料统一为 `Document(page_content, metadata)`，metadata 管过滤/溯源/增量更新；Loader 家族（Text/PDF/Office/Web/CSV-JSON/代码/云盘 + `DirectoryLoader` 批量）；紧接 Split：`RecursiveCharacterTextSplitter` + chunk_size/overlap（中文补句末标点）；**铁律：索引与查询同一 embedding 模型**；检索可封装为 Tool 融入 Agent | 2026-10-11 |

---

## 📊 学习历程时间线

> 从上到下按时间排列，每天各板块学什么一目了然。

| 日期 | 🧩 JavaSE | 🖥️ JavaWeb | 🍃 Redis |
|------|-----------|------------|----------|
| 7/5 | — | — | 基础入门 |
| 7/6 | — | — | （休息） |
| 7/7 | — | — | 优惠券秒杀 · 分布式锁 |
| 7/8 | — | — | 秒杀优化 · 消息队列 |
| 7/9 | 入门六篇 | 全套 15 篇 | 达人探店 |
| 7/10–7/15 | 休息 6 天 | 休息 | 休息 |
| 7/16 | 面向对象 · String · 常用API | — | — |
| 7/17–7/18 | 休息 | 休息 | — |
| 7/19 | 克隆 · 正则 · 日期类 | — | — |
| 7/20 | 集合框架 · List · 泛型 | — | — |
| 7/21 | ArrayList/LinkedList 源码 | — | — |
| 7/22 | 数据结构 · Set 集合 | — | — |
| 7/23 | Map 集合 · HashMap/TreeMap 源码 | — | — |
| 7/24 | 集合综练 · 斗地主 · 不可变集合 · Stream | — | — |
| 7/25 | Stream 流进阶 · 方法引用 | — | — |
| 7/26 | 异常 · File · IO 流基础 · IO 流进阶 | — | — |
| 7/27 | IO 流进阶深化（P94→P110） | — | — |
| 7/28 | IO 流扫尾 · 多线程/JUC · 网络编程（P110→P168） | — | — |
| 7/29 | 完结 P168→P200（反射·动态代理） | — | 补写短信登录笔记 |
| 7/30 | 补写网络编程·反射·动态代理笔记 | — | 实战篇完结（好友关注·GEO·签到·UV统计） |
| 8/2 | — | — | 高级篇开始：持久化(RDB·AOF)·主从复制 |
| 8/3 | — | — | 高级篇：哨兵 · 分片集群 |
| 8/4 | 补写继承笔记（extends·super·重写·抽象类） | — | 多级缓存（Caffeine·OpenResty·Canal） · 最佳实践（键值/BigKey） |
| 8/5 | — | — | 原理篇开始：数据结构（SDS·intset·Dict·ZipList）P160；补充最佳实践（批处理/服务端/集群） |
| 8/6 | — | — | 原理篇：网络模型（IO多路复用 select/poll/epoll·事件驱动 Reactor·6.0 多线程IO） |
| 8/7 | — | — | 🎉 Redis 全课程完结！原理篇收尾：通信协议(RESP) · 内存回收（过期删除·淘汰策略·LRU） |
| 8/7 | — | — | 新主线开启：hello-agents（Agent）· all-in-rag（RAG），克隆仓库入学习；完成 hello-agents 第一章（初识智能体·动手实现旅行助手） |
| 8/11 | — | — | hello-agents 第三章 大语言模型基础（N-gram→RNN→Transformer→Decoder-Only、提示工程、分词 BPE、模型选型、缩放法则与幻觉） |
| 8/13 | — | — | hello-agents 第六章 框架开发实践（AutoGen·AgentScope·CAMEL·LangGraph 四大框架，核心实战 AgentScope 消息驱动/三国狼人杀、CAMEL 角色扮演/电子书、LangGraph 图式状态机/三步问答助手） |
| 8/14 | — | — | hello-agents 第七章 构建你的Agent框架（自建轻量框架理念/万物皆为工具、HelloAgentsLLM多提供商封装、Message·Config·Agent抽象基类、五种Agent范式·统一工具系统） |
| 10/20 | ✅ JUC 并发编程三大特性（JMM·原子性·可见性·有序性·指令重排·volatile·happens-before） | — | — |
| 10/21 | ✅ 原子类与锁机制（AtomicIntegerArray·引用原子类·LongAdder·CAS 三大问题·自旋锁·锁升级·ReentrantLock 全家桶·锁优化实践，P49~P67） | — | — |
| 8/18 | — | — | hello-agents 第八章 记忆与检索（四种记忆·MemoryManager、RAG五层七步架构·向量库检索增强、智能文档问答助手实战；补看 learn Claude Code） |
| 8/29 | — | — | Zotero 文献管理·基础使用（文献库/分类集/标签、网页抓取·DOI导入、PDF阅读高亮、Word插件自动引用·参考文献、引文格式切换、同步备份） |
| 9/17 | — | — | Learn Claude Code 前三章（Agent Loop 循环工程化·工具调用 name/description/schema·三层权限隔离：白名单→参数校验→人工确认） |
| 9/18 | — | — | Learn Claude Code 第四章 钩子函数（生命周期事件三类粒度、三层配置结构、5 种 handler、退出码 0/2、PreToolUse 四决策与 PermissionRequest 权限接管、实战拦截 rm 与自动格式化） |
| 9/20 | — | — | Learn Claude Code 第五章 TodoWrite（元工具定位·Permission=No、四态生命周期、**提醒机制：宿主注入系统消息·工具调用后与收工前两条触发线·与 Hook 同源·提醒成本计入可用性**、SDK tool_use 流与防御式解析、模型可用性：新模型默认不提供改给 Task 四件套、Ctrl+T/跨压缩存活/TASK_LIST_ID 跨会话共享） |
| 9/21 | — | — | Learn Claude Code 第六章 Subagent 与 Skill 加载（Subagent：隔离上下文·只回摘要·内置 Explore/Plan/general-purpose·五级作用域·启动加载项·Resume；Skill：描述常驻+正文按需·Reference vs Task·内容生命周期与压缩预算·allowed-tools 安全·context: fork；上下文成本总表与选型：CLAUDE.md 订阅制 / Skill 按次 / Subagent 独立核算 / Hook 免费外包） |
| 9/22 | — | — | Learn Claude Code 第七章 上下文压缩（四级降级：①工具结果截断 ②消息数量压缩（头3+尾47、掐中间）③消息内容压缩（老结果→文件路径引用化、再压新结果）④LLM 摘要兜底（输入按前1/4+后3/4裁剪）；与第六章构成「事前预防 + 事后补救」上下文管理闭环） |
| 10/4 | — | — | Learn Claude Code 第八章 记忆系统（LLM 无状态→记忆=工程问题：上下文内工作/会话记忆 + 上下文外长期文件/外部知识；CLAUDE.md 显式长期记忆·按轮计费；自动记忆=上下文外化为文件；与上下文压缩互补——重要信息先落盘再压缩；设计心法：该记的记·该忘的忘·该想起来时想得起来） |
| 10/6 | — | — | LangChain（一）模型调用与消息体系（init_chat_model 统一初始化 provider:model / 六种调用 invoke·ainvoke·stream·astream·batch·abatch：batch 更快但同步阻塞改成 abatch / 额外参数 model_kwargs 与 extra_body（DeepSeek thinking）/ LangSmith 可观测平台 tracing·monitoring·debug·evaluate / AIMessage 特有 response_metadata 与 tool_calls + ToolMessage 靠 tool_call_id 配对） |
| 10/8 | — | — | LangChain（二）工具调用 Tool Use（`@tool` 三要素·`StructuredTool`；**模型只提议不执行**：`bind_tools` 把 schema 预绑定进请求、AIMessage 带 tool_calls；手动回路 invoke→执行→ToolMessage 回灌→再 invoke；`create_agent` 内置循环；工具 schema 占上下文 → MVTS） |
| 10/8 | — | — | LangChain（三）结构化输出（底层仍是 Function Calling——「只有 schema 无实现的虚拟工具」只取 args；`with_structured_output(Pydantic)` 进出强类型；Schema 设计 description/Literal/Optional/嵌套≤3层；备用 bind_tools+tool_choice；失败兜底：校验器·重试·few-shot） |
| 10/8 | — | — | LangChain（四）Agent（**Agent = LLM + 工具 + 循环**；ReAct Thought-Action-Observation → 现代原生 Function Calling 版；`create_agent` 取代 AgentExecutor·内部图 model→tool_calls判断→tools→回灌→终止；Middleware 钩子=压缩·工具审批 HITL·动态工具集 ≈ Claude Code Hook；checkpointer + thread_id 会话记忆；HITL 四决策） |
| 10/10 | — | — | LangChain（五）中间件 Middleware（**Middleware = Agent 的 AOP**；六大钩子 node-style 顺序执行·改 state·jump_to vs wrap-style 包住调用·控制 0/1/N 次·request.override；装饰器 vs 类·state_schema/tools/transformers；state 更新机制差异；before 正序·after 逆序·wrap 嵌套；内置中间件全览 ToolRetry/ModelFallback/Summarization/HITL/PII/CallLimit/TodoList/SubAgent/ContextEditing；实战：动态 prompt·动态模型·动态工具集·工具监控） |
| 10/11 | — | — | LangChain（六）RAG 与文档加载（**RAG = 检索增强生成**，解决知识过时·幻觉·无私有数据；微调改「说话方式」vs RAG 改「手边材料」；两阶段：离线索引（加载→切分→向量化→入库）+ 在线检索生成（检索→拼 Prompt→生成）；**Document 对象** page_content 进向量·metadata 管过滤/溯源/更新；Loader 家族 TextLoader/PyPDFLoader/Office/WebBaseLoader/结构化 + `DirectoryLoader` 批量加载；切分 `RecursiveCharacterTextSplitter`·chunk_size/overlap·中文补匀末标点；**铁律：索引与查询同一 embedding 模型**） |
| 10/18 | — | — | hello-agents 第二章 智能体发展史（补学：符号主义·物理符号系统假说·接地难题 → 专家系统·知识获取瓶颈 → 强化学习·策略/奖励/探索利用 → LLM 智能体；四代主线对照表 + 现代范式祖先 ReAct/Reflexion/Plan-and-Solve） |
| 10/19 | — | — | hello-agents 第九章 上下文工程（上下文工程 vs 提示工程·上下文腐蚀与注意力预算；上下文解剖学：系统提示分区/工具 MVTS/示例；JIT 上下文与渐进式披露；长时程三件套：压缩整合·结构化笔记·子代理架构；**ContextBuilder GSSC 流水线**：Gather 多源容错汇集 → Select 相关性×新近性(指数衰减)+阈值过滤+贪心填充 → Structure Role/Task/Evidence/Context/Output 五分区 → Compress 分区截断兜底；NoteTool 结构化笔记 · TerminalTool 文件系统 JIT 访问） |
| 10/22 | — | — | 复习日：第七章 构建你的Agent框架 + 第八章 记忆与检索（前半）回顾，无新笔记 |
| 10/24 | — | — | LangGraph（一）图基础与 State 状态管理（**LangGraph = 有向图 + 共享 State**，状态机思维；建图五步 State→Node→Edge→compile→invoke；**节点只返回增量**而非整份 state；**Reducer**：无注解=LastValue 覆盖·`Annotated[int, operator.add]` 相加·`add_messages` 按 id 更新；条件边 → review↔write 反思-修正循环 + `GraphRecursionError`/`recursion_limit`；stream_mode updates(按节点增量)/values(完整快照)/messages(token)；**checkpointer** super-step 快照 + thread_id 多轮记忆与线程隔离 + `get_state_history` 时间旅行；与第四章 `create_agent` 内部图、第五章 HITL 打通；langgraph 1.2.16 本机实测） |
| 10/25 | — | — | hello-agents 8.3.5 高级检索：**MQE 多查询扩展**（LLM 生成 N 个语义等价变体·并行检索·治词汇不匹配·召回率+30~50%）+ **HyDE 假设文档嵌入**（"用答案找答案"·先编一段答案再检索·治问句/答句语义鸿沟·补专业术语密度）；统一扩展框架「扩展→检索→合并」三步 + `candidate_pool_multiplier=4`（去重会缩水·宁可多捞）+ 按 memory_id 去重保留最高分 + 扩展失败回退原 query + metadata 三层过滤（memory_type/is_rag_data/rag_namespace）隔离记忆与文档；选型：一般用 MQE·专业领域同开·延迟敏感走基础检索；LangGraph（二）进阶建图（`add_sequence` 批量连链·图构建即代码；`add_conditional_edges`+`path_map` 业务语义与拓扑分层·返回 list 固定扇出·路由异常必须兜底+Literal 标注；**Router=纯函数决策层**对照 `Command(goto)`；**`Send` 动态并行扇出**·payload 即实例 state·reducer 汇回·与 MQE 同构；**`defer=True` 真相**：仅同一 super-step 内推迟·线性链/中间节点无效·主链 END 不取消它；`interrupt`+`Command(resume)` 三铁律：需 checkpointer·节点整段重放→前置代码须幂等·resume 可序列化) |
| 10/26 | — | — | hello-agents 第九章补充：**JIT 及时上下文**（预检索赌一把 vs 按需取用·窗口里放引用不放数据·元数据路径/大小/时间本身传语义·渐进式披露 ls→挑→head/grep→只带片段·代价是慢需混合策略）+ **GSSC 四步**（Gather 五源 try-except 容错/系统指令 1.0 不参与评分/历史只留5条 → Select 先扣宪法预算再分配·Jaccard 相关 + exp 新近夹[0.1,1]·权重即产品性格·贪心背包可解释 → Structure Role/Task/Evidence/Context/Output → Compress 分区截断保结构完整）+ **Transformer**（Q/K/V·softmax(QKᵀ/√d)·多头·RoPE·因果掩码 → n² 稀释即上下文腐蚀根源，**注意力预算=上下文工程的物理上限**） |
| 10/28 | — | — | **Transformer 实战：从零手搓 Transformer 做英译中**（[源码仓库](https://github.com/JiangYuxin-Jim/Transformer-pytorch)，PyTorch 约 1500 行跑通全流程）：数据层（语料合并·对齐校验·中英各训 32k BPE·padding/因果/合并三种 mask 对照·Teacher Forcing 错位一格）；模型层（Embedding×√512·PE 的 exp/log 数值技巧·除以 √d_k 防 softmax 饱和·MHA 形状 [B,L,512]→[B,8,L,64]→拼接·手写 LayerNorm 按特征维归一·**Post-LN vs Pre-LN：这是论文必须 warmup 的真正原因**·交叉注意力是唯一跨语言通道·Xavier 只初始化权重矩阵）；训练（label-wise CE 按 ntokens 归一·**Noam warmup=10000 逆平方根**·**MultiGPULossCompute 分块算 logits 只累加标量再拼梯度**·**模型选择用 BLEU 而非 dev_loss**）；推理（**Beam Search 手写全解**：`//` 取来源 beam、`%` 取词 id·Encoder 只跑一次 repeat 扇出 memory·**已完句提前退出**·回溯重建；无 KV Cache 所以每步重跑全前缀）；**BLEU 26.30**（25 万句·3 epoch，对照 paper 450 万句 27.3）＋ paper 差异清单（未用 Label Smoothing·无长度惩罚）＋6 条真实踩坑（`test()` 签名 bug·`os` 只在 `__main__` 导入·evaluate 极慢·MPS 未适配·词表权重必须配套·3 epoch 只是跑通非收敛）＋7 项改进（KV Cache / Label Smoothing / 长度惩罚 / Pre-LN 对照 / attention 热力图对齐） |

---

## 📌 学习进度

- ✅ JavaSE（完整 37 篇笔记）— 全部完结 🎉（补写网络编程·反射·动态代理·继承）
- 🔄 **JUC 并发补充** — ✅ 36 JUC 三大特性（JMM 内存模型·原子性/可见性/有序性·指令重排·volatile·happens-before）· ✅ 37 原子类与锁机制（原子类家族·LongAdder·CAS 三大问题·锁升级·ReentrantLock 全家桶·锁优化实践）
- ✅ JavaWeb（15 篇笔记）— 已完成
- ✅ **Redis（全部完结 🎉）** — 基础篇✅ 实战篇✅ 高级篇(持久化·主从·哨兵·集群·多级缓存·最佳实践)✅ 原理篇(数据结构·网络模型·通信协议RESP·内存回收)✅，175 集全学完
- 🔄 **AI 智能体与 RAG（新主线，优先）** — **hello-agents**（智能体 16 章）✅第一章(理论+动手) · ✅第二章(智能体发展史) · ✅第三章(LLM基础) · ✅第六章(框架开发实践) · ✅第七章(构建你的Agent框架) · ✅第八章(记忆与检索) · ✅第九章(上下文工程·含 JIT 上下文与 GSSC 流水线精读) · ✅8.3.5 高级检索(MQE+HyDE)；all-in-rag（RAG 9章）✅clone → 待学；**工具/框架基础** ✅Zotero 文献管理基础 · ✅Learn Claude Code 前八章（Loop / 工具调用 / 三层权限 / 钩子函数 / TodoWrite / Subagent 与 Skill 加载 / 上下文压缩 / 记忆系统）· ✅LangChain（一）模型调用与消息体系 · ✅LangChain（二）工具调用 Tool Use · ✅LangChain（三）结构化输出 · ✅LangChain（四）Agent（ai/tools/）· ✅LangChain（五）中间件 Middleware（六大钩子·装饰器/类·state·执行顺序·内置全览·四个实战）· ✅LangChain（六）RAG 与文档加载（RAG 两阶段·Document·Loader 家族·DirectoryLoader·切分策略）· ✅LangGraph（一）图基础与状态管理 · ✅LangGraph（二）进阶建图（defer/条件边/sequence/Router/Send·interrupt 对照）· 🔥**Transformer 实战：从零手搓 Transformer 英译中跑通全流程**（[源码仓库](https://github.com/JiangYuxin-Jim/Transformer-pytorch)·PyTorch 手写 Encoder-Decoder·Noam 优化器·Beam Search·**BLEU 26.30**）
- ⏳ 下一阶段：**LangGraph 继续**（LangGraph（三）Subgraph 子图·retry_policy/cache_policy/timeout/error_handler → 手搓 ReAct Agent 图对照 create_agent）↔ **LangChain RAG 线继续**（向量化 Embeddings → 向量库 VectorStore → 检索器 Retriever → 高级检索）↔ all-in-rag ch3 对照 → hello-agents 第十章（智能体通信协议 MCP/A2A/ANP）→ 天机学堂（Java/Spring AI 落地） 🎯
