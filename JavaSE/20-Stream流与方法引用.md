# Stream 流进阶与方法引用

> JavaSE 进阶：Stream 流的中间/终结操作 · collect 收集 · 方法引用
> 课程：黑马 JavaSE 进阶/高级（BV1yW4y1Y7Ms · P37-P50）

---

## 一、Stream 流中间方法

中间方法返回新的 Stream 流，可以继续链式调用。

### 1.1 filter - 过滤

```java
List<String> list = List.of("张三丰","张无忌","张翠山","王麻子","谢广坤");
list.stream().filter(s -> s.startsWith("张"))
             .filter(s -> s.length() == 3)
             .forEach(System.out::println);
// 输出：张三丰 张无忌
```

### 1.2 limit - 截取前 n 个

```java
list.stream().limit(3).forEach(System.out::println);
// 张三丰 张无忌 张翠山
```

### 1.3 skip - 跳过前 n 个

```java
list.stream().skip(2).forEach(System.out::println);
// 张翠山 王麻子 谢广坤
```

### 1.4 distinct - 去重（依赖 hashCode 和 equals）

```java
List<Integer> nums = List.of(1,2,3,4,5,1,2,3);
nums.stream().distinct().forEach(System.out::println);
// 1 2 3 4 5
```

### 1.5 map - 转换元素类型

```java
List<String> list = List.of("10","20","30","40","50");
list.stream().map(Integer::parseInt).forEach(System.out::println);
// 10 20 30 40 50（int 类型）
```

### 1.6 concat - 合并两个流

```java
Stream.concat(list1.stream(), list2.stream()).forEach(System.out::println);
```

> **注意：** 中间方法只是声明操作，不会真正执行。只有调用了终结方法，整个流水线才触发（**惰性求值**）。

---

## 二、Stream 流终结方法

终结方法执行后，流水线结束，Stream 不再可用。

### 2.1 forEach - 遍历

```java
list.stream().forEach(s -> System.out.println(s));
```

### 2.2 count - 统计个数

```java
long count = list.stream().filter(s -> s.length() == 3).count();
```

### 2.3 max / min - 最大/最小值

```java
// 取最大年龄
Optional<Integer> max = ages.stream().max((a,b) -> a - b);
```

### 2.4 toArray - 收集到数组

```java
String[] arr = list.stream().toArray(String[]::new);
```

### 2.5 collect - 收集到集合（详见第三节）

---

## 三、collect 收集方法详解

`collect` 是 Stream 的终结方法，将流中元素收集到集合中。

### 3.1 收集到 List

```java
List<String> list = stream.collect(Collectors.toList());

// 收集到不可变 List
List<String> list2 = stream.collect(Collectors.toUnmodifiableList());
```

### 3.2 收集到 Set

```java
Set<String> set = stream.collect(Collectors.toSet());

// 收集到不可变 Set
Set<String> set2 = stream.collect(Collectors.toUnmodifiableSet());
```

### 3.3 收集到 Map

```java
// 键为姓名，值为年龄
Map<String, Integer> map = list.stream()
    .collect(Collectors.toMap(
        s -> s.getName(),   // key 提取
        s -> s.getAge()     // value 提取
    ));
```

### 3.4 收集到指定集合（如 ArrayList）

```java
ArrayList<String> arr = stream.collect(Collectors.toCollection(ArrayList::new));
```

### 3.5 分组收集

```java
// 按姓名分组
Map<String, List<Student>> map = list.stream()
    .collect(Collectors.groupingBy(Student::getName));

// 分组并统计每组个数
Map<String, Long> countMap = list.stream()
    .collect(Collectors.groupingBy(Student::getName, Collectors.counting()));
```

### 3.6 下游收集器

```java
// 分组后收集到 Set
Map<String, Set<String>> map = list.stream()
    .collect(Collectors.groupingBy(
        Student::getName,
        Collectors.mapping(Student::getAddress, Collectors.toSet())
    ));
```

---

## 四、Stream 流综合练习

### 练习 1：筛选过滤并收集

```java
// 筛选出姓张的、长度为3的，收集到 List
List<String> result = list.stream()
    .filter(s -> s.startsWith("张"))
    .filter(s -> s.length() == 3)
    .collect(Collectors.toList());
```

### 练习 2：自定义对象筛选

```java
// 筛选年龄 18-40 之间的男演员，存到集合
List<Actor> result = actorList.stream()
    .filter(a -> a.getAge() >= 18 && a.getAge() <= 40)
    .filter(a -> "男".equals(a.getSex()))
    .collect(Collectors.toList());
```

---

## 五、方法引用

方法引用是 Lambda 表达式的**语法糖**，让代码更简洁。
格式：`类名/对象 :: 方法名`

### 5.1 引用静态方法

```java
// 格式：类名::静态方法名
list.stream().map(Integer::parseInt);        // 相当于 s -> Integer.parseInt(s)
list.stream().max(Integer::compare);         // 相当于 (a,b) -> Integer.compare(a,b)
```

### 5.2 引用成员方法

有两种格式：

**引用其他对象的成员方法：**

```java
// 格式：对象::方法名
StringBuilder sb = new StringBuilder();
list.stream().forEach(sb::append);           // 相当于 s -> sb.append(s)
```

**引用本类或父类的成员方法：**

```java
// 格式：this::方法名（只能在非静态方法中使用）
this.list.stream().forEach(this::print);     // 相当于 s -> this.print(s)

// 格式：super::方法名
super.list.stream().forEach(super::print);
```

### 5.3 引用构造方法

```java
// 格式：类名::new
Student s = nameStream.map(Student::new).collect(Collectors.toList());
// 相当于 name -> new Student(name)
```

### 5.4 类名引用成员方法

```java
// 格式：类名::方法名
list.stream().map(String::toUpperCase);      // 相当于 s -> s.toUpperCase()
list.stream().map(Student::getName);         // 相当于 s -> s.getName()
```

### 5.5 引用数组的构造方法

```java
// 格式：类型[]::new
String[] arr = list.stream().toArray(String[]::new);
// 相当于 length -> new String[length]
```

### 5.6 方法引用练习

**练习 1：转换并收集到数组**

```java
// 字符串集合 → 自定义对象数组
Student[] arr = list.stream()
    .map(Student::new)
    .toArray(Student[]::new);
```

**练习 2：提取属性并收集到数组**

```java
// 提取姓名属性到数组
String[] names = students.stream()
    .map(Student::getName)
    .toArray(String[]::new);
```

---

## 六、要点总结

| 分类 | 方法 | 说明 |
|------|------|------|
| 中间方法 | filter | 过滤，保留符合条件的元素 |
| | limit / skip | 截取/跳过前 n 个 |
| | distinct | 去重（需重写 hashCode/equals） |
| | map | 类型转换 |
| | concat | 合并两个流 |
| 终结方法 | forEach | 遍历 |
| | count | 计数 |
| | max / min | 最大/最小值 |
| | collect | 收集到集合 |
| | toArray | 收集到数组 |
| 方法引用 | 类名::静态方法 | `Integer::parseInt` |
| | 对象::成员方法 | `sb::append` |
| | 类名::new | `Student::new` |
| | 类名::成员方法 | `String::toUpperCase` |
| | 类型[]::new | `String[]::new` |

---

> **下一篇预告：** 异常体系 · File · IO 流基础
