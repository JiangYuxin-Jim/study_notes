# 34 - 动态代理

> 📅 2026-07-30 | 🏷️ JavaSE / 动态代理 / JDK Proxy / 装饰者模式 / AOP

---

## 为什么需要动态代理？

### 场景：给所有方法加日志

```java
// 原本的接口和实现
public interface UserService {
    void addUser(String name);
    void deleteUser(int id);
    User findUser(int id);
}

public class UserServiceImpl implements UserService {
    public void addUser(String name) {
        System.out.println("添加用户: " + name);
    }
    public void deleteUser(int id) {
        System.out.println("删除用户: " + id);
    }
    public User findUser(int id) {
        System.out.println("查找用户: " + id);
        return new User(id, "张三");
    }
}
```

现在要给每个方法加日志和事务：

```java
// ❌ 硬编码：每个方法都要加，耦合高、重复代码多
public class UserServiceImpl implements UserService {
    public void addUser(String name) {
        System.out.println("[日志] 开始执行 addUser");
        System.out.println("[事务] 开启事务");
        try {
            System.out.println("添加用户: " + name);
            System.out.println("[事务] 提交事务");
        } catch (Exception e) {
            System.out.println("[事务] 回滚事务");
        }
        System.out.println("[日志] 执行完成 addUser");
    }
    // ... 其他方法都要重复写
}
```

**动态代理**：在运行时动态创建代理对象，在代理对象中增强方法，无需修改原始代码。

## JDK 动态代理

### 前提条件

JDK 动态代理**只能代理接口**：

```
目标类必须实现至少一个接口
```

### 核心类：Proxy + InvocationHandler

```java
// 1. 创建 InvocationHandler（处理被代理的方法调用）
public class LogInvocationHandler implements InvocationHandler {
    
    // 被代理的真实对象
    private final Object target;
    
    public LogInvocationHandler(Object target) {
        this.target = target;
    }
    
    @Override
    public Object invoke(Object proxy, Method method, Object[] args) 
            throws Throwable {
        // 增强前
        System.out.println("[日志] 开始执行 " + method.getName());
        System.out.println("[事务] 开启事务");
        
        try {
            // 调用真实对象的方法
            Object result = method.invoke(target, args);
            
            // 增强后（正常返回）
            System.out.println("[事务] 提交事务");
            System.out.println("[日志] 执行完成 " + method.getName());
            
            return result;
        } catch (Exception e) {
            // 增强后（异常回滚）
            System.out.println("[事务] 回滚事务");
            System.out.println("[日志] 执行失败 " + method.getName() + 
                               ": " + e.getMessage());
            throw e;
        }
    }
}

// 2. 创建代理对象
UserService target = new UserServiceImpl();
UserService proxy = (UserService) Proxy.newProxyInstance(
    target.getClass().getClassLoader(),     // 类加载器
    target.getClass().getInterfaces(),      // 要实现的接口
    new LogInvocationHandler(target)        // 调用处理器
);

// 3. 使用代理对象
proxy.addUser("张三");  // 自动有日志和事务
proxy.deleteUser(1);    // 自动有日志和事务
```

### Proxy.newProxyInstance 参数详解

```java
public static Object newProxyInstance(
    ClassLoader loader,        // 类加载器（通常用目标类的）
    Class<?>[] interfaces,     // 代理要实现的接口列表
    InvocationHandler h        // 调用处理器
) throws IllegalArgumentException
```

## InvocationHandler 的 invoke 方法

```java
Object invoke(Object proxy, Method method, Object[] args) 
    throws Throwable
```

| 参数 | 说明 |
|------|------|
| `proxy` | 生成的代理对象本身（少用，小心递归） |
| `method` | 当前被调用的方法反射对象 |
| `args` | 方法参数 |

**注意**：不要在 invoke 中调用 `proxy` 对象的方法，会死循环！

```java
// ❌ 错误：死循环
public Object invoke(Object proxy, Method method, Object[] args) {
    proxy.toString();  // 又触发 invoke，无限递归
    return null;
}

// ✅ 正确：调用真实对象
public Object invoke(Object proxy, Method method, Object[] args) {
    return method.invoke(target, args);
}
```

## 动态代理的执行流程

```
proxy.addUser("张三")
    → 调用 InvocationHandler.invoke(proxy, addUser方法, ["张三"])
    → 在 invoke 中可以：
        1. 方法执行前增强（日志、权限检查、开启事务）
        2. 调用 target.addUser("张三") ← 真实业务
        3. 方法执行后增强（日志、提交事务、资源清理）
    → 返回结果
```

## 一个通用的代理工厂

```java
public class ProxyFactory {
    
    public static Object getProxy(Object target) {
        return Proxy.newProxyInstance(
            target.getClass().getClassLoader(),
            target.getClass().getInterfaces(),
            (proxy, method, args) -> {
                System.out.println("[代理] 前置处理");
                Object result = method.invoke(target, args);
                System.out.println("[代理] 后置处理");
                return result;
            }
        );
    }
    
    // 使用 Lambda 简化
    public static <T> T getProxy(T target, Consumer<T> before, 
                                  Consumer<T> after) {
        return (T) Proxy.newProxyInstance(
            target.getClass().getClassLoader(),
            target.getClass().getInterfaces(),
            (proxy, method, args) -> {
                before.accept(target);
                Object result = method.invoke(target, args);
                after.accept(target);
                return result;
            }
        );
    }
}
```

## JDK 动态代理的局限

| 局限 | 说明 |
|------|------|
| **只能代理接口** | 目标类必须实现接口 |
| 无法代理类 | 如果类没有实现接口，JDK Proxy 无法使用 |

### 解决方案：CGLib 动态代理

Spring 中同时支持 JDK Proxy 和 CGLib：

| 代理方式 | 原理 | 适用范围 |
|---------|------|---------|
| JDK Proxy | 实现接口的代理 | 目标类有接口 |
| CGLib | 继承目标类（子类代理） | 目标类无接口也可 |

```java
// Spring 中的配置
@EnableAspectJAutoProxy(proxyTargetClass = true)  // 强制用 CGLib
```

## 动态代理的应用场景

### 1. Spring AOP

```java
@Aspect
@Component
public class LogAspect {
    
    @Around("execution(* com.example.service.*.*(..))")
    public Object around(ProceedingJoinPoint joinPoint) 
            throws Throwable {
        System.out.println("[AOP] 前置通知");
        Object result = joinPoint.proceed(); // 调用目标方法
        System.out.println("[AOP] 后置通知");
        return result;
    }
}
```

Spring AOP 底层就是动态代理：
- 目标类实现接口 → JDK Proxy
- 目标类没有接口 → CGLib

### 2. MyBatis Mapper 接口

MyBatis 的 Mapper 接口没有实现类，运行时会动态创建代理对象：

```java
public interface UserMapper {
    @Select("SELECT * FROM user WHERE id = #{id}")
    User findById(int id);
}
// MyBatis 在运行时：通过动态代理创建 Mapper 接口的实现
// 在 invoke 中解析注解 SQL，执行数据库操作
```

### 3. 统一异常处理

```java
public class ExceptionProxyFactory {
    public static Object getProxy(Object target) {
        return Proxy.newProxyInstance(
            target.getClass().getClassLoader(),
            target.getClass().getInterfaces(),
            (proxy, method, args) -> {
                try {
                    return method.invoke(target, args);
                } catch (Exception e) {
                    System.out.println("方法 " + method.getName() + 
                                       " 异常: " + e.getMessage());
                    return null; // 返回默认值
                }
            }
        );
    }
}
```

## 动态代理 vs 静态代理（装饰者模式）

### 静态代理（装饰者）

```java
public class UserServiceLogDecorator implements UserService {
    private UserService target;
    
    public UserServiceLogDecorator(UserService target) {
        this.target = target;
    }
    
    public void addUser(String name) {
        System.out.println("[日志] " + name);
        target.addUser(name);
    }
    // 每个方法都要写一次增强代码
}
```

### 区别

| 对比 | 静态代理 | 动态代理 |
|------|---------|---------|
| 代码量 | 每个类/接口都要写一个代理类 | 写一次 InvocationHandler |
| 灵活性 | 编译期固定 | 运行时动态生成 |
| 维护性 | 接口新增方法，代理类也要改 | 自动适配 |
| 性能 | 稍好 | 略差（反射调用） |

---

## 总结

| 知识点 | 核心要点 |
|--------|---------|
| 动态代理作用 | 不修改源码，增强方法（日志、事务、权限） |
| JDK Proxy | 只能代理接口 |
| 核心类 | Proxy + InvocationHandler |
| Proxy.newProxyInstance | loader + interfaces + handler |
| InvocationHandler.invoke | proxy + method + args |
| invoke 中调用 | 调用 target 的真实方法，别调 proxy |
| AOP 底层 | Spring AOP = JDK Proxy（有接口）或 CGLib（无接口） |
| 应用场景 | AOP、MyBatis Mapper、统一异常处理 |
