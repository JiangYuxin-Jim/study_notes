# 学习笔记

> 📚 基于黑马程序员课程，按知识板块整理的学习笔记。
> 内容使用 AI 辅助生成和润色。

---

## 📊 学习历程可视化

> 下图直观展示了每天学习的内容分布，色块越深代表当天学习量越大。

<svg viewBox="0 0 960 600" width="100%" xmlns="http://www.w3.org/2000/svg">
  <style>
    .tl-title   { font-size: 20px; font-weight: 650; fill: #172033; }
    .tl-subtitle{ font-size: 13px; fill: #5b6475; }
    .tl-small   { font-size: 11px; fill: #5b6475; }
    .tl-xlabel  { font-size: 11px; fill: #5b6475; text-anchor: middle; }
    .tl-legend  { font-size: 12px; fill: #172033; }
    .tl-grid    { stroke: #e2e8f0; stroke-width: 1; stroke-dasharray: 4 4; }
    .tl-axis    { stroke: #64748b; stroke-width: 1.5; }
    .tl-sl      { font-size: 11px; fill: #172033; text-anchor: end; dominant-baseline: central; }
    .tl-bl      { font-size: 9px;  fill: #fff;     text-anchor: middle; dominant-baseline: central; }
    .tl-skip    { font-size: 11px; fill: #dc2626;   text-anchor: middle; }
  </style>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- 标题 & 图例 -->
  <!-- ═══════════════════════════════════════════════════════════════ -->
  <text x="20" y="30" class="tl-title">📚 学习历程时间线</text>
  <text x="20" y="52" class="tl-subtitle">2026-07-05 → 2026-07-22 · 每格代表当天学习的内容板块</text>

  <rect x="640" y="20" width="14" height="14" rx="3" fill="#3b82f6" opacity="0.7"/>
  <text x="660" y="31" class="tl-legend">JavaSE</text>
  <rect x="730" y="20" width="14" height="14" rx="3" fill="#10b981" opacity="0.7"/>
  <text x="750" y="31" class="tl-legend">JavaWeb</text>
  <rect x="820" y="20" width="14" height="14" rx="3" fill="#f59e0b" opacity="0.7"/>
  <text x="840" y="31" class="tl-legend">Redis</text>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- 左侧行标签 -->
  <!-- ═══════════════════════════════════════════════════════════════ -->
  <text x="60" y="110" class="tl-sl">Redis</text>
  <text x="60" y="155" class="tl-sl">JavaSE 基础</text>
  <text x="60" y="200" class="tl-sl">JavaSE 面向对象</text>
  <text x="60" y="245" class="tl-sl">JavaSE 进阶</text>
  <text x="60" y="290" class="tl-sl">JavaWeb</text>
  <text x="60" y="335" class="tl-sl">项目实战</text>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- 水平网格线 -->
  <!-- ═══════════════════════════════════════════════════════════════ -->
  <line x1="70" y1="125" x2="940" y2="125" class="tl-grid"/>
  <line x1="70" y1="170" x2="940" y2="170" class="tl-grid"/>
  <line x1="70" y1="215" x2="940" y2="215" class="tl-grid"/>
  <line x1="70" y1="260" x2="940" y2="260" class="tl-grid"/>
  <line x1="70" y1="305" x2="940" y2="305" class="tl-grid"/>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- 日列（18 天，列宽 48px）                                        -->
  <!-- 公式：col_x = 75 + n*48    text_x = 98 + n*48                  -->
  <!-- 行 Y：Redis=88, SE基础=133, SE_OOP=178, SE进阶=223, JavaWeb=268 -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <!-- d00: 7/5 三 ───────────────────────────────────────────────── -->
  <g id="d00-0705">
    <text x="98"  y="365" class="tl-xlabel">7/5</text>
    <text x="98"  y="380" class="tl-xlabel tl-small">三</text>
    <rect x="75"  y="88"  width="46" height="33" rx="4" fill="#f59e0b" opacity="0.85"/>
    <text x="98"  y="105" class="tl-bl">基础入门</text>
  </g>

  <!-- d01: 7/6 四（休息）───────────────────────────────────────── -->
  <g id="d01-0706">
    <text x="146" y="365" class="tl-xlabel">7/6</text>
    <text x="146" y="380" class="tl-xlabel tl-small">四</text>
    <text x="146" y="400" class="tl-skip">×</text>
  </g>

  <!-- d02: 7/7 五 ───────────────────────────────────────────────── -->
  <g id="d02-0707">
    <text x="194" y="365" class="tl-xlabel">7/7</text>
    <text x="194" y="380" class="tl-xlabel tl-small">五</text>
    <rect x="171" y="88"  width="46" height="33" rx="4" fill="#f59e0b" opacity="0.85"/>
    <text x="194" y="105" class="tl-bl">秒杀/锁</text>
  </g>

  <!-- d03: 7/8 六 ───────────────────────────────────────────────── -->
  <g id="d03-0708">
    <text x="242" y="365" class="tl-xlabel">7/8</text>
    <text x="242" y="380" class="tl-xlabel tl-small">六</text>
    <rect x="219" y="88"  width="46" height="33" rx="4" fill="#f59e0b" opacity="0.85"/>
    <text x="242" y="105" class="tl-bl">MQ</text>
  </g>

  <!-- d04: 7/9 日（Redis + JavaSE基础 + JavaWeb 三线并行）──────── -->
  <g id="d04-0709">
    <text x="290" y="365" class="tl-xlabel">7/9</text>
    <text x="290" y="380" class="tl-xlabel tl-small">日</text>
    <rect x="267" y="88"  width="46" height="33" rx="4" fill="#f59e0b" opacity="0.85"/>
    <text x="290" y="105" class="tl-bl">探店</text>
    <rect x="267" y="133" width="46" height="33" rx="4" fill="#3b82f6" opacity="0.85"/>
    <text x="290" y="150" class="tl-bl">入门到JVM</text>
    <rect x="267" y="268" width="46" height="33" rx="4" fill="#10b981" opacity="0.85"/>
    <text x="290" y="285" class="tl-bl">全15篇</text>
  </g>

  <!-- d05~d10: 7/10~7/15（休息）────────────────────────────────── -->
  <g id="d05-0710"><text x="338" y="365" class="tl-xlabel">7/10</text><text x="338" y="380" class="tl-xlabel tl-small">一</text><text x="338" y="400" class="tl-skip">×</text></g>
  <g id="d06-0711"><text x="386" y="365" class="tl-xlabel">7/11</text><text x="386" y="380" class="tl-xlabel tl-small">二</text><text x="386" y="400" class="tl-skip">×</text></g>
  <g id="d07-0712"><text x="434" y="365" class="tl-xlabel">7/12</text><text x="434" y="380" class="tl-xlabel tl-small">三</text><text x="434" y="400" class="tl-skip">×</text></g>
  <g id="d08-0713"><text x="482" y="365" class="tl-xlabel">7/13</text><text x="482" y="380" class="tl-xlabel tl-small">四</text><text x="482" y="400" class="tl-skip">×</text></g>
  <g id="d09-0714"><text x="530" y="365" class="tl-xlabel">7/14</text><text x="530" y="380" class="tl-xlabel tl-small">五</text><text x="530" y="400" class="tl-skip">×</text></g>
  <g id="d10-0715"><text x="578" y="365" class="tl-xlabel">7/15</text><text x="578" y="380" class="tl-xlabel tl-small">六</text><text x="578" y="400" class="tl-skip">×</text></g>

  <!-- d11: 7/16 日（JavaSE OOP 开始）────────────────────────────── -->
  <g id="d11-0716">
    <text x="626" y="365" class="tl-xlabel">7/16</text>
    <text x="626" y="380" class="tl-xlabel tl-small">日</text>
    <rect x="603" y="178" width="46" height="33" rx="4" fill="#3b82f6" opacity="0.85"/>
    <text x="626" y="195" class="tl-bl">OOP/String/API</text>
  </g>

  <!-- d12~d13: 7/17~7/18（休息）────────────────────────────────── -->
  <g id="d12-0717"><text x="674" y="365" class="tl-xlabel">7/17</text><text x="674" y="380" class="tl-xlabel tl-small">一</text><text x="674" y="400" class="tl-skip">×</text></g>
  <g id="d13-0718"><text x="722" y="365" class="tl-xlabel">7/18</text><text x="722" y="380" class="tl-xlabel tl-small">二</text><text x="722" y="400" class="tl-skip">×</text></g>

  <!-- d14: 7/19 三 ──────────────────────────────────────────────── -->
  <g id="d14-0719">
    <text x="770" y="365" class="tl-xlabel">7/19</text>
    <text x="770" y="380" class="tl-xlabel tl-small">三</text>
    <rect x="747" y="178" width="46" height="33" rx="4" fill="#3b82f6" opacity="0.75"/>
    <text x="770" y="195" class="tl-bl">克隆/正则/日期</text>
  </g>

  <!-- d15: 7/20 四（JavaSE 进阶阶段）────────────────────────────── -->
  <g id="d15-0720">
    <text x="818" y="365" class="tl-xlabel">7/20</text>
    <text x="818" y="380" class="tl-xlabel tl-small">四</text>
    <rect x="795" y="223" width="46" height="33" rx="4" fill="#3b82f6" opacity="0.8"/>
    <text x="818" y="240" class="tl-bl">集合(一)</text>
  </g>

  <!-- d16: 7/21 五 ──────────────────────────────────────────────── -->
  <g id="d16-0721">
    <text x="866" y="365" class="tl-xlabel">7/21</text>
    <text x="866" y="380" class="tl-xlabel tl-small">五</text>
    <rect x="843" y="223" width="46" height="33" rx="4" fill="#3b82f6" opacity="0.85"/>
    <text x="866" y="240" class="tl-bl">List/泛型</text>
  </g>

  <!-- d17: 7/22 六（上部完结）──────────────────────────────────── -->
  <g id="d17-0722">
    <text x="914" y="365" class="tl-xlabel">7/22</text>
    <text x="914" y="380" class="tl-xlabel tl-small">六</text>
    <rect x="891" y="223" width="46" height="33" rx="4" fill="#3b82f6" opacity="0.95"/>
    <text x="914" y="240" class="tl-bl">数据结构</text>
  </g>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- 底部坐标轴 & 里程碑注释 -->
  <!-- ═══════════════════════════════════════════════════════════════ -->
  <line x1="70" y1="395" x2="940" y2="395" class="tl-axis"/>

  <circle cx="75"  cy="418" r="4" fill="#f59e0b"/>
  <circle cx="290" cy="438" r="4" fill="#10b981"/>
  <circle cx="603" cy="458" r="4" fill="#3b82f6"/>
  <circle cx="795" cy="478" r="4" fill="#3b82f6"/>
  <circle cx="914" cy="498" r="4" fill="#3b82f6"/>

  <text x="75"  y="420" class="tl-small">↑ 7/5 开始学 Redis</text>
  <text x="290" y="440" class="tl-small">↑ 7/9 JavaWeb + JavaSE 入门笔记</text>
  <text x="603" y="460" class="tl-small">↑ 7/16 OOP &amp; String 开始</text>
  <text x="795" y="480" class="tl-small">↑ 7/20 集合进阶阶段开始</text>
  <text x="891" y="500" class="tl-small">↑ 7/22 上部学完 🎉</text>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- 底部摘要 -->
  <!-- ═══════════════════════════════════════════════════════════════ -->
  <text x="20" y="550" class="tl-subtitle">已完成：Redis 篇 · JavaSE 上部 · JavaWeb 全套</text>
  <text x="20" y="570" class="tl-subtitle">进行中：JavaSE 下部（进阶）</text>
</svg>

---

## 📂 目录

### Redis 缓存

| 序号 | 内容 | 完成时间 |
|------|------|----------|
| [01 - 认识 Redis](./redis缓存/01-认识Redis.md) | Redis 介绍、数据类型、常用命令 | 2026-07-05 |
| [02 - 缓存穿透/雪崩/击穿](./redis缓存/02-缓存穿透雪崩击穿.md) | 三大缓存问题及解决方案 | 2026-07-05 |
| [03 - 优惠券秒杀](./redis缓存/03-优惠券秒杀.md) | 全局唯一ID、RedisIdWorker、超卖问题、乐观锁/悲观锁、一人一单 | 2026-07-07 |
| [04 - 分布式锁](./redis缓存/04-分布式锁.md) | SETNX 演进路线、UUID + Lua 原子解锁、Redisson（WatchDog/可重入/RedLock） | 2026-07-07 |
| [05 - 秒杀优化与消息队列](./redis缓存/05-秒杀优化与消息队列.md) | Lua 脚本前置判断、异步下单、Redis 消息队列（List/PubSub/Stream）、消费者组 | 2026-07-08 |
| [06 - 达人探店](./redis缓存/06-达人探店.md) | 发布探店笔记、图片上传、点赞/取消点赞、SortedSet 点赞排行榜 | 2026-07-09 |

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

---
