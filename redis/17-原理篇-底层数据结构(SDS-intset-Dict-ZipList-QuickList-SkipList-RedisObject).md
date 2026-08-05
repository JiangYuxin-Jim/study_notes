# 17 - Redis 原理篇：底层数据结构（SDS / intset / Dict / ZipList / QuickList / SkipList / RedisObject）

> 📅 2026-08-05 | 🏷️ Redis / 原理篇 / 数据结构 / 底层实现

> 说明：本系列为 Redis **原理篇**的第一部分「数据结构」。已学到第 160 集（ZipList 压缩列表）。本篇按课程讲义整理底层各数据结构：SDS、intset、Dict、ZipList、QuickList、SkipList、RedisObject。网络模型、通信协议、内存回收等后续学到再补。

> ⚠️ 版本说明：本课程基于 **Redis 6.x**（RESP2 协议时代），List 底层为 QuickList（节点是 ZipList），**尚未引入 Redis 7.0 的 listpack** 替换。

---

## 一、SDS（简单动态字符串）— String 底层

Redis 没有直接用 C 语言的字符串，因为 C 字符串有三个问题：
- **获取长度需要遍历运算**（O(n)）
- **非二进制安全**（遇到 `\0` 就截断，无法存二进制数据）
- **不可修改**（是常量，追加需重新分配）

Redis 自建了 **SDS（Simple Dynamic String，简单动态字符串）** 来解决。

### SDS 结构体
```c
struct sdshdr {
    int len;        // 已用长度
    int alloc;      // 已分配容量
    char buf[];     // 字节数组（柔性数组）
};
```
- 记录 `len` 和 `alloc`，取长度 O(1)，二进制安全（以 len 为准，不以 `\0` 判断）。
- 头部保存了长度，追加时判断容量够不够。

### 动态扩容（内存预分配）
SDS 具备**动态扩容**能力，追加字符串时会**预分配**内存，避免频繁 realloc：
- 如果扩展后字符串**小于 1MB**：新空间 = 扩展后长度 × 2 + 1
- 如果扩展后字符串**大于 1MB**：新空间 = 扩展后长度 + 1MB + 1

> 一句话：**空间换时间**，减少扩容次数。

---

## 二、IntSet（整数集合）— Set 底层之一

IntSet 是 Redis Set 集合的一种实现，基于**整数数组**，具备**长度可变、有序**特征。

### 结构
```c
typedef struct intset {
    uint32_t encoding;   // 编码方式（决定每个整数占几字节）
    uint32_t length;     // 元素个数
    int8_t contents[];   // 整数数组（升序排列）
} intset;
```

### encoding 三种模式
| 编码 | 每个整数大小 |
|------|-------------|
| INTSET_ENC_INT16 | 2 字节 |
| INTSET_ENC_INT32 | 4 字节 |
| INTSET_ENC_INT64 | 8 字节 |

所有整数**按照升序**依次保存在 contents 数组中，方便二分查找。

### 升级机制（自动扩容编码）
当要添加的元素超出当前编码范围时（如往 int16 集合添加 50000），intset **自动升级编码**：
1. 升级编码到能容纳新元素的大小（如 INT16 → INT32），并**扩容数组**。
2. **倒序**依次将原数组元素拷贝到扩容后的正确位置。
3. 将新元素放入数组末尾。
4. 更新 encoding 和 length 属性。

### IntSet 特点小结
- 确保元素**唯一、有序**。
- 具备**类型升级机制**，可以节省内存（小整数用小编码存）。
- 底层采用**二分查找**查询。

> 升级机制只能**由小到大**，不能降级。Set 元素都是整数且少时用 intset（省内存），有非整数或超阈值时升级为哈希表（dict）。

---

## 三、Dict（字典/哈希表）— 所有 key 和大部分 value 的底层

Redis 是键值型数据库，键到值的映射关系就是通过 **Dict** 实现的。数据库本身、Hash 类型、Set 类型底层都用 Dict。

### Dict 三部分
1. **哈希表 DictHashTable**（数组 + 链表）
2. **哈希节点 DictEntry**（存 key/value、next 指针解决冲突）
3. **字典 Dict**（管理结构，含两个哈希表 ht[0]、ht[1]）

### 存储过程
- 根据 key 计算 hash 值 h。
- 用 `h & sizemask` 计算索引位置（sizemask = size - 1）。
- 哈希冲突通过**单向链表**解决（头插）。

### 扩容时机（LoadFactor = used / size）
- 满足以下任一时触发**扩容**：
  1. LoadFactor ≥ **1**，且服务器没有执行 BGSAVE/BGREWRITEAOF 等后台进程
  2. LoadFactor > **5**（无论有无后台进程）
- **收缩**：LoadFactor < **0.1** 时触发。

### rehash（渐进式）
扩容/收缩都要创建新哈希表，size 和 sizemask 变化，必须对每个 key **重新计算索引**，这个过程叫 rehash：
1. 计算新 size：扩容为第一个 ≥ used+1 的 2^n；收缩为第一个 ≥ used 的 2^n（最小 4）。
2. 申请内存创建新哈希表给 ht[1]。
3. 设 `rehashidx = 0` 开始 rehash。
4. 每次访问 Dict 时**执行一次 rehash**（把 ht[0] 部分数据搬移到 ht[1]），渐进式、不阻塞。
5. ht[0] 全部搬完 → ht[1] 赋给 ht[0]，清空 ht[1]，`rehashidx = -1` 结束。

**rehash 期间的增删改查规则**：
- **新增**只写 ht[1]（保证 ht[0] 数据只减不增）。
- **查询/修改/删除**在 ht[0] 和 ht[1] 两个表依次查找。

### Dict 特点小结
- 类似 Java 的 HashMap，底层数组 + 链表解决哈希冲突。
- 包含两个哈希表 ht[0]（平时用）、ht[1]（rehash 用）。
- 采用**渐进式 rehash**，避免一次性搬迁阻塞主线程。

---

## 四、ZipList（压缩列表）— List/Hash/ZSet 的小数据底层 ⭐

ZipList 是一种特殊的**"双端链表"**，由一系列特殊编码的**连续内存块**组成，可以在任意一端压入/弹出，时间复杂度 O(1)。

> 核心思想：小数据时用**连续内存 + 紧凑编码**，不用指针，最大程度**节省内存**（省下指针占用的空间）。代价是随机访问能力弱、修改可能要搬迁。

### 整体布局（连续内存）
```
<zlbytes> <zltail> <zllen> <entry>...<entry> <zlend>
```
| 属性 | 类型 | 长度 | 用途 |
|------|------|------|------|
| zlbytes | uint32_t | 4 字节 | 整个压缩列表占用内存字节数 |
| zltail | uint32_t | 4 字节 | 表尾节点距起始地址偏移量（方便倒序遍历） |
| zllen | uint16_t | 2 字节 | 节点数量（超过 65535 需遍历统计） |
| entry | 列表节点 | 不定 | 各节点，长度由内容决定 |
| zlend | uint8_t | 1 字节 | 结束标记 0xFF（255） |

### ZipListEntry 的结构
不记录前后指针（省 16 字节），而是用长度+编码来寻址：
```
<previous_entry_length> <encoding> <contents>
```
- **previous_entry_length**：前一个节点的长度，占 **1 或 5 字节**，用于倒序遍历。
  - 前一节点长度 < 254 字节 → 用 1 字节
  - 前一节点长度 ≥ 254 字节 → 用 5 字节（首字节 0xFE 标记，后 4 字节真实长度）
- **encoding**：记录 content 数据类型（字符串 or 整数）及长度，占 1/2/5 字节。
- **contents**：实际数据，可以是字符串或整数。

> 所有长度数值采用**小端字节序**（低位在前），如 0x1234 实际存 0x3412。

### Encoding 编码
**字符串类型**（encoding 以 `00`、`01`、`10` 开头）：

| 编码 | 编码长度 | 字符串大小 |
|------|----------|-----------|
| `00pppppp` | 1 字节 | ≤ 63 字节 |
| `01pppppp qqqqqqqq` | 2 字节 | ≤ 16383 字节 |
| `10000000 qqqqqqqq rrrrrrrr ssssssss tttttttt` | 5 字节 | ≤ 4294967295 字节 |

**整数类型**（encoding 以 `11` 开头，固定占 1 字节）：

| 编码 | 编码长度 | 整数类型 |
|------|----------|---------|
| 11000000 | 1 | int16_t（2 字节） |
| 11010000 | 1 | int32_t（4 字节） |
| 11100000 | 1 | int64_t（8 字节） |
| 11110000 | 1 | 24 位有符号整数（3 字节） |
| 11111110 | 1 | 8 位有符号整数（1 字节） |
| 1111xxxx | 1 | 直接在 xxxx 保存，范围 0001~1101，减 1 为实际值 |

### 连锁更新（Cascade Update）⚠️ 核心考点
每个 entry 的 `previous_entry_length` 记录**前一个节点的长度**，占 1 或 5 字节动态决定。

当有 N 个连续的、长度在 250~253 字节之间的 entry 时，它们的 prevlen 都用 1 字节：
```
entry1{...253字节} entry2{prevlen:1字节 ...253字节} entry3{prevlen:1字节 ...}
```
此时若在**中间插入/删除一个较大的节点**（≥254 字节），会导致：
- 插入点后第一个 entry 的 prevlen 需从 1 字节扩展为 5 字节 → 自身变长
- 又导致它后面 entry 的 prevlen 也要扩展……
- **连锁反应**，往后一串 entry 都要重新分配内存、拷贝数据 → 最坏 **O(N²)** 耗时

这种特殊情况下产生的连续多次空间扩展，就叫**连锁更新**。**新增、删除都可能导致**。

### ZipList 特点小结
- 可看作连续内存空间的"双向链表"（能在两端操作）。
- 节点间**不是指针连接**，而是**记录上一节点和本节点长度**来寻址，内存占用低。
- 数据过多、链表过长时，**查询性能**会变差（需遍历）。
- 增删**较大数据**时可能发生**连锁更新**问题。

---

## 五、QuickList — List 的底层（3.2 版本后）

**问题背景**：
1. ZipList 省内存，但**申请内存必须连续**，占用较多时申请效率低 → 需限制 ZipList 长度和 entry 大小。
2. 要存储大量数据，超 ZipList 上限怎么办？→ 创建**多个 ZipList 分片存储**。
3. 多个 ZipList 分散，如何管理和查找？→ 用**双端链表**把它们串起来。

**QuickList = 双端链表 + 每个节点是一个 ZipList**（Redis 3.2 引入）。

### 控制 ZipList 大小
配置项 `list-max-ziplist-size`：
- 值为**正**：每个 ZipList 允许的最大 **entry 个数**。
- 值为**负**：每个 ZipList 的最大**内存大小**（5 档）：
  - -1：≤ 4kb
  - -2：≤ 8kb
  - -3：≤ 16kb
  - -4：≤ 32kb
  - -5：≤ 64kb
- **默认值 -2**（每个 ZipList ≤ 8kb）。

### QuickList 特点小结
- 是节点为 ZipList 的**双端链表**。
- 节点用 ZipList，解决了传统链表的**内存占用**问题。
- 控制了 ZipList 大小，解决**连续内存申请效率**问题。
- **中间节点可以压缩**，进一步节省内存。

---

## 六、SkipList（跳表）— ZSet 底层

SkipList（跳表）本质是**链表**，但与传统链表不同：
- 元素**按升序排列**存储。
- 节点可能包含**多个指针**，指针跨度不同（层级高、跨度大）。

### 特点小结
- 是一个**双向链表**，每个节点包含 **score** 和 **ele** 值。
- 节点按 **score 排序**，score 相同则按 ele **字典序**排序。
- 每个节点可包含**多层指针**，层数是 **1 到 32 之间的随机数**。
- 不同层指针到下一节点跨度不同，**层级越高跨度越大**。
- 增删改查效率与**红黑树基本一致**，但**实现更简单**。

---

## 七、RedisObject（Redis 对象）— 所有 value 的通用封装

Redis 中任意数据类型的**键和值**都会被封装为一个 **RedisObject（robj）**。

> 为什么需要：Redis 的 key 固定是 string（SDS），但 value 可以是多种类型（string/list/hash/set/zset）。为了在同一个 dict 里存不同类型，需要一个**通用的数据结构**来承载，这就是 robj。

### 编码方式（11 种）
| 编号 | 编码 | 说明 |
|------|------|------|
| 0 | OBJ_ENCODING_RAW | raw 编码动态字符串 |
| 1 | OBJ_ENCODING_INT | long 类型整数的字符串 |
| 2 | OBJ_ENCODING_HT | 哈希表（dict） |
| 3 | OBJ_ENCODING_ZIPMAP | 已废弃 |
| 4 | OBJ_ENCODING_LINKEDLIST | 双端链表 |
| 5 | OBJ_ENCODING_ZIPLIST | 压缩列表 |
| 6 | OBJ_ENCODING_INTSET | 整数集合 |
| 7 | OBJ_ENCODING_SKIPLIST | 跳表 |
| 8 | OBJ_ENCODING_EMBSTR | embstr 动态字符串 |
| 9 | OBJ_ENCODING_QUICKLIST | 快速列表 |
| 10 | OBJ_ENCODING_STREAM | Stream 流 |

### 各数据类型可能的编码
| 数据类型 | 编码方式 |
|----------|---------|
| OBJ_STRING | int、embstr、raw |
| OBJ_LIST | LinkedList 和 ZipList（3.2 前）、QuickList（3.2 后） |
| OBJ_SET | intset、HT |
| OBJ_ZSET | ZipList、HT、SkipList |
| OBJ_HASH | ZipList、HT |

> 编码方式由 `OBJECT ENCODING key` 查看，体现"小数据用紧凑编码、大数据用高效结构"的自动切换策略。

---

## 八、核心要点速记

- **SDS**：String 底层，记录 len/alloc → O(1) 取长度、二进制安全、可扩容；超过 1MB 空间预分配规则。
- **IntSet**：Set 的全整数底层，有序唯一、二分查找、可升级编码省内存（不能降级）。
- **Dict**：数组+链表，两个哈希表 ht[0]/ht[1]；LoadFactor ≥1（无子进程）或 >5 扩容，<0.1 收缩；**渐进式 rehash**，rehash 期间新增只写 ht[1]。
- **ZipList**：连续内存"双端链表"，无指针靠 prevlen 寻址省内存；entry = `prevlen|encoding|contents`；**连锁更新**（插/删大节点引发一串扩展，最坏 O(N²)）；增删大节点有隐患。
- **QuickList**：List 底层，双端链表+每节点一个 ZipList，`list-max-ziplist-size` 控制（默认 -2 即 8kb）。
- **SkipList**：ZSet 底层，按 score 升序、多层指针（1~32 随机层）、查询快、实现比红黑树简单。
- **RedisObject**：所有 value 的通用封装，11 种编码，按类型+数据规模自动选编码（少而小→紧凑，多而大→高效）。
