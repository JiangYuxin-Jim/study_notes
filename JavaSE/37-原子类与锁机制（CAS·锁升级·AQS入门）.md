# 原子类与锁机制（CAS · 锁升级 · AQS 入门）

> 从「原子类 → CAS 原理 → 锁的分类与升级 → synchronized vs Lock」
> 前置：`36-JUC并发编程三大特性（原子性·可见性·有序性）`、`32-多线程进阶（并发工具与线程池）`

---

## 一、原子类家族总览

`java.util.concurrent.atomic` 包下的类，全部基于 **CAS + volatile** 实现，无锁、无阻塞、比 synchronized 轻。

| 分类 | 代表类 | 说明 |
|------|--------|------|
| **基本类型原子类** | `AtomicInteger` / `AtomicLong` / `AtomicBoolean` | `incrementAndGet()`、`compareAndSet()` |
| **数组原子类** | `AtomicIntegerArray` / `AtomicLongArray` / `AtomicReferenceArray` | 数组**每个元素**都能原子更新（注意：不是数组引用原子） |
| **引用类型原子类** | `AtomicReference` / `AtomicStampedReference` / `AtomicMarkableReference` | 引用原子更新；后两个防 ABA |
| **对象属性原子类** | `AtomicIntegerFieldUpdater` / `AtomicReferenceFieldUpdater` | 反射方式原子更新某对象的 volatile 字段 |
| **累加器（JDK8+）** | `LongAdder` / `LongAccumulator` / `DoubleAdder` | 高并发下性能优于 `AtomicLong` |

---

## 二、AtomicIntegerArray（P49）

```java
int[] arr = {1, 2, 3};
AtomicIntegerArray aia = new AtomicIntegerArray(arr);

aia.getAndIncrement(0);        // 下标 0 自增，返回旧值 → 1
aia.addAndGet(1, 10);          // 下标 1 加 10 → 12
aia.compareAndSet(2, 3, 100);  // 下标 2 期望 3 才改成 100

System.out.println(aia.get(0));   // 2
System.out.println(arr[0]);       // 1 ← 原数组不受影响（内部复制了一份）
```

**要点：**

- 构造时**复制**传入数组，后续修改不影响原数组
- 原子性体现在「单个下标的读改写」，`aia.length()` 语义是**数组长度**而非元素数
- 常见用途：单词计数、分桶计数、并发标记位

---

## 三、引用类型原子类（P50）

### 1. AtomicReference

```java
User u1 = new User("张三", 18);
AtomicReference<User> ref = new AtomicReference<>(u1);

User u2 = new User("李四", 20);
ref.compareAndSet(u1, u2);   // 引用地址比较，成功则替换
System.out.println(ref.get().getName());  // 李四
```

**注意：CAS 比的是「引用地址」（`==`），不是对象内容**。想按内容比较得自己用 `equals` 包一层。

### 2. AtomicStampedReference —— 解决 ABA

```java
AtomicStampedReference<Integer> asr = new AtomicStampedReference<>(100, 0); // 值 + 版本号

int stamp = asr.getStamp();
asr.compareAndSet(100, 200, stamp, stamp + 1);  // 值 和 版本号 都匹配才成功
```

### 3. AtomicMarkableReference —— 只关心「是否被改过」

```java
AtomicMarkableReference<String> amr = new AtomicMarkableReference<>("A", false);
amr.compareAndSet("A", "B", false, true);  // 一个 boolean 标记位
```

| 类 | 额外状态 | 适用 |
|----|----------|------|
| `AtomicReference` | 无 | 普通引用原子替换 |
| `AtomicStampedReference` | `int` 版本号 | 防 ABA，需要知道改了几次 |
| `AtomicMarkableReference` | `boolean` 标记 | 只关心「有没有被改过」 |

### 4. 字段更新器

```java
class Account {
    public volatile int balance;   // 必须 volatile + public（或可反射访问）
}
AtomicIntegerFieldUpdater<Account> updater =
        AtomicIntegerFieldUpdater.newUpdater(Account.class, "balance");

Account acc = new Account();
updater.incrementAndGet(acc);
```

**为什么用字段更新器？** 已有大量对象数组想原子更新字段时，不必为每个对象包一层 `AtomicInteger`，省内存。

---

## 四、累加器 LongAdder（P51）

`AtomicLong` 高并发下的问题：所有线程抢**同一个** CAS 变量，竞争失败就自旋重试，CPU 空转。

**LongAdder 破局思路 —— 分散热点：**

```
AtomicLong:   N 个线程 → 抢 1 个 value        （串行化）
LongAdder:    N 个线程 → 各写各自的 Cell 槽位  （并行）
              求和时再把 base + 所有 Cell 累加
```

```java
LongAdder adder = new LongAdder();
IntStream.range(0, 1_000_000).parallel().forEach(i -> adder.increment());
System.out.println(adder.sum());   // 1000000
```

| | AtomicLong | LongAdder |
|---|---|---|
| 原理 | 单点 CAS | 分段 CAS（base + Cell[]） |
| 写性能 | 高并发下急剧下降 | 高并发下接近线性扩展 |
| 读性能 | `get()` 就是值，O(1) | `sum()` 要遍历 Cell，O(n) 且**非强一致** |
| 适用 | 读写均衡、需要强一致 | **写多读少**（统计 QPS、计数器） |

**要点：** `sum()` 返回的是"近似值"，遍历时若有线程正在写，可能读到中间态。需要精确值时才用 `AtomicLong`。

---

## 五、锁的江湖（P52~P54）

### 1. 乐观锁 vs 悲观锁（P53）

| | 悲观锁 | 乐观锁 |
|---|---|---|
| 思路 | 先加锁再操作，假设一定冲突 | 不加锁直接干，提交时校验版本 |
| 实现 | `synchronized`、`ReentrantLock`、数据库 `for update` | CAS、版本号、时间戳 |
| 适用 | **写多**、冲突频繁 | **读多**、冲突少 |
| 缺点 | 阻塞、上下文切换、可能死锁 | 失败要重试，长事务下重试成本高 |

数据库版乐观锁就是典型的 `UPDATE ... WHERE version = 3`，`affectedRows = 0` 说明被别人改过。

### 2. CAS 三大问题（P54）

CAS 全称 **Compare And Swap**，三个操作数：`V`（内存值）、`A`（期望值）、`B`（新值）。
由 CPU 的 `cmpxchg` 指令保证原子性（配合 `lock` 前缀）。

```java
// Unsafe 的方法，AtomicInteger 内部就是调它
public final native boolean compareAndSwapInt(Object o, long offset, int expected, int x);
```

**问题 1：ABA**（P56）
线程1 读 A → 线程2 把 A 改成 B 再改回 A → 线程1 CAS 成功，但世界已经变了。
玩法：加版本号（`AtomicStampedReference`）、加标记（`AtomicMarkableReference`）。

**问题 2：自旋开销（P55）**
CAS 失败会 `while(true)` 重试。竞争激烈时大量 CPU 空转。
缓解：`LongAdder` 分散热点、`synchronized` 锁升级中的自适应自旋、`-XX:PreBlockSpin`。

**问题 3：只能保证一个变量原子**
多个变量要一起原子更新时，CAS 无能为力 → 封装成对象用 `AtomicReference`，或者上锁。

### 3. 自旋锁（P55）

```java
// 手写自旋锁：用 AtomicReference 当锁标志
class SpinLock {
    private final AtomicReference<Thread> owner = new AtomicReference<>();

    public void lock() {
        Thread cur = Thread.currentThread();
        while (!owner.compareAndSet(null, cur)) {
            // 空转等待
        }
    }
    public void unlock() {
        owner.compareAndSet(Thread.currentThread(), null);
    }
}
```

**适用：** 临界区极短（几条指令），省去线程挂起/唤醒的开销。
**不适用：** 临界区长 → 白烧 CPU，不如直接阻塞。JDK 的 `ReentrantLock` 是**自适应自旋**：先自旋一小会儿，不行再挂起。

---

## 六、wait 与 sleep（P57）

| | `Object.wait()` | `Thread.sleep()` |
|---|---|---|
| 所属类 | `Object` | `Thread` |
| 是否释放锁 | **释放**（必须持有锁才能调） | **不释放** |
| 唤醒方式 | `notify()` / `notifyAll()` / 超时 | 时间到 / `interrupt()` |
| 使用前提 | 必须在 `synchronized` 块内 | 无要求 |
| 异常 | InterruptedException | InterruptedException |
| 用途 | **线程间协作**（等我条件满足） | 单纯暂停一段时间 |

**经典陷阱：**

```java
synchronized (lock) {
    lock.wait();   // 释放锁并挂起
    // 被唤醒时，要重新抢锁才能从这里继续
}
```

> `wait` 醒来不代表条件成立——必须放在 `while` 循环里判断条件，防止**虚假唤醒**。

```java
synchronized (lock) {
    while (!condition) {   // ❌ 不能写 if
        lock.wait();
    }
    // 干活
}
```

---

## 七、生产者消费者模式（P58）

### 1. synchronized + wait/notifyAll

```java
class Buffer {
    private final Queue<Integer> queue = new LinkedList<>();
    private final int capacity = 10;

    public synchronized void put(int v) throws InterruptedException {
        while (queue.size() == capacity) wait();   // 满了就等
        queue.offer(v);
        notifyAll();                                // 唤醒消费者
    }

    public synchronized int take() throws InterruptedException {
        while (queue.isEmpty()) wait();             // 空了就等
        int v = queue.poll();
        notifyAll();                                // 唤醒生产者
        return v;
    }
}
```

**为什么用 `notifyAll` 而不是 `notify`？**
因为生产者可能唤醒了另一个生产者（多余），真正该醒的消费者还在睡 → **信号丢失**。`notifyAll` 唤醒所有同类，抢不到锁的继续 wait，代价是惊群但不会丢信号。

### 2. ReentrantLock + Condition（更精准）

```java
ReentrantLock lock = new ReentrantLock();
Condition notFull  = lock.newCondition();
Condition notEmpty = lock.newCondition();

void put(int v) throws InterruptedException {
    lock.lock();
    try {
        while (queue.size() == capacity) notFull.await();
        queue.offer(v);
        notEmpty.signal();          // 精确唤醒消费者，不惊群
    } finally { lock.unlock(); }
}

int take() throws InterruptedException {
    lock.lock();
    try {
        while (queue.isEmpty()) notEmpty.await();
        int v = queue.poll();
        notFull.signal();           // 精确唤醒生产者
        return v;
    } finally { lock.unlock(); }
}
```

> **一个 Lock 可以 new 多个 Condition**，把「生产者队列」和「消费者队列」分开，实现精准唤醒 —— 这正是 `ArrayBlockingQueue` 的做法。
> `synchronized` 只有一个等待队列，只能靠 `notifyAll` 粗暴唤醒。

**工程上更推荐直接上阻塞队列：**

```java
BlockingQueue<Integer> q = new ArrayBlockingQueue<>(10);
q.put(1);      // 满则阻塞
q.take();      // 空则阻塞
```

---

## 八、synchronized 锁升级（P59）

同步代码块在 JVM 里的状态不是"要么锁要么不锁"，而是四次升级（**不可逆**）：

```
无锁 → 偏向锁 → 轻量级锁（自旋CAS） → 重量级锁（OS 互斥量）
       ↑ 只有一个线程反复进
               ↑ 有竞争但很轻、临界区短
                                  ↑ 竞争激烈/自旋失败
```

| 状态 | 触发条件 | 实现 | 开销 |
|------|----------|------|------|
| **无锁** | 初始 | — | — |
| **偏向锁** | 只有线程A反复进入 | 对象头 Mark Word 记录线程 ID | 几乎为 0（一个 CAS 都省了） |
| **轻量级锁** | 线程B 来抢 | 栈帧里建 Lock Record，CAS 指向对象头 | 少量 CAS 自旋 |
| **重量级锁** | 自旋失败 / 竞争激烈 | 指向 `ObjectMonitor`，线程 park | 用户态↔内核态切换，最贵 |

**Mark Word（64 位 JVM）关键位：**

```
偏向锁: [线程ID(54) | Epoch(2) | 1 | 01]          → 偏向模式
轻量锁: [指向栈中 Lock Record 的指针(62) | 00]     → 轻量级锁
重量锁: [指向 ObjectMonitor 的指针(62) | 10]       → 重量级锁
GC:     [分代年龄等 | 11]
```

**补充：**
- JDK 15 起**偏向锁默认关闭**（可用 `-XX:+UseBiasedLocking` 开启），JDK 18 彻底废弃 —— 因为现代应用里锁竞争普遍，偏向锁的撤销成本（`safepoint`）不划算。
- 升级单向不可逆，但**重量级锁释放后会退回无锁**（不是退回轻量级）。
- 锁只能升级不能降级，是为了避免频繁升降带来的开销。

---

## 九、重入锁与 ReentrantLock（P60~P65）

### 1. 什么是可重入（P60）

同一线程可以**重复获取自己已持有的锁**，不会死锁。

```java
synchronized void a() { b(); }        // a 持锁，进 b 时再拿一次，计数器 +1
synchronized void b() { /* ... */ }   // 出 b 时计数器 -1，归零才真正释放
```

原理：锁对象里维护 **持有线程 + 重入计数**。`synchronized` 是隐式维护，`ReentrantLock` 是 `state` 字段（AQS 的 32 位 int）。

```java
final void lock() {
    if (compareAndSetState(0, 1))       // 第一次抢
        setExclusiveOwnerThread(Thread.currentThread());
    else
        acquire(1);                      // 重入 or 排队
}

protected final boolean tryAcquire(int acquires) {
    if (state == 0) { /* CAS 抢 */ }
    else if (current == getExclusiveOwnerThread()) {  // 是自己 → 重入
        int nextc = state + acquires;
        setState(nextc);                  // 不 CAS，因为已持锁
        return true;
    }
    return false;
}
```

### 2. ReentrantLock 基本使用（P61）

```java
Lock lock = new ReentrantLock();

lock.lock();                       // 一直等，直到拿到
try {
    // 临界区
} finally {
    lock.unlock();                 // ⚠️ 必须写在 finally，且成对出现
}
```

**为什么必须 try-finally？** 临界区抛异常时，`unlock` 必须执行，否则锁永久泄漏。

### 3. tryLock（P62）

```java
if (lock.tryLock()) {              // 立即返回，拿不到就 false
    try { /* ... */ } finally { lock.unlock(); }
} else {
    // 拿不到锁 → 干别的（降级策略、提示用户稍后再试）
}

if (lock.tryLock(3, TimeUnit.SECONDS)) {   // 最多等 3 秒
    try { /* ... */ } finally { lock.unlock(); }
}
```

**价值：`synchronized` 拿不到锁只能无限等，`tryLock` 给了「拿不到就放弃」的能力**，是防死锁的重要手段。

### 4. 打断等待线程（P63）

```java
Thread t = new Thread(() -> {
    try {
        lock.lockInterruptibly();      // 可被 interrupt 中断的加锁
        try { /* ... */ } finally { lock.unlock(); }
    } catch (InterruptedException e) {
        System.out.println("等待中被打断，放弃抢锁");
    }
});
```

| 方法 | 可否被 interrupt |
|------|------------------|
| `lock.lock()` | ❌ 忽略中断，继续等 |
| `lock.lockInterruptibly()` | ✅ 抛 `InterruptedException` |
| `lock.tryLock()` | ✅（返回即中断标记保留） |

同理 `synchronized` 的等待**不可中断**，这是 `Lock` 的关键优势之一。

### 5. 公平锁 vs 非公平锁（P64）

```java
new ReentrantLock(true);    // 公平锁
new ReentrantLock();        // 非公平锁（默认）
```

| | 公平锁 | 非公平锁 |
|---|---|---|
| 规则 | 严格 FIFO，先到先得 | 新来的线程可以插队抢 |
| 实现 | `hasQueuedPredecessors()` 检查队列有无前驱 | 直接 CAS 抢 |
| 吞吐 | 低（频繁线程切换） | **高**（减少上下文切换） |
| 饥饿 | 不会 | 可能（但概率很低） |

> **为什么非公平反而快？** 释放锁的线程刚唤醒排队线程A，A还没来得及跑，新线程B进来一把抢走 —— 而 A 的唤醒开销白花了。但 B 直接用上锁（缓存热、栈帧在），整体吞吐更高。**"插队"的机会主义设计**。

`synchronized` 是**非公平**的（且不可配置）。

### 6. 排他锁 vs 共享锁（P65）

| | 排他锁（独占） | 共享锁 |
|---|---|---|
| 同义 | 写锁 | 读锁 |
| 共存 | 独占，其他线程读写都不行 | 多个读线程可同时持有 |
| 实现 | `ReentrantLock`、`synchronized` | `ReentrantReadWriteLock.ReadLock`、`Semaphore` |

```java
ReentrantReadWriteLock rw = new ReentrantReadWriteLock();
Lock r = rw.readLock();     // 共享：可多个线程同时读
Lock w = rw.writeLock();    // 排他：写时独占

r.lock();  /* 读读共享 */ r.unlock();
w.lock();  /* 写写互斥、读写互斥 */ w.unlock();
```

**读多写少场景（缓存、配置）用读写锁能显著提吞吐。** 注意：写锁可降级为读锁（先写后读），读锁**不能**升级为写锁（会死锁）。

---

## 十、synchronized 与 Lock 对比（P66）

| 维度 | synchronized | ReentrantLock |
|------|--------------|---------------|
| 层级 | JVM 关键字，字节码 `monitorenter/exit` | JDK 类，基于 AQS |
| 释放 | 自动（异常也释放） | **手动 finally unlock** |
| 公平性 | 只能非公平 | 可选公平/非公平 |
| 可中断 | ❌ | ✅ `lockInterruptibly()` |
| 尝试加锁 | ❌ | ✅ `tryLock()` |
| 超时 | ❌ | ✅ `tryLock(timeout)` |
| 条件队列 | 1 个（wait/notify） | **多个 Condition** |
| 读写分离 | ❌ | ✅ `ReadWriteLock` |
| 锁升级 | ✅ 偏向→轻量→重量 | ❌ 直接阻塞排队 |

**选型口诀：**

> **能用 synchronized 就用 synchronized**（简单、自动释放、JVM 优化好）；
> 需要 **超时、可中断、公平、多条件队列、读写分离** 时才上 `ReentrantLock`。

---

## 十一、高并发锁机制优化最佳实践（P67）

### 1. 减少锁持有时间

```java
// ❌ 整个方法加锁，包括 IO 和耗时计算
synchronized void process() {
    String s = loadFromDb();    // 慢
    int r = compute(s);         // 慢
    cache.put(r);
}

// ✅ 只锁必要的一小段
void process() {
    String s = loadFromDb();
    int r = compute(s);         // 在锁外算
    synchronized (this) { cache.put(r); }
}
```

### 2. 减小锁粒度

把一把大锁拆成多把小锁：`ConcurrentHashMap`（JDK7 分段锁 Segment，JDK8 改为 `CAS + synchronized` 锁单个桶头）、`LongAdder` 的 Cell 分散。

### 3. 锁分离（读写分离）

读多写少 → `ReentrantReadWriteLock` / `StampedLock`（乐观读，性能更高）。

```java
// StampedLock 乐观读：读的时候完全不加锁
long stamp = sl.tryOptimisticRead();
int v = data;
if (!sl.validate(stamp)) {           // 期间被改过 → 退化为悲观读
    stamp = sl.readLock();
    try { v = data; } finally { sl.unlockRead(stamp); }
}
```

### 4. 锁消除 / 锁粗化（JVM 自动）

- **锁消除**：逃逸分析发现锁对象不逃逸 → 直接删掉锁（如方法内 `new StringBuffer()` 的 append）
- **锁粗化**：相邻的多次加解锁合并成一次（循环内反复 `synchronized`）

### 5. 其他工程手段

| 手段 | 说明 |
|------|------|
| **无锁化** | 用 `Atomic*` / `LongAdder` 替代锁 |
| **线程本地** | `ThreadLocal` 避免共享（注意内存泄漏，用完 `remove()`） |
| **不可变对象** | `final` + 不提供修改方法，天然线程安全（String、Integer） |
| **CAS + 重试上限** | 防自旋风暴，超过次数就降级 |
| **避免嵌套锁** | 必须嵌套时，**全局统一加锁顺序**，防死锁 |
| **锁对象不要用 String/包装类** | 字符串常量池/缓存导致锁"共享"，不同逻辑互坑 |

---

## 十二、面试速查

1. **CAS 三大问题？** → ABA、自旋开销、只能保证单个变量原子
2. **ABA 怎么解决？** → `AtomicStampedReference`（版本号）/ `AtomicMarkableReference`（标记位）
3. **LongAdder 为什么比 AtomicLong 快？** → 分段 Cell 分散 CAS 竞争；代价是 `sum()` 非强一致
4. **wait 和 sleep 的核心区别？** → wait 释放锁 + 需在 synchronized 内 + 靠 notify 唤醒；sleep 不释放锁
5. **为什么 wait 要包在 while 里？** → 防虚假唤醒（醒来了但条件不成立）
6. **synchronized 锁升级过程？** → 无锁 → 偏向 → 轻量（CAS 自旋）→ 重量（ObjectMonitor）；单向，不可降级
7. **偏向锁为什么被废弃？** → 撤销需要 safepoint，高竞争场景下成本大于收益（JDK15 默认关闭、JDK18 移除）
8. **synchronized 和 ReentrantLock 怎么选？** → 默认 synchronized；要超时/中断/公平/多条件/读写分离上 Lock
9. **tryLock 有什么用？** → 拿不到锁可以走降级逻辑，避免死等，是防死锁利器
10. **公平锁为什么不公平锁慢？** → 公平锁每次都要唤醒排队线程 + 上下文切换；非公平让新线程直接抢，缓存更热
11. **读锁能升级成写锁吗？** → 不能（死锁），写锁可以降级为读锁

---

## 十三、总结：一张图串起来

```
        原子类 Atomic*（CAS + volatile，无锁）
            ├─ 基础/数组/引用（StampedReference 防 ABA）
            ├─ 字段更新器（省对象包装）
            └─ LongAdder（分段 CAS，写多读少神器）
                  ↑
              CAS 原理 ← 乐观锁
                  ↓
        锁 (悲观) ── synchronized（JVM，自动释放，锁升级）
                  └─ Lock/AQS（JDK，手动释放，超时/中断/公平/多条件）
                        ├─ ReentrantLock（可重入、公平/非公平、排他）
                        └─ ReadWriteLock（读共享、写排他）
                  ↓
        优化：减持有时间 · 减粒度 · 锁分离 · 锁消除/粗化 · 无锁化
```

一句话收尾：**并发编程的本质是「在正确性与吞吐量之间做权衡」** —— CAS 牺牲了「读的准确性」换写的扩展性；悲观锁牺牲吞吐换简单正确；锁升级牺牲一致性换性能。理解每种手段**付出了什么、买到了什么**，比记住它们怎么实现更重要。
