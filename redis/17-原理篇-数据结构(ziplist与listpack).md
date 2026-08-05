# 17 - Redis 原理篇：数据结构（ziplist 压缩列表 / listpack）

> 📅 2026-08-05 | 🏷️ Redis / 原理篇 / 数据结构 / ziplist / listpack

> 说明：本系列为 Redis **原理篇**的「数据结构」课程。学到了 ziplist（压缩列表），顺带把与之相关的 listpack 替换、intset、quicklist 一起梳理清楚。Redis 原理篇后续还有网络模型、通信协议、内存回收，学完继续补充。

## 一、为什么要有 ziplist：内存效率的极致追求

Redis 作为**内存数据库**，内存就是它的命根子。`dict`（哈希表）、`跳表`（skiplist）这类结构查找快，但**开销大**——每个节点有指针、分配方式浪费内存。对于**元素很少的小对象**，用这种"重型"结构就太亏了。

所以 Redis 对小数据搞了一套**压缩编码（compact encoding）**，用**连续内存** + **紧凑布局**存储，省内存为首要目标，牺牲一点 O(1) 随机访问能力。

**什么时候用**（转换条件，元素少时自动切换）：

| 数据结构 | 触发 ziplist 的条件 |
|----------|--------------------|
| **List** | 元素个数 < **512** 且每个元素长度 < **64B**（`list-max-ziplist-size` / `list-max-ziplist-value`，6.0+ 改成了 quicklist） |
| **Hash** | 元素个数 < **512** 且每个 value 长度 < **64B** |
| **ZSet** | 元素个数 < **128** 且每个元素长度 < **64B** |

> 元素一旦超过阈值，就会**升级**成重型结构（listpack → dict/skiplist）。这个"少而小"的判定是 ziplist 的核心使用场景。

---

## 二、ziplist 的整体布局（连续内存块）

ziplist 本质是**一段连续的内存**，没有指针，通过**记录上一个节点的长度**来定位。整体结构：

```
<zlbytes><zltail><zllen><entry>...<entry><zlend>
```

| 字段 | 大小 | 说明 |
|------|------|------|
| **zlbytes** | 4字节 | 整个 ziplist 占用的字节数 |
| **zltail** | 4字节 | 表尾节点偏移量（便于从尾部倒序遍历） |
| **zllen** | 2字节 | 节点数量（超过 65535 时需遍历统计） |
| **entry** | 变长 | 若干个节点 |
| **zlend** | 1字节 | 结束标记（0xFF） |

**每个 entry 的结构**（核心）：

```
<prevlen><encoding><len><data>
```

| 字段 | 说明 |
|------|------|
| **prevlen** | 前一个节点的长度（用于从后往前遍历）。前节点 < 254B 用 1 字节存；≥ 254B 用 5 字节存（首字节 0xFE 标记） |
| **encoding** | 编码类型（标识 data 是整数还是字符串、多长） |
| **len** | 数据长度 |
| **data** | 实际数据（可存整数或字符串） |

**优点**：连续内存、无指针、内存紧凑 → **极省内存**，特别适合小对象、缓存大量小 value 的场景（如商品、用户信息）。

---

## 三、ziplist 的致命痛点：连锁更新（Cascade Update）⚠️

这是 ziplist 最著名的坑，也是它最终被 listpack 取代的根本原因。

### 问题来源
每个 entry 的 `prevlen` 记录**前一个节点的长度**，而 prevlen 的字节数是**动态的**：
- 前节点长度 < 254B → prevlen 占 **1 字节**
- 前节点长度 ≥ 254B → prevlen 占 **5 字节**（需要扩展）

### 连锁更新过程
1. 往 ziplist **中间插入**一个较大的节点（长度 ≥ 254B）。
2. 它后面的节点的 `prevlen` 原本是 1 字节，现在因为前节点变长 >254B，**需要扩展成 5 字节**。
3. 该节点自身变大了，又导致**它后面的节点**的 prevlen 也要扩展……
4. 于是**从插入点往后，一串节点都要重新分配内存、移动数据**，最坏情况是 O(N²) 的时间复杂度！

### 后果
- **插入 / 删除**大节点时，可能引发**大面积的内存重新分配和数据搬移**，**耗时暴涨**。
- 最坏情况下，Redis 单线程会因此**卡顿**，影响其他命令。

---

## 四、listpack：ziplist 的替代者（Redis 7.0）

为了解决连锁更新，Redis 7.0 用 **listpack** 全面替换了 ziplist（Hash 的 ziplist、ZSet 的 ziplist、List 的 quicklist 里的 ziplist 节点，全部换成 listpack）。

### listpack 与 ziplist 的关键区别

| 对比项 | ziplist | listpack |
|--------|---------|----------|
| 前向遍历方式 | 存 `prevlen`（前一个节点长度）→ 导致连锁更新 | **不存前一个节点长度**，反向遍历靠**从后往前算当前节点长度** |
| 连锁更新 | **有**（prevlen 变长引发） | **无**（节点之间不互相依赖长度） |
| entry 结构 | `<prevlen><encoding><len><data>` | `<encoding-type><element-data><element-total-len>` |
| 定位 | 用 prevlen 往前跳 | 每个节点自带 `element-total-len`（总长度），尾部标记结束 |
| 结论 | 紧凑但有隐患 | **紧凑且无连锁更新**，更安全 |

### listpack 的 entry 设计
```
<encoding-type><element-data><element-total-len>
```
- **element-total-len** 放在**末尾**，表示该节点总长度，用于**从后往前**遍历时定位上一个节点。
- 因为不依赖"前一个节点的长度"，所以**新增/删除节点时，其他节点的长度不受影响** → 从根源上消除了连锁更新。

> 📌 **一句话记忆**：ziplist 是"记住前面的人有多胖"，前面人一变肥，后面全要跟着长；listpack 是"不管前面，每个人自己带着总长度标记"，谁变肥都不影响别人。

---

## 五、ziplist 家族相关结构：quicklist 与 intset

### 1. quicklist（List 的底层，Redis 7.0 前）

- 老版本 List 底层用 **quicklist** =「双向链表 + 每个节点是一个 ziplist」的结合体。
- 每个 ziplist 节点存一小段连续数据，**兼顾了**链表（好插入删除、不用整体移动）和 ziplist（紧凑省内存）的优点。
- Redis 7.0 后，quicklist 里的 ziplist 节点也被**换成 listpack**。
- 好处：超大 List 不会被单个连续内存撑爆，插入删除只在局部 ziplist 内做，性能稳定。

### 2. intset（整数集合，Set 的底层之一）

- 当 Set 的元素**全是整数**且数量少时，用 **intset（整数集合）** 存储。
- 元素从小到大有序排列，用二分查找定位，**极省内存**（比哈希表省）。
- 超过阈值或出现非整数时，**升级**成哈希表（dict）。

---

## 六、数据结构小结：各结构底层编码

| 数据结构 | 小数据时 | 大数据时 | 说明 |
|----------|----------|----------|------|
| **String** | — | SDS | 动态字符串，几乎万能 |
| **List** | listpack（7.0 前 quicklist+ziplist） | quicklist | 7.0 后内层用 listpack |
| **Hash** | listpack（7.0 前 ziplist） | dict（哈希表） | 小对象紧凑，大对象转哈希 |
| **Set** | intset（全整数时） | dict | 整数小集合极省内存 |
| **ZSet** | listpack（7.0 前 ziplist） | skiplist + dict | 小对象紧凑，大对象转跳表 |

> 核心思想：**"少而小"用压缩编码省内存，"多而大"用快速结构保性能**，两者自动切换。

---

## 七、核心要点速记

- **ziplist**：连续内存的紧凑结构，没有指针，靠 prevlen 定位，**极省内存**，适合"元素少且小"的小对象。
- **触发条件**：Hash/List 元素 <512 且值 <64B，ZSet <128 且值 <64B，超了自动升级重型结构。
- **ziplist 布局**：`zlbytes | zltail | zllen | entries... | zlend`；entry = `prevlen | encoding | len | data`。
- **连锁更新（致命坑）**：prevlen 要记录前节点长度，插/删大节点会让后续一串节点 prevlen 变长 → 内存重分配 + 数据搬移，最坏 O(N²)，单线程会卡。
- **listpack（7.0 替代 ziplist）**：entry 末尾带 element-total-len，**不再依赖前节点长度** → 从根源消除连锁更新。
- **quicklist**：双向链表 + 每节点一段 listpack，List 的底层，兼顾插入删除与紧凑。
- **intset**：全整数小 Set 的紧凑存储，二分查找，升哈希。
- **总原则**：少而小用压缩编码省内存，多而大用快速结构保性能，自动切换。
