# 35 - 继承（Inheritance）

> 本文补全 `07-面向对象编程.md` 中只做了概述而未展开的「继承」部分。
> 三大特征：**封装**（已在 07 详细讲）、**继承**（本篇）、**多态**（下一篇）。

## 1. 为什么需要继承

如果两个类有大量重复的属性和方法，直接复制粘贴会带来问题：

- **代码冗余**：相同代码写多遍
- **维护困难**：要改一处逻辑，得同时改多个类
- **扩展性差**：加新类还得再复制一遍

```java
// 没有继承的写法：Dog 和 Cat 大量代码重复
public class Dog {
    String name;
    int age;
    public void eat() { System.out.println(name + "在吃饭"); }
}

public class Cat {
    String name;
    int age;
    public void eat() { System.out.println(name + "在吃饭"); }
}
```

用**继承**把公共部分抽取到父类（Animal），子类只写自己的独有内容。

## 2. 继承的语法（extends）

```java
public class Animal {          // 父类（基类 / 超类）
    String name;
    public void eat() { System.out.println("吃饭"); }
    public void sleep() { System.out.println("睡觉"); }
}

public class Dog extends Animal {   // 子类（派生类）继承父类
    public void watchHome() { System.out.println("看家"); }  // 子类独有
}

public class Cat extends Animal {
    public void catchMouse() { System.out.println("抓老鼠"); }
}
```

- 关键字：`extends`
- **一个子类只能有一个直接父类（单继承）**，但 Java 中类可以**多层继承**（孙子类继承子类）
- 子类自动拥有父类的**非 private** 成员（属性、方法）

## 3. 继承的特点

| 特点 | 说明 |
|------|------|
| 单继承 | 一个类只能继承一个直接父类（`class A extends B` 只能有一个 B） |
| 多层继承 | A extends B，B extends C，A 可以层层继承 C 的内容 |
| 不支持多继承 | Java 类不能一个 extends 多个（接口可以多实现，后面讲） |
| 继承传递性 | 父类的父类（爷爷类）成员也能被使用 |
| 私有成员不继承 | 父类 private 成员子类不能直接访问（可通过 public 方法间接访问） |

```java
// 多层继承示例
public class GrandFather { public void a() {} }
public class Father extends GrandFather { public void b() {} }
public class Son extends Father { public void c() {} }
// Son 可以调用 a() b() c()
```

## 4. super 关键字

`super` 代表**父类对象的引用**，用于在子类中访问父类的成员。

| 用法 | 示例 | 说明 |
|------|------|------|
| 访问父类成员变量 | `super.变量名` | 当子类变量与父类重名时，区分 |
| 调用父类成员方法 | `super.方法名()` | 调用父类被重写的方法 |
| 调用父类构造器 | `super(参数)` | **必须在子类构造器的第一行** |

```java
public class Animal {
    String name = "动物";
    public Animal() { System.out.println("父类构造器"); }
    public void eat() { System.out.println("动物吃饭"); }
}

public class Dog extends Animal {
    String name = "狗";
    public Dog() {
        super();            // 调用父类无参构造器（默认自动加，可省略）
        System.out.println("子类构造器");
    }
    public void show() {
        System.out.println(name);     // 子类的 name = 狗
        System.out.println(super.name); // 父类的 name = 动物
    }
    public void eat() {               // 重写
        super.eat();                  // 调用父类被重写的方法
    }
}
```

**关于 `super()` 的规则（重点）：**
- 子类构造器中，`super()` 默认是**系统自动加上**的（调用父类无参构造器）
- 如果父类**没有无参构造器**（只有有参构造器），子类构造器必须**显式**写 `super(参数)`
- `super(...)` 和 `this(...)` 都**必须是构造器第一行**，二者不能同时出现

## 5. 构造方法的执行流程

**子类对象创建时，会先执行父类构造器，再执行子类构造器。**

```java
public class Animal {
    public Animal() { System.out.println("1. Animal 构造器"); }
}
public class Dog extends Animal {
    public Dog() {
        super();                        // 隐式
        System.out.println("2. Dog 构造器");
    }
}
// new Dog() 输出：
// 1. Animal 构造器
// 2. Dog 构造器
```

原因：子类要使用父类的成员，必须先初始化父类（先有父再有子）。

## 6. 方法重写（Override）

子类对父类的**同名同参方法**重新实现，叫**重写**。

```java
public class Animal {
    public void eat() { System.out.println("动物吃饭"); }
}
public class Dog extends Animal {
    @Override                      // 注解：声明这是重写，方便编译器校验
    public void eat() { System.out.println("狗吃骨头"); }
}
```

**重写的规则：**

| 规则 | 说明 |
|------|------|
| 方法名、参数列表 | 必须与父类**完全相同** |
| 返回值类型 | 相同，或子类（返回类型是父类返回类型的子类） |
| 访问权限 | 不能比父类更严格（父类 public，子类不能 private） |
| 被 static / final / private 修饰 | 不能重写 |

**重写 vs 重载对比（常考）：**

| 对比 | 重写 Override | 重载 Overload |
|------|--------------|--------------|
| 位置 | 子类中 | 同一个类中 |
| 方法名 | 相同 | 相同 |
| 参数列表 | 必须相同 | 必须不同 |
| 返回值 | 相同或子类 | 无关（参数不同即可） |
| 关键词 | @Override | 无 |
| 关系 | 父子类之间 | 同一个类内 |

## 7. final 关键字

`final`（最终的、不可改变的）用于修饰：

| 修饰对象 | 效果 | 示例 |
|---------|------|------|
| 类 | 不能被继承（不能有子类） | `public final class String {}` |
| 方法 | 不能被重写 | `public final void show() {}` |
| 变量 | 值不能被修改（常量） | `final int x = 10;` |
| 局部变量 | 只能赋值一次 | `final double PI = 3.14;` |

```java
final class MathUtils { }        // MathUtils 不能被继承
// class MyMath extends MathUtils {}   // 编译报错：final 类不能继承
```

## 8. Object 类

- **所有类都直接或间接继承 `Object` 类**（Java 的根类）
- 自定义类不写 extends，默认继承 Object
- 常用方法：`toString()`、`equals()`、`hashCode()`

```java
public class Student {
    private String name;
    private int age;
    // 构造器、getter/setter 省略

    @Override
    public String toString() {
        return "Student{name=" + name + ", age=" + age + "}";
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;                 // 同一对象
        if (o == null || getClass() != o.getClass()) return false;
        Student s = (Student) o;
        return age == s.age && name.equals(s.name);
    }
}
```

| 方法 | 默认行为 | 建议 |
|------|---------|------|
| `toString()` | 返回"类名@十六进制地址" | 重写为对象的文本描述 |
| `equals()` | 默认比较地址（同 ==） | 重写为比较内容 |
| `hashCode()` | 默认与地址相关 | 重写 equals 时通常要一起重写 |

> 常用 IDEA 快捷键：`Alt + Insert` 一键生成 toString / equals / hashCode。

## 9. 抽象类（abstract）

**抽象类**：用 `abstract` 修饰的类，不能实例化（不能 new），专用于被继承。

**抽象方法**：只有声明没有方法体的方法，必须由子类重写实现。

```java
public abstract class Shape {          // 抽象类
    // 抽象方法：没有方法体
    public abstract double area();

    // 抽象类里也可以有普通方法
    public void show() {
        System.out.println("面积 = " + area());
    }
}

public class Circle extends Shape {
    private double r;
    public Circle(double r) { this.r = r; }
    @Override
    public double area() { return Math.PI * r * r; }   // 必须实现抽象方法
}
```

**抽象类特点（常考）：**

- 抽象类**不能直接 new**，只能通过子类
- 抽象方法必须在**抽象类**中（普通类不能有抽象方法）
- **子类必须重写父类所有抽象方法**，除非子类也是抽象类
- 抽象类可以**没有抽象方法**（纯普通方法的抽象类），但有抽象方法的一定是抽象类
- 抽象类可以有构造器（用于子类初始化），但不能 new

## 10. 继承 vs 组合

| 对比 | 继承（is-a） | 组合（has-a） |
|------|-------------|--------------|
| 关系 | 子类是父类的一种 | 类是另一个类的组成部分 |
| 关键字 | extends | 成员变量持有对象 |
| 耦合度 | 高（改动父类影响子类） | 低（灵活替换） |
| 例子 | Dog extends Animal | Car 里有 Engine |
| 适用 | 强血缘的"是"关系 | 弱耦合的"有"关系 |

```java
// 组合：Car 持有 Engine 对象
public class Engine { public void start() { /* ... */ } }
public class Car {
    private Engine engine = new Engine();   // 组合
    public void run() { engine.start(); }
}
```

**继承的优缺点（面试常问）：**
- 优点：代码复用、层次清晰、易于维护扩展
- 缺点：强耦合、打破封装（暴露父类细节）、继承层级过深难维护
- 原则：**优先使用组合，而非继承**（组合大于继承）

## 11. 总结

- 继承用 `extends`，核心是**代码复用**，只支持单继承、可多层继承
- `super` 访问父类成员，`super()` 调父类构造器（必须在第一行）
- 创建子类对象时**先执行父类构造器**
- **重写** vs **重载**：重写是父子类同名同参，重载是同类内同名不同参
- `final` 修饰类不可继承、方法不可重写、变量不可改
- 所有类默认继承 `Object`，重写 `toString` / `equals` / `hashCode`
- **抽象类**不能 new，抽象方法必须由子类实现
- 继承要合理使用，优先组合；下一篇讲**多态**
