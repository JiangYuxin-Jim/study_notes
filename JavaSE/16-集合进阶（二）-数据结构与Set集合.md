# 数据结构与 Set 集合

> 集合进阶（二）：数据结构基础 + HashSet / LinkedHashSet / TreeSet
> 课程：黑马 JavaSE 入门到起飞（BV17F411T7Ao）

---

## 一、数据结构基础

### 1.1 二叉树（Binary Tree）

**特点：**
- 每个节点最多有两个子节点（左子节点、右子节点）
- 满二叉树：所有叶子节点在同一层，且每个非叶子节点都有两个子节点
- 完全二叉树：除了最后一层，其他层都是满的，最后一层的叶子节点靠左排列

```
        根
      /    \
    左     右
   / \    / \
  L   R  L   R

满二叉树：所有层全满
完全二叉树：非最后层全满，最后层靠左排列
```

### 1.2 二叉查找树（BST, Binary Search Tree）

**核心规则：**
- 左子树所有节点的值 < 根节点的值
- 右子树所有节点的值 > 根节点的值
- 左右子树也分别是二叉查找树

```
        10
      /    \
     5      15
    / \    /  \
   3   7  12   20
```

**查找效率：** O(log n) ~ O(n)
- 理想情况（平衡）：O(log n)
- 最差情况（退化成链表）：O(n)

**退化成链表的情况：** 插入顺序正好有序（如 1, 2, 3, 4, 5）

```
1
 \
  2
   \
    3
     \
      4
       \
        5    ← 查找 5 需要 5 步，O(n)
```

---

### 1.3 平衡二叉树（AVL Tree）

**解决的痛点：** 二叉查找树会退化成链表 → 查找变慢

**平衡：** 任意节点的左右子树高度差 ≤ 1

**平衡因子（Balance Factor, BF）：** 左子树高度 - 右子树高度

- BF = 0：左右等高
- BF = 1：左高
- BF = -1：右高
- BF = 2 或 -2：不平衡，需要旋转

#### 旋转机制

**四种不平衡情况与对应旋转：**

| 情况 | 描述 | 旋转方式 |
|------|------|----------|
| LL（左左） | 在左子树的左子树插入 | 右旋 |
| LR（左右） | 在左子树的右子树插入 | 先左旋后右旋 |
| RR（右右） | 在右子树的右子树插入 | 左旋 |
| RL（右左） | 在右子树的左子树插入 | 先右旋后左旋 |

**左旋步骤（RR情况）：**
```
原：         10
              \
               20
                \
                 30

1. 新根 = 右子节点 = 20
2. 原根的右子树 = 新根的左子树（null）
3. 新根的左子树 = 原根（10）
4. 新根成为新的根节点

结果：       20
          /    \
         10     30
```

**右旋步骤（LL情况）：**
```
原：         30
            /
          20
          /
         10

1. 新根 = 左子节点 = 20
2. 原根的左子树 = 新根的右子树（null）
3. 新根的右子树 = 原根（30）
4. 新根成为新的根节点

结果：       20
          /    \
         10     30
```

**LR（左右）旋转：先左旋后右旋**
```
原：      30
         /
        10
         \
          20

左旋（10-20分支）：
        30
       /
      20
     /
    10

右旋（30-20分支）：
        20
      /    \
     10     30
```

**RL（右左）旋转：先右旋后左旋**
```
原：      10
           \
            30
           /
          20

右旋（30-20分支）：
      10
        \
         20
           \
            30

左旋（10-20分支）：
        20
      /    \
     10     30
```

---

### 1.4 红黑树（Red-Black Tree）

**红黑树 vs 平衡二叉树：**
- 平衡二叉树（AVL）：严格平衡，BF ≤ 1，查找快但插入/删除频繁旋转
- 红黑树：**近似平衡**，查找稍慢于 AVL，但插入/删除旋转次数少，综合性能更好

**Java 中采用红黑树的场景：**
- `HashMap`（JDK 8+，链表长度 ≥ 8 时转红黑树）
- `TreeSet`、`TreeMap`
- 红黑树是计算机科学中最常用的自平衡二叉查找树

#### 红黑规则（5条）

```
1. 每个节点是红色或黑色
2. 根节点必须是黑色
3. 叶子节点（NIL）是黑色
4. 红色节点的子节点必须是黑色
   → 不能有连续的红色节点
5. 从任意节点到其所有叶子节点的路径上，黑色节点数量相同
   → 任意路径的黑色节点数一样（黑高相同）
```

**为什么规则 4+5 能保证近似平衡？**
- 最短路径：全是黑色节点（没有红色）
- 最长路径：红黑交替（红色节点数 = 黑色节点数 - 1）
- 最长路径长度 ≤ 2 × 最短路径长度

#### 红黑树插入后的修复

插入新节点默认为红色（破坏最小，只可能违反规则 4）。

**插入后的 3 种情况：**

| 情况 | 描述 | 处理方式 |
|------|------|----------|
| 插入的是根节点 | 违反规则 2 | 直接变黑 |
| 父节点是黑色 | 没违反任何规则 | ✅ 不需要处理 |
| 父节点是红色 | 违反规则 4（红红相连） | 按叔父节点颜色处理 |

**叔父节点是红色：**
- 父节点 → 黑色
- 叔父节点 → 黑色
- 祖父节点 → 红色
- 将祖父节点视为新插入节点，继续向上修复

```
    黑                    红
   /  \                  /  \
 红    红      →       黑    黑
/                     /
红（新插入）          红
```

**叔父节点是黑色（自底向上看属于 RR/LL/LR/RL 情况）：**
- 先旋转（LL右旋、RR左旋、LR左右旋、RL右左旋）
- 变色（父变黑、祖父变红）

```
RR 情况：
   黑（祖父）             黑
     \               →   /  \
     红（父）            红   红
       \
       红（子）

步骤：左旋 + 父变黑 + 祖父变红
```

---

## 二、Set 集合

### 2.1 体系结构

```
Set
├── HashSet（无序、无索引、不重复）
│   └── LinkedHashSet（有序版：添加顺序）
└── TreeSet（可排序、无索引、不重复）
```

### 2.2 Set 接口共性方法

Set 继承自 Collection，没有特有方法——所有方法都来自 Collection。

```java
Set<String> set = new HashSet<>();
set.add("Java");
set.add("Python");
set.remove("Java");
set.contains("Python");
set.size();
set.isEmpty();
```

### 2.3 HashSet 详解

**底层结构：** 哈希表（数组 + 链表 + 红黑树，JDK 8+）

**HashSet 去重原理（关键）：**
1. 先计算元素的 `hashCode()`，确定放入哪个桶
2. 桶内有元素？→ 用 `equals()` 比较
3. 不同 → 放入链表
4. 相同 → 不放入

**存储流程：**

```
1. 计算 hashCode() → 哈希值
2. 通过哈希值计算桶索引（类似 index = hash & (len-1)）
3. 该桶为空 → 直接放入
4. 该桶不为空 → equals() 比较
   - true → 不存储（去重）
   - false → 存入链表/红黑树
```

**JDK 8+ 优化：**
- 链表长度 ≥ 8 且数组长度 ≥ 64 → 链表转红黑树
- 红黑树节点数 ≤ 6 → 转回链表
- 目的是缓解哈希冲突导致的查询性能退化

**重写 hashCode 和 equals 的规范：**
- 两个对象 equals 相等 → hashCode 必须相等
- 两个对象 hashCode 不等 → equals 肯定不等（性质，非必须）
- 所以：重写 equals 时必须重写 hashCode

```java
public class Student {
    private String name;
    private int age;
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Student student = (Student) o;
        return age == student.age && Objects.equals(name, student.name);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(name, age);
    }
}
```

### 2.4 LinkedHashSet 详解

**特点：** 有顺序（按添加顺序存储），其余同 HashSet

**底层结构：** 哈希表 + 双向链表

```
             链表方向 →
[桶1] → [元素A] ←→ [元素B] → ...
[桶2] → ...
[桶3] → [元素C] ←→ ...

双向链表维护元素的添加顺序，迭代时按此顺序输出
```

```java
LinkedHashSet<String> set = new LinkedHashSet<>();
set.add("A");
set.add("B");
set.add("C");
// 输出：A B C（保持添加顺序）

HashSet<String> set2 = new HashSet<>();
set2.add("A");
set2.add("B");
set2.add("C");
// 输出：顺序不确定（可能 B C A...）
```

**应用场景：** 需要去重且保持顺序（如去重同时保持第一次出现的顺序）

---

### 2.5 TreeSet 详解

**特点：** 可排序（默认升序）、无索引、不重复

**底层结构：** 红黑树

```java
TreeSet<Integer> set = new TreeSet<>();
set.add(5);
set.add(1);
set.add(3);
set.add(2);
set.add(4);
System.out.println(set);  // [1, 2, 3, 4, 5] 自动排序
```

**存储规则：**
- 比较器返回值 < 0 → 放左边
- 比较器返回值 > 0 → 放右边
- 比较器返回值 = 0 → 视为重复，不存储

#### 第一种排序方式：自然排序（Comparable）

元素实现 `Comparable` 接口，重写 `compareTo` 方法。

```java
// 方式1：类实现 Comparable
public class Student implements Comparable<Student> {
    private String name;
    private int age;
    
    @Override
    public int compareTo(Student o) {
        // 按年龄升序
        return this.age - o.age;
        // 降序：return o.age - this.age;
    }
}

// 使用时
TreeSet<Student> set = new TreeSet<>();
set.add(new Student("张三", 20));
set.add(new Student("李四", 18));
set.add(new Student("王五", 22));
// 按年龄排序：[李四(18), 张三(20), 王五(22)]
```

**⚠️ 注意：** TreeSet 通过 compareTo 的返回值判断重复，而不是 equals。如果 compareTo 返回 0，即使两个对象属性不完全一样，也会被视为重复而不存储。

```java
// 多条件排序
@Override
public int compareTo(Student o) {
    // 先按年龄排
    int result = this.age - o.age;
    // 年龄相同，按姓名排
    if (result == 0) {
        result = this.name.compareTo(o.name);
    }
    return result;
}
```

#### 第二种排序方式：比较器排序（Comparator）

不修改元素类，在创建 TreeSet 时传入 Comparator。

```java
// 方式1：匿名内部类
TreeSet<Student> set = new TreeSet<>(new Comparator<Student>() {
    @Override
    public int compare(Student o1, Student o2) {
        return o1.getAge() - o2.getAge();
    }
});

// 方式2：Lambda 表达式（推荐）
TreeSet<Student> set = new TreeSet<>(
    (o1, o2) -> o1.getAge() - o2.getAge()
);

// 方式3：方法引用 + 链式比较
TreeSet<Student> set = new TreeSet<>(
    Comparator.comparingInt(Student::getAge)
              .thenComparing(Student::getName)
);
```

#### 两种排序方式的关系

| | 自然排序（Comparable） | 比较器排序（Comparator） |
|------|------|------|
| 位置 | 元素类内部实现 | TreeSet 构造时传入 |
| 侵入性 | 有侵入，修改原类 | 无侵入 |
| 优先级 | 低（默认） | 高（覆盖 Comparable） |
| 适用 | 元素的天然排序规则 | 临时/外部排序规则 |

**优先级：** 比较器 > 自然排序。如果同时存在，以比较器为准，Comparable 被忽略。

#### 常见类型的默认排序

```java
// Integer：数字升序
TreeSet<Integer> set = new TreeSet<>();  // 1, 2, 3, 4, 5

// String：字典序（ASCII/Unicode）
TreeSet<String> set = new TreeSet<>();   // "A", "B", "C"...

// 自定义对象：需要实现 Comparable 或传入 Comparator
```

#### TreeSet 排序 vs 去重的关系

- TreeSet 用 `compareTo()` / `compare()` 的返回值判断是否重复
- 返回值 = 0 → 不存储（即使实际对象不同）
- 所以：**排序规则 = 去重规则**

```java
// 如果想让年龄相同但名字不同的学生都存进去
// 必须在比较时把名字也纳入比较逻辑
@Override
public int compareTo(Student o) {
    int result = this.age - o.age;
    if (result == 0) {
        result = this.name.compareTo(o.name);  // 名字不同就不算重复
    }
    return result;
}
```

---

## 三、Set 集合对比总结

| 特性 | HashSet | LinkedHashSet | TreeSet |
|------|---------|---------------|---------|
| 底层结构 | 哈希表（数组+链表+红黑树） | 哈希表+双向链表 | 红黑树 |
| 元素顺序 | 无序 | 添加顺序 | 自然/比较器排序 |
| 查询速度 | 最快 O(1) | 较快 O(1) | O(log n) |
| 去重依据 | hashCode() + equals() | hashCode() + equals() | compareTo() / compare() |
| 是否允许 null | 允许（最多一个） | 允许（最多一个） | 不允许（JDK 17+ 允许？需确认） |

**选型建议：**
- 只要去重，不关心顺序 → `HashSet`
- 去重且保持添加顺序 → `LinkedHashSet`
- 去重且需要排序 → `TreeSet`

---

## 四、综合练习

### 练习1：自定义对象去重

```java
public class Student {
    private String name;
    private int age;
    
    public Student(String name, int age) {
        this.name = name;
        this.age = age;
    }
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Student student = (Student) o;
        return age == student.age && Objects.equals(name, student.name);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(name, age);
    }
}

// HashSet 用
HashSet<Student> set = new HashSet<>();
set.add(new Student("张三", 20));
set.add(new Student("张三", 20));  // 重复，不存储
// ⚠️ 必须重写 hashCode + equals，否则默认用 Object 的实现（比较地址），不会去重
```

### 练习2：TreeSet 多条件排序

```java
// 需求：按年龄升序 → 年龄相同按姓名升序
TreeSet<Student> set = new TreeSet<>(
    (s1, s2) -> {
        int ageDiff = s1.getAge() - s2.getAge();
        return ageDiff != 0 ? ageDiff : s1.getName().compareTo(s2.getName());
    }
);

// 或使用方法引用链
TreeSet<Student> set = new TreeSet<>(
    Comparator.comparingInt(Student::getAge)
              .thenComparing(Student::getName)
);
```

### 练习3：字符串去重+排序

```java
public class TreeSetDemo {
    public static void main(String[] args) {
        // 给一堆字符串，去重并排序
        String[] words = {"banana", "apple", "orange", "apple", "banana"};
        
        TreeSet<String> set = new TreeSet<>();
        for (String word : words) {
            set.add(word);
        }
        
        // 结果：[apple, banana, orange]
        System.out.println(set);
        
        // 如需降序
        TreeSet<String> setDesc = new TreeSet<>((s1, s2) -> s2.compareTo(s1));
        for (String word : words) {
            setDesc.add(word);
        }
        // 结果：[orange, banana, apple]
        System.out.println(setDesc);
    }
}
```

### 练习4：TreeSet 排序唯一性问题

```java
// ⚠️ 经典坑：只按某个属性排序但该属性相同
class Person implements Comparable<Person> {
    String name;
    int age;
    
    Person(String name, int age) {
        this.name = name;
        this.age = age;
    }
    
    @Override
    public int compareTo(Person o) {
        return this.age - o.age;  // 只按年龄排
    }
}

public class Test {
    public static void main(String[] args) {
        TreeSet<Person> set = new TreeSet<>();
        set.add(new Person("张三", 20));
        set.add(new Person("李四", 20));
        set.add(new Person("王五", 20));
        
        System.out.println(set.size());  // 1！不是 3！
        // 因为三个人的 age 相同 → compareTo 返回 0 → 视为重复，只存第一个
    }
}
```

**解决方案：** 比较时把 name 也加进去，确保不同对象返回非 0
