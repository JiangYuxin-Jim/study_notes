# 08 - 字符串 (String)

## 1. String 概述

### 1.1 什么是字符串？

`java.lang.String` 类代表字符串。Java 程序中所有的字符串字面量（如 `"Hello"`）都是 String 类的实例。

```java
String s1 = "Hello";           // 直接赋值
String s2 = new String("Hello");  // 通过构造方法
```

### 1.2 String 的特点

| 特点 | 说明 |
|------|------|
| **不可变性** | String 一旦创建，内容不可改变（底层是 `private final byte[] value`） |
| **不可继承** | String 类被 `final` 修饰，不能被继承 |
| **序列化** | 实现了 `Serializable`，可以读写到文件/网络 |
| **可比较** | 实现了 `Comparable`，支持字符串比较 |

---

## 2. 创建 String 的两种方式

### 2.1 直接赋值（推荐）

```java
String s1 = "Hello";
String s2 = "Hello";
```

### 2.2 通过构造方法

```java
String s1 = new String();                     // 空字符串 ""
String s2 = new String("Hello");              // 传入字符串字面量
char[] chs = {'H', 'e', 'l', 'l', 'o'};
String s3 = new String(chs);                  // 传入字符数组 "Hello"
byte[] bytes = {72, 101, 108, 108, 111};
String s4 = new String(bytes);                // 传入字节数组 "Hello"
```

### 2.3 两种方式的区别（内存分析）

```java
// 方式 1：直接赋值
String s1 = "Hello";
String s2 = "Hello";
// s1 == s2 → true（指向字符串常量池中同一个对象）

// 方式 2：new 对象
String s3 = new String("Hello");
String s4 = new String("Hello");
// s3 == s4 → false（堆中两个不同对象）
```

```
内存结构：

┌──────────────────────────────────────────────────┐
│ 堆内存                                           │
│                              ┌──────────────┐    │
│  字符串常量池                  │ Hello        │    │
│  (String Table)              └──────────────┘    │
│                                  ↑               │
│                              s1 / s2 指向这里     │
│                                                  │
│  ┌────────────────────┐   ┌──────────────────┐   │
│  │ String 对象 #3      │   │ String 对象 #4    │   │
│  │ value ───────→"Hello"│   │ value ───────→"Hello"│
│  │ (指向常量池的引用)   │   │ (指向常量池的引用)   │   │
│  └────────────────────┘   └──────────────────┘   │
│       ↑ s3                       ↑ s4            │
└──────────────────────────────────────────────────┘
```

> **结论**：直接赋值会复用常量池中的对象，`new String()` 每次都会在堆中创建新对象。**推荐使用直接赋值。**

---

## 3. 字符串的比较

### 3.1 `==` 比较的是什么？

- **基本类型**：比较值
- **引用类型**：比较地址值（是否指向同一个对象）

```java
String s1 = "Hello";
String s2 = "Hello";
String s3 = new String("Hello");

System.out.println(s1 == s2);   // true（常量池中同一个对象）
System.out.println(s1 == s3);   // false（堆中新对象）
```

### 3.2 `equals()` — 比较内容

```java
String s1 = "Hello";
String s2 = new String("Hello");

System.out.println(s1.equals(s2));      // true（比较内容）
System.out.println(s1.equals("HELLO")); // false（区分大小写）
System.out.println(s1.equalsIgnoreCase("HELLO")); // true（忽略大小写）
```

### 3.3 练习：模拟用户登录

```java
import java.util.Scanner;

public class LoginDemo {
    public static void main(String[] args) {
        // 假设数据库中保存的用户名和密码
        String correctUsername = "admin";
        String correctPassword = "123456";

        Scanner sc = new Scanner(System.in);

        for (int i = 3; i > 0; i--) {
            System.out.print("请输入用户名：");
            String username = sc.next();
            System.out.print("请输入密码：");
            String password = sc.next();

            if (correctUsername.equals(username)
                    && correctPassword.equals(password)) {
                System.out.println("登录成功！");
                return;
            }
            System.out.println("用户名或密码错误，剩余 " + (i - 1) + " 次机会");
        }
        System.out.println("账户已锁定，请联系管理员");
    }
}
```

---

## 4. String 常用 API

### 4.1 获取相关

```java
String s = "Hello World";

int len = s.length();            // 11（注意是有括号的！）
char c = s.charAt(0);            // 'H'（取索引 0 处的字符）
String sub = s.substring(6);     // "World"（从 6 到末尾）
String sub2 = s.substring(0, 5); // "Hello"（[0, 5) 左闭右开）
```

### 4.2 转换相关

```java
char[] chars = s.toCharArray();   // {'H','e','l','l','o',' ','W','o','r','l','d'}
byte[] bytes = s.getBytes();      // 转为字节数组
String upper = s.toUpperCase();   // "HELLO WORLD"
String lower = s.toLowerCase();   // "hello world"
String replaced = s.replace('l', '*');  // "He**o Wor*d"
```

### 4.3 判断相关

```java
boolean isEqual = s1.equals(s2);                           // 完全相等
boolean isEqualIgnore = s1.equalsIgnoreCase(s2);           // 忽略大小写
boolean startsWith = s.startsWith("Hello");                 // 是否以...开头
boolean endsWith = s.endsWith("World");                     // 是否以...结尾
boolean contains = s.contains("lo");                        // 是否包含
boolean isEmpty = s.isEmpty();                              // 是否为空（长度为0）
boolean isBlank = s.isBlank();                              // 是否为空白（JDK 11+）
```

### 4.4 查找相关

```java
int idx1 = s.indexOf('l');         // 2（首次出现的位置）
int idx2 = s.indexOf('l', 3);      // 3（从索引3开始找）
int idx3 = s.lastIndexOf('l');     // 9（最后一次出现的位置）
int idx4 = s.indexOf("World");     // 6
```

### 4.5 其他

```java
String trimmed = "  Hello  ".trim();      // "Hello"（去除首尾空格）
String[] parts = "java,python,c++".split(",");  // ["java", "python", "c++"]
String joined = String.join("-", "a", "b", "c");  // "a-b-c"（JDK 8+）

// 字符串与基本类型的转换
String numStr = String.valueOf(123);       // "123"
int num = Integer.parseInt("123");          // 123（字符串 → int）
double d = Double.parseDouble("3.14");     // 3.14（字符串 → double）
```

---

## 5. 字符串遍历

```java
String s = "Hello";

// 方案 1：charAt() + length()
for (int i = 0; i < s.length(); i++) {
    char c = s.charAt(i);
    System.out.println(c);
}

// 方案 2：toCharArray()
char[] chars = s.toCharArray();
for (char c : chars) {
    System.out.println(c);
}
```

---

## 6. String 的不可变性

### 6.1 什么是不可变？

String 对象一旦创建，其内容**不可改变**。

```java
String s = "Hello";
s = s + " World";
// 看起来是字符串变长了，但实际是：
// 1. 创建了新的 String 对象 "Hello World"
// 2. s 指向了新的对象
// 3. 原来的 "Hello" 还在常量池中（变成垃圾）
```

```
s ──→ "Hello"          ← 不可变对象
  ↓
 重复步骤 1-3 后...
s ──→ "Hello World"    ← 新对象，旧对象等待 GC

内存变化：
┌──────┐     第一步          ┌──────────┐
│ s    │──→ 字符串常量池中的   │ "Hello"   │
└──────┘                     └──────────┘
                                  │
┌──────┐     拼接后              │
│ s    │──→ 堆中的新 String 对象  │(指向常量池)
└──────┘     value ───→ "Hello World"
                              ┌─────────────┐
                              │ "Hello World"│(常量池中新的字符串)
                              └─────────────┘
```

### 6.2 为什么设计成不可变？

| 原因 | 说明 |
|------|------|
| **常量池复用** | 多个变量可以安全指向同一字符串 |
| **安全性** | String 常用于类名/路径/密码/数据库连接等 |
| **缓存 HashCode** | 不可变则哈希值固定，`HashMap` 中 String 作为 key 效率高 |
| **线程安全** | 不可变对象天然线程安全，无需同步 |

---

## 7. StringBuilder

### 7.1 为什么需要 StringBuilder？

```java
// 问题：String 拼接会产生大量临时对象
String s = "";
for (int i = 0; i < 10000; i++) {
    s += i;               // 每次拼接都创建新 String 对象
}
// 10000 次拼接 → 创建了 10000 个临时 String 对象！性能极差
```

### 7.2 StringBuilder 的特点

- **可变的字符序列**，拼接时直接在底层数组上操作
- **不创建新对象**，性能远高于 String 拼接

### 7.3 基本使用

```java
// 1. 创建
StringBuilder sb = new StringBuilder();            // 空
StringBuilder sb2 = new StringBuilder("Hello");    // 初始内容 "Hello"

// 2. 添加（append）
sb.append("Hello");
sb.append(" ");
sb.append("World");
sb.append(2024);                    // 可以追加任意类型
// 链式调用（append 返回 this）
sb.append("Hello").append(" ").append("World");

// 3. 插入
sb.insert(5, " Java");    // "Hello Java World"

// 4. 反转
sb.reverse();             // "dlroW avaJ olleH"

// 5. 删除
sb.delete(5, 10);         // 删除 [5, 10) 范围的字符

// 6. 转为 String
String result = sb.toString();
```

### 7.4 性能对比

```java
public class PerformanceTest {
    public static void main(String[] args) {
        long start, end;

        // String 拼接（慢）
        start = System.currentTimeMillis();
        String s = "";
        for (int i = 0; i < 100000; i++) {
            s += i;
        }
        end = System.currentTimeMillis();
        System.out.println("String 拼接：" + (end - start) + "ms");

        // StringBuilder（快）
        start = System.currentTimeMillis();
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 100000; i++) {
            sb.append(i);
        }
        end = System.currentTimeMillis();
        System.out.println("StringBuilder：" + (end - start) + "ms");
    }
}
// 输出示例：
// String 拼接：2850ms
// StringBuilder：5ms
```

### 7.5 常见面试题

```java
// 问：下面这段代码创建了几个对象？
String s1 = "Hello";
String s2 = "World";
String s3 = s1 + s2;

// 答：底层等价于：
// String s3 = new StringBuilder().append(s1).append(s2).toString();
// 创建了 StringBuilder 对象 + toString() 创建的新 String 对象
// 但编译器优化可能不同，面试中使用 javap 反编译来分析
```

---

## 8. StringJoiner（JDK 8+）

### 8.1 什么是 StringJoiner？

用于构造**有分隔符、前缀、后缀**的字符串序列。

```java
import java.util.StringJoiner;

// 1. 只用分隔符
StringJoiner sj = new StringJoiner(", ");
sj.add("Java");
sj.add("Python");
sj.add("C++");
System.out.println(sj);  // Java, Python, C++

// 2. 分隔符 + 前缀 + 后缀
StringJoiner sj2 = new StringJoiner(", ", "[", "]");
sj2.add("Java");
sj2.add("Python");
sj2.add("C++");
System.out.println(sj2);  // [Java, Python, C++]
```

### 8.2 对比 StringBuilder

```java
// StringBuilder 实现 [a, b, c]
StringBuilder sb = new StringBuilder("[");
sb.append("a").append(", ").append("b").append(", ").append("c").append("]");
System.out.println(sb);  // [a, b, c]

// StringJoiner 实现 [a, b, c]（更清晰）
StringJoiner sj = new StringJoiner(", ", "[", "]");
sj.add("a").add("b").add("c");
System.out.println(sj);  // [a, b, c]
```

### 8.3 实战：拼接数组

```java
public static String arrayToString(int[] arr) {
    StringJoiner sj = new StringJoiner(", ", "[", "]");
    for (int num : arr) {
        sj.add(String.valueOf(num));
    }
    return sj.toString();
}

// int[] arr = {1, 2, 3, 4, 5};
// arrayToString(arr) → "[1, 2, 3, 4, 5]"
```

---

## 9. 综合练习

### 9.1 反转字符串

```java
public static String reverse(String s) {
    return new StringBuilder(s).reverse().toString();
}
// reverse("Hello") → "olleH"
```

### 9.2 统计字符出现次数

```java
public static Map<Character, Integer> countChars(String s) {
    Map<Character, Integer> map = new HashMap<>();
    for (char c : s.toCharArray()) {
        map.put(c, map.getOrDefault(c, 0) + 1);
    }
    return map;
}
// countChars("hello") → {h=1, e=1, l=2, o=1}
```

### 9.3 手机号脱敏

```java
public static String maskPhone(String phone) {
    // "13812345678" → "138****5678"
    return phone.substring(0, 3)
            + "****"
            + phone.substring(7);
}
```

### 9.4 敏感词替换

```java
public static String filterSensitive(String text) {
    String[] sensitiveWords = {"敏感词1", "敏感词2", "敏感词3"};
    String result = text;
    for (String word : sensitiveWords) {
        result = result.replace(word, "***");
    }
    return result;
}
```

---

## 10. StringBuilder vs StringBuffer vs String

| 对比 | String | StringBuilder | StringBuffer |
|------|--------|---------------|--------------|
| **可变性** | 不可变 | 可变 | 可变 |
| **线程安全** | 安全（不可变） | 不安全 | 安全（synchronized） |
| **性能** | 修改时慢（创建新对象） | 快 | 较慢（加锁开销） |
| **适用场景** | 内容不变或少量拼接 | 单线程大量字符串操作 | 多线程字符串操作 |

> **日常开发建议**：
> - 内容不变 → `String`
> - 单线程大量拼接 → `StringBuilder`
> - 多线程环境 → `StringBuffer`
> - 需要分隔符/前后缀 → `StringJoiner`

---

## 11. 总结

| 知识点 | 核心要点 |
|--------|----------|
| 创建方式 | 直接赋值（常量池复用）优于 `new String()` |
| 比较 | `==` 比地址，`equals()` 比内容 |
| 不可变性 | String 对象内容不可变，拼接产生新对象 |
| 常用 API | `length()`、`charAt()`、`substring()`、`split()`、`equals()` |
| StringBuilder | 可变字符序列，链式调用，性能远高于 String 拼接 |
| StringJoiner | 专用于带分隔符/前后缀的拼接 |
| StringBuffer | 线程安全的 StringBuilder，一般用 StringBuilder 即可 |
| 实践建议 | 大量字符串操作一定用 StringBuilder |
