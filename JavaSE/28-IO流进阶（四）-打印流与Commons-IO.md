# IO流进阶（四）- 打印流与 Commons-IO

## 1. 打印流

### 1.1 概述

**打印流**只有输出流，没有输入流。分为字节打印流和字符打印流，但它们有**共同的特点**：

- **只负责输出**，不负责读
- **永不抛出 IOException**（内部捕获了，可以通过 checkError() 检查）
- **有自动刷新**（自动 flush）机制
- 可以方便地打印**各种数据类型**

### 1.2 PrintStream（字节打印流）

```java
// 构造方法
PrintStream(OutputStream out)
PrintStream(File file)
PrintStream(String fileName)

// 常用方法
print(各种类型)       // 不换行打印
println(各种类型)     // 打印后换行
printf(String format, Object... args)  // 格式化输出
```

### 1.3 PrintWriter（字符打印流）

```java
// 构造方法
PrintWriter(Writer out)
PrintWriter(OutputStream out)
PrintWriter(File file)
PrintWriter(String fileName)
```

### 1.4 System.out 的本质

```java
System.out  // 就是 PrintStream 类型
```

```java
// 修改输出目的地
System.setOut(new PrintStream("log.txt"));
System.out.println("这行不会打印到控制台，而是写入 log.txt 文件");
```

### 1.5 使用示例

```java
// 字节打印流
try (PrintStream ps = new PrintStream("ps.txt")) {
    ps.println(97);           // 打印数字 97
    ps.println(true);         // 打印布尔值
    ps.println("你好世界");   // 打印字符串
    ps.println(3.14);         // 打印小数
    
    // 格式化输出
    ps.printf("姓名：%s，年龄：%d，分数：%.1f", "张三", 23, 95.5);
}

// 字符打印流（支持字符缓冲区，效率更高）
try (PrintWriter pw = new PrintWriter(new FileWriter("pw.txt"))) {
    pw.println("字符打印流");
    pw.println("一行一个");
}
```

### 1.6 自动刷新模式

```java
// 开启自动刷新（autoFlush=true）
PrintWriter pw = new PrintWriter(new FileWriter("auto.txt"), true);
// PrintStream 同理

// 自动刷新的触发条件：
// 1. println() 方法调用后
// 2. printf() 格式化输出后
// 3. 遇到换行符 \n 时

// 注意：print() 不会自动刷新
pw.print("不会自动刷新");  // 如果缓冲区没满，数据留在缓冲区内
pw.println("会自动刷新");  // println 触发 flush
```

## 2. Commons-IO 工具包

### 2.1 概述

Commons-IO 是 Apache 提供的 **IO 工具库**，封装了大量文件/IO 操作的静态方法，极大简化代码。

### 2.2 引入依赖

```xml
<!-- Maven -->
<dependency>
    <groupId>commons-io</groupId>
    <artifactId>commons-io</artifactId>
    <version>2.11.0</version>
</dependency>
```

### 2.3 FileUtils 核心方法

```java
// 1. 读取文件内容
String content = FileUtils.readFileToString(new File("a.txt"), "UTF-8");
List<String> lines = FileUtils.readLines(new File("a.txt"), "UTF-8");

// 2. 写入文件
FileUtils.writeStringToFile(new File("b.txt"), "内容", "UTF-8");
FileUtils.writeLines(new File("b.txt"), lines, "\n");

// 3. 复制
FileUtils.copyFile(new File("src.txt"), new File("dest.txt"));
FileUtils.copyDirectory(new File("srcDir"), new File("destDir"));
FileUtils.copyURLToFile(url, new File("downloaded.html"));

// 4. 删除
FileUtils.deleteDirectory(new File("dir"));  // 删除整个目录（含子目录）

// 5. 获取文件大小
long size = FileUtils.sizeOf(new File("a.txt"));  // 字节数
String sizeStr = FileUtils.byteCountToDisplaySize(size);  // 友好格式 "1.5 GB"

// 6. 文件过滤
File[] files = new File(".").listFiles(FileFilterUtils.suffixFileFilter(".txt"));
```

### 2.4 IOUtils 核心方法

```java
// 复制流
IOUtils.copy(inputStream, outputStream);
IOUtils.copy(reader, writer);

// 读流转为字符串
String content = IOUtils.toString(inputStream, "UTF-8");
byte[] bytes = IOUtils.toByteArray(inputStream);

// 关闭连接
IOUtils.closeQuietly(inputStream);  // 静默关闭，忽略 null 和异常
```

### 2.5 对比：原生 vs Commons-IO

**原生 Java 文件复制**：
```java
try (FileInputStream fis = new FileInputStream("src.txt");
     FileOutputStream fos = new FileOutputStream("dest.txt")) {
    byte[] buf = new byte[8192];
    int len;
    while ((len = fis.read(buf)) != -1) {
        fos.write(buf, 0, len);
    }
}
```

**Commons-IO 一行搞定**：
```java
FileUtils.copyFile(new File("src.txt"), new File("dest.txt"));
```

## 3. 压缩流

### 3.1 概述

Java 通过 **java.util.zip** 包提供 ZIP 格式的压缩和解压缩支持。

### 3.2 ZipOutputStream（压缩）

```java
// 步骤
// 1. 创建 ZipOutputStream 包装 FileOutputStream
// 2. 每个文件创建一个 ZipEntry
// 3. 写入文件内容
// 4. closeEntry() 结束当前条目

public class ZipDemo {
    public static void main(String[] args) throws IOException {
        // 要压缩的文件列表
        File src1 = new File("a.txt");
        File src2 = new File("b.txt");
        
        try (ZipOutputStream zos = new ZipOutputStream(
                new FileOutputStream("files.zip"))) {
            
            // 压缩第一个文件
            zos.putNextEntry(new ZipEntry("a.txt"));
            FileUtils.copyFile(src1, zos);  // 用 Commons-IO 简化
            zos.closeEntry();
            
            // 压缩第二个文件
            zos.putNextEntry(new ZipEntry("b.txt"));
            FileUtils.copyFile(src2, zos);
            zos.closeEntry();
        }
    }
}
```

### 3.3 ZipInputStream（解压缩）

```java
public class UnzipDemo {
    public static void main(String[] args) throws IOException {
        try (ZipInputStream zis = new ZipInputStream(
                new FileInputStream("files.zip"))) {
            
            ZipEntry entry;
            while ((entry = zis.getNextEntry()) != null) {
                System.out.println("解压：" + entry.getName());
                
                // 解压到当前目录
                FileUtils.copyInputStreamToFile(zis, new File(entry.getName()));
                
                zis.closeEntry();
            }
        }
    }
}
```

## 4. IO 流进阶总结

```
IO流进阶体系
├── 缓冲流（提升性能）
│   ├── 字节缓冲流：BufferedInputStream / BufferedOutputStream
│   └── 字符缓冲流：BufferedReader(readLine) / BufferedWriter(newLine)
├── 转换流（指定编码）
│   ├── InputStreamReader：字节流→字符流
│   └── OutputStreamWriter：字符流→字节流
├── 序列化流（持久化对象）
│   ├── ObjectOutputStream：对象→字节（writeObject）
│   └── ObjectInputStream：字节→对象（readObject）
├── 打印流（方便输出）
│   ├── PrintStream（字节）
│   └── PrintWriter（字符，可自动刷新）
├── 压缩流（ZIP 操作）
│   ├── ZipOutputStream：压缩
│   └── ZipInputStream：解压缩
└── Commons-IO（工具库，简化操作）
    ├── FileUtils：文件/目录操作
    └── IOUtils：流操作
```

### Commons-IO 常用方法速查

| 方法 | 作用 |
|------|------|
| FileUtils.readFileToString(file, charset) | 读取文件为字符串 |
| FileUtils.readLines(file, charset) | 读取文件为行列表 |
| FileUtils.writeStringToFile(file, str, charset) | 写入字符串到文件 |
| FileUtils.writeLines(file, list, lineEnding) | 逐行写入 |
| FileUtils.copyFile(src, dest) | 复制文件 |
| FileUtils.copyDirectory(src, dest) | 复制目录 |
| FileUtils.deleteDirectory(dir) | 删除目录 |
| IOUtils.copy(input, output) | 复制流 |
| IOUtils.toString(input, charset) | 流转字符串 |
| IOUtils.toByteArray(input) | 流转字节数组 |
| IOUtils.closeQuietly(closeable) | 静默关闭 |
