# 02 · LambdaQueryWrapper 与 LambdaUpdateWrapper 精讲

> 课程：黑马 2026 微服务技术栈（BV1S142197x7）· MyBatis-Plus 模块
> 前置：[01 - MyBatis-Plus](./01-MyBatisPlus.md)
> 版本核实：MyBatis-Plus **3.5.9**（本机下载 jar 用 `javap` 逐个方法签名验证，非抄博客）

---

## 0. 一句话定位

- **LambdaQueryWrapper** = 用来**拼 WHERE 条件**（SELECT / DELETE 都靠它）
- **LambdaUpdateWrapper** = 用来**拼 SET 赋值 + WHERE 条件**（UPDATE 专用）

两个都是 `Wrapper` 家族的 Lambda 版。所谓「Lambda 版」，本质就一件事：**字段名不写字符串，写方法引用 `User::getAge`**。

```java
// 字符串版（QueryWrapper）      // Lambda 版
qw.eq("age", 18)                 qw.eq(User::getAge, 18)
        ↑                              ↑
   拼错不报错                     编译期就报错
   改字段名要全局搜字符串          重构改字段名，IDE 一键全改
```

> 💡 方法引用怎么变成列名？MP 用 `SerializedLambda` 反射出 `getAge`，去掉 `get` 再首字母转小写变 `age`，再按 `@TableField` / 驼峰下划线规则映射成 `age`。所以**必须有 getter**，否则方法引用无从谈起。

---

## 1. 继承关系：为什么两个类的查询方法一模一样

```
Wrapper<T>（抽象基类）
 └─ AbstractWrapper<T, R, Children>            ← 所有 eq/ge/like/in/isNull/orderBy 都在这
     ├─ AbstractLambdaWrapper<T, Children>     ← 多了「方法引用 → 列名」的转换
     │   ├─ LambdaQueryWrapper<T>   implements Query  (select / 只拼 WHERE)
     │   └─ LambdaUpdateWrapper<T>  implements Update (set / setSql / setIncrBy)
     └─ (字符串版) QueryWrapper / UpdateWrapper
```

三个泛型参数记住含义：
- `T` 实体类型
- `R` = **列名的表示形态**（Lambda 版是 `SFunction<T, ?>`，字符串版是 `String`）
- `Children` = 自身类型，用来让所有方法返回 `this`，实现**无限链式**（自限定泛型技巧）

**关键结论**：`LambdaUpdateWrapper` 的 WHERE 能力和 `LambdaQueryWrapper` **完全一样**（都继承自 `AbstractWrapper`），它只是**额外**多了 `set` 系列。所以「LambdaUpdate 能不能做复杂条件查询」这个问题答案是：能拼条件，但它 `select` 不了，查询还是得用 Query。

---

## 2. 怎么创建：`new` 还是 `Wrappers`

两种都对，`Wrappers` 是静态工厂（`javap` 验证存在这些方法）：

```java
// 方式一：new
LambdaQueryWrapper<User>  qw = new LambdaQueryWrapper<>();
LambdaUpdateWrapper<User> uw = new LambdaUpdateWrapper<>();

// 方式二：Wrappers 静态工厂（推荐，链式更顺）
import static com.baomidou.mybatisplus.core.toolkit.Wrappers.*;

Wrappers.<User>lambdaQuery()
Wrappers.<User>lambdaQuery(User::getUsername, "tom")   // 等价 eq 第一个条件
Wrappers.<User>lambdaUpdate()
Wrappers.<User>lambdaUpdate(User::getId, 1L)
```

`Wrappers.lambdaQuery(T entity)` 这个重载有个妙用：直接传一个**实体的非 null 字段**当条件：

```java
User u = new User();
u.setUsername("tom");
u.setAge(18);
List<User> list = userMapper.selectList(Wrappers.lambdaQuery(u)); // WHERE username='tom' AND age=18
```

⚠️ 注意这是「**非 null 字段全用 AND 等值**」，不是「传什么用什么」，字段多了容易意外命中，**只适合简单场景**。

---

## 3. LambdaQueryWrapper 全方法速查

### 3.1 比较 / 区间 / 模糊 / 集合 / 空值

```java
LambdaQueryWrapper<User> qw = new LambdaQueryWrapper<>();

// 比较
qw.eq(User::getUsername, "tom");            // username = 'tom'
qw.ne(User::getAge, 18);                    // age <> 18
qw.gt / ge / lt / le(User::getAge, 18);     // > >= < <=

// 区间
qw.between(User::getAge, 18, 30);           // BETWEEN 18 AND 30
qw.notBetween(User::getAge, 18, 30);

// 模糊（注意 % 加在哪边）
qw.like(User::getUsername, "tom");          // %tom%     前后都模糊
qw.likeLeft(User::getUsername, "tom");      // %tom      左边模糊 = 以 tom 结尾
qw.likeRight(User::getUsername, "tom");     // tom%      右边模糊 = 以 tom 开头
qw.notLike / notLikeLeft / notLikeRight

// 集合
qw.in(User::getId, Arrays.asList(1, 2, 3)); // id IN (1,2,3)
qw.notIn(User::getId, ids);
qw.in(User::getId, 1, 2, 3);                // 可变参数重载

// 空值 —— 最常用也最容易被忘
qw.isNull(User::getEmail);                  // email IS NULL
qw.isNotNull(User::getEmail);               // email IS NOT NULL
```

> 🔴 **`in` 的空集合坑**：`qw.in(User::getId, emptyList())` 生成的是 `id IN ()`，MySQL 直接语法错误。**必须自己判空**：
> ```java
> qw.in(CollUtil.isNotEmpty(ids), User::getId, ids);   // 用 condition 参数，安全
> ```

> 🔴 **`like` 的通配符坑**：用户输入里带 `%` `_` 会被当通配符。需要精确模糊搜索时要转义（MP 不自动处理）。

### 3.2 排序 / 分组 / 指定字段 / 拼接

```java
qw.orderByAsc(User::getAge);                          // ORDER BY age ASC
qw.orderByDesc(User::getCreateTime);                  // ORDER BY create_time DESC
qw.orderBy(true, false, User::getId);                 // 参数：condition, isAsc, 字段
qw.orderByAsc(User::getAge, User::getId);             // 多字段一并升序

qw.groupBy(User::getDeptId);                          // GROUP BY dept_id
qw.having("count(*) > 1");                            // HAVING（只能写字符串！）

qw.select(User::getId, User::getUsername);            // SELECT id, username （省带宽）
qw.select(User.class, f -> !f.getProperty().equals("password"));  // 排除字段的写法

qw.last("limit 10");                                  // 拼在 SQL 最末尾
qw.first("/*+ INDEX(user idx_age) */");               // 拼在 SELECT 之后
qw.apply("date_format(create_time,'%Y') = {0}", "2026"); // 参数化拼接（比 last 安全）
qw.exists("select 1 from dept d where d.id = user.dept_id");
qw.notExists(...);
```

`having` 是**唯一必须写字符串**的常用方法——因为聚合结果没有实体字段可引用。这是设计上的不得已，不算缺陷。

### 3.3 ⭐ condition 布尔参数：动态 SQL 的唯一正确姿势

**每一个条件方法**（`javap` 里数过，全部都有 `boolean` 首参重载）都支持：

```java
qw.eq(boolean condition, R column, Object val)
```

`condition == false` 时，这个条件**整条不拼进 SQL**（连 `AND` 都不加）。

```java
// ❌ 错：手动 if，代码爆炸
if (StringUtils.isNotBlank(name)) qw.like(User::getUsername, name);
if (age != null)                  qw.ge(User::getAge, age);

// ✅ 对：
LambdaQueryWrapper<User> qw = Wrappers.<User>lambdaQuery()
    .like(StringUtils.isNotBlank(name), User::getUsername, name)
    .ge(age != null, User::getAge, age)
    .between(start != null && end != null, User::getCreateTime, start, end)
    .orderByDesc(User::getCreateTime);
```

这就是 MP 里替代 XML `<if test="...">` 的东西，**一个 boolean 参数干掉一坨标签**。

> ⚠️ 但 `condition` 只是「拼不拼」，**不解决「值是否合法」**。`like(flag, ..., "")` 在 flag=true 时会拼出 `LIKE '%%'`（全表命中）。判空要写在 `condition` 里，别偷懒。

### 3.4 ⭐ 嵌套：`or()` 的优先级血案

**默认所有条件是 AND 连接。`or()` 直接破坏优先级。**

```java
// 需求：username = 'tom' AND (age > 18 OR email IS NULL)

// ❌ 错 → WHERE username='tom' AND age>18 OR email IS NULL
qw.eq(User::getUsername, "tom")
  .gt(User::getAge, 18)
  .or()
  .isNull(User::getEmail);

// ✅ 对 → WHERE username='tom' AND (age>18 OR email IS NULL)
qw.eq(User::getUsername, "tom")
  .and(w -> w.gt(User::getAge, 18).or().isNull(User::getEmail));
```

`Nested` 接口给了四个装括号的方法（`javap` 验证）：

| 方法 | 生成 SQL |
|------|---------|
| `and(Consumer)` | `AND ( ... )` |
| `or(Consumer)` | `OR ( ... )` |
| `nested(Consumer)` | `( ... )` ← **不带连接词**，让下一个条件决定 |
| `not(Consumer)` | `NOT ( ... )` |
| `or()` | 单个 `OR`（裸的，破坏优先级的就是它） |

`nested` 与 `and`/`or` 的区别值得记：`and(w->...)` 自带 `AND`，如果你前面已经有 `OR` 了，用 `nested` 才不会被强行接 `AND`。

```java
// 三个条件：A OR (B AND C)
qw.eq(User::getUsername, "tom")
  .or(w -> w.gt(User::getAge, 18).isNotNull(User::getEmail));
```

**口诀：只要句子里出现 `or`，就一定要有一个 `lambda` 包裹层。写的时候先在纸上画出括号，再翻译成代码。**

### 3.5 常用「结果方法」搭配

LambdaQueryWrapper 只是参数，真正执行靠 mapper / service：

```java
// Mapper 层
List<User>  list  = userMapper.selectList(qw);
User        one   = userMapper.selectOne(qw);            // 多于 1 条抛异常！
boolean     exist = userMapper.exists(qw);               // 3.5.x 新增，只查 1 条判存在
Long        count = userMapper.selectCount(qw);
List<Map<String,Object>> maps = userMapper.selectMaps(qw); // 只取几列时用它
IPage<User> page  = userMapper.selectPage(new Page<>(1, 10), qw);

// Service 层（继承 IService<User>）
User one = userService.getOne(Wrappers.<User>lambdaQuery().eq(User::getId, 1L));
User one = userService.getOne(qw, false);                // 第二条参数 throwEx=false：多条不抛，取第一条
Optional<User> opt = userService.getOneOpt(qw);          // 3.5.x 支持 Optional
List<User> list = userService.list(qw);
```

> `selectOne` 的 `throwEx`：`false` 时不抛异常返回第一条，但**这是掩盖脏数据的做法**。业务上「应该唯一」就该用 `true` 让它炸出来，早发现数据问题。

### 3.6 Service 层的链式写法 `lambdaQuery()`

`IService` 提供了一个直接出结果的方法（`javap` 验证 `IRepository` 里有）：

```java
// 不用先建 wrapper，直接链到底
User user = userService.lambdaQuery()
    .eq(User::getUsername, "tom")
    .one();

List<User> list = userService.lambdaQuery()
    .ge(User::getAge, 18)
    .orderByDesc(User::getId)
    .list();

long count = userService.lambdaQuery().eq(User::getAge, 18).count();
boolean has = userService.lambdaQuery().eq(User::getId, 1L).exists();
```

`lambdaQuery()` 返回的是 **`LambdaQueryChainWrapper`**（不是 `LambdaQueryWrapper`），它继承条件能力 + 自己带 `.list() / .one() / .count() / .exists() / .page()` 等终结方法。

**区别**：ChainWrapper **只能一次用完**（终结方法执行完就没法再加条件）；Wrapper 可以先攒条件、传多次、复用。

---

## 4. LambdaUpdateWrapper

### 4.1 为什么需要它

`updateById(entity)` 有个致命默认行为：**null 字段不更新**（MP 默认 `FieldStrategy.NOT_NULL`）。

所以这三件事 `updateById` 干不了：

1. 把字段**置空**（`set email = null`）
2. **原子自增**（`age = age + 1`，不需要先查再改，无并发问题）
3. **按条件批量改**（`update ... where status = 0`）

`LambdaUpdateWrapper` 全都能。

### 4.2 set 系列方法（`javap` 验证完整签名）

```java
LambdaUpdateWrapper<User> uw = new LambdaUpdateWrapper<>();

uw.set(User::getEmail, null);                 // SET email = null          ← updateById 做不到
uw.set(User::getStatus, 1);
uw.set(true, User::getRemark, "备注");         // 带 condition 的 set
uw.setSql("age = age + 1");                    // 裸 SQL
uw.setSql("email = concat(email, {0})", "@x"); // 参数化（安全）
uw.setIncrBy(User::getAge, 1);                 // 3.5.x 新增：SET age = age + 1  ← 推荐
uw.setDecrBy(User::getAge, 1);                 // 3.5.x 新增：SET age = age - 1

uw.eq(User::getId, 1L);                        // WHERE 条件和 QueryWrapper 一模一样
userMapper.update(null, uw);                   // 第一个参数传 null
```

**`setIncrBy` / `setDecrBy` 是 3.5.x 才加的**（`Update` 接口里 `javap` 能看到），比 `setSql("age = age + 1")` 干净，字段名也是方法引用不会拼错。老项目里见的都是 `setSql`。

### 4.3 `update(null, wrapper)` 的第一个参数到底是什么

`BaseMapper` 有两个 update 重载（`javap` 验证）：

```java
int updateById(T entity);                  // 实体全字段非 null 更新
int update(T entity, Wrapper<T> wrapper);  // 实体 + 条件
int update(Wrapper<T> wrapper);            // 3.5.x 新增单参数版本
```

`update(T entity, Wrapper<T> uw)` 里，**entity 的非 null 字段也会变成 SET 的一部分**，和 wrapper 的 set 合并：

```java
User u = new User();
u.setNickname("新昵称");        // 只有这一个字段非 null

LambdaUpdateWrapper<User> uw = Wrappers.<User>lambdaUpdate()
    .set(User::getEmail, null)  // 置空
    .eq(User::getId, 1L);

userMapper.update(u, uw);
// 生成：UPDATE user SET nickname='新昵称', email=null WHERE id=1
```

**传 `null` 就是「只用 wrapper 的 set」**，语义最清晰，推荐。混合用法只在「大部分字段从实体来、个别要置空/自增」时才划算。

### 4.4 `UpdateWrapper` vs `LambdaUpdateWrapper` vs 链式版

| 类 | 字段名写法 | 场景 |
|----|-----------|------|
| `UpdateWrapper<T>` | 字符串 `"age"` | 动态列名（列名来自变量）时不得不用 |
| `LambdaUpdateWrapper<T>` | 方法引用 `User::getAge` | ⭐ 99% 场景 |
| `LambdaUpdateChainWrapper<T>` | 方法引用 | Service 层 `.update()` 一次到底 |

```java
// UpdateWrapper 唯一优势：列名是变量
String col = "age";  // 来自配置/参数
new UpdateWrapper<User>().setSql(col + " = " + col + " + 1");
// ⚠️ 这就直接字符串拼 SQL 了，有注入风险，列名必须白名单校验

// Lambda 链式版（Service）
boolean ok = userService.lambdaUpdate()
    .set(User::getEmail, null)
    .eq(User::getId, 1L)
    .update();
```

`UpdateWrapper` 还有个副产品方法 `.lambda()`，能把字符串版转成 lambda 版继续用——迁移老代码时有用。

### 4.5 🔴 没有 WHERE 的 UPDATE / DELETE = 全表血案

```java
userMapper.update(null, new LambdaUpdateWrapper<User>().set(User::getStatus, 1));
// 💀 UPDATE user SET status=1     ← 没写 where，全表改了
```

两个防线：

**① 代码层**：永远先 `eq` 再 `set`，习惯性顺序。

**② 配置层：`BlockAttackInnerInterceptor`（防全表攻击）**

```java
@Bean
public MybatisPlusInterceptor mybatisPlusInterceptor() {
    MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();

    // ⚠️ 注意顺序：多租户 → 分页 → 防全表攻击（分页要最后，防全表要在业务拦截器之后）
    interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL));
    interceptor.addInnerInterceptor(new BlockAttackInnerInterceptor());  // 无 where 直接抛异常

    return interceptor;
}
```

它会拦截没有 `WHERE`（或 `WHERE` 恒真）的 `UPDATE` / `DELETE`，直接抛 `MybatisPlusException: Prohibition of table update operation`。

> 这个类在 **`mybatis-plus-jsqlparser`** 包里（3.5.9 拆分后），没引这个依赖会 `ClassNotFound`——和 `PaginationInnerInterceptor` 同一个包，引一次两个都能用。

---

## 5. 二者协同：一个真实的 service 方法

```java
@Service
@RequiredArgsConstructor
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements IUserService {

    /** 分页条件查询 */
    public IPage<User> page(UserQueryDTO dto) {
        LambdaQueryWrapper<User> qw = Wrappers.<User>lambdaQuery()
            .like(StringUtils.isNotBlank(dto.getKeyword()), User::getUsername, dto.getKeyword())
            .eq(dto.getStatus() != null, User::getStatus, dto.getStatus())
            .between(dto.getStartTime() != null && dto.getEndTime() != null,
                     User::getCreateTime, dto.getStartTime(), dto.getEndTime())
            .and(dto.getOnlyVip(), w -> w.gt(User::getVipLevel, 0).or().isNotNull(User::getVipExpire))
            .select(User::getId, User::getUsername, User::getStatus, User::getCreateTime)
            .orderByDesc(User::getCreateTime);

        return page(new Page<>(dto.getPageNo(), dto.getPageSize()), qw);
    }

    /** 变更状态 + 原子累加积分（不能先查再改） */
    public void approve(Long userId) {
        boolean ok = lambdaUpdate()
            .set(User::getStatus, 1)
            .setIncrBy(User::getScore, 10)
            .eq(User::getId, userId)
            .eq(User::getStatus, 0)   // ← 幂等保护：已审批过的不会再改
            .update();

        if (!ok) throw new BizException("用户不存在或已审批");
    }
}
```

`approve()` 里的 `.eq(User::getStatus, 0)` 很重要：**没有它，重复调用会把积分加两次**。带上它就是一次 CAS（compare-and-set），返回 `false` 说明没命中，天然幂等。

---

## 6. 踩坑清单（按踩到的频率排序）

1. **`or()` 没包括号** → 优先级错乱查出脏数据。句子里有 or 就必须有 lambda 包裹层。
2. **`updateById` 置空失效** → 默认 null 不更新。置空必须 `LambdaUpdateWrapper.set(field, null)`。
3. **没有 WHERE 的 update/delete** → 全表。装配 `BlockAttackInnerInterceptor`。
4. **`in()` 传空集合** → `IN ()` 语法错误。条件前面加 `CollUtil.isNotEmpty(ids)` 判断。
5. **`selectOne` 抛 `TooManyResultsException`** → 忘了 `.last("limit 1")`，或数据本身不唯一。先想清楚「是否真唯一」再决定用 `throwEx=false` 还是加 limit。
6. **复用一个 wrapper 传多次** → wrapper 内部有 `paramNameSeq` 和 `paramNameValuePairs` 状态，**同一实例第二次使用序号和值可能错位**。要复用请每次 `new`。
7. **`like` 的 `%` 位置搞反** → `likeRight("tom")` 是 `tom%`（前缀匹配，能走索引），`like("tom")` 是两侧模糊（**索引失效**）。查询接口用哪个要想清楚。
8. **`orderBy` 用了 SQL 函数** → `orderByDesc(User::getAge, ...)` 只能传字段，要 `ORDER BY IF(...)` 得用 `last()` 或 `orderBy(..., "sql")`。
9. **`having` 里塞了用户输入** → 它是纯字符串拼接，注入风险，必须白名单。
10. **`setIncrBy` 在 3.5.9 之前不存在** → 老版本只能 `setSql`，升级后可以简化但要注意别升出兼容问题。
11. **`condition` 参数传了 `true` 但值是空串/空集合** → 仍然拼条件，`LIKE '%%'` 全命中。condition 要表达「值有效」而不是「flag 打开了」。
12. **wrapper 里的 lambda 方法引用在 `@Transactional` 代理对象上取不到** → 极少数情况（CGLIB 代理 + 方法引用在代理类上解析），报「can not find lambda cache for this entity」。解法：用 `new LambdaQueryWrapper<>(User.class)` 显式指定实体类。

---

## 7. 和上一章的呼应

`01 - MyBatis-Plus` 里讲了 MP 的增强都是「拦截器 + 注解」，这一章的两个 Wrapper 是**纯应用层**的东西，不涉及拦截器——它们就是「**Java 对象树 → SQL 片段字符串**」的构造器。

真正的对应关系：

| 你写的代码 | MP 内部 | 结果 |
|-----------|---------|------|
| `qw.eq(User::getAge, 18)` | 往 `MergeSegments` 里追加 `NormalSegment` | `AND age = #{ew.paramNameValuePairs.MPGENVAL1}` |
| `uw.set(User::getEmail, null)` | 往 `SharedString sqlSet` 拼 | `SET email = null` |
| `@TableLogic` | `LogicDeleteInnerInterceptor` | 自动追加 `AND deleted = 0` |
| 分页 `selectPage` | `PaginationInnerInterceptor` 改写 SQL | 追加 `LIMIT ?,?` 并自动 count |

**记忆抓手**：Wrapper 管「条件怎么写」，拦截器管「SQL 出去前怎么改」。两套机制正交，可以叠加。

---

## 8. 一页速查

```java
// 建
Wrappers.<User>lambdaQuery()     Wrappers.<User>lambdaUpdate()
new LambdaQueryWrapper<User>()   new LambdaUpdateWrapper<User>()

// 条件（两者共有）
eq ne gt ge lt le between notBetween
like likeLeft likeRight notLike notLikeLeft notLikeRight
in notIn isNull isNotNull
and(c) or(c) nested(c) not(c)
orderByAsc orderByDesc groupBy having
// 每个都有 boolean condition 首参重载

// 查询专有
select(...)  last(...)  first(...)  apply(...)  exists(...)  notExists(...)

// 更新专有
set(col, val)  set(cond, col, val)  setSql(...)  setIncrBy  setDecrBy

// 执行
mapper.selectList/selectOne/exists/selectCount/selectPage/wrapper
mapper.update(null, uw) / mapper.update(entity, uw)
service.list/one/count/exists/page/lambdaQuery()/lambdaUpdate()
```

---

> 📌 学习日期：2026-11-18
> 📌 相关：`springcloud/01-MyBatisPlus.md`（Wrapper 家族总览 + 注解 + 拦截器）
> 📌 验证方式：MyBatis-Plus 3.5.9 jar 下载后用 `javap` 逐个核对方法签名，区别于此前的博客式记录
