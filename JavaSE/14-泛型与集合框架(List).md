# 泛型与集合框架 - List 篇

> **对应课程**：黑马 JavaSE 进阶
> **核心内容**：泛型、数据结构（栈/队列/数组/链表）、ArrayList 源码分析、LinkedList 源码分析、迭代器

---

## 一、泛型（Generics）

### 1.1 为什么需要泛型

在没有泛型之前，集合可以存储任意类型：

```java
List list = new ArrayList();
list.add("hello");
list.add(123);        // ❌ 编译不报错，但取出来可能 ClassCastException
String s = (String) list.get(1);  // 运行时异常
```

**泛型的作用**：将类型检查从运行时提前到编译时，消除强制类型转换。

### 1.2 泛型类

```java
// 定义一个泛型类，T 是类型参数
public class Box<T> {
    private T value;

    public void set(T value) { this.value = value; }
    public T get() { return this.value; }
}

// 使用
Box<String> box = new Box<>();   // 钻石运算符 <>
box.set("hello");
String s = box.get();            // 不用强转
```

**类型参数命名约定**：
| 符号 | 含义 |
|------|------|
| E | Element（集合元素） |
| K | Key（键） |
| V | Value（值） |
| T | Type（任意类型） |
| N | Number（数字） |

### 1.3 泛型方法

```java
public class Utils {
    // 泛型方法：<T> 放在返回值前
    public static <T> T getLast(List<T> list) {
        return list.get(list.size() - 1);
    }

    // 多个类型参数
    public static <K, V> boolean compare(Pair<K, V> p1, Pair<K, V> p2) {
        return p1.getKey().equals(p2.getKey()) &&
               p1.getValue().equals(p2.getValue());
    }
}
```

### 1.4 泛型接口

```java
public interface Repository<T> {
    void save(T item);
    T findById(int id);
    List<T> findAll();
}

// 实现类
public class UserRepository implements Repository<User> {
    @Override
    public void save(User user) { /* ... */ }
    @Override
    public User findById(int id) { /* ... */ }
    @Override
    public List<User> findAll() { /* ... */ }
}
```

### 1.5 类型通配符

```java
// ? 表示未知类型
public void printList(List<?> list) {
    for (Object obj : list) {
        System.out.println(obj);
    }
}

// 上限通配符 <? extends T> —— 读取安全
public double sum(List<? extends Number> list) {
    double s = 0;
    for (Number n : list) s += n.doubleValue();
    return s;
}

// 下限通配符 <? super T> —— 写入安全
public void addNumbers(List<? super Integer> list) {
    list.add(1);  // ✅ 可以写入 Integer
    list.add(2);
}
```

> **PECS 原则**：Producer Extends, Consumer Super
> - 要从集合读取数据（生产者）→ `? extends T`
> - 要向集合写入数据（消费者）→ `? super T`

### 1.6 泛型擦除

Java 泛型是**编译期**的，运行时会被擦除：

```java
// 编译后泛型信息会被擦除为原始类型
List<String> strs = new ArrayList<>();
List<Integer> ints = new ArrayList<>();
System.out.println(strs.getClass() == ints.getClass());  // true

// 不能这样写（运行时无法区分）
// if (list instanceof List<String>) { }  ❌ 编译错误
```

**泛型擦除后**：
- `Box<String>` → `Box`
- `Box<? extends Number>` → `Box<Number>`
- `Box<? super String>` → `Box<Object>`

---

## 二、数据结构基础

### 2.1 栈（Stack）

**特点**：后进先出（LIFO, Last In First Out）

```
        ┌─────┐
       │  5  │ ← 栈顶（push/pop 操作端）
        ├─────┤
       │  3  │
        ├─────┤
       │  1  │ ← 栈底
        └─────┘
```

**核心操作**：
| 操作 | 说明 | 时间复杂度 |
|------|------|:----------:|
| push(e) | 入栈（压栈） | O(1) |
| pop() | 出栈（弹出栈顶） | O(1) |
| peek() | 查看栈顶元素 | O(1) |
| empty() | 是否为空 | O(1) |

**Java 实现**：
```java
Deque<Integer> stack = new ArrayDeque<>();  // 推荐，非线程安全
stack.push(1);    // 入栈
stack.push(2);
int top = stack.pop();   // 出栈 → 2
int peek = stack.peek(); // 查看栈顶 → 1

// 或者使用 Vector 的子类 Stack（不推荐，性能差）
Stack<Integer> oldStack = new Stack<>();
```

**应用场景**：
- 方法调用栈（JVM 栈帧）
- 括号匹配 / 表达式求值
- 撤销操作（Undo）
- 浏览器的前进后退

### 2.2 队列（Queue）

**特点**：先进先出（FIFO, First In First Out）

```
 入队 → │ 1 │ 2 │ 3 │ 4 │ 5 │ → 出队
         ↑                ↑
       队尾              队头
```

**核心操作**：
| 操作 | 说明 | 时间复杂度 |
|------|------|:----------:|
| offer(e) | 入队（队尾添加） | O(1) |
| poll() | 出队（队头移除） | O(1) |
| peek() | 查看队头元素 | O(1) |

**Java 实现**：
```java
// 普通队列
Queue<String> queue = new LinkedList<>();
queue.offer("A");
queue.offer("B");
String head = queue.poll();  // → "A"

// 双端队列（Deque — 两端都能进出）
Deque<String> deque = new LinkedList<>();
deque.offerFirst("A");     // 头插
deque.offerLast("B");      // 尾插
deque.pollFirst();         // 头出
deque.pollLast();          // 尾出
```

**应用场景**：
- 任务调度（线程池任务队列）
- 消息队列
- BFS（广度优先搜索）
- 生产者-消费者模式

### 2.3 数组（Array）

**特点**：连续内存空间，固定长度，随机访问

```
  ┌───┬───┬───┬───┬───┬───┐
  │ 1 │ 2 │ 3 │ 4 │ 5 │   │
  └───┴───┴───┴───┴───┴───┘
    0   1   2   3   4   5
  arr[2] → 直接通过 [基地址 + 2 × 元素大小] 计算 → O(1)
```

**时间和空间复杂度**：
| 操作 | 时间复杂度 |
|------|:----------:|
| 随机访问 arr[i] | O(1) |
| 尾部插入 | O(1) |
| 中间插入/删除 | O(n)（需要移动元素） |
| 查找（无序） | O(n) |
| 查找（有序二分） | O(log n) |

### 2.4 链表（Linked List）

**单链表**：

```
 head → │ 1 │ ●→│ 2 │ ●→│ 3 │ null
```

**双向链表**（Java LinkedList 使用的结构）：

```
 null ← ●│ 1 │●→←●│ 2 │●→←●│ 3 │●→ null
         prev next    prev next  prev next
```

**时间和空间复杂度**：
| 操作 | 时间复杂度 |
|------|:----------:|
| 头部插入/删除 | O(1) |
| 尾部插入/删除 | O(1)（有尾指针） |
| 中间插入/删除 | O(n)（需先遍历找到位置） |
| 随机访问 | O(n)（必须遍历） |
| 查找 | O(n) |

### 数据结构对比

| 结构 | 随机访问 | 头部增删 | 尾部增删 | 中间增删 | 内存 |
|:----:|:--------:|:--------:|:--------:|:--------:|:----|
| 数组 | O(1) ✅ | O(n) ❌ | O(1) ✅ | O(n) ❌ | 连续 |
| 链表 | O(n) ❌ | O(1) ✅ | O(1) ✅ | O(n) | 离散 |
| 栈 | — | O(1) ✅ | — | — | — |
| 队列 | — | — | O(1) | O(1) | — |

---

## 三、ArrayList 源码分析

### 3.1 继承体系

```
Iterable
  └── Collection
        └── List
              ├── ArrayList      ← 数组实现
              └── LinkedList     ← 双向链表实现
```

### 3.2 核心属性

```java
public class ArrayList<E> {
    // 默认初始容量
    private static final int DEFAULT_CAPACITY = 10;

    // 空数组（无参构造用——初始容量为0）
    private static final Object[] EMPTY_ELEMENTDATA = {};

    // 懒加载空数组（有参构造容量=0时用，与上面区分）
    private static final Object[] DEFAULTCAPACITY_EMPTY_ELEMENTDATA = {};

    // 真正存数据的数组（transient 表示不参与默认序列化）
    transient Object[] elementData;

    // 当前元素个数
    private int size;
}
```

### 3.3 构造方法

```java
// 1. 无参构造 —— 初始为空数组（懒加载）
ArrayList<String> list1 = new ArrayList<>();
// elementData = DEFAULTCAPACITY_EMPTY_ELEMENTDATA (size=0)

// 2. 指定初始容量
ArrayList<String> list2 = new ArrayList<>(100);
// elementData = new Object[100] (size=0)

// 3. 传入已有集合
ArrayList<String> list3 = new ArrayList<>(anotherList);
// 复制 anotherList 到 elementData
```

> **为什么无参构造不直接给 10？**
> 这是 JDK 8 的优化——**懒加载**。创建时不给容量，等第一次 add 时才扩容到 10，避免创建大量空 ArrayList 时浪费内存。

### 3.4 add() 方法 —— 尾部添加

```java
// 调用链路：
public boolean add(E e) {
    ensureCapacityInternal(size + 1);  // 确保容量够
    elementData[size++] = e;           // 数组尾部赋值
    return true;
}
```

**扩容机制**：

```java
private void ensureCapacityInternal(int minCapacity) {
    // 1. 如果是懒加载空数组，把 minCapacity 设为 max(默认10, minCapacity)
    if (elementData == DEFAULTCAPACITY_EMPTY_ELEMENTDATA) {
        minCapacity = Math.max(DEFAULT_CAPACITY, minCapacity);
    }
    // 2. 确认是否需要扩容
    ensureExplicitCapacity(minCapacity);
}

private void ensureExplicitCapacity(int minCapacity) {
    modCount++;  // 结构性修改计数（用于 fail-fast 机制）
    if (minCapacity - elementData.length > 0)
        grow(minCapacity);  // 需要扩容
}

private void grow(int minCapacity) {
    int oldCapacity = elementData.length;
    int newCapacity = oldCapacity + (oldCapacity >> 1);  // 扩容 1.5 倍
    if (newCapacity - minCapacity < 0)
        newCapacity = minCapacity;
    if (newCapacity - MAX_ARRAY_SIZE > 0)
        newCapacity = hugeCapacity(minCapacity);
    elementData = Arrays.copyOf(elementData, newCapacity);
    // Arrays.copyOf 会创建新数组并复制旧数据
}
```

**扩容流程总结**：

```
add(e)
  │
  ├─ 数组是空？（第一回 add）
  │     └─ minCapacity = max(DEFAULT_CAPACITY, 1) = 10
  │
  ├─ 容量够？
  │     ├─ ✅ 直接赋值 elementData[size++] = e
  │     └─ ❌ 扩容
  │           └─ newCapacity = old + (old >> 1) = 1.5 倍原容量
  │           └─ Arrays.copyOf() 复制到新数组
```

**扩容示例**：
```
初始: size=0, elementData=[]   (懒加载空数组)
add 1次: 扩容到 10, size=1
...
add 10次: size=10, elementData.length=10
add 11次: 扩容 10 → 15, size=11
add 16次: 扩容 15 → 22, size=16
```

### 3.5 add(index, element) —— 指定位置添加

```java
public void add(int index, E element) {
    rangeCheckForAdd(index);                // 下标越界检查
    ensureCapacityInternal(size + 1);       // 容量检查
    // 🔑 关键：元素后移
    System.arraycopy(elementData, index,
                     elementData, index + 1,
                     size - index);
    elementData[index] = element;
    size++;
}
```

```
插入前：
│ 1 │ 2 │ 3 │ 4 │ 5 │ _ │
      ↑ index=2

System.arraycopy 将 index=2 开始的元素后移一位：
│ 1 │ 2 │ 3 │ 3 │ 4 │ 5 │

赋值 elementData[2] = newElement：
│ 1 │ 2 │ new │ 3 │ 4 │ 5 │
```

**时间复杂度**：O(n) —— 需要移动后面的所有元素

### 3.6 remove() 方法

```java
public E remove(int index) {
    rangeCheck(index);
    modCount++;
    E oldValue = elementData(index);
    int numMoved = size - index - 1;
    if (numMoved > 0)
        // 被删元素后的所有元素前移一位
        System.arraycopy(elementData, index + 1,
                         elementData, index,
                         numMoved);
    elementData[--size] = null;  // 置空让 GC 回收
    return oldValue;
}
```

```
删除 index=1 前：
│ A │ B │ C │ D │ E │
      ↑ 删除 B

前移后：
│ A │ C │ D │ E │ E │  ← 最后一个 E 是残留引用

置空后：
│ A │ C │ D │ E │ null │
```

**时间复杂度**：O(n)

### 3.7 get() / set() —— 随机访问

```java
public E get(int index) {
    rangeCheck(index);
    return elementData(index);   // 直接数组下标，O(1)
}

public E set(int index, E element) {
    rangeCheck(index);
    E oldValue = elementData(index);
    elementData[index] = element;
    return oldValue;
}
```

### 3.8 ArrayList 特点总结

| 方面 | 说明 |
|------|------|
| 底层结构 | Object[] 数组 |
| 随机访问 | O(1)，非常快 |
| 尾部增删 | O(1)（有扩容开销，均摊后仍是 O(1)） |
| 中间增删 | O(n)，需要移动元素 |
| 线程安全 | ❌ 非线程安全 |
| 扩容比例 | 1.5 倍 |
| 初始容量 | 10（懒加载） |
| 序列化 | transient 数组 + 自定义 writeObject/readObject |

---

## 四、LinkedList 源码分析

### 4.1 底层结构 —— 双向链表

```java
public class LinkedList<E> {
    // 链表长度
    transient int size = 0;

    // 头节点
    transient Node<E> first;

    // 尾节点
    transient Node<E> last;
}

// 节点内部类
private static class Node<E> {
    E item;           // 数据
    Node<E> next;     // 后继指针
    Node<E> prev;     // 前驱指针

    Node(Node<E> prev, E element, Node<E> next) {
        this.item = element;
        this.next = next;
        this.prev = prev;
    }
}
```

```
 null ←●│ A │●→←●│ B │●→←●│ C │●→ null
         first ↑          last ↑
```

### 4.2 add() 方法 —— 尾部添加

```java
public boolean add(E e) {
    linkLast(e);
    return true;
}

void linkLast(E e) {
    final Node<E> l = last;              // 原来的尾节点
    final Node<E> newNode = new Node<>(l, e, null);  // 新建节点，prev 指向原尾
    last = newNode;                       // 更新尾指针
    if (l == null)
        first = newNode;                 // 原来是空链表，头尾都是它
    else
        l.next = newNode;                // 原尾的 next 指向新节点
    size++;
    modCount++;
}
```

```
添加前：
first → A ↔ B ↔ C ← last

添加 D：
1. newNode.prev = C
2. last = D
3. C.next = D

添加后：
first → A ↔ B ↔ C ↔ D ← last
               ↑    ↑
            原last  新last
```

**时间复杂度**：O(1) —— 只需修改指针

### 4.3 add(index, element) —— 指定位置添加

```java
public void add(int index, E element) {
    checkPositionIndex(index);
    if (index == size)
        linkLast(element);        // 尾插
    else
        linkBefore(element, node(index));  // 插在指定节点前
}
```

**关键方法 node(index) —— 二分查找优化**：

```java
Node<E> node(int index) {
    // size >> 1：判断 index 在左半还是右半
    if (index < (size >> 1)) {
        Node<E> x = first;
        for (int i = 0; i < index; i++)
            x = x.next;
        return x;
    } else {
        Node<E> x = last;
        for (int i = size - 1; i > index; i--)
            x = x.prev;
        return x;
    }
}
```

> **优化点**：LinkedList 的随机查找并不是从头傻遍历到尾——而是先比较 index 在链表前半段还是后半段，选择从 first 或 last 开始，最多遍历 n/2 次。

### 4.4 remove() 方法

```java
public boolean remove(Object o) {
    if (o == null) {
        for (Node<E> x = first; x != null; x = x.next) {
            if (x.item == null) {
                unlink(x);
                return true;
            }
        }
    } else {
        for (Node<E> x = first; x != null; x = x.next) {
            if (o.equals(x.item)) {
                unlink(x);
                return true;
            }
        }
    }
    return false;
}

// 真正的删除操作
E unlink(Node<E> x) {
    final E element = x.item;
    final Node<E> next = x.next;
    final Node<E> prev = x.prev;

    // 断开前驱
    if (prev == null) {
        first = next;            // 删的是头节点
    } else {
        prev.next = next;
        x.prev = null;           // 断引用，助 GC
    }

    // 断开后继
    if (next == null) {
        last = prev;             // 删的是尾节点
    } else {
        next.prev = prev;
        x.next = null;           // 断引用，助 GC
    }

    x.item = null;               // 数据置空
    size--;
    modCount++;
    return element;
}
```

```
删除前：A ↔ B ↔ C ↔ D

删除 B：
1. A.next → C（跳过 B）
2. C.prev → A（跳过 B）
3. B 的 prev/next/item 全部置 null

删除后：A ↔ C ↔ D
```

**时间复杂度**：O(n) —— 需要先遍历找到节点，删除本身 O(1)

### 4.5 get() 方法

```java
public E get(int index) {
    checkElementIndex(index);
    return node(index).item;  // node() 使用二分查找优化遍历
}
```

**时间复杂度**：O(n) —— 即使有二分优化，最坏仍需遍历 n/2

### 4.6 LinkedList 特点总结

| 方面 | 说明 |
|------|------|
| 底层结构 | 双向链表（Node< E>） |
| 随机访问 | O(n)，需遍历 |
| 头部增删 | O(1) |
| 尾部增删 | O(1) |
| 中间增删 | O(n)（查找需遍历） |
| 内存 | 每个节点额外存 prev/next 引用，开销大于数组 |
| 线程安全 | ❌ 非线程安全 |
| 空间占用 | 比 ArrayList 大（每个元素多两个指针） |

---

## 五、ArrayList vs LinkedList 对比

| 对比项 | ArrayList | LinkedList |
|:------:|:---------:|:----------:|
| 底层 | Object[] 数组 | 双向链表 |
| 随机访问 get(i) | O(1) ✅ | O(n) ❌ |
| 尾部 add | O(1)均摊 ✅ | O(1) ✅ |
| 头部 add | O(n) ❌ | O(1) ✅ |
| 中间 add | O(n) | O(n) |
| 内存 | 连续，紧凑 ✅ | 每个元素多 2 个指针 ❌ |
| 扩容 | 1.5 倍复制 | 无需扩容 ✅ |
| CPU 缓存 | 友好（连续内存） | 不友好（离散内存） |

**选择建议**：
- **大部分场景选 ArrayList** —— 随机访问快，内存紧凑
- **频繁在表头/中间增删** → 选 LinkedList
- **不确定** → 默认 ArrayList

---

## 六、迭代器

### 6.1 Iterator 接口

```java
public interface Iterator<E> {
    boolean hasNext();   // 是否还有下一个
    E next();            // 获取下一个元素
    void remove();       // 删除当前元素（可选）
}
```

### 6.2 使用示例

```java
List<String> list = new ArrayList<>();
list.add("A");
list.add("B");
list.add("C");

// 方式一：for-each 本质就是迭代器
for (String s : list) {
    System.out.println(s);
}

// 方式二：显式使用迭代器
Iterator<String> it = list.iterator();
while (it.hasNext()) {
    String s = it.next();
    System.out.println(s);
}

// 方式三：遍历时删除元素
Iterator<String> it2 = list.iterator();
while (it2.hasNext()) {
    String s = it2.next();
    if ("B".equals(s)) {
        it2.remove();           // ✅ 安全删除
    }
}
// list.remove("B");  ← ❌ for-each/迭代期间用集合的 remove 会抛异常
```

### 6.3 fail-fast 机制

```java
// 迭代器遍历期间，如果集合结构被修改（add/remove），会立即抛出 ConcurrentModificationException
List<String> list = new ArrayList<>(Arrays.asList("A", "B", "C"));
for (String s : list) {
    if ("B".equals(s)) {
        list.remove(s);   // ❌ ConcurrentModificationException！
    }
}
```

**实现原理**：
- ArrayList 内部维护一个 `modCount`（修改计数器）
- 创建迭代器时记录 `expectedModCount = modCount`
- 每次 `next()` 时检查：`if (modCount != expectedModCount) throw ConcurrentModificationException`

**正确删除方式**：
```java
// ✅ 迭代器的 remove
Iterator<String> it = list.iterator();
while (it.hasNext()) {
    it.next();
    it.remove();  // 迭代器自己的 remove 会同步 expectedModCount
}

// ✅ Java 8+ 使用 removeIf
list.removeIf("B"::equals);
```

### 6.4 ListIterator —— 双向迭代

```java
List<String> list = new ArrayList<>(Arrays.asList("A", "B", "C"));

ListIterator<String> it = list.listIterator();
it.next();                    // → "A"
it.next();                    // → "B"
it.previous();                // → "B"（往回走）
it.set("X");                  // 修改当前元素
it.add("Y");                  // 在当前位置插入
```

| ListIterator 特点 | 说明 |
|:----:|------|
| 前向后向 | hasNext/next + hasPrevious/previous |
| 修改元素 | set() 修改当前元素 |
| 插入元素 | add() 在当前迭代位置插入 |
| 获取索引 | nextIndex() / previousIndex() |

---

## 总结

| 知识点 | 核心要点 |
|:------:|:---------|
| 泛型 | 编译期类型安全，消除强转，有擦除机制 |
| PECS 原则 | Producer Extends / Consumer Super |
| 数据结构 | 栈(LIFO)、队列(FIFO)、数组(随机访问O(1))、链表(头尾增删O(1)) |
| ArrayList | 数组实现，随机访问快，中间增删慢，1.5倍扩容 |
| LinkedList | 双向链表实现，头尾增删快，随机访问慢，二分查找优化 |
| 迭代器 | for-each 本质，fail-fast 机制，ListIterator 支持双向 |
| 选择 | 默认 ArrayList，频繁头尾操作选 LinkedList |
