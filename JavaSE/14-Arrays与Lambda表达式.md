# Arrays 与 Lambda 表达式

> JavaSE 上部（189 集附近内容）
> 课程：黑马 JavaSE 入门到起飞（BV17F411T7Ao）

---

## 一、Arrays 工具类

`java.util.Arrays` 是 Java 提供的一个操作数组的工具类，包含大量静态方法。

### 1.1 常用方法

| 方法 | 说明 |
|------|------|
| `toString(数组)` | 将数组转为字符串格式 |
| `sort(数组)` | 对数组进行排序（默认升序） |
| `sort(数组, fromIndex, toIndex)` | 对指定范围排序 |
| `binarySearch(数组, 元素)` | 二分查找（必须先排序） |
| `copyOf(原数组, 新长度)` | 拷贝数组，新长度可截断或补默认值 |
| `copyOfRange(数组, from, to)` | 拷贝指定范围 |
| `equals(数组1, 数组2)` | 比较两个数组内容是否相等 |
| `fill(数组, 值)` | 用指定值填充数组 |
| `asList(T... a)` | 将数组转为 List（固定长度） |

### 1.2 基本使用示例

```java
import java.util.Arrays;

public class ArraysDemo {
    public static void main(String[] args) {
        int[] arr = {5, 2, 8, 1, 9, 3};
        
        // toString
        System.out.println(Arrays.toString(arr));   // [5, 2, 8, 1, 9, 3]
        
        // 排序
        Arrays.sort(arr);
        System.out.println(Arrays.toString(arr));   // [1, 2, 3, 5, 8, 9]
        
        // 二分查找（必须先排序）
        int index = Arrays.binarySearch(arr, 5);
        System.out.println("5 的索引：" + index);     // 3
        
        // copyOf
        int[] newArr = Arrays.copyOf(arr, 10);
        System.out.println(Arrays.toString(newArr)); // [1, 2, 3, 5, 8, 9, 0, 0, 0, 0]
    }
}
```

### 1.3 注意点

- `binarySearch` 必须先排序，否则结果不可预测
- 如果找不到元素，返回 `-(插入点) - 1`
- `asList` 返回的 List 不可变（不能 `add` / `remove`），但可以 `set`
- 排序会改变原数组

---

## 二、Lambda 表达式

### 2.1 什么是 Lambda

Lambda 是 Java 8 引入的函数式编程特性，允许把**函数**作为方法的参数传递。

### 2.2 基础语法

```
(参数列表) -> { 方法体 }
```

- `->` 被称为箭头操作符或 Lambda 操作符
- 左侧：参数列表（可省略参数类型）
- 右侧：方法体

### 2.3 简化规则

| 情况 | 写法 |
|------|------|
| 无参数 | `() -> System.out.println("Hi")` |
| 单参数 | `x -> x * 2`（省略括号） |
| 多参数 | `(a, b) -> a + b` |
| 方法体单行 | 省略 `{}` 和 `return` |
| 方法体多行 | 必须加 `{}` 和 `return` |

### 2.4 实际案例：排序

**匿名内部类方式：**
```java
Integer[] arr = {5, 2, 8, 1, 9};

Arrays.sort(arr, new Comparator<Integer>() {
    @Override
    public int compare(Integer o1, Integer o2) {
        return o2 - o1;  // 降序
    }
});
```

**Lambda 方式：**
```java
Arrays.sort(arr, (o1, o2) -> o2 - o1);
```

完整示例：

```java
import java.util.Arrays;

public class LambdaDemo {
    public static void main(String[] args) {
        Integer[] arr = {5, 2, 8, 1, 9, 3};
        
        // Lambda 降序排序
        Arrays.sort(arr, (Integer o1, Integer o2) -> {
            return o2 - o1;
        });
        
        // 进一步简化
        Arrays.sort(arr, (o1, o2) -> o2 - o1);
        
        System.out.println(Arrays.toString(arr));  // [9, 8, 5, 3, 2, 1]
    }
}
```

### 2.5 函数式接口

Lambda 表达式只能用于**函数式接口**——即只有一个抽象方法的接口。

Java 内置的常用函数式接口：

| 接口 | 方法 | 用途 |
|------|------|------|
| `Runnable` | `run()` | 无参无返回值 |
| `Comparator<T>` | `compare(T, T)` | 比较两个对象 |
| `Consumer<T>` | `accept(T)` | 消费一个参数 |
| `Supplier<T>` | `get()` | 供应一个返回值 |
| `Function<T,R>` | `apply(T)` | 输入 T 输出 R |
| `Predicate<T>` | `test(T)` | 条件判断 |

示例：

```java
// Consumer：打印每个元素
Arrays.asList("A", "B", "C").forEach(s -> System.out.println(s));
```

---

## 三、Comparator 排序进阶

### 3.1 自然排序 vs 比较器排序

- **自然排序（Comparable）**：类实现 `Comparable` 接口，定义自身比较规则
- **比较器排序（Comparator）**：单独定义一个比较器，不改变原类

### 3.2 使用 Comparator 排序对象数组

```java
public class Student {
    private String name;
    private int age;
    private double score;
    
    // 构造、getter、setter 省略...
}

// 按成绩降序
Arrays.sort(students, (s1, s2) -> Double.compare(s2.getScore(), s1.getScore()));

// 按年龄升序，年龄相同按名字字典序
Arrays.sort(students, (s1, s2) -> {
    int ageDiff = s1.getAge() - s2.getAge();
    if (ageDiff != 0) return ageDiff;
    return s1.getName().compareTo(s2.getName());
});
```

### 3.3 方法引用（Lambda 的进阶形式）

当 Lambda 体只是调用一个已有方法时，可以用方法引用：

```java
// Lambda
list.forEach(s -> System.out.println(s));

// 方法引用
list.forEach(System.out::println);
```

方法引用类型：

| 类型 | 语法 | 示例 |
|------|------|------|
| 静态方法引用 | `类名::静态方法` | `Math::max` |
| 实例方法引用 | `对象::实例方法` | `this::print` |
| 特定类方法引用 | `类名::实例方法` | `String::length` |
| 构造器引用 | `类名::new` | `Student::new` |

---

## 四、综合练习

使用 Lambda + Arrays 对自定义对象排序：

```java
import java.util.Arrays;

public class Practice {
    public static void main(String[] args) {
        Student[] students = {
            new Student("张三", 22, 85.5),
            new Student("李四", 20, 92.0),
            new Student("王五", 22, 88.0),
            new Student("赵六", 21, 85.5)
        };
        
        // 需求：按成绩降序→成绩相同按年龄升序→年龄相同按姓名升序
        Arrays.sort(students, (s1, s2) -> {
            int scoreDiff = Double.compare(s2.getScore(), s1.getScore());
            if (scoreDiff != 0) return scoreDiff;
            int ageDiff = s1.getAge() - s2.getAge();
            if (ageDiff != 0) return ageDiff;
            return s1.getName().compareTo(s2.getName());
        });
        
        for (Student s : students) {
            System.out.println(s);
        }
    }
}
```

---

**总结：**
- Arrays 工具类提供了 `sort`、`binarySearch`、`copyOf`、`toString` 等快捷操作
- Lambda 简化了匿名内部类的写法，使代码更简洁
- 结合 Arrays.sort + Comparator Lambda 可以灵活排序各种对象数组
- 方法引用是 Lambda 的语法糖，让代码更简洁优雅
