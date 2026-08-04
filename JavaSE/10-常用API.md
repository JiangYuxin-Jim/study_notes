# 09 - 常用 API

## 1. API 概述

API（Application Programming Interface，应用程序编程接口）就是 Java 官方提供的现成类和方法，我们直接拿来用，不用重复造轮子。

Java 的 API 文档（JDK 文档）包含了所有官方类的详细说明，开发中遇到不确定的类就去查文档。

---

## 2. Math

### 2.1 概述

`java.lang.Math` 包含用于执行基本数学运算的方法，如初等指数、对数、平方根和三角函数。

> 注意：`Math` 类在 `java.lang` 包下，使用时无需导包。所有方法都是 `static` 的，直接用类名调用。

### 2.2 常用方法

```java
// 绝对值
Math.abs(-10);          // 10
Math.abs(-3.14);        // 3.14

// 向上取整 / 向下取整
Math.ceil(3.14);        // 4.0
Math.floor(3.14);       // 3.0

// 四舍五入
Math.round(3.14);       // 3
Math.round(3.56);       // 4
Math.round(-3.5);       // -3（注意：往正无穷方向舍入）

// 最大值 / 最小值
Math.max(10, 20);       // 20
Math.min(10, 20);       // 10

// 幂运算
Math.pow(2, 10);        // 1024.0（2^10）
Math.pow(3, 3);         // 27.0（3^3）

// 平方根
Math.sqrt(100);         // 10.0
Math.sqrt(2);           // 1.4142135623730951

// 随机数
Math.random();          // [0.0, 1.0) 之间的随机 double

// 圆周率 / 自然常数
Math.PI;                // 3.141592653589793
Math.E;                 // 2.718281828459045
```

### 2.3 Math.random() 应用：生成指定范围随机数

```java
// 生成 [1, 100] 之间的随机整数
int num = (int)(Math.random() * 100) + 1;

// 通用公式：[min, max]
// (int)(Math.random() * (max - min + 1)) + min

// 生成 [5, 15] 的随机整数
int n = (int)(Math.random() * 11) + 5;
```

### 2.4 练习：猜数字

```java
import java.util.Scanner;

public class GuessNumber {
    public static void main(String[] args) {
        int target = (int)(Math.random() * 100) + 1;
        Scanner sc = new Scanner(System.in);

        while (true) {
            System.out.print("猜一个 1-100 的数字：");
            int guess = sc.nextInt();

            if (guess > target) {
                System.out.println("大了");
            } else if (guess < target) {
                System.out.println("小了");
            } else {
                System.out.println("恭喜你猜对了！");
                break;
            }
        }
    }
}
```

---

## 3. System

### 3.1 概述

`java.lang.System` 类包含一些有用的类字段和方法。不能被实例化。

### 3.2 常用方法

```java
// 1. System.currentTimeMillis() — 获取当前时间戳（毫秒）
long now = System.currentTimeMillis();
System.out.println(now);  // 1721188800000（1970-01-01 到现在的毫秒数）

// 可用于计算程序运行时间
long start = System.currentTimeMillis();
// ... 执行一些代码 ...
long end = System.currentTimeMillis();
System.out.println("耗时：" + (end - start) + "ms");

// 2. System.exit(0) — 终止当前运行的 JVM
// 参数 0 表示正常退出，非 0 表示异常退出
System.exit(0);  // 后面的代码不会执行了
System.out.println("这行不会输出");

// 3. System.arraycopy() — 数组复制
int[] src = {1, 2, 3, 4, 5};
int[] dest = new int[5];
// 参数：源数组, 源起始索引, 目标数组, 目标起始索引, 复制长度
System.arraycopy(src, 0, dest, 0, src.length);
System.out.println(Arrays.toString(dest));  // [1, 2, 3, 4, 5]

// 部分复制
int[] dest2 = new int[3];
System.arraycopy(src, 1, dest2, 0, 3);     // src[1] 开始复制 3 个
System.out.println(Arrays.toString(dest2)); // [2, 3, 4]
```

### 3.3 arraycopy 注意事项

```java
int[] arr = {1, 2, 3, 4, 5};
int[] copy = new int[10];
System.arraycopy(arr, 0, copy, 0, arr.length);
// copy → [1, 2, 3, 4, 5, 0, 0, 0, 0, 0]

// 常见异常：
// ArrayIndexOutOfBoundsException — 索引越界
// NullPointerException — 源数组或目标数组为 null
```

---

## 4. Runtime

### 4.1 概述

`java.lang.Runtime` 每个 Java 应用程序都有一个 `Runtime` 实例，允许应用程序与运行环境交互。

> **不能 `new`**，必须通过 `Runtime.getRuntime()` 获取单例对象。

### 4.2 常用方法

```java
// 1. 获取 Runtime 对象（单例模式）
Runtime rt = Runtime.getRuntime();

// 2. 获取 JVM 相关信息
System.out.println("可用处理器数：" + rt.availableProcessors());  // 通常是 CPU 核心数
System.out.println("总内存：" + rt.totalMemory() / 1024 / 1024 + "MB");      // JVM 总内存
System.out.println("空闲内存：" + rt.freeMemory() / 1024 / 1024 + "MB");     // JVM 空闲内存
System.out.println("最大内存：" + rt.maxMemory() / 1024 / 1024 + "MB");      // JVM 最大可用内存

// 3. 执行系统命令（不推荐生产环境使用）
Process process = rt.exec("notepad.exe");   // Windows 打开记事本
// Process process = rt.exec("calc");       // 打开计算器
// Linux/Mac 示例：
// Process process = rt.exec("ls -la");
```

### 4.3 执行系统命令并读取输出

```java
public class RuntimeDemo {
    public static void main(String[] args) throws Exception {
        Runtime rt = Runtime.getRuntime();
        // 在 Linux 上执行命令
        Process process = rt.exec("ping -c 3 baidu.com");

        // 读取命令输出
        BufferedReader reader = new BufferedReader(
            new InputStreamReader(process.getInputStream())
        );
        String line;
        while ((line = reader.readLine()) != null) {
            System.out.println(line);
        }

        // 等待命令执行完成
        int exitCode = process.waitFor();
        System.out.println("退出码：" + exitCode);
        // 0 = 正常退出，非 0 = 异常
    }
}
```

### 4.4 练习：查看系统信息

```java
Runtime rt = Runtime.getRuntime();

System.out.println("===== 系统信息 =====");
System.out.println("CPU 核心数：" + rt.availableProcessors());
System.out.println("JVM 总内存：" + rt.totalMemory() / 1024 / 1024 + "MB");
System.out.println("JVM 空闲内存：" + rt.freeMemory() / 1024 / 1024 + "MB");
System.out.println("JVM 最大内存：" + rt.maxMemory() / 1024 / 1024 + "MB");
System.out.println("Java 版本：" + System.getProperty("java.version"));
System.out.println("操作系统：" + System.getProperty("os.name"));
```

---

## 5. Object

### 5.1 概述

`java.lang.Object` 是**所有类的根类**（超类/父类）。每个类都直接或间接继承 Object。如果没有明确继承某个类，默认继承 Object。

```java
// 以下两种写法完全等价
public class Student { ... }                    // 默认继承 Object
public class Student extends Object { ... }     // 显式声明
```

### 5.2 常用方法

```java
// 1. toString() — 返回对象的字符串表示
Student s = new Student("张三", 20);
System.out.println(s.toString());  // com.example.Student@15db9742（默认：类名@哈希值）
System.out.println(s);             // 同上，println 会自动调用 toString()

// 2. equals() — 比较两个对象是否"相等"
Student s1 = new Student("张三", 20);
Student s2 = new Student("张三", 20);
System.out.println(s1 == s2);           // false（比较地址）
System.out.println(s1.equals(s2));      // false（Object 默认也是比较地址）

// 3. hashCode() — 返回对象的哈希码
System.out.println(s1.hashCode());      // 类似 356573597

// 4. getClass() — 返回对象的运行时类
System.out.println(s.getClass().getName());   // "com.example.Student"
```

### 5.3 重写 toString()

```java
public class Student {
    private String name;
    private int age;

    // 构造方法、getter/setter 省略...

    @Override
    public String toString() {
        return "Student{name='" + name + "', age=" + age + "}";
    }
}

// 使用
Student s = new Student("张三", 20);
System.out.println(s);  // Student{name='张三', age=20}（不再是地址了）
```

> 实际开发中 IDE（如 IntelliJ IDEA）可以一键生成 `toString()`，`Alt + Insert` 选择即可。

### 5.4 重写 equals()

```java
public class Student {
    private String name;
    private int age;

    // 构造方法、getter/setter 省略...

    @Override
    public boolean equals(Object o) {
        // 1. 判断是否是同一个对象
        if (this == o) return true;
        // 2. 判断类型是否一致
        if (o == null || getClass() != o.getClass()) return false;
        // 3. 强转为当前类型
        Student student = (Student) o;
        // 4. 比较关键字段
        return age == student.age && Objects.equals(name, student.name);
    }

    @Override
    public int hashCode() {
        return Objects.hash(name, age);
    }
}

// 使用
Student s1 = new Student("张三", 20);
Student s2 = new Student("张三", 20);
System.out.println(s1.equals(s2));  // true（按内容比较）
```

### 5.5 为什么重写 equals 必须重写 hashCode？

**规则：** 两个对象 equals 相等，hashCode 必须相等；hashCode 相等，equals 不一定相等。

```java
// 如果只重写 equals 不重写 hashCode：
Student s1 = new Student("张三", 20);
Student s2 = new Student("张三", 20);

System.out.println(s1.equals(s2));        // true（重写过）
System.out.println(s1.hashCode());        // 可能不同！（没重写）
System.out.println(s2.hashCode());        // 不同

// 问题：HashMap/HashSet 先比较 hashCode 再比较 equals
// hashCode 不同 → 直接视为不同对象
// s1 和 s2 明明内容一样，但在 HashSet 中会被存两次（重复！）
Set<Student> set = new HashSet<>();
set.add(s1);
set.add(s2);
System.out.println(set.size());  // 2（本应该是 1！）
```

---

## 6. Objects（工具类）

### 6.1 概述

`java.util.Objects` 是一个工具类，提供了一些静态方法来操作对象，主要用于**空指针安全**的操作。

### 6.2 常用方法

```java
import java.util.Objects;

// 1. equals — 安全比较（避免空指针）
String a = null;
String b = "hello";

// a.equals(b)  // ❌ 空指针异常！
Objects.equals(a, b);  // ✅ 返回 false，不会抛异常
Objects.equals(null, null);  // true

// 2. isNull / nonNull
Objects.isNull(a);     // true
Objects.nonNull(b);    // true

// 3. requireNonNull — 检查非空，为空则抛异常
Objects.requireNonNull(a, "a 不能为空！");
// Exception in thread "main" java.lang.NullPointerException: a 不能为空！

// 4. toString — 安全转字符串
Objects.toString(a);          // "null"（不抛异常）
Objects.toString(a, "默认值"); // "默认值"
```

---

## 8. BigInteger 与 BigDecimal

### 8.1 BigInteger — 大整数运算

Java 中基本整数类型有范围限制：
- `int`：约 ±21 亿（32 位）
- `long`：约 ±922 亿亿（64 位）

超出范围会**溢出**（变成负数），这时就需要 `java.math.BigInteger`。

```java
import java.math.BigInteger;

// long 的最大值是 9223372036854775807
// 更大怎么办？用 BigInteger！

BigInteger b1 = new BigInteger("999999999999999999999999");
BigInteger b2 = new BigInteger("2");

// 加减乘除（必须用方法，不能用 +-*/）
BigInteger sum   = b1.add(b2);                    // 加
BigInteger diff  = b1.subtract(b2);               // 减
BigInteger prod  = b1.multiply(b2);               // 乘
BigInteger quot  = b1.divide(b2);                 // 除
BigInteger[] res = b1.divideAndRemainder(b2);     // 除 + 余数

System.out.println(sum);    // 1000000000000000000000001
System.out.println(res[0]); // 商
System.out.println(res[1]); // 余数

// 比较（不能用 > < ==）
b1.compareTo(b2);  // 正数/0/负数
b1.equals(b2);     // true/false

// int/long 转 BigInteger
BigInteger bi = BigInteger.valueOf(100);          // 推荐，只能转 long 范围内的值
BigInteger bi2 = BigInteger.valueOf(Long.MAX_VALUE);

// BigInteger → 基本类型
long l = b1.longValue();       // 不超 long 范围
int  i = b1.intValue();        // 不超 int 范围
String s = b1.toString();      // 最安全，不会溢出

// 常量
BigInteger.ZERO;   // 0
BigInteger.ONE;    // 1
BigInteger.TEN;    // 10
```

### 8.2 BigDecimal — 精确小数运算

#### 为什么需要 BigDecimal？

计算机用二进制存储浮点数，很多十进制小数无法精确表示：

```java
System.out.println(0.1 + 0.2);  // 0.30000000000000004（不精确！）
System.out.println(1.0 - 0.9);  // 0.09999999999999998

// 对于金融、计费等场景，这种误差不能接受 → 用 BigDecimal
```

#### 创建 BigDecimal

```java
import java.math.BigDecimal;
import java.math.RoundingMode;

// ✅ 正确姿势：用字符串
BigDecimal d1 = new BigDecimal("0.1");    // 精确
BigDecimal d2 = new BigDecimal("0.2");    // 精确

// ❌ 错误姿势：用 double
BigDecimal bad = new BigDecimal(0.1);     // 实际存的是 0.10000000000000000555...
System.out.println(bad);                  // 0.1000000000000000055511151231257827021181583404541015625

// ✅ 推荐：用 valueOf
BigDecimal d = BigDecimal.valueOf(0.1);   // 内部调用了 Double.toString()，精确
```

#### 四则运算

```java
BigDecimal d1 = new BigDecimal("0.1");
BigDecimal d2 = new BigDecimal("0.2");

BigDecimal sum = d1.add(d2);              // 加
BigDecimal diff = d1.subtract(d2);        // 减
BigDecimal prod = d1.multiply(d2);        // 乘

System.out.println(sum);  // 0.3（精确！）
```

#### 除法 — 必须指定精度和舍入模式

```java
BigDecimal d3 = new BigDecimal("10");
BigDecimal d4 = new BigDecimal("3");

// d3.divide(d4);  // ❌ 非整除会抛 ArithmeticException！

// ✅ 指定精度（保留 2 位小数，四舍五入）
BigDecimal result = d3.divide(d4, 2, RoundingMode.HALF_UP);
System.out.println(result);  // 3.33

// 重载形式
result = d3.divide(d4, 2, RoundingMode.HALF_UP);             // 指定小数位数 + 舍入模式
result = d3.divide(d4, new MathContext(2, RoundingMode.HALF_UP));  // 用 MathContext
```

#### 舍入模式

| 模式 | 含义 | 示例（2.5 / -2.5→整数） |
|------|------|------------------------|
| `HALF_UP` | 四舍五入（最常用） | 3 / -3 |
| `HALF_DOWN` | 五舍六入 | 2 / -2 |
| `HALF_EVEN` | 银行家舍入（五看奇偶） | 2 / -2 |
| `CEILING` | 向上取整（往正无穷） | 3 / -2 |
| `FLOOR` | 向下取整（往负无穷） | 2 / -3 |
| `UP` | 远离零取整 | 3 / -3 |
| `DOWN` | 趋近零取整（截断） | 2 / -2 |

> 💡 **银行家舍入（HALF_EVEN）**：正好 5 时看前一位，奇进偶不进，可减少统计偏差，银行常用。

#### 常用方法

```java
BigDecimal d = new BigDecimal("3.14159");

// 设置小数位数（返回新对象）
d.setScale(2, RoundingMode.HALF_UP);      // 3.14

// 比较（不能用 equals！）
BigDecimal a = new BigDecimal("0.10");
BigDecimal b = new BigDecimal("0.1");

System.out.println(a.equals(b));  // false!（因为精度不同，0.10 vs 0.1）
System.out.println(a.compareTo(b));  // 0（正确，数值相等）

// 比较大小
BigDecimal x = new BigDecimal("10");
BigDecimal y = new BigDecimal("20");
x.compareTo(y);   // -1（小于）
y.compareTo(x);   // 1（大于）

// 常用常量
BigDecimal.ZERO;
BigDecimal.ONE;
BigDecimal.TEN;
```

#### 金融计算实践

```java
import java.math.BigDecimal;
import java.math.RoundingMode;

public class MoneyCalculator {

    /** 加法，保留两位小数 */
    public static BigDecimal add(BigDecimal a, BigDecimal b) {
        return a.add(b).setScale(2, RoundingMode.HALF_UP);
    }

    /** 乘法后保留两位小数（如单价×数量） */
    public static BigDecimal multiply(BigDecimal price, BigDecimal qty) {
        return price.multiply(qty).setScale(2, RoundingMode.HALF_UP);
    }

    /** 计算折扣 */
    public static BigDecimal discount(BigDecimal price, double rate) {
        return price.multiply(BigDecimal.valueOf(rate))
                     .setScale(2, RoundingMode.HALF_UP);
    }

    public static void main(String[] args) {
        BigDecimal price = new BigDecimal("19.99");
        BigDecimal qty   = new BigDecimal("3");

        BigDecimal total = multiply(price, qty);
        System.out.println("总价: " + total);               // 59.97

        BigDecimal afterDiscount = discount(total, 0.8);
        System.out.println("打8折: " + afterDiscount);      // 47.98
    }
}
```

### 8.3 BigInteger vs BigDecimal 对比

| 特性 | BigInteger | BigDecimal |
|------|-----------|------------|
| 用途 | 大整数运算 | 精确小数运算 |
| 构造参数 | 字符串、int、long | 字符串、int、double、long |
| 创建推荐 | `valueOf(long)` | `valueOf(double)` 或字符串 |
| 除法 | 整除 + 余数(`divideAndRemainder`) | 必须指定精度和舍入模式 |
| 比较 | `compareTo()`，少用 `equals()` | `compareTo()`，别用 `equals()` |
| 不可变性 | ✅ 不可变 | ✅ 不可变 |
| 常用场景 | 大数阶乘、RSA 加密、超大整数计算 | 金额、税率、科学计算 |

#### 大数阶乘示例

```java
public static BigInteger factorial(int n) {
    BigInteger result = BigInteger.ONE;
    for (int i = 2; i <= n; i++) {
        result = result.multiply(BigInteger.valueOf(i));
    }
    return result;
}

System.out.println(factorial(50));  // 30414093201713378043612608166064768844377641568960512000000000000
```

---

## 9. 常用 API 对比总结

| 类 | 包 | 特点 | 常用方法 |
|----|----|------|---------|
| **Math** | `java.lang` | 数学运算，所有方法都是 static | `abs()` `ceil()` `floor()` `round()` `max()` `min()` `pow()` `sqrt()` `random()` |
| **System** | `java.lang` | 系统相关，不能被实例化 | `currentTimeMillis()` `exit()` `arraycopy()` |
| **Runtime** | `java.lang` | 单例模式，获取运行环境信息 | `getRuntime()` `availableProcessors()` `totalMemory()` `freeMemory()` `exec()` |
| **Object** | `java.lang` | 所有类的根类 | `toString()` `equals()` `hashCode()` `getClass()` |
| **Objects** | `java.util` | 对象操作工具类，空指针安全 | `equals()` `isNull()` `requireNonNull()` |
| **BigInteger** | `java.math` | 任意精度的整数运算 | `add()` `subtract()` `multiply()` `divide()` |
| **BigDecimal** | `java.math` | 精确的小数运算，解决浮点精度问题 | `add()` `subtract()` `multiply()` `divide()` + 舍入模式 |

---

## 10. 总结

| 知识点 | 核心要点 |
|--------|----------|
| Math | 数学相关工具类，所有方法静态，`random()` 生成 `[0,1)` 随机数 |
| System | `currentTimeMillis()` 计时，`exit(0)` 终止 JVM，`arraycopy()` 复制数组 |
| Runtime | 单例获取，查看 CPU/内存，`exec()` 执行系统命令 |
| Object | 所有类的父类，`toString()` 默认输出地址需重写，`equals()` 默认比地址需重写 |
| equals + hashCode | 同时重写，否则 HashSet/HashMap 会出问题 |
| Objects | 空指针安全的操作工具，`requireNonNull()` 可用于参数校验 |
| BigInteger | 解决大整数溢出的问题 |
| BigDecimal | 解决浮点数运算精度丢失，除法必须指定模式和精度 |
