# File 类

> JavaSE 进阶：File 概述 · 构造方法 · 常用 API · 递归遍历 · 文件搜索
> 课程：黑马 JavaSE 进阶/高级（BV1yW4y1Y7Ms · P62-P66）

---

## 一、File 概述

`java.io.File` 是 Java 中**文件和目录路径名的抽象表示**。

> ⚠️ **注意：** File 对象只是一个路径的抽象表示，并不是真正的文件对象。创建 File 对象时，文件可以不存在。

### 1.1 三种构造方法

```java
// 方式一：直接传路径字符串
File f1 = new File("D:\\myfile\\a.txt");   // Windows
File f1 = new File("/home/user/a.txt");     // Linux / Mac

// 方式二：父路径 + 子路径（最常用）
File f2 = new File("D:\\myfile", "a.txt");

// 方式三：父 File 对象 + 子路径
File parent = new File("D:\\myfile");
File f3 = new File(parent, "a.txt");
```

**路径写法注意：**

1. Windows 用 `\\` 或 `/` 都行，推荐 `/`（Java 会自动转换）
2. 如果用 `\\`，第一个是转义字符，第二个才是反斜杠
3. 相对路径默认相对于**当前项目根目录**

```java
// 相对路径示例
File f = new File("a.txt");          // 相对于当前项目根目录下的 a.txt
File f2 = new File("src/a.txt");     // src 目录下的 a.txt
```

---

## 二、File 常用方法

### 2.1 判断功能

| 方法 | 说明 |
|------|------|
| `exists()` | 文件或目录是否存在 |
| `isFile()` | 是否为文件 |
| `isDirectory()` | 是否为目录 |
| `isHidden()` | 是否隐藏 |

```java
File f = new File("D:\\myfile\\a.txt");
System.out.println(f.exists());      // true / false
System.out.println(f.isFile());      // true
System.out.println(f.isDirectory()); // false
```

### 2.2 获取功能

| 方法 | 说明 |
|------|------|
| `getName()` | 获取文件名（含后缀）或目录名 |
| `length()` | 获取文件大小（字节数），目录无效 |
| `getAbsolutePath()` | 获取绝对路径（String） |
| `getAbsoluteFile()` | 获取绝对路径表示的 File 对象 |
| `getParentFile()` | 获取父级目录的 File 对象 |
| `lastModified()` | 最后修改时间（毫秒时间戳） |

```java
File f = new File("D:\\myfile\\a.txt");
System.out.println(f.getName());         // a.txt
System.out.println(f.length());          // 文件字节数，如 1024
System.out.println(f.getAbsolutePath()); // D:\myfile\a.txt
System.out.println(f.getParentFile());   // D:\myfile（File 对象）
```

### 2.3 创建功能

| 方法 | 说明 |
|------|------|
| `createNewFile()` | 创建文件，已存在则返回 false |
| `mkdir()` | 创建**单级**目录 |
| `mkdirs()` | 创建**多级**目录（最常用） |

```java
// 创建文件
File f1 = new File("D:\\test\\hello.txt");
boolean flag1 = f1.createNewFile();  // 创建成功返回 true，文件已存在返回 false

// 创建目录
File f2 = new File("D:\\test\\aa");
f2.mkdir();    // 创建单级目录 aa，如果父目录 D:\\test 不存在则失败

File f3 = new File("D:\\test\\aa\\bb\\cc");
f3.mkdirs();   // ✅ 创建多级目录，父目录不存在也会一并创建
```

> **注意：** `createNewFile()` 和 `mkdir()`/`mkdirs()` 返回 boolean，如果文件/目录已存在则返回 false，不会抛异常。

### 2.4 删除功能

| 方法 | 说明 |
|------|------|
| `delete()` | 删除文件或空目录，**不走回收站** |

```java
File f = new File("D:\\test\\a.txt");
f.delete();  // 直接删除，不经过回收站，慎用！

File dir = new File("D:\\test\\emptyDir");
dir.delete();  // 只能删除空目录
```

> ⚠️ `delete()` 只能删除文件或**空目录**，目录不为空则删除失败（返回 false）。

### 2.5 遍历功能

| 方法 | 说明 |
|------|------|
| `list()` | 返回 String 数组，包含所有文件和子目录名 |
| `listFiles()` | 返回 File 数组，包含所有文件和子目录的 File 对象 |

```java
File dir = new File("D:\\myfile");
String[] names = dir.list();         // 获取所有文件名/目录名的字符串数组
File[] files = dir.listFiles();      // 获取所有文件/目录的 File 对象数组

for (File file : files) {
    if (file.isFile()) {
        System.out.println("文件：" + file.getName());
    } else if (file.isDirectory()) {
        System.out.println("目录：" + file.getName());
    }
}
```

**listFiles 要注意：**

- 如果 `listFiles()` 的调用者（File 对象）不是一个目录，返回 **null**
- 如果目录没有访问权限，返回 **null**
- 如果目录是空的，返回一个长度为 **0** 的数组

```java
File f = new File("D:\\not_exist_dir");
File[] files = f.listFiles();  // null，因为目录不存在

File empty = new File("D:\\empty_dir");
File[] emptyFiles = empty.listFiles();  // 空数组，长度为 0
```

---

## 三、File 递归遍历

### 3.1 递归遍历文件夹中所有文件

```java
public class FileTraversal {
    public static void main(String[] args) {
        File dir = new File("D:\\myfile");
        traverse(dir);
    }

    public static void traverse(File dir) {
        File[] files = dir.listFiles();
        if (files == null) return;

        for (File file : files) {
            if (file.isFile()) {
                System.out.println(file.getAbsolutePath());
            } else {
                // 子目录，递归遍历
                traverse(file);
            }
        }
    }
}
// 输出示例：
// D:\myfile\a.txt
// D:\myfile\subdir\b.java
// D:\myfile\subdir\subsub\c.jpg
```

### 3.2 搜索指定类型文件（如 .java）

```java
public class FileSearcher {
    public static void main(String[] args) {
        File dir = new File("D:\\workspace");
        searchJavaFiles(dir);
    }

    public static void searchJavaFiles(File dir) {
        File[] files = dir.listFiles();
        if (files == null) return;

        for (File file : files) {
            if (file.isFile()) {
                if (file.getName().endsWith(".java")) {
                    System.out.println("找到 Java 文件：" + file.getAbsolutePath());
                }
            } else {
                searchJavaFiles(file);
            }
        }
    }
}
```

### 3.3 递归删除文件夹

```java
public class FileDeleter {
    public static void main(String[] args) {
        File dir = new File("D:\\to_delete");
        deleteDir(dir);
    }

    public static void deleteDir(File dir) {
        File[] files = dir.listFiles();
        if (files == null) return;

        for (File file : files) {
            if (file.isFile()) {
                file.delete();                 // 删除文件
                System.out.println("已删除文件：" + file.getName());
            } else {
                deleteDir(file);               // 递归删除子目录
            }
        }
        dir.delete();                          // 最后删除自己（空目录）
        System.out.println("已删除目录：" + dir.getName());
    }
}
```

### 3.4 FileFilter 文件过滤器

`listFiles()` 可传入 `FileFilter` 或 `FilenameFilter` 来过滤结果：

```java
// 方式一：FileFilter——过滤所有 .java 文件
File dir = new File("D:\\myfile");
File[] javaFiles = dir.listFiles(new FileFilter() {
    @Override
    public boolean accept(File pathname) {
        return pathname.isFile() && pathname.getName().endsWith(".java");
    }
});

// 方式二：FilenameFilter——第二个参数是文件名
File[] txtFiles = dir.listFiles(new FilenameFilter() {
    @Override
    public boolean accept(File dir, String name) {
        return name.endsWith(".txt");
    }
});

// Lambda 简化
File[] files = dir.listFiles(f -> f.isFile() && f.getName().endsWith(".java"));
```

---

## 四、要点总结

| 分类 | 方法 | 说明 |
|------|------|------|
| 构造 | File(String / File, String) | 三种构造方式 |
| 判断 | exists / isFile / isDirectory | 文件/目录是否存在，类型判断 |
| 获取 | getName / length / getAbsolutePath | 名字、大小、绝对路径 |
| 创建 | createNewFile / mkdir / mkdirs | 创建文件/单级目录/多级目录 |
| 删除 | delete | 直接删除，不走回收站 |
| 遍历 | list / listFiles | 列目录内容 |
| 过滤 | FileFilter / FilenameFilter | 结合 listFiles 过滤文件 |

> **下一篇预告：** IO 流基础（字节流与字符流）
