# 32 - 网络编程

> 📅 2026-07-30 | 🏷️ JavaSE / 网络编程 / UDP / TCP / Socket

---

## 网络编程概述

网络编程：实现计算机之间数据交换的编程技术。

### 网络模型

- **OSI 七层模型**：物理层 → 数据链路层 → 网络层 → 传输层 → 会话层 → 表示层 → 应用层
- **TCP/IP 四层模型**：网络接口层 → 网际层 → 传输层 → 应用层

Java 主要关注**传输层**的 TCP 和 UDP 协议。

## 网络编程三要素

1. **IP 地址**：定位设备（哪个电脑）
2. **端口号**：定位进程（哪个程序），范围 0~65535，0~1023 为系统保留
3. **协议**：通信规则（TCP/UDP）

### IP 地址

```java
// 获取本机 IP
InetAddress localHost = InetAddress.getLocalHost();
System.out.println(localHost.getHostAddress()); // 192.168.x.x
System.out.println(localHost.getHostName());    // 主机名

// 根据域名获取 IP
InetAddress baidu = InetAddress.getByName("www.baidu.com");
System.out.println(baidu.getHostAddress());

// 判断是否能 ping 通
System.out.println(baidu.isReachable(3000));
```

#### IPv4 vs IPv6
- **IPv4**：32 位，4 字节，约 43 亿地址（已耗尽）
- **IPv6**：128 位，16 字节，号称"地球上每粒沙子都能分一个 IP"

#### 特殊 IP
- `127.0.0.1` / `localhost`：本机回环地址
- `192.168.x.x`：局域网私有地址
- `0.0.0.0`：本机所有 IP

### 端口号

- 0~65535，同一台机器上端口不能冲突
- 知名端口：HTTP(80)、HTTPS(443)、MySQL(3306)、Redis(6379)、SSH(22)

## UDP 通信

**User Datagram Protocol**：用户数据报协议

### 特点
| 特性 | 说明 |
|------|------|
| 面向无连接 | 不需要建立连接，直接发 |
| 不可靠 | 可能丢包、乱序 |
| 效率高 | 无连接建立开销 |
| 数据报大小 | 最多 64KB |

### UDP 发送端

```java
// 1. 创建 DatagramSocket（无需指定端口，系统分配）
DatagramSocket socket = new DatagramSocket();

// 2. 将数据打包
byte[] data = "你好，世界！".getBytes();
InetAddress address = InetAddress.getByName("127.0.0.1");
int port = 8888;
DatagramPacket packet = new DatagramPacket(data, data.length, address, port);

// 3. 发送
socket.send(packet);

// 4. 关闭
socket.close();
```

### UDP 接收端

```java
// 1. 创建 DatagramSocket，绑定端口
DatagramSocket socket = new DatagramSocket(8888);

// 2. 创建接收包（指定缓冲区大小）
byte[] buf = new byte[1024 * 64]; // 最大 64KB
DatagramPacket packet = new DatagramPacket(buf, buf.length);

// 3. 接收（阻塞等待）
socket.receive(packet);

// 4. 解析数据
byte[] data = packet.getData();
int length = packet.getLength();
String message = new String(data, 0, length);
System.out.println("收到: " + message);
System.out.println("来自: " + packet.getAddress() + ":" + packet.getPort());

// 5. 关闭
socket.close();
```

### UDP 通信注意点

1. **先启动接收端**，再启动发送端
2. 发和收是**一对一**的（一个端口对应一个接收端）
3. `DatagramPacket` 的缓冲区（`buf.length`）不要超过 64KB

### UDP 实现聊天室

```java
// 发送线程
new Thread(() -> {
    DatagramSocket socket = new DatagramSocket();
    Scanner sc = new Scanner(System.in);
    while (true) {
        String msg = sc.nextLine();
        if ("exit".equals(msg)) break;
        byte[] data = msg.getBytes();
        DatagramPacket packet = new DatagramPacket(data, data.length,
            InetAddress.getByName("255.255.255.255"), 8888); // 广播地址
        socket.send(packet);
    }
    socket.close();
}).start();

// 接收线程
new Thread(() -> {
    DatagramSocket socket = new DatagramSocket(8888);
    while (true) {
        byte[] buf = new byte[1024];
        DatagramPacket packet = new DatagramPacket(buf, buf.length);
        socket.receive(packet);
        String msg = new String(packet.getData(), 0, packet.getLength());
        System.out.println(packet.getAddress() + ": " + msg);
    }
}).start();
```

## TCP 通信

**Transmission Control Protocol**：传输控制协议

### 特点
| 特性 | 说明 |
|------|------|
| 面向连接 | 需要三次握手建立连接 |
| 可靠传输 | 确认重传、按序到达 |
| 效率较低 | 有连接建立和维护开销 |
| 无数据大小限制 | 以流的形式传输 |

### TCP 客户端

```java
// 1. 创建 Socket，连接服务器（IP + 端口）
Socket socket = new Socket("127.0.0.1", 9999);

// 2. 获取输出流，发送数据
OutputStream os = socket.getOutputStream();
os.write("你好，服务器！".getBytes());

// 3. 获取输入流，接收响应
InputStream is = socket.getInputStream();
byte[] buf = new byte[1024];
int len = is.read(buf);
System.out.println("服务器响应: " + new String(buf, 0, len));

// 4. 关闭
socket.close();
```

### TCP 服务端

```java
// 1. 创建 ServerSocket，绑定端口
ServerSocket serverSocket = new ServerSocket(9999);

// 2. 等待客户端连接（阻塞）
Socket socket = serverSocket.accept();

// 3. 获取输入流，读取数据
InputStream is = socket.getInputStream();
byte[] buf = new byte[1024];
int len = is.read(buf);
System.out.println("收到: " + new String(buf, 0, len));

// 4. 获取输出流，回写响应
OutputStream os = socket.getOutputStream();
os.write("收到，谢谢！".getBytes());

// 5. 关闭
socket.close();
serverSocket.close();
```

### TCP 通信注意点

1. **必须先启动服务端**，再启动客户端
2. `accept()` 是**阻塞**方法，等待客户端连接
3. `read()` 也是**阻塞**的，直到数据到达或流关闭
4. 需要约定**结束标记**（如 shutdownOutput / 约定 \n / 发送特殊字符串）

### 避免 read() 阻塞的问题

```java
// 方案 1：发送方关闭输出流（通知接收方结束）
socket.shutdownOutput();  // 发送完数据后调用

// 方案 2：约定结束标记
// 发送方：每行末尾加 \n
// 接收方：用 BufferedReader.readLine() 按行读取

// 方案 3：先发送数据长度
// 发送：先写 4 字节表示数据长度，再写数据体
// 接收：先读前 4 字节得到长度，再读指定字节数
```

### TCP 多线程服务端

```java
ServerSocket serverSocket = new ServerSocket(9999);
while (true) {
    Socket socket = serverSocket.accept();
    // 每个客户端开一个线程处理
    new Thread(() -> {
        try {
            InputStream is = socket.getInputStream();
            OutputStream os = socket.getOutputStream();
            // 处理通信...
            socket.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }).start();
}
```

### TCP 实现文件上传

```java
// 客户端
Socket socket = new Socket("127.0.0.1", 10000);
FileInputStream fis = new FileInputStream("test.jpg");
OutputStream os = socket.getOutputStream();

byte[] buf = new byte[8192];
int len;
while ((len = fis.read(buf)) != -1) {
    os.write(buf, 0, len);
}
socket.shutdownOutput();  // 告诉服务器文件发完了

// 接收响应
InputStream is = socket.getInputStream();
int len2 = is.read(buf);
System.out.println(new String(buf, 0, len2));

fis.close();
socket.close();

// 服务端
ServerSocket ss = new ServerSocket(10000);
Socket socket = ss.accept();

BufferedInputStream bis = new BufferedInputStream(socket.getInputStream());
BufferedOutputStream bos = new BufferedOutputStream(
    new FileOutputStream(System.currentTimeMillis() + ".jpg"));

byte[] buf = new byte[8192];
int len;
while ((len = bis.read(buf)) != -1) {
    bos.write(buf, 0, len);
}

OutputStream os = socket.getOutputStream();
os.write("上传成功".getBytes());

bos.close();
socket.close();
ss.close();
```

### 三次握手与四次挥手

**三次握手（建立连接）**：
1. 客户端 → 服务器：SYN（同步位），请求连接
2. 服务器 → 客户端：SYN + ACK，确认收到，我也发连接
3. 客户端 → 服务器：ACK，确认收到，连接建立

**四次挥手（断开连接）**：
1. 客户端 → 服务器：FIN，我要断开了
2. 服务器 → 客户端：ACK，收到断开请求
3. 服务器 → 客户端：FIN，我也要断开了
4. 客户端 → 服务器：ACK，收到，连接断开

## UDP vs TCP 对比

| 对比项 | UDP | TCP |
|--------|-----|-----|
| 连接 | 无连接 | 面向连接（三次握手） |
| 可靠性 | 不可靠，可能丢包 | 可靠传输 |
| 速度 | 快 | 相对慢 |
| 数据量 | 64KB 上限 | 无限制（流式） |
| 适用场景 | 视频/语音通话、DNS、游戏 | 文件传输、网页、邮件 |

## BS 架构（浏览器-服务器）

本质也是 TCP，浏览器充当客户端。

```java
// 简易 BS 服务器
ServerSocket ss = new ServerSocket(8080);
Socket socket = ss.accept();

// 读取 HTTP 请求
BufferedReader br = new BufferedReader(
    new InputStreamReader(socket.getInputStream()));
String line;
while ((line = br.readLine()) != null && !line.isEmpty()) {
    System.out.println(line);
}

// 返回 HTTP 响应
PrintWriter pw = new PrintWriter(socket.getOutputStream());
pw.println("HTTP/1.1 200 OK");
pw.println("Content-Type: text/html;charset=utf-8");
pw.println();
pw.println("<h1>Hello Browser!</h1>");
pw.flush();

socket.close();
ss.close();
```

**多线程 BS 服务器**：每个请求一个线程，返回静态资源（HTML/CSS/JS/图片）。

---

## 总结

| 知识点 | 核心要点 |
|--------|---------|
| 三要素 | IP（设备）+ 端口（进程）+ 协议（UDP/TCP） |
| UDP | DatagramSocket + DatagramPacket，无连接，64KB 上限 |
| TCP | Socket + ServerSocket，三次握手，流式可靠传输 |
| 阻塞问题 | read() 阻塞，用 shutdownOutput 或约定结束标记 |
| 文件上传 | TCP 流式传输 + 多线程处理 |
| BS 架构 | TCP + HTTP 协议，浏览器当客户端 |
