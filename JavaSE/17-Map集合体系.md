# Map 集合体系

> JavaSE 进阶：双列集合 · Map · HashMap/TreeMap
> 课程：黑马 JavaSE 进阶/高级（BV1yW4y1Y7Ms）

---

## 一、双列集合概述

### 1.1 为什么需要双列集合

之前学的 Collection 都是单列集合（List / Set），存储的是单个元素。但实际开发中经常需要存储**键值对**（key-value）关系的数据，比如：

- 学号 → 学生信息
- 商品ID → 商品详情
- 用户名 → 密码

双列集合的核心是 **键（Key）** 和 **值（Value）** 的映射关系。

### 1.2 双列集合的特点

| 特性 | 说明 |
|------|------|
| 存储方式 | 键值对（Key-Value） |
| 键的唯一性 | **键不能重复**，值可以重复 |
| 数据结构 | 每个键值对叫一个 Entry，Set 存 Key，Collection 存 Value |
| 主要实现 | HashMap、LinkedHashMap、TreeMap、Hashtable |

### 1.3 Map 体系结构

```
Map (接口)
├── HashMap（最常用，无序，允许 null）
│   └── LinkedHashMap（有序，双向链表维护插入顺序）
├── TreeMap（排序，红黑树，键自然排序或自定义比较器）
└── Hashtable（线程安全，不允许 null，已过时）
    └── Properties（配置文件专用）
```

---

## 二、Map 常用 API

### 2.1 创建 Map

```java
// 键为 String，值为 Integer
Map<String, Integer> map = new HashMap<>();
```

### 2.2 常用方法

| 方法 | 说明 |
|------|------|
| `put(K key, V value)` | 添加元素（键存在则覆盖旧值） |
| `remove(Object key)` | 根据键删除键值对 |
| `clear()` | 清空 |
| `containsKey(Object key)` | 判断是否包含某个键 |
| `containsValue(Object value)` | 判断是否包含某个值 |
| `isEmpty()` | 判断是否为空 |
| `size()` | 获取键值对个数 |

```java
Map<String, Integer> map = new HashMap<>();

// 添加元素
map.put("张三", 88);
map.put("李四", 95);
map.put("王五", 72);

// 键存在时覆盖旧值
map.put("张三", 90);    // 张三的值变为 90

// 删除
map.remove("王五");

// 判断
System.out.println(map.containsKey("张三"));   // true
System.out.println(map.containsValue(95));     // true

// 大小
System.out.println(map.size());               // 2
```

### 2.3 注意事项

- put 返回**被覆盖的旧值**（如果没有旧值返回 null）
- HashMap 允许 key 和 value 均为 null
- key 不能重复，如果重复添加，后覆盖前

---

## 三、Map 的三种遍历方式

### 3.1 方式一：键找值（keySet）

先获取所有键的集合（Set），再通过键获取值。

```java
Map<String, Integer> map = new HashMap<>();
map.put("A", 1);
map.put("B", 2);
map.put("C", 3);

// 1. 获取所有键
Set<String> keys = map.keySet();

// 2. 遍历键，获取值
for (String key : keys) {
    int value = map.get(key);
    System.out.println(key + " = " + value);
}
```

**特点：** 简单直观，但需要 get 查询两次（keySet 一次 + 取 value 一次）。

### 3.2 方式二：键值对（entrySet）

获取所有键值对对象（Set<Entry>），直接获取 key 和 value。

```java
// 1. 获取所有键值对对象
Set<Map.Entry<String, Integer>> entries = map.entrySet();

// 2. 遍历
for (Map.Entry<String, Integer> entry : entries) {
    String key = entry.getKey();
    int value = entry.getValue();
    System.out.println(key + " = " + value);
}
```

**特点：** 稍复杂一点，但效率更高（不需要二次查询）。

### 3.3 方式三：Lambda 表达式（forEach）

Java 8 提供的 Lambda 方式，最简洁。

```java
map.forEach((key, value) -> {
    System.out.println(key + " = " + value);
});

// 单行可省略大括号
map.forEach((k, v) -> System.out.println(k + " = " + v));
```

**参数说明：** `forEach` 接收一个 `BiConsumer<? super K, ? super V>` 接口，即两个参数的 Consumer。

### 3.4 三种方式对比

| 方式 | 语法 | 推荐场景 |
|------|------|----------|
| `keySet` + `get` | 最传统，易理解 | 只需要键，或简单遍历 |
| `entrySet` | 一次获取全部 | 需要同时拿键值，性能更好 |
| `forEach(Lambda)` | 最简洁 | 日常开发首选 |

---

## 四、HashMap

### 4.1 基本使用

```java
Map<String, String> map = new HashMap<>();
map.put("001", "张三");
map.put("002", "李四");
map.put("003", "王五");
```

### 4.2 存储自定义对象作为键

当使用自定义对象作为 HashMap 的 **键** 时，**必须重写 hashCode 和 equals 方法**，否则即使属性相同也会被视为不同对象。

```java
public class Student {
    private String name;
    private int age;
    
    public Student(String name, int age) {
        this.name = name;
        this.age = age;
    }
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Student student = (Student) o;
        return age == student.age && Objects.equals(name, student.name);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(name, age);
    }
    
    // getter / setter / toString 省略
}

// 使用自定义对象作为 key
Map<Student, String> map = new HashMap<>();
map.put(new Student("张三", 20), "北京");
map.put(new Student("李四", 22), "上海");
map.put(new Student("张三", 20), "广州");    // 会覆盖第一个张三，因为 hashCode 和 equals 相同
```

### 4.3 利用 Map 进行统计

Map 最常见的应用场景之一——**统计计数**。

```java
// 统计每个字符出现的次数
String str = "aababcabcdabcde";
Map<Character, Integer> countMap = new HashMap<>();

for (int i = 0; i < str.length(); i++) {
    char c = str.charAt(i);
    
    // 方式一：传统 if-else
    if (countMap.containsKey(c)) {
        countMap.put(c, countMap.get(c) + 1);
    } else {
        countMap.put(c, 1);
    }
    
    // 方式二：getOrDefault 简化
    // countMap.put(c, countMap.getOrDefault(c, 0) + 1);
}

System.out.println(countMap);
// 输出：{a=5, b=4, c=3, d=2, e=1}
```

**`getOrDefault` 方法：** 如果键存在返回值，不存在返回默认值，非常适合统计场景。

---

## 五、LinkedHashMap

### 5.1 特点

- 继承自 `HashMap`
- 底层多了一个**双向链表**维护**插入顺序**
- 迭代顺序 = 存入顺序（和 HashMap 的随机顺序不同）

### 5.2 使用

```java
Map<String, Integer> map = new LinkedHashMap<>();
map.put("A", 1);
map.put("B", 2);
map.put("C", 3);

System.out.println(map);  // {A=1, B=2, C=3} 保持插入顺序
```

### 5.3 HashMap vs LinkedHashMap

| 特性 | HashMap | LinkedHashMap |
|------|---------|---------------|
| 迭代顺序 | 无序（取决于哈希值） | 保持插入顺序 |
| 底层 | 数组+链表+红黑树 | 数组+链表+红黑树+双向链表 |
| 性能 | 略快 | 略慢（维护链表） |
| 适用场景 | 不关心顺序 | 需要保持插入顺序 |

---

## 六、TreeMap

### 6.1 特点

- 底层是**红黑树**
- **键会按自然顺序或自定义比较器排序**
- 键不能为 null（会抛 NPE）

### 6.2 基本使用

```java
// 默认按自然顺序（升序）
Map<Integer, String> map = new TreeMap<>();
map.put(3, "C");
map.put(1, "A");
map.put(2, "B");

System.out.println(map);   // {1=A, 2=B, 3=C} 自动排序
```

### 6.3 自定义对象作为键

自定义对象要实现 `Comparable` 接口，或者在创建 TreeMap 时传入 `Comparator`。

**方式一：HashMap 和 TreeMap 的区别**

如果键是自定义对象：

| Map 实现 | 去重依据 | 要求 |
|----------|---------|------|
| HashMap | `hashCode()` + `equals()` | 必须重写这两个方法 |
| TreeMap | `compareTo()` / `compare()` | 实现 Comparable 或传入 Comparator |

**方式二：传入 Comparator**

```java
// 按年龄升序
Map<Student, String> map = new TreeMap<>((s1, s2) -> {
    int ageDiff = s1.getAge() - s2.getAge();
    if (ageDiff != 0) return ageDiff;
    return s1.getName().compareTo(s2.getName());
});
```

### 6.4 TreeMap 统计练习

```java
// 统计字符串中每个字符出现的次数，并按字母顺序输出
String str = "aababcabcdabcde";
Map<Character, Integer> map = new TreeMap<>();

for (int i = 0; i < str.length(); i++) {
    char c = str.charAt(i);
    map.put(c, map.getOrDefault(c, 0) + 1);
}

System.out.println(map);
// 输出：{a=5, b=4, c=3, d=2, e=1} 自动按字母排序
```

---

## 七、HashMap 源码解析

### 7.1 核心数据结构

HashMap 底层是 **数组 + 链表 + 红黑树**。

```
数组（Node<K,V>[] table）
├── 每个元素是一个桶（bucket）
├── 默认长度 16
├── 装填因子（loadFactor）默认 0.75
└── 当元素个数 > 数组长度 × 0.75 时扩容（2 倍）
```

```
数组索引
┌──┬──┬──┬──┬──┬──┬──┬──┐
│  │  │K3→K7│  │  │K5│  │  │  ...
└──┴──┴─┼┴──┴──┴──┴──┴──┘
         ├── 链表（长度>8 → 红黑树）
```

### 7.2 存储过程（put）

```
put(key, value)
  │
  ├── 1. 计算 key 的 hashCode()
  │
  ├── 2. 二次哈希：hash = (h >>> 16) ^ h
  │     让高 16 位也参与索引计算，减少 hash 碰撞
  │
  ├── 3. 计算数组索引：index = (n - 1) & hash
  │
  ├── 4. 如果该位置为 null → 直接存入
  │
  ├── 5. 如果该位置不为 null：
  │     ├── 判断 key 是否 equals → 相同则覆盖
  │     ├── 判断是否是红黑树节点 → 红黑树插入
  │     └── 遍历链表查找：
  │           ├── 找到相同 key → 覆盖
  │           └── 没找到 → 尾部插入
  │               └── 链表长度 >= 8 且 数组长度 >= 64 → 转红黑树
  │
  └── 6. 元素总数 >= threshold（容量 × loadFactor）→ 扩容
```

### 7.3 获取过程（get）

```
get(key)
  │
  ├── 1. 计算 hash 和索引
  │
  ├── 2. 如果数组位置为 null → 返回 null
  │
  ├── 3. 如果第一个节点匹配 → 直接返回
  │
  ├── 4. 如果下个节点不为 null：
  │     ├── 红黑树节点 → 红黑树查找
  │     └── 链表节点 → 遍历链表查找
  └── 5. 没找到 → 返回 null
```

### 7.4 扩容机制（resize）

当元素数量 >= `threshold = 容量 × loadFactor` 时触发扩容。

**扩容流程：**
1. 新数组 = 原数组长度 × 2
2. 重新计算所有元素的索引位置
3. 如果原桶中是链表：
   - 根据位运算将节点分为"低位链表"和"高位链表"
   - 低位链表保持在原索引，高位链表移动到「原索引 + 原容量」
4. 如果原桶中是红黑树：
   - 拆分为两个小树或退化回链表

**为什么扩容后新索引是「原索引」或「原索引 + 原容量」？**

因为扩容后 `n` 变成 `2n`，`(2n - 1) & hash` 相当于在原来基础上多看一位：

```
原数组长度 n=16：  index = (16-1) & hash = 1111 & hash
扩容后长度 32：    index = (32-1) & hash = 11111 & hash
  
差别在于第 5 位（二进制）。
如果第 5 位是 0 → 索引不变
如果第 5 位是 1 → 新索引 = 原索引 + 16（原容量）
```

### 7.5 JDK 7 vs JDK 8 的区别

| 对比项 | JDK 7 | JDK 8 |
|--------|-------|-------|
| 数据结构 | 数组 + 链表 | 数组 + 链表 + 红黑树 |
| 链表插入 | 头插法（死锁风险） | 尾插法 |
| hash 计算 | 复杂多次扰动 | 一次扰动 |
| 扩容 rehash | 全部重新计算 | 不需 rehash，位运算判断 |

---

## 八、TreeMap 源码解析

### 8.1 核心数据结构

TreeMap 底层是 **红黑树（Red-Black Tree）**，一种自平衡的二叉查找树。

红黑树五大性质：
1. 每个节点是红色或黑色
2. 根节点是黑色
3. 叶子节点（NIL）是黑色
4. 红色节点的子节点必须是黑色（不能有两个连续的红色节点）
5. 任意节点到其所有叶子节点的路径上，黑色节点数量相同

### 8.2 put 流程

```
put(key, value)
  │
  ├── 1. 如果根节点为 null → 创建根节点，返回
  │
  ├── 2. 从根开始比较：
  │     ├── compare(key, node.key) < 0 → 走左子树
  │     ├── compare(key, node.key) > 0 → 走右子树
  │     └── compare == 0 → 覆盖旧值
  │
  ├── 3. 找到插入位置（叶子节点下），插入新节点（红色）
  │
  └── 4. 红黑树修复（fixAfterInsertion）：
        ├── 父节点是黑色 → 直接结束
        └── 父节点是红色（冲突）：
              ├── 叔叔节点也是红色 → 颜色翻转
              ├── 叔叔节点是黑色 → 旋转 + 变色
              └── 具体：LL / LR / RL / RR 旋转
```

### 8.3 旋转操作

**左旋（RR 情况）：**

```
    黑 P                   黑 R
   /  \                  /    \
  A   红 R      →       红 P   E
      /  \             /  \
     C   红 E          A    C
```

**右旋（LL 情况）：**

```
        黑 P               黑 L
       /  \              /    \
    红 L   D      →     A    红 P
    /  \                    /   \
   A   红 R               红 R   D
```

### 8.4 get 流程

```
get(key) — 二分查找
  │
  ├── 从根节点开始
  ├── compare(key, node.key) < 0 → 左子树
  ├── compare(key, node.key) > 0 → 右子树
  └── compare == 0 → 返回 node.value
```

**时间复杂度：** O(log n) — 红黑树的高度不超过 2log(n+1)

---

## 九、HashMap 与 TreeMap 对比

| 特性 | HashMap | TreeMap |
|------|---------|---------|
| 底层数据结构 | 数组+链表+红黑树 | 红黑树 |
| 元素顺序 | 无序 | 有序（自然/比较器） |
| 时间复杂度 | 平均 O(1)，最坏 O(log n) | O(log n) |
| 空间开销 | 较大（数组预留） | 较小 |
| 允许 null 键 | ✔ 允许 | ❌ 不允许（NPE） |
| 自定义类作为键 | 需重写 hashCode+equals | 需实现 Comparable 或传 Comparator |
| 适用场景 | 快速存取，不关心顺序 | 需要排序，或范围查询 |

---

## 总结

- **Map** 是双列集合的核心接口，存储键值对，键不可重复
- **三种遍历方式**：keySet → entrySet → forEach(Lambda)，后者最简洁
- **HashMap** 底层用数组+链表+红黑树，put 过程涉及 hash 计算、碰撞处理、扩容
- **LinkedHashMap** 保持插入顺序，多了一个双向链表
- **TreeMap** 底层红黑树，自动排序，适合需要有序键的场景
- 统计计数是 Map 最经典的应用场景，结合 `getOrDefault` 更简洁
