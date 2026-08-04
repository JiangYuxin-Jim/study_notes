# 不可变集合与 Stream 流基础

> JavaSE 进阶：不可变集合 · Stream 流的思想与获取
> 课程：黑马 JavaSE 进阶/高级（BV1yW4y1Y7Ms · P34-P36）

---

## 一、不可变集合

### 1.1 什么是不可变集合

不可变集合（Immutable Collection）指创建后**不能修改**的集合——不能添加、删除、修改元素。

**为什么需要？**
- 数据安全：方法返回不希望调用方修改的内部数据时
- 常量定义：固定数据（如星期、月份、省份列表等）
- 函数式编程：配合 Stream 使用时更安全

### 1.2 创建方式

JDK 9 引入了 `List.of()`、`Set.of()`、`Map.of()` 等静态工厂方法。

#### List 不可变集合

```java
// 方式一：of 方法
List<String> list = List.of("a", "b", "c", "d");
// list.add("e");      // ❌ UnsupportedOperationException
// list.remove("a");   // ❌ UnsupportedOperationException

// 方式二：copyOf（从已有集合复制）
List<String> original = new ArrayList<>(Arrays.asList("x", "y", "z"));
List<String> copied = List.copyOf(original);
```

#### Set 不可变集合

```java
Set<String> set = Set.of("a", "b", "c");
// Set.of 不能有重复元素，否则 IllegalArgumentException
```

#### Map 不可变集合

```java
// 最多 10 个键值对（of 的重载）
Map<String, Integer> map = Map.of("a", 1, "b", 2, "c", 3);

// 超过 10 个用 ofEntries
Map<String, Integer> map2 = Map.ofEntries(
    Map.entry("a", 1),
    Map.entry("b", 2),
    Map.entry("c", 3)
    // ...
);
```

### 1.3 注意事项

| 限制 | 说明 |
|------|------|
| 不能增删改 | add、remove、set、put 都会抛异常 |
| 不能有 null | of 方法的元素**不能为 null**，否则 NPE |
| Set 不能重复 | Set.of 传入重复元素抛 IllegalArgumentException |
| Map 不能重复 key | Map.of 传入重复 key 抛 IllegalArgumentException |
| copyOf 原集变化不影响 | 复制后不可变，原集合任意修改不影响副本 |

### 1.4 适用场景

```java
// 1. 固定常量
public static final List<String> WEEK_DAYS = List.of(
    "周一", "周二", "周三", "周四", "周五", "周六", "周日"
);

// 2. 方法返回安全数据
public List<String> getBlacklist() {
    return List.of("user1", "user2");   // 调用方无法修改
}

// 3. 配合 Stream
List<String> result = Stream.of("a", "b", "c")
    .filter(s -> s.startsWith("a"))
    .toList();   // 返回的就是不可变 List
```

---

## 二、Stream 流概述

### 2.1 为什么要用 Stream？

传统操作集合的方式：

```java
// 需求：从 List 中筛选出以"张"开头的元素，装到一个新集合
ArrayList<String> list = new ArrayList<>();
Collections.addAll(list, "张三", "李四", "张三丰", "王五", "张无忌");

// 传统方式
ArrayList<String> result = new ArrayList<>();
for (String name : list) {
    if (name.startsWith("张")) {
        result.add(name);
    }
}
System.out.println(result);   // [张三, 张三丰, 张无忌]
```

用 Stream 的方式：

```java
List<String> result = list.stream()
    .filter(name -> name.startsWith("张"))
    .collect(Collectors.toList());

System.out.println(result);   // [张三, 张三丰, 张无忌]
```

**Stream 流的优势：**
- **声明式编程：** 写"要什么"而不是"怎么做"
- **流水线操作：** 过滤 → 转换 → 收集，一行式解决
- **惰性求值：** 中间操作不立即执行，终结操作才触发
- **并行支持：** 一行代码 `.parallelStream()` 即可多线程处理

### 2.2 什么是 Stream

> Stream（流）是 JDK 8 引入的一种**函数式编程风格**的数据处理方式。

```
数据源（List/Set/数组/Map） → Stream → 中间操作（n个） → 终结操作
                                           ↓
                                     过滤/映射/去重/排序...
```

**三要素：**
1. **数据源** — 从哪里获取流
2. **中间操作** — 对数据进行处理（过滤、映射、排序等）
3. **终结操作** — 产生结果（收集到集合、遍历、统计等）

**特点：**
- Stream 不存储数据，只是对数据的操作视图
- Stream 不会修改数据源，操作结果产生新的流
- Stream 具有延迟执行特性（只有终结操作时才执行）

---

## 三、获取 Stream 的四种方式

### 3.1 单列集合：`Collection.stream()`

Collection 接口中的默认方法，List 和 Set 都能用。

```java
// List → Stream
List<String> list = new ArrayList<>();
Collections.addAll(list, "a", "b", "c");
Stream<String> stream1 = list.stream();

// Set → Stream
Set<String> set = new HashSet<>();
Collections.addAll(set, "x", "y", "z");
Stream<String> stream2 = set.stream();
```

### 3.2 双列集合：先转单列再 stream()

Map 没有直接的 stream() 方法，需要先获取键/值/键值对的集合。

```java
Map<String, Integer> map = new HashMap<>();
map.put("a", 1);
map.put("b", 2);
map.put("c", 3);

// 方式一：获取所有键
Stream<String> keyStream = map.keySet().stream();

// 方式二：获取所有值
Stream<Integer> valueStream = map.values().stream();

// 方式三：获取所有键值对（Entry）
Stream<Map.Entry<String, Integer>> entryStream = map.entrySet().stream();
```

### 3.3 数组：`Arrays.stream()` 或 `Stream.of()`

```java
// 方式一：Arrays.stream()
int[] arr1 = {1, 2, 3, 4, 5};
IntStream intStream = Arrays.stream(arr1);    // IntStream 是 int 类型的特化流

String[] arr2 = {"a", "b", "c"};
Stream<String> stringStream = Arrays.stream(arr2);

// 方式二：Stream.of() — 更推荐，自动识别数组
Stream<String> stream3 = Stream.of(arr2);
```

### 3.4 零散数据：`Stream.of()`

```java
// 传入零散数据
Stream<String> stream = Stream.of("a", "b", "c", "d");

// 不限定类型
Stream<Object> mixed = Stream.of(1, "hello", 3.14);
```

**📌 注意：** `Stream.of(T... values)` 既可以传零散数据也可以传数组，但如果是基本类型数组：

```java
int[] arr = {1, 2, 3};
Stream<int[]> stream = Stream.of(arr);   // ❌ 错误！会把整个数组当成一个元素

// 正确用法
IntStream stream = Arrays.stream(arr);   // ✅ 用 Arrays.stream()
```

---

## 四、Stream 流水线模式

### 4.1 操作分类

```
                  数据源
                    │
              Stream 流诞生
                    │
    ┌───────────────┼───────────────┐
    │               │               │
  中间操作         中间操作       中间操作
(filter/map/     (sorted/)      (distinct/)
 sort/distinct)   limit/skip     map
    │               │               │
    └───────────────┼───────────────┘
                    │
                 终结操作
            (collect/forEach/
              count/max/min)
                    │
             最终结果（集合/数值/遍历）
```

**中间操作（Intermediate）：** 返回 Stream 本身，可以链式调用，惰性执行
**终结操作（Terminal）：** 返回最终结果或副作用，触发流水线执行

```java
// 链式调用示例
list.stream()                          // 1. 获取流
    .filter(s -> s.startsWith("张"))    // 2. 中间：过滤（惰性）
    .filter(s -> s.length() == 3)      // 3. 中间：再过滤（惰性）
    .forEach(System.out::println);     // 4. 终结：遍历（触发执行）
```

### 4.2 第一个完整的 Stream 示例

```java
// 需求：从列表中筛选姓张且长度为3的名字，输出
ArrayList<String> list = new ArrayList<>();
Collections.addAll(list, "张三", "李四", "张三丰", "王五", "张无忌", "张飞");

list.stream()                      // 获取流
    .filter(name -> name.startsWith("张"))   // 筛选姓张
    .filter(name -> name.length() == 3)      // 筛选三字名
    .forEach(name -> System.out.println(name)); // 输出

// 输出：张三丰  张无忌
```

---

## 总结

| 知识点 | 核心要点 |
|--------|----------|
| 不可变集合 | `List.of()` `Set.of()` `Map.of()`，不能增删改、不能 null |
| copyOf | 从可变集合创建不可变副本，原集变化不影响副本 |
| Stream 概念 | 函数式数据处理方式，声明式编程，惰性求值 |
| 获取方式 | 单列 `stream()`、Map 转 `keySet/values/entrySet` 再 stream、数组 `Arrays.stream()` 或 `Stream.of()` |
| 流水线 | 数据源 → 中间操作（惰性）→ 终结操作（触发执行） |

**下一节预告：** Stream 流中间方法（filter/map/sorted/distinct/limit/skip）和终结方法（forEach/count/collect/max/min）。
