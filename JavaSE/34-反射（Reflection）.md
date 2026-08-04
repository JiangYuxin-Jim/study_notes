# 33 - 反射

> 📅 2026-07-30 | 🏷️ JavaSE / 反射 / Class / 类加载 / 框架底层

---

## 反射概述

**反射（Reflection）**：在运行时动态获取类的信息（构造器、方法、字段等），并能操作这些成员的机制。

### 为什么需要反射？

```java
// 传统方式：编译时就确定类型
User user = new User();
user.setName("张三");

// 反射方式：运行时才知道类型和要调用的方法
Class<?> clazz = Class.forName("com.example.User");
Object obj = clazz.newInstance();
Method method = clazz.getMethod("setName", String.class);
method.invoke(obj, "张三");
```

反射是**框架的底层核心技术**：Spring 的 IOC 容器、MyBatis 的 ORM、Tomcat 的 Servlet 加载，都依赖反射。

## 获取 Class 对象的三种方式

```java
// 方式 1：Class.forName（最常用，写配置文件/框架时用）
Class<?> clazz1 = Class.forName("com.example.User");

// 方式 2：类名.class（适用于明确知道类的情况）
Class<User> clazz2 = User.class;

// 方式 3：对象.getClass()（已有对象时）
User user = new User();
Class<? extends User> clazz3 = user.getClass();

// 三者获取的是同一个 Class 对象
System.out.println(clazz1 == clazz2 && clazz2 == clazz3); // true
```

### 什么时候用哪种？

| 方式 | 适用场景 |
|------|---------|
| `Class.forName()` | 配置文件/外部数据指定类名（框架底层） |
| `类名.class` | 编译期间已知类型 |
| `对象.getClass()` | 已有对象实例 |

## 使用反射获取构造方法

```java
Class<?> clazz = Class.forName("com.example.User");

// 获取所有公共构造方法
Constructor<?>[] constructors = clazz.getConstructors();

// 获取所有构造方法（包括私有）
Constructor<?>[] declaredConstructors = clazz.getDeclaredConstructors();

// 获取指定参数类型的构造方法
Constructor<?> constructor = clazz.getConstructor(String.class, int.class);

// 获取私有构造方法
Constructor<?> privateConstructor = clazz.getDeclaredConstructor(String.class);

// 暴力反射：访问私有成员
privateConstructor.setAccessible(true);

// 通过构造方法创建对象
User user = (User) constructor.newInstance("张三", 18);
```

### 获取 Member 的 API 命名规则

所有获取类的成员（构造器/方法/字段），API 命名都有规律：

| 方法 | 返回 |
|------|------|
| `getXxx()` | 获取**公共**的指定成员 |
| `getXxxs()` | 获取**所有公共**成员 |
| `getDeclaredXxx()` | 获取指定成员（包括私有） |
| `getDeclaredXxxs()` | 获取**所有**成员（包括私有） |

## 使用反射获取成员变量

```java
Class<?> clazz = Class.forName("com.example.User");

// 获取所有公共字段
Field[] fields = clazz.getFields();

// 获取所有字段（包括私有）
Field[] declaredFields = clazz.getDeclaredFields();

// 获取指定名字的字段
Field nameField = clazz.getDeclaredField("name");

// 私有字段需要暴力反射
nameField.setAccessible(true);

// 获取字段值
Object value = nameField.get(userObj);

// 设置字段值
nameField.set(userObj, "李四");
```

## 使用反射获取方法

```java
Class<?> clazz = Class.forName("com.example.User");

// 获取所有公共方法（包括继承的）
Method[] methods = clazz.getMethods();

// 获取所有本类方法（包括私有，不包括继承的）
Method[] declaredMethods = clazz.getDeclaredMethods();

// 获取指定方法（方法名 + 参数类型列表）
Method setNameMethod = clazz.getMethod("setName", String.class);

// 获取私有方法
Method privateMethod = clazz.getDeclaredMethod("secretMethod");

// 暴力反射
privateMethod.setAccessible(true);

// 调用方法（对象 + 参数）
Object result = setNameMethod.invoke(userObj, "王五");

// 调用静态方法（对象传 null）
Method staticMethod = clazz.getMethod("staticMethod");
staticMethod.invoke(null);
```

## 核心方法 `invoke` 详解

```java
// invoke 的签名
Object invoke(Object obj, Object... args)
```

- **obj**：调用方法的对象（实例方法）
- **args**：方法参数
- **return**：方法返回值
- 静态方法：obj 传 null

```java
// 实例方法
Method m = clazz.getMethod("setName", String.class);
m.invoke(userObj, "张三");  // userObj.setName("张三")

// 静态方法
Method m2 = clazz.getMethod("staticMethod");
m2.invoke(null);  // User.staticMethod()
```

## 反射 vs 直接调用性能

反射有性能损耗：
- 类型检查、安全检查等额外开销
- 建议：在循环/高频调用中**缓存 Method 对象**，避免重复获取

```java
// ❌ 不推荐：每次都反射获取
for (int i = 0; i < 10000; i++) {
    Method m = clazz.getMethod("setName", String.class);
    m.invoke(obj, "test");
}

// ✅ 推荐：缓存 Method 对象
Method m = clazz.getMethod("setName", String.class);
for (int i = 0; i < 10000; i++) {
    m.invoke(obj, "test");
}
```

## setAccessible(true) 的作用

`setAccessible(true)` 被称为**暴力反射**，作用是：

- 取消 Java 语言访问检查
- 可以访问私有构造器、方法、字段
- 同时也有**一定的性能提升**（跳过安全检查）

```java
Constructor<?> c = clazz.getDeclaredConstructor();
c.setAccessible(true);  // 允许通过私有构造器创建对象
Object obj = c.newInstance();
```

## 反射的应用场景

### 1. 配置文件驱动（工厂模式）

```properties
# config.properties
class=com.example.User
method=setName
param=张三
```

```java
// 读取配置文件，动态创建对象并调用方法
Properties prop = new Properties();
prop.load(new FileInputStream("config.properties"));

Class<?> clazz = Class.forName(prop.getProperty("class"));
Object obj = clazz.newInstance();
Method method = clazz.getMethod(prop.getProperty("method"), String.class);
method.invoke(obj, prop.getProperty("param"));
```

### 2. JDBC 加载驱动

```java
// 反射加载数据库驱动
Class.forName("com.mysql.cj.jdbc.Driver");
```

### 3. 框架依赖注入

```java
// 简化的 Spring IOC 容器
public class SimpleIOC {
    public static Object getBean(String className) throws Exception {
        Class<?> clazz = Class.forName(className);
        Object obj = clazz.newInstance();
        
        // 遍历字段，如果标注了 @Autowired 就注入
        for (Field field : clazz.getDeclaredFields()) {
            if (field.isAnnotationPresent(Autowired.class)) {
                field.setAccessible(true);
                Object dependency = getBean(field.getType().getName());
                field.set(obj, dependency);
            }
        }
        return obj;
    }
}
```

## 反射的优缺点

| 优点 | 缺点 |
|------|------|
| 运行时动态创建/操作对象 | 性能比直接调用慢 |
| 提高代码灵活性 | 代码可读性差 |
| 框架底层基础设施 | 破坏封装性 |
| 绕过访问控制 | 内部使用 breakage risk |

---

## 总结

| 知识点 | 核心要点 |
|--------|---------|
| Class 获取 | forName / .class / getClass |
| 构造器 | getConstructor / getDeclaredConstructor + newInstance |
| 字段 | getField / getDeclaredField + get/set |
| 方法 | getMethod / getDeclaredMethod + invoke |
| 暴力反射 | setAccessible(true) 访问私有成员 |
| 核心场景 | 框架 IOC、配置驱动、检测类信息 |
| 性能 | 缓存 Method/Field 对象，避免重复反射获取 |
