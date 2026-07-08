# 01 - 认识 Redis

> 📅 2026-07-05 | 🏷️ Redis / 缓存

---

## 一、Redis 是什么

**Redis**（Remote Dictionary Server）是一个开源的、基于内存的键值存储数据库。

核心特点：

| 特点 | 说明 |
|------|------|
| **基于内存** | 数据存在内存中，读写速度极快（微秒级） |
| **持久化** | 支持 RDB 快照和 AOF 日志，重启不丢数据 |
| **丰富的数据类型** | 不仅是 String，还支持 List、Set、Hash 等 |
| **单线程模型** | 命令执行是单线程的，避免竞争，但依然很快 |
| **支持事务** | 一组命令按顺序执行，保证原子性 |

---

## 二、Redis 常用五大数据类型

### 1. String（字符串）

最基础的类型，可以存字符串、数字、JSON。

```bash
SET name "zhangsan"        # 存
GET name                   # 取 -> "zhangsan"
SET count 1
INCR count                 # 自增 -> 2
SETEX token 300 "abc123"   # 存，300秒后过期
```

**应用场景**：验证码、Token、计数器、分布式锁。

---

### 2. Hash（哈希）

存对象，一个 key 下面有多个 field-value。

```bash
HSET user:1001 name "张三" age 25
HGET user:1001 name        # -> "张三"
HGETALL user:1001          # 获取全部字段
```

**应用场景**：用户信息、购物车、商品详情。

---

### 3. List（列表）

有序可重复的字符串列表，底层是双向链表。

```bash
LPUSH queue "任务1" "任务2"   # 左侧插入
RPUSH queue "任务3"          # 右侧插入
LPOP queue                   # 左侧弹出
LRANGE queue 0 -1            # 查看全部
```

**应用场景**：消息队列、最新动态列表、时间线。

---

### 4. Set（集合）

无序、不重复的集合。

```bash
SADD tags:article1 "Java" "Redis" "Spring"
SMEMBERS tags:article1       # 查看全部
SINTER set1 set2             # 交集
SUNION set1 set2             # 并集
```

**应用场景**：标签、共同好友、抽奖去重。

---

### 5. Sorted Set（有序集合）

每个元素带一个 score，按 score 排序。

```bash
ZADD rank 100 "张三" 90 "李四" 80 "王五"
ZRANGE rank 0 -1             # 按分数升序
ZREVRANGE rank 0 -1          # 按分数降序
ZSCORE rank "张三"           # 查分数 -> "100"
```

**应用场景**：排行榜、延迟队列、带权重的消息队列。

---

## 三、通用命令

```bash
KEYS pattern         # 查找匹配的 key（生产环境慎用）
EXISTS key           # 判断 key 是否存在
DEL key              # 删除 key
EXPIRE key 60        # 设置过期时间（秒）
TTL key              # 查看剩余过期时间，-1永不过期，-2已过期
TYPE key             # 查看 key 的类型
```

---

## 四、总结

```
Redis = 内存存储 + 五大数据类型 + 持久化 + 高并发

String  → 缓存数据、计数器
Hash    → 存对象
List    → 消息队列
Set     → 去重、交集并集
ZSet    → 排行榜
```

> 💡 下一步：学习 Redis 在实际业务中的缓存问题（穿透、雪崩、击穿）
