# JUC 并发编程三大特性（原子性 · 可见性 · 有序性）

> 并发编程核心：JMM 内存模型 · 指令重排 · 三大特性 · volatile 与 happens-before
> 前置：`31-多线程基础（创建与线程安全）`、`32-多线程进阶（并发工具与线程池）`

---

## 一、为什么需要 JMM？

多线程出问题的根源，一句话概括：**共享变量的读写不是"直接对着内存干"的**。

为了弥补 CPU 与内存之间巨大的速度差，现代计算机加了多层缓存：

```
CPU 寄存器 → L1/L2/L3 高速缓存 → 主内存(堆)
```

每个 CPU 核心有自己的缓存，共享变量在各核缓存里可能存在**多份副本**。于是产生了三个经典问题：

| 问题 | 本质 | 典型表现 |
|------|------|----------|
| **可见性** | 一个线程改了值，另一个线程看不到 | 死循环不停 |
| **原子性** | 一个操作被拆成多步，中间被打断 | `count++` 少加 |
| **有序性** | 指令执行顺序被重排 | 半初始化对象 |

### JMM（Java Memory Model）是什么

JMM 是 Java 层面的抽象规范，它不等同于 JVM 内存结构（堆/栈/方法区），而是定义了**线程与主内存之间的交互规则**：

- 所有共享变量存在**主内存**
- 每个线程有自己的**工作内存**（对 CPU 缓存/寄存器的抽象）
- 线程读变量 → 从主内存拷贝副本到工作内存 → 操作副本 → 再写回主内存

```java
// JMM 抽象视图
// 主内存：  flag = false
// 线程A工作内存：flag 副本 = false  → 修改为 true → 写回主内存
// 线程B工作内存：flag 副本 = false  ← 没重新读，一直看到 false
```

这就是可见性问题的抽象来源。

---

## 二、原子性（Atomicity）

### 2.1 什么是原子性

一个或多个操作，**要么全部执行且不被中断，要么全部不执行**。

```java
int count = 0;
count++;   // 看似一行，实际是三条字节码指令
```

`count++` 编译后实际是：

```
getfield   // 1. 读 count 到操作数栈
iconst_1   // 2. 压入 1
iadd       // 3. 相加
putfield   // 4. 写回
```

因为读-改-写不是原子的，两个线程可能同时读到 `count=0`，各自加完都写 `1` → 少加一次。

### 2.2 经典验证代码

```java
public class AtomicTest {
    static int count = 0;

    public static void main(String[] args) throws InterruptedException {
        Runnable task = () -> {
            for (int i = 0; i < 10000; i++) {
                count++;   // 非原子
            }
        };

        Thread t1 = new Thread(task);
        Thread t2 = new Thread(task);
        t1.start(); t2.start();
        t1.join();  t2.join();

        System.out.println(count); // 期望 20000，实际往往小于它
    }
}
```

### 2.3 怎么保证原子性

| 方案 | 说明 | 代价 |
|------|------|------|
| `synchronized` | 互斥锁，把复合操作包成一个整体 | 重，阻塞 |
| `Lock` | 显式锁，效果同上，更灵活 | 需手动释放 |
| `AtomicInteger` | CAS 无锁自旋 | 高并发下有自旋开销 |

```java
// 方案1：synchronized
synchronized (AtomicTest.class) { count++; }

// 方案2：AtomicInteger（CAS 底层）
AtomicInteger count = new AtomicInteger(0);
count.incrementAndGet();   // 内部 CAS 循环，保证原子
```

**关键结论：`volatile` 不保证原子性。** 它只解决可见性和有序性，`volatile int count; count++` 依然是线程不安全的。

---

## 三、可见性（Visibility）

### 3.1 什么是可见性

一个线程修改了共享变量的值，**其他线程能否立即看到**这个修改。

### 3.2 经典死循环案例

```java
public class VisibilityTest {
    static boolean flag = false;   // 不加 volatile

    public static void main(String[] args) throws InterruptedException {
        new Thread(() -> {
            while (!flag) {
                // 空转，JIT 之后可能把 flag 提到寄存器，只读一次
            }
            System.out.println("线程结束");
        }).start();

        Thread.sleep(1000);
        flag = true;   // 主线程改了，子线程看不到 → 永远不结束
    }
}
```

**为什么会看不到？**

1. 子线程把 `flag` 副本读到工作内存（甚至 JIT 优化后放进寄存器）
2. 主线程改的是主内存中的 `flag`
3. 子线程一直用自己工作内存里的旧副本 → 死循环

### 3.3 用 volatile 解决

```java
static volatile boolean flag = false;
```

`volatile` 的语义：

- **写 volatile 变量**：立刻刷新到主内存，并让其他线程的副本失效
- **读 volatile 变量**：直接读主内存（或被失效后强制重新加载）

由此实现了可见性。

### 3.4 其他保证可见性的方式

- `synchronized` / `Lock`：解锁前把变量刷回主内存，加锁时清空工作内存
- 线程的 `start()`、`join()`、`Thread.sleep()` 等也可能带来内存屏障效果
- `AtomicXXX`：底层 CAS 本身带 volatile 语义

---

## 四、有序性（Ordering）与指令重排

### 4.1 指令重排是什么

为了充分利用 CPU 流水线，编译器和 CPU 会在**不影响单线程语义**的前提下，调整指令执行顺序。这就是"as-if-serial"原则：

> 不管怎么重排，单线程执行结果不能变。

但多线程下，这个前提被打破了——**单线程看起来没问题，多线程就可能出大问题**。

重排的三个层次：

| 层次 | 谁在重排 |
|------|----------|
| 编译器重排 | javac / JIT 编译器 |
| 指令级并行重排 | CPU 乱序执行 |
| 内存系统重排 | 写缓冲区导致写入延迟 |

### 4.2 经典案例：半初始化对象

```java
public class Singleton {
    private static Singleton instance;   // 注意：没有 volatile

    private Singleton() {}

    public static Singleton getInstance() {
        if (instance == null) {
            synchronized (Singleton.class) {
                if (instance == null) {
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }
}
```

`instance = new Singleton()` 实际分三步：

```
1. 分配内存空间
2. 调用构造方法初始化对象
3. 把 instance 指向这块内存   ← 赋值引用
```

编译器/CPU 可能把 **2 和 3 重排**：

```
1. 分配内存空间
3. instance 指向内存（此时对象还是"半成品"，字段都是默认值）
2. 初始化对象
```

于是另一个线程在 `if (instance == null)` 处看到 `instance != null`，拿到的却是一个**字段还没初始化完的对象** → 空指针或数据错误。

**修复：加 volatile**

```java
private static volatile Singleton instance;
```

`volatile` 禁止了这段代码里的重排，保证 2 在 3 之前完成。

> 这就是 DCL（双重检查锁）单例**必须加 volatile** 的原因，面试高频考点。

### 4.3 重排规则：哪些能排，哪些不能

- 有**数据依赖**的不能重排：`a = 1; b = a;` 中 `b` 依赖 `a`
- 有**控制依赖**的不能随便重排：`if (flag) x = 1;`
- `volatile` 读写、`synchronized` 块前后会插入**内存屏障**，限制重排

内存屏障（Memory Barrier）四种：

| 屏障 | 作用 |
|------|------|
| LoadLoad | 禁止前面的读与后面的读重排 |
| StoreStore | 禁止前面的写与后面的写重排 |
| LoadStore | 禁止前面的读与后面的写重排 |
| StoreLoad | 禁止前面的写与后面的读重排（开销最大，volatile 写后插入） |

---

## 五、volatile 到底做了什么

把三大特性对号入座：

| 特性 | volatile 是否保证 | 原因 |
|------|------------------|------|
| 可见性 | ✅ 保证 | 写后刷主内存 + 读穿到主内存 |
| 有序性 | ✅ 保证 | 插入内存屏障禁止重排 |
| 原子性 | ❌ 不保证 | 只保证单次读/写原子，`i++` 依然不安全 |

**适用场景**：

- 状态标志位（`volatile boolean running`）
- DCL 单例的引用变量
- 一写多读、且写操作不依赖当前值的场景

**不适用场景**：

- 计数器、累加（用 `AtomicInteger` 或锁）
- 复合判断（`if (a && b)` 里 a、b 都是 volatile 也不保证整体原子）

---

## 六、happens-before 原则

这是 JMM 给出的**最高层判定规则**：如果 A happens-before B，那么 A 的执行结果对 B 可见。

核心几条（背下来）：

1. **程序顺序规则**：同一个线程内，前面的代码 happens-before 后面的代码
2. **锁规则**：一个锁的 unlock happens-before 后续对同一个锁的 lock
3. **volatile 规则**：对 volatile 变量的写 happens-before 后续对这个变量的读
4. **线程启动规则**：`Thread.start()` happens-before 该线程中的任何操作
5. **线程终止规则**：线程中的所有操作 happens-before 其他线程从 `join()` 返回
6. **中断规则**：`interrupt()` happens-before 被中断线程检测到中断
7. **传递性**：A → B，B → C，则 A → C

**实用价值**：判断"我的代码到底安不安全"时，不用去想底层缓存和屏障，只问一句——**这里存在 happens-before 关系吗？** 有就安全，没有就要自己加同步。

---

## 七、三大特性速查表

| 特性 | 问题来源 | 保证手段 |
|------|----------|----------|
| 原子性 | 读-改-写被拆解、被打断 | `synchronized`、`Lock`、`AtomicXXX` |
| 可见性 | 工作内存副本 + CPU 缓存 | `volatile`、`synchronized`、`Lock` |
| 有序性 | 编译器/CPU 指令重排 | `volatile`（内存屏障）、`synchronized` |

**一句话记忆：**

> `volatile` 管「看得见」和「不乱序」，`synchronized` 三样全管但重，`Atomic` 专治原子性且轻量。

---

## 八、面试与实战要点

1. **`count++` 为什么线程不安全？** → 三步字节码，非原子
2. **`volatile` 能替代 `synchronized` 吗？** → 不能，缺原子性
3. **DCL 单例为什么要加 volatile？** → 防止"分配内存 → 赋值引用 → 初始化"重排导致的半初始化对象
4. **`i = 1` 是原子操作吗？** → 32 位基本类型赋值是原子的；`long`/`double` 在 32 位 JVM 上不是（需要 volatile 或加锁）
5. **synchronized 和 volatile 的区别？** → synchronized 能保证三者且互斥；volatile 只保可见性+有序性，不阻塞
6. **调试建议**：死循环排查优先怀疑可见性（加 volatile 试试）；计数对不上优先怀疑原子性；初始化相关空指针优先怀疑重排

---

## 九、总结

并发三大特性的本质，都是**"多核缓存 + 重排优化"**这一物理现实在软件层的投影：

```
                 ┌─────────────┐
                 │   主内存     │
                 └──────┬──────┘
        ┌───────────────┼───────────────┐
   ┌────┴────┐     ┌────┴────┐     ┌────┴────┐
   │ 工作内存 │     │ 工作内存 │     │ 工作内存 │
   │  线程A   │     │  线程B   │     │  线程C   │
   └─────────┘     └─────────┘     └─────────┘
      ↑ 可见性问题：副本不同步
      ↑ 原子性问题：读改写被打断
      ↑ 有序性问题：指令重排
```

JMM 通过 **happens-before** 给出规则，通过 **volatile / synchronized / final** 等关键字提供工具，让开发者能在有并发的情况下，写出可预期的正确代码。

理解这三者之后，再看 `ConcurrentHashMap`、`AQS`、线程池的源码，就会发现它们全都是在不同层次上解决这三个问题而已。
