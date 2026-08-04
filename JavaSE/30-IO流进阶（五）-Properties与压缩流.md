# IO 流进阶（五）- Properties 配置处理与压缩流

> JavaSE 进阶：Properties 配置文件读写 · 压缩流（ZipOutputStream/ZipInputStream） · 解压流
> 课程：黑马 JavaSE 进阶/高级（BV1yW4y1Y7Ms · P95-P110）

---

## 一、Properties

`Properties` 继承自 `Hashtable`，本质是一个 Map 集合，但**键值对都是 String 类型**。常用于读写 `.properties` 配置文件。

### 1.1 常用方法

```java
// 创建对象
Properties prop = new Properties();

// 存/取（Map 方法）
prop.setProperty("key", "value");       // 存
String val = prop.getProperty("key");   // 取
Set<String> keys = prop.stringPropertyNames(); // 获取所有键

// 与 IO 结合
prop.load(new FileReader("config.properties"));       // 从文件加载
prop.store(new FileWriter("config.properties"), null); // 写入文件
```

### 1.2 读写配置文件

**config.properties：**
```properties
username=admin
password=123456
timeout=5000
```

**加载配置：**
```java
Properties prop = new Properties();
prop.load(new FileReader("config.properties"));

String username = prop.getProperty("username");  // "admin"
String password = prop.getProperty("password");  // "123456"
int timeout = Integer.parseInt(prop.getProperty("timeout")); // 5000
```

### 1.3 修改配置并保存

```java
Properties prop = new Properties();
prop.load(new FileReader("config.properties"));

// 修改或新增
prop.setProperty("timeout", "10000");
prop.setProperty("url", "jdbc:mysql://localhost:3306/db");

// 写回文件（会覆盖原文件）
prop.store(new FileWriter("config.properties"), "Updated config");
```

**📌 注意：** `.store()` 会写入注释和时间戳，如果不想要可以传 `null`。

---

## 二、压缩流（ZipOutputStream）

Java 用 `ZipOutputStream` 和 `ZipInputStream` 处理 ZIP 压缩。

### 2.1 压缩单个文件

```java
// 创建压缩输出流
ZipOutputStream zos = new ZipOutputStream(new FileOutputStream("out.zip"));

// 创建压缩条目
File file = new File("test.txt");
ZipEntry entry = new ZipEntry(file.getName());
zos.putNextEntry(entry);

// 写入文件内容
FileInputStream fis = new FileInputStream(file);
byte[] bytes = new byte[8192];
int len;
while ((len = fis.read(bytes)) != -1) {
    zos.write(bytes, 0, len);
}

fis.close();
zos.closeEntry();
zos.close();
```

### 2.2 压缩整个目录

```java
public static void zipDir(File source, ZipOutputStream zos, String parent) throws IOException {
    File[] files = source.listFiles();
    if (files == null) return;

    for (File file : files) {
        if (file.isDirectory()) {
            // 递归处理子目录
            zipDir(file, zos, parent + file.getName() + "/");
        } else {
            // 文件：创建 ZipEntry
            ZipEntry entry = new ZipEntry(parent + file.getName());
            zos.putNextEntry(entry);

            FileInputStream fis = new FileInputStream(file);
            byte[] bytes = new byte[8192];
            int len;
            while ((len = fis.read(bytes)) != -1) {
                zos.write(bytes, 0, len);
            }
            fis.close();
            zos.closeEntry();
        }
    }
}
```

### 2.3 解压

```java
ZipInputStream zis = new ZipInputStream(new FileInputStream("out.zip"));
ZipEntry entry;

while ((entry = zis.getNextEntry()) != null) {
    System.out.println("解压: " + entry.getName());

    // 如果是目录，创建目录
    File file = new File("dest/" + entry.getName());
    if (entry.isDirectory()) {
        file.mkdirs();
    } else {
        // 确保父目录存在
        file.getParentFile().mkdirs();
        // 写出文件
        FileOutputStream fos = new FileOutputStream(file);
        byte[] bytes = new byte[8192];
        int len;
        while ((len = zis.read(bytes)) != -1) {
            fos.write(bytes, 0, len);
        }
        fos.close();
    }
    zis.closeEntry();
}
zis.close();
```

### 2.4 Apache Commons-Compress

除了 Java 自带的 ZIP，Commons-Compress 支持更多格式（tar.gz、7z、rar 等），但这不是本课程的重点。

---

## 三、IO 流小结

### 字节流 vs 字符流

| | 字节流 | 字符流 |
|--|--------|--------|
| 基类 | InputStream / OutputStream | Reader / Writer |
| 数据单位 | 字节 (byte) | 字符 (char) |
| 适用场景 | 图片、视频、音频等二进制 | 文本文件 |
| 编码问题 | 不处理编码 | 自动处理编码 |

### 流类体系

```
字节输入流 InputStream
  ├── FileInputStream：文件输入
  ├── BufferedInputStream：缓冲
  ├── ObjectInputStream：反序列化
  └── ZipInputStream：解压

字节输出流 OutputStream
  ├── FileOutputStream：文件输出
  ├── BufferedOutputStream：缓冲
  ├── ObjectOutputStream：序列化
  ├── PrintStream：打印
  └── ZipOutputStream：压缩

字符输入流 Reader
  ├── FileReader：文件输入
  ├── BufferedReader：缓冲 + readLine()
  └── InputStreamReader：转换流（字节→字符）

字符输出流 Writer
  ├── FileWriter：文件输出
  ├── BufferedWriter：缓冲 + newLine()
  └── OutputStreamWriter：转换流（字符→字节）
```

### 选择原则

1. **纯文本** → 字符流（Reader/Writer）
2. **二进制文件**（图片/音视频） → 字节流
3. **需要缓冲** → 加 BufferedXXX
4. **需要编码转换** → 转换流（InputStreamReader/OutputStreamWriter）
5. **序列化对象** → ObjectOutputStream/ObjectInputStream
6. **读写配置** → Properties + load/store
7. **压缩文件** → ZipOutputStream/ZipInputStream

---

> **📝 笔记说明：** 本章对应 P95~P110，包括 Properties 配置处理、压缩流/解压流。项目练习（拼图游戏、随机点名器等）因已学过 JavaWeb，直接跳过。
