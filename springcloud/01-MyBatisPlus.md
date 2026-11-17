# 01 · MyBatis-Plus 快速上手与进阶

> 课程：黑马 2026 微服务技术栈（BV1S142197x7）· 第一模块
> 配套：`javaweb/06-JDBC与MyBatis.md`（先看那篇再看这篇）

---

## 1. 它到底是什么

一句话：**MyBatis-Plus（MP）是 MyBatis 的增强工具，只做增强不做改变。**

- 底层仍然是 MyBatis，SqlSessionFactory、Mapper 接口、`#{}` 占位符、`resultType` 映射——整套东西一个字没动
- MP 在 MyBatis 之上加了一层**通用 Mapper**：启动时用反射读实体类，自动帮你生成单表的增删改查 SQL
- 所以：**单表 CRUD 不用写 SQL，复杂 SQL 照样写 XML**

```
你的 Mapper 接口
      ↓ extends
   BaseMapper<T>          ← MP 提供的，自带 17 个方法
      ↓
  MyBatis 原生 Mapper
      ↓
    数据库
```

### 1.1 和 MyBatis 的对照

| 能力 | 原生 MyBatis | MyBatis-Plus |
|------|-------------|--------------|
| 单表 CRUD | 每个方法写 SQL / XML | 继承 `BaseMapper` 白拿 |
| 分页 | 手写 `limit`，自己 count | 一个拦截器搞定，还帮你 count |
| 条件查询 | XML 里一堆 `<if test>` | `LambdaQueryWrapper` 链式拼 |
| 逻辑删除 | 每个 SQL 手动加 `deleted=0` | 注解 + 全局配置，自动加 |
| 字段自动填充 | 手写 setter | `MetaObjectHandler` 统一填 |
| 乐观锁 | 自己写 `version = version + 1` | `@Version` + 拦截器 |
| 代码生成 | 无 | 代码生成器一键出全套 |

> ⚠️ 注意别搞混：MP **不是 ORM 框架**（不是 JPA/Hibernate 那种全自动映射），它是「MyBatis 的脚手架」，SQL 依然可控可读。

---

## 2. 快速上手

### 2.1 依赖

Spring Boot 3.x 用 `mybatis-plus-spring-boot3-starter`（包名带 `spring-boot3`，别用错成 2.x 的 `spring-boot-starter`）。

```xml
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-spring-boot3-starter</artifactId>
    <version>3.5.9</version>
</dependency>

<!-- MP 3.5.9 起，分页插件被拆出去了，要单独引 -->
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-jsqlparser</artifactId>
    <version>3.5.9</version>
</dependency>

<dependency>
    <groupId>com.mysql</groupId>
    <artifactId>mysql-connector-j</artifactId>
    <scope>runtime</scope>
</dependency>
```

### 2.2 配置文件

```yaml
spring:
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://localhost:3306/mp_demo?serverTimezone=Asia/Shanghai&useUnicode=true&characterEncoding=utf8
    username: root
    password: 1234

mybatis-plus:
  configuration:
    map-underscore-to-camel-case: true    # 下划线转驼峰，默认就是 true
    log-impl: org.apache.ibatis.logging.stdout.StdOutImpl   # 打印 SQL，调试点必开
  global-config:
    db-config:
      id-type: assign_id                  # 全局主键策略：雪花算法
      logic-delete-field: deleted         # 全局逻辑删除字段
      logic-delete-value: 1
      logic-not-delete-value: 0
  mapper-locations: classpath*:/mapper/**/*.xml   # 只有写 XML 才需要
```

### 2.3 实体类

```java
@Data
@TableName("tb_user")                       // 表名和类名不一致时必须写
public class User {
    @TableId(type = IdType.ASSIGN_ID)       // 主键，雪花算法
    private Long id;

    private String username;                // → username
    private String password;

    @TableField("nick_name")                // 字段名不一致时映射
    private String nickName;

    private Integer age;
    private String email;

    @TableField(fill = FieldFill.INSERT)    // 插入时自动填
    private LocalDateTime createTime;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;

    @TableLogic                             // 逻辑删除字段
    private Integer deleted;

    @Version                                // 乐观锁版本号
    private Integer version;

    @TableField(exist = false)              // 数据库里没有这个字段
    private String tempField;
}
```

### 2.4 Mapper

```java
@Mapper
public interface UserMapper extends BaseMapper<User> {
    // 单表 CRUD 一行不写就有
}

// 启动类上加 @MapperScan("com.example.mapper") 可以代替逐个 @Mapper
```

### 2.5 Service

MP 提供了 `IService` + `ServiceImpl`，把 Mapper 的 CRUD 再包一层，加了批量操作。

```java
public interface IUserService extends IService<User> { }

@Service
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements IUserService { }
```

```java
// 使用
userService.save(user);                    // 单条新增
userService.saveBatch(list);                // 批量新增（默认 1000 一批，分批提交）
userService.saveOrUpdate(user);             // 存在就改，不存在就增
userService.getById(1L);
userService.list();                         // 全表
userService.removeById(1L);
userService.count();
```

---

## 3. BaseMapper 的 17 个方法

MP 3.5.x 的 `BaseMapper<T>` 提供的全部方法，背下来能省一半时间：

### 增
| 方法 | 说明 |
|------|------|
| `insert(T entity)` | 插入，返回影响行数 |

### 删
| 方法 | 说明 |
|------|------|
| `deleteById(Serializable id)` | 按主键删 |
| `deleteByMap(Map<String,Object>)` | 按 map 条件删（老 API，少用） |
| `delete(Wrapper<T>)` | 按条件删 |
| `deleteBatchIds(Collection<?>)` | 按主键批量删 |

### 改
| 方法 | 说明 |
|------|------|
| `updateById(T entity)` | 按主键改，**只改非 null 字段** |
| `update(T entity, Wrapper<T>)` | 按条件改 |

### 查
| 方法 | 说明 |
|------|------|
| `selectById(Serializable id)` | 按主键查 |
| `selectBatchIds(Collection)` | 按主键批量查 |
| `selectByMap(Map)` | 按 map 条件查 |
| `selectOne(Wrapper)` | 查一条，**多于一条会抛异常** |
| `selectCount(Wrapper)` | 查总数 |
| `selectList(Wrapper)` | 查列表 |
| `selectMaps(Wrapper)` | 查成 `List<Map>`，适合只取几个字段 |
| `selectObjs(Wrapper)` | 只查第一列，查成 `List<Object>` |
| `selectPage(IPage<T>, Wrapper)` | 分页 |
| `selectMapsPage(IPage<Map>, Wrapper)` | 分页成 Map |

> 💡 `updateById` 的坑：**null 字段不更新**。想置空必须用 `UpdateWrapper.set()` 或全局配置 `update-strategy`。

---

## 4. Wrapper 条件构造器

这是 MP 最核心的 API。所有条件查询都靠它。

### 4.1 家族

```
Wrapper（抽象类）
 ├─ AbstractWrapper（提供 eq/like/gt/... 所有条件方法）
 │   ├─ QueryWrapper<T>             字符串字段名
 │   ├─ QueryChainWrapper<T>        链式 lambda（.list() 直出结果）
 │   └─ LambdaQueryWrapper<T>       方法引用，防手写字段名错
 ├─ UpdateWrapper<T>                拼 set 条件
 └─ LambdaUpdateWrapper<T>
```

**永远优先用 Lambda 版**——字段名写在方法引用里，重构改名不会漏。

### 4.2 常用条件

```java
LambdaQueryWrapper<User> qw = new LambdaQueryWrapper<>();

// 比较
qw.eq(User::getUsername, "tom");           // = 
qw.ne(User::getAge, 18);                   // <>
qw.gt(User::getAge, 18);                   // >
qw.ge(User::getAge, 18);                   // >=
qw.lt / le                                 // < / <=

// 区间
qw.between(User::getAge, 18, 30);          // BETWEEN ... AND

// 模糊
qw.like(User::getUsername, "tom");         // %tom%
qw.likeLeft(User::getUsername, "tom");     // %tom
qw.likeRight(User::getUsername, "tom");    // tom%

// 集合
qw.in(User::getId, Arrays.asList(1, 2, 3));
qw.notIn(User::getId, ids);

// 空值（重要！）
qw.isNull(User::getEmail);
qw.isNotNull(User::getEmail);

// 排序
qw.orderByAsc(User::getAge);
qw.orderByDesc(User::getCreateTime);

// 分组 / having
qw.groupBy(User::getAge);
qw.having("count(*) > 1");

// 只查指定字段（省带宽）
qw.select(User::getId, User::getUsername);

// 最后拼一段 SQL（慎用，有注入风险）
qw.last("limit 10");
```

### 4.3 条件判断：if 拼接的正确写法

```java
// ❌ 错：每次都调用，条件为 null 时行为不可控
qw.eq(StringUtils.isNotBlank(name), User::getUsername, name);

// ✅ 对：第一个参数是布尔，false 时整个条件不拼进去
LambdaQueryWrapper<User> qw = new LambdaQueryWrapper<User>()
    .eq(StringUtils.isNotBlank(name), User::getUsername, name)
    .ge(age != null, User::getAge, age)
    .orderByDesc(User::getCreateTime);
```

这就是 MP 替代 XML 里 `<if test="...">` 的方式。**所有 `eq/like/gt` 重载里都有一个 `boolean condition` 版本**，动态 SQL 全靠它。

### 4.4 嵌套条件（and / or）

这是个高频坑点：**默认全部用 AND 连接，`or()` 会破坏优先级**。

```java
// 需求：username = 'tom' AND (age > 18 OR email IS NULL)

// ❌ 错：变成 username='tom' AND age>18 OR email IS NULL
qw.eq(User::getUsername, "tom").gt(User::getAge, 18).or().isNull(User::getEmail);

// ✅ 对：用 and(...) 包成一个整体
qw.eq(User::getUsername, "tom")
  .and(w -> w.gt(User::getAge, 18).or().isNull(User::getEmail));
// 生成：WHERE username = ? AND ( age > ? OR email IS NULL )
```

规则：**只要出现 `or()`，就必须用 `and(...)` / `or(...)` 的 lambda 形式包一层**。

### 4.5 UpdateWrapper：把字段置空 / 自增

```java
LambdaUpdateWrapper<User> uw = new LambdaUpdateWrapper<>();
uw.set(User::getEmail, null)                // set email = null
  .setSql("age = age + 1")                  // 原子自增（不用先查再改）
  .eq(User::getId, 1L);
userMapper.update(null, uw);
```

`update(null, uw)` 的第一个参数传 `null`，表示只按 wrapper 里的 set 改。

---

## 5. 常用注解逐个数

### 5.1 `@TableName`

```java
@TableName("tb_user")                              // 指定表名
@TableName(value = "tb_user", schema = "shop")     // 连库名一起
@TableName(autoResultMap = true)                   // 需要字段类型处理器时开
```

> 默认规则：类名驼峰转下划线（`UserInfo` → `user_info`）。开启 `table-prefix` 可以统一加前缀。

### 5.2 `@TableId` 主键策略

`IdType` 五个值，**这是必须记住的一张表**：

| 策略 | 说明 | 何时用 |
|------|------|--------|
| `AUTO` | 数据库自增 | 数据库建表用 `AUTO_INCREMENT` |
| `NONE` | 跟随全局配置 | 默认 |
| `INPUT` | 手动 set | 自己生成 ID（如 UUID） |
| `ASSIGN_ID` | **雪花算法**（Long/String） | ⭐ 默认值，分布式首选 |
| `ASSIGN_UUID` | UUID（无横线，32 位） | 不想暴露自增规律时 |

**雪花算法**：64 bit = 1 符号位 + 41 时间戳（约 69 年）+ 10 机器 ID + 12 序列号（单机每毫秒 4096 个）。

为什么分布式系统要它：数据库自增在多库分表下会撞，雪花算法**不用访问数据库就能保证全局唯一**。

> ⚠️ Long 型 ID 传给前端会丢精度（JS Number 只有 53 位有效）。解决：Jackson 配置 `ToStringSerializer` 把 Long 序列化成字符串，或实体字段直接用 `String`。

### 5.3 `@TableField`

```java
@TableField("nick_name")           // 字段名映射
@TableField(exist = false)         // 不是数据库字段（VO 字段）
@TableField(select = false)        // 查询时不返回（密码等敏感字段）
@TableField(fill = FieldFill.INSERT)             // 插入时自动填
@TableField(fill = FieldFill.INSERT_UPDATE)      // 插入和更新都填
@TableField(fill = FieldFill.UPDATE)             // 只有更新时填
@TableField(updateStrategy = FieldStrategy.NOT_NULL)   // 更新策略
```

### 5.4 `@TableLogic` 逻辑删除

```java
@TableLogic
private Integer deleted;
```

配置：

```yaml
mybatis-plus:
  global-config:
    db-config:
      logic-delete-value: 1        # 删了变成 1
      logic-not-delete-value: 0    # 没删是 0
```

**关键：配置之后，下面这些操作全部自动改写 SQL——你不用改任何业务代码**

| 你写的 | 实际执行的 SQL |
|--------|---------------|
| `deleteById(1)` | `UPDATE tb_user SET deleted=1 WHERE id=1 AND deleted=0` |
| `selectById(1)` | `SELECT ... WHERE id=1 AND deleted=0` |
| `selectList(w)` | `SELECT ... WHERE ... AND deleted=0` |
| `update(...)` | `UPDATE ... WHERE ... AND deleted=0` |

> ⚠️ 两个坑：
> 1. **XML 手写 SQL 不受影响**，得自己加 `deleted = 0`
> 2. 逻辑删除后唯一索引会冲突（旧记录还在表里），需要配合「删除时同时改某个唯一字段」或改用 `NULL` 语义

---

## 6. 自动填充：MetaObjectHandler

创建时间、更新时间、创建人这些字段每次都手写太烦。MP 提供了统一入口。

### 6.1 实体加注解

```java
@TableField(fill = FieldFill.INSERT)
private LocalDateTime createTime;

@TableField(fill = FieldFill.INSERT_UPDATE)
private LocalDateTime updateTime;
```

### 6.2 写处理器

```java
@Component
public class MyMetaObjectHandler implements MetaObjectHandler {

    @Override
    public void insertFill(MetaObject metaObject) {
        this.strictInsertFill(metaObject, "createTime", LocalDateTime.class, LocalDateTime.now());
        this.strictInsertFill(metaObject, "updateTime", LocalDateTime.class, LocalDateTime.now());
        // 需要从上下文取用户时也从这拿
        // this.strictInsertFill(metaObject, "createBy", Long.class, UserContext.getUserId());
    }

    @Override
    public void updateFill(MetaObject metaObject) {
        this.strictUpdateFill(metaObject, "updateTime", LocalDateTime.class, LocalDateTime.now());
    }
}
```

> ⚠️ 坑：`strictInsertFill` 只在该字段**当前为 null** 时才填。如果你先手动 set 了值，填充就会被跳过。
> 一定要覆盖已有值时用 `setFieldValByName("updateTime", LocalDateTime.now(), metaObject)`。

---

## 7. 乐观锁

### 7.1 解决的问题

两个人同时改一条数据，后提交的会**覆盖**先提交的（丢失更新）。

```
A 读 age=18  →  A 改成 19
B 读 age=18  →  B 改成 20     最终 20，A 的修改丢了
```

### 7.2 MP 的做法

```java
// 1. 实体加 @Version
@Version
private Integer version;
```

```java
// 2. 注册拦截器（和分页一起）
@Configuration
public class MybatisPlusConfig {
    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
        interceptor.addInnerInterceptor(new OptimisticLockerInnerInterceptor());
        interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL));
        return interceptor;
    }
}
```

**注意顺序：乐观锁拦截器必须在分页拦截器之前。**

```java
// 3. 用的时候：先查，再改，改的时候必须带着查出来的 version
User user = userMapper.selectById(1L);   // version = 3
user.setAge(19);
userMapper.updateById(user);
// SQL: UPDATE tb_user SET age=19, version=4 WHERE id=1 AND version=3
```

返回影响行数为 0 → 说明被别人改过了，业务层要提示重试。

> ⚠️ 三个前提，缺一不可：
> 1. `@Version` 注解
> 2. 注册 `OptimisticLockerInnerInterceptor`
> 3. **必须 `updateById(entity)`，且 entity 里 version 有值**——如果只传 id 不传 version，拦截器不生效
>
> 另外：`update(entity, wrapper)` 这种写法**不支持**乐观锁，只有 `updateById` 支持。

---

## 8. 分页：拦截器模式

### 8.1 为什么是「拦截器」而不是「SQL 改写工具」

MP 的哲学：**所有增强都通过 MyBatis 的插件（Interceptor）机制挂在 SQL 执行链上**。

```
你的 Mapper 方法
   ↓
MyBatis 执行器 Executor
   ↓
┌────────────── 拦截链（按注册顺序）──────────────┐
│ 分页拦截器 → 解析 SQL → 追加 LIMIT → 自动 COUNT │
│ 乐观锁拦截器 → 给 UPDATE 追加 version 条件       │
│ 防止全表更新删除拦截器                           │
└────────────────────────────────────────────────┘
   ↓
数据库
```

### 8.2 配置

```java
@Bean
public MybatisPlusInterceptor mybatisPlusInterceptor() {
    MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();

    // 分页（建议最后加）
    PaginationInnerInterceptor page = new PaginationInnerInterceptor(DbType.MYSQL);
    page.setMaxLimit(500L);          // 单页最大条数，防止被刷爆
    page.setOverflow(false);         // 页码超出总页数时：false 返回空，true 回到第一页
    interceptor.addInnerInterceptor(page);

    return interceptor;
}
```

### 8.3 使用

```java
Page<User> page = new Page<>(1, 10);          // 第 1 页，每页 10 条
LambdaQueryWrapper<User> qw = new LambdaQueryWrapper<User>()
        .like(User::getUsername, "tom");

IPage<User> result = userMapper.selectPage(page, qw);

result.getRecords();      // 当前页数据
result.getTotal();        // 总记录数
result.getPages();        // 总页数
result.getCurrent();      // 当前页码
result.getSize();         // 每页条数
```

### 8.4 分页的几个细节

1. **自动 COUNT**：查数据前会先执行一次 `SELECT COUNT(*)`，并把原 SQL 的 `ORDER BY` 去掉（否则 count 很慢）。如果 SQL 有 `GROUP BY` 导致 count 不准，可以自定义 count SQL。
2. **不分页不查 count**：`page.setSearchCount(false)` 可以跳过 count（比如移动端下拉刷新只要数据）。
3. **自定义 Mapper 方法分页**：第一个参数必须是 `IPage`，返回值也必须带 `IPage`。

```java
@Mapper
public interface UserMapper extends BaseMapper<User> {
    IPage<User> selectByAge(IPage<User> page, @Param("age") Integer age);
}
```

### 8.5 踩坑

- **没注册拦截器 → 分页不生效，返回全量数据**（最常见）
- 忘记引 `mybatis-plus-jsqlparser` → 启动直接报 `ClassNotFoundException: net.sf.jsqlparser...`
- 拦截器顺序错 → 乐观锁失效或分页失效

---

## 9. 代码生成器

MP 3.5.x 用的是新版的 `FastAutoGenerator`。

```xml
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-generator</artifactId>
    <version>3.5.9</version>
</dependency>
<dependency>
    <groupId>org.apache.velocity</groupId>
    <artifactId>velocity-engine-core</artifactId>
    <version>2.3</version>
</dependency>
```

```java
public class CodeGenerator {
    public static void main(String[] args) {
        FastAutoGenerator.create("jdbc:mysql://localhost:3306/mp_demo", "root", "1234")
            // 全局配置
            .globalConfig(builder -> builder
                .author("JiangYuxin")
                .outputDir(System.getProperty("user.dir") + "/src/main/java")
                .disableOpenDir())
            // 包配置
            .packageConfig(builder -> builder
                .parent("com.example")
                .moduleName("user")
                .entity("po")
                .mapper("mapper")
                .service("service")
                .serviceImpl("service.impl")
                .controller("controller"))
            // 策略配置
            .strategyConfig(builder -> builder
                .addInclude("tb_user")                    // 要生成的表
                .addTablePrefix("tb_")                    // 去掉表前缀
                .entityBuilder()
                    .enableLombok()
                    .logicDeleteColumnName("deleted")     // 逻辑删除字段
                    .versionColumnName("version")         // 乐观锁字段
                    .enableTableFieldAnnotation()         // 加 @TableField
                .controllerBuilder()
                    .enableRestStyle()                    // @RestController
                .serviceBuilder()
                    .formatServiceFileName("%sService"))
            .execute();
    }
}
```

生成出来：Entity + Mapper + Mapper.xml + Service + ServiceImpl + Controller。**修修补补比从零写快得多。**

---

## 10. 选型：什么时候别用 MP

MP 不是银弹，这几类场景建议老老实实写 MyBatis XML：

| 场景 | 原因 |
|------|------|
| 多表 JOIN 查询结果集 | Wrapper 只能拼单表，多表还是 XML 清晰 |
| 复杂动态 SQL（几十个 if） | XML 的 `<if>/<choose>` 可读性反而更好 |
| 需要精细控制 SQL（性能调优） | Wrapper 生成的 SQL 有时不是最优 |
| 存储过程 / 复杂子查询 | 直接写 XML |

**经验法则：单表用 MP，多表用 XML，两者在同一个 Mapper 里共存完全没问题。**

---

## 11. 踩坑清单

1. **依赖包名错**：Spring Boot 3 必须用 `mybatis-plus-spring-boot3-starter`，用成 `mybatis-plus-boot-starter` 会启动失败
2. **3.5.9+ 分页要额外引 `mybatis-plus-jsqlparser`**，否则 `ClassNotFoundException`
3. **不注册 `MybatisPlusInterceptor` → 分页静默失效**，返回全量数据，不报错
4. **拦截器顺序**：乐观锁 → 分页（顺序错则乐观锁失效）
5. **`updateById` 不更新 null**：想置空必须用 `UpdateWrapper.set(field, null)`
6. **乐观锁只有 `updateById` 生效**，`update(entity, wrapper)` 不支持
7. **`or()` 破坏优先级**：出现 `or` 必须用 `and(w -> ...)` 包起来
8. **逻辑删除对 XML 手写 SQL 无效**，要自己加 `deleted = 0`
9. **`strictInsertFill` 只填 null 字段**，已有值会跳过
10. **Long 主键传给前端丢精度**，要序列化成 String
11. **`selectOne` 查到多条直接抛 `TooManyResultsException`**，别拿来当「取第一条」
12. **`@TableField(exist = false)` 忘了加** → MP 把 VO 字段当数据库字段拼进 SQL，报 `Unknown column`

---

## 12. 和前面学的打通

MP 是「微服务地基」这个定位很准，往后看会发现它反复出现：

- **微服务拆分后**：每个服务一个库，MP 的单表 CRUD 正好覆盖 80% 的日常操作，剩下 20% 复杂查询写 XML
- **雪花算法 = 分布式 ID 的必要性**：多库分表后数据库自增必然撞，这也是后面要学分布式 ID 方案的起点
- **乐观锁 vs 分布式锁**：乐观锁解决单行并发，跨服务/跨资源还得上 Redis 分布式锁（Redis 篇学过的那套）
- **多租户**：MP 有 `TenantLineInnerInterceptor`，靠拦截器给所有 SQL 自动加 `tenant_id` 条件——和逻辑删除同一套思路，也是 SaaS 系统的标准做法

> 一句话总结：**MP 的价值不在「少写 SQL」，而在「把企业开发里反复出现的横切关注点（分页/逻辑删除/填充/乐观锁/多租户）统一成拦截器和注解」。** 这和后面学的 Spring AOP、MyBatis 插件、微服务网关是同一个思路——横切逻辑，统一插桩。

---

## 附：一句话速查

```
MP = MyBatis 增强，单表零 SQL，多表仍写 XML

继承 BaseMapper<T>  → 17 个方法白拿
继承 ServiceImpl    → saveBatch/saveOrUpdate 等

条件统一 LambdaQueryWrapper，动态条件用 eq(boolean, ...)
出现 or 必须 and(w -> ...) 包起来

@TableId(ASSIGN_ID)  雪花 ID
@TableLogic          逻辑删除（自动加 deleted=0）
@Version + 拦截器    乐观锁（只认 updateById）
MetaObjectHandler    自动填充
MybatisPlusInterceptor 里挂分页 + 乐观锁（注意顺序）
```
