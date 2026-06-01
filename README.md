# 会议室预约管理系统

这是一个基于 Python 标准库实现的会议室预约管理系统，采用客户端/服务端分离架构：

- 服务端：Socket RPC、多线程请求处理、SQLite 数据库存储。
- 客户端：Tkinter 图形界面。
- 通信协议：自定义长度前缀 JSON RPC。
- 数据库：SQLite，首次启动自动建表并初始化会议室数据。
- 打包方式：PyInstaller 生成服务端 exe 和客户端 exe，IExpress 生成客户端安装包。
- 远程部署：支持把服务端源码部署到 Linux 服务器，并注册为 systemd 服务。

当前客户端默认连接的公网服务端地址在 `packaging/client-config.ini` 和 `dist/client/config.ini` 中配置为：

```ini
[client]
server_host = 47.108.143.209
server_port = 8888
timeout = 5
```

如果服务器地址变化，只需要修改客户端 `config.ini`，不需要重新改代码。

## 目录结构总览

```text
.
├── meeting_room_system/              # 系统主源码包
│   ├── config.py                     # 运行时配置读取
│   ├── client/                       # Tkinter 客户端
│   └── server/                       # RPC 服务端、业务层、数据库层
├── src/                              # 兼容入口脚本，供 PyInstaller 使用
├── tests/                            # 单元测试
├── docs/                             # 项目说明和部署说明
├── packaging/                        # 打包配置模板、安装包脚本
├── dist/                             # PyInstaller 输出目录，生成后出现
├── build/                            # PyInstaller/IExpress/Linux 部署包中间目录，生成后出现
├── installer/                        # 客户端安装包输出目录，生成后出现
├── build_exe.ps1                     # 构建 Windows 服务端/客户端 exe
├── build_client_installer.ps1        # 构建客户端安装包
├── build_server_linux_package.py     # 构建 Linux 服务端源码包
├── deploy_server.py                  # 通过 SSH 部署 Linux 服务端
├── requirements.txt                  # 运行时依赖
├── requirements-build.txt            # 构建和部署依赖
└── README.md                         # 当前说明文档
```

## 快速开始

### 1. 安装依赖

源码运行客户端需要 Pillow 显示 PNG/WebP logo：

```powershell
pip install -r requirements.txt
```

打包 exe、生成安装包、远程部署服务器时还需要构建依赖：

```powershell
pip install -r requirements-build.txt
```

### 2. 本机源码运行

先启动服务端：

```powershell
python -m meeting_room_system.server.app
```

再打开另一个终端启动客户端：

```powershell
python -m meeting_room_system.client.app
```

源码模式下，程序会从当前工作目录读取 `config.ini`。如果没有 `config.ini`，会使用默认值：

- 服务端默认监听：`127.0.0.1:8888`
- 客户端默认连接：`127.0.0.1:8888`
- 数据库默认路径：`data/meetings.db`

### 3. 使用已打包客户端

未安装版客户端：

```powershell
dist\client\meeting-client.exe
```

客户端配置文件：

```text
dist/client/config.ini
```

安装包：

```text
installer/meeting-client-setup.exe
```

安装后默认位置：

```text
%LOCALAPPDATA%\Programs\MeetingRoomClient
```

## 系统架构

系统运行时分为三层：

```text
Tkinter 客户端
    |
    | 长度前缀 JSON RPC，TCP 8888
    v
RPC 服务端
    |
    | 调用业务服务 MeetingService
    v
SQLite 数据库
```

客户端只负责显示界面、收集用户输入、发送 RPC 请求。服务端负责所有业务校验和数据持久化。这样可以保证多个客户端连接同一个服务端时，预约冲突判断都在服务端统一完成。

## 通信协议

客户端和服务端使用 TCP socket 通信。每次请求/响应都是：

```text
4 字节大端整数：JSON 数据长度
N 字节 UTF-8 JSON 数据
```

请求格式：

```json
{
  "action": "bookMeeting",
  "data": {
    "organizerName": "张三",
    "roomName": "1层10人1",
    "topic": "项目讨论",
    "startTime": "2099-06-02 10:00",
    "endTime": "2099-06-02 11:00",
    "attendeeCount": 6
  }
}
```

成功响应格式：

```json
{
  "success": true,
  "code": "OK",
  "msg": "预约成功",
  "data": {
    "meetingId": 1
  }
}
```

失败响应格式：

```json
{
  "success": false,
  "code": "TIME_CONFLICT",
  "msg": "该会议室在所选时间段已被预约",
  "data": {}
}
```

## 支持的 RPC action

| action | 作用 | 主要参数 |
| --- | --- | --- |
| `login` | 登录/登记用户 | `username` |
| `listRooms` | 查询全部会议室 | 无 |
| `listAllMeetings` | 查询全部预约，管理员页面使用 | 无 |
| `bookMeeting` / `book` | 创建预约 | `organizerName`, `roomName` 或 `roomId`, `topic`, `startTime`, `endTime`, `attendeeCount` |
| `queryByID` / `queryById` | 按预约 ID 查询 | `meetingId` |
| `queryByOrganizer` | 按组织者查询预约 | `organizerName` |
| `queryByRoom` | 按会议室查询预约 | `roomName` 或 `roomId` |
| `queryAvailableRooms` | 查询指定时间段和人数可用会议室 | `startTime`, `endTime`, `attendeeCount` |
| `cancelMeeting` / `cancel` | 取消预约 | `meetingId`, `requesterName`, `isAdmin` |

## 业务规则

服务端的核心业务规则集中在 `meeting_room_system/server/service.py`：

1. 用户名不能为空，登录时会写入 `users` 表。
2. 组织者、会议主题不能为空。
3. 参会人数必须是大于 0 的整数。
4. 会议室必须存在。
5. 参会人数不能超过会议室容量。
6. 时间格式必须是 `yyyy-MM-dd HH:mm`。
7. 开始时间必须早于结束时间。
8. 开始时间不能早于当前时间。
9. 同一会议室同一时间段不能冲突。
10. 同一会议室首尾相接不算冲突，例如 `10:00-11:00` 和 `11:00-12:00` 可以同时存在。
11. 不同会议室允许同一时间段预约。
12. 普通用户只能取消自己的预约。
13. 用户名为 `Admin` 时进入管理员模式，可以查看全部预约并取消任意预约。

## 数据模型和数据库

### 数据模型

`meeting_room_system/server/models.py` 定义两个核心数据类：

- `Room`：会议室，字段包括 `room_id`, `name`, `floor`, `capacity`。
- `Meeting`：预约，字段包括 `meeting_id`, `organizer_name`, `room_id`, `room_name`, `topic`, `start_time`, `end_time`, `attendee_count`。

`TIME_FORMAT = "%Y-%m-%d %H:%M"` 是全系统统一时间格式。

### 默认会议室

系统首次启动时会自动初始化 30 个会议室：

- 1 到 6 层。
- 每层 3 个 10 人会议室。
- 每层 2 个 5 人会议室。

会议室名称由 `default_rooms()` 生成。

### SQLite 表结构

数据库由 `meeting_room_system/server/repository.py` 自动创建。

`users` 表：

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE
);
```

`rooms` 表：

```sql
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    floor INTEGER NOT NULL,
    capacity INTEGER NOT NULL
);
```

`meetings` 表：

```sql
CREATE TABLE IF NOT EXISTS meetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organizer_name TEXT NOT NULL,
    room_id INTEGER NOT NULL,
    topic TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    attendee_count INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id)
);
```

索引：

```sql
CREATE INDEX IF NOT EXISTS idx_meetings_room_time
    ON meetings(room_id, start_time, end_time);

CREATE INDEX IF NOT EXISTS idx_meetings_organizer
    ON meetings(organizer_name);
```

## 配置机制

配置读取逻辑在 `meeting_room_system/config.py`。

程序优先读取运行目录下的：

```text
config.ini
```

当程序被 PyInstaller 打包成 exe 时，运行目录是 exe 所在目录。当使用源码运行时，运行目录是当前终端所在目录。

### 服务端配置

```ini
[server]
host = 0.0.0.0
port = 8888
db_path = data/meetings.db
```

字段说明：

- `host`：服务端监听地址。`127.0.0.1` 只允许本机访问，`0.0.0.0` 允许其他机器访问。
- `port`：服务端监听端口。
- `db_path`：SQLite 数据库路径，相对路径会相对运行目录解释。

服务端环境变量覆盖：

```powershell
$env:MEETING_HOST="0.0.0.0"
$env:MEETING_PORT="8888"
$env:MEETING_DB="data/meetings.db"
```

### 客户端配置

```ini
[client]
server_host = 47.108.143.209
server_port = 8888
timeout = 5
```

字段说明：

- `server_host`：服务端 IP 或域名。
- `server_port`：服务端端口。
- `timeout`：客户端连接超时时间，单位秒。

客户端环境变量覆盖：

```powershell
$env:MEETING_SERVER_HOST="47.108.143.209"
$env:MEETING_SERVER_PORT="8888"
$env:MEETING_TIMEOUT="5"
```

## 文件功能说明

### 根目录文件

| 文件 | 作用 |
| --- | --- |
| `README.md` | 项目总说明，包含架构、运行、打包、部署和文件说明。 |
| `requirements.txt` | 运行时依赖。目前包含 `Pillow`，用于 Tkinter 加载 PNG/WebP logo。 |
| `requirements-build.txt` | 构建和远程部署依赖。目前包含 `PyInstaller` 和 `paramiko`。 |
| `build_exe.ps1` | Windows 构建脚本。使用 PyInstaller 生成 `meeting-server.exe` 和 `meeting-client.exe`，并复制默认配置文件。 |
| `build_client_installer.ps1` | 客户端安装包构建脚本。使用 Windows 自带 IExpress，把客户端 exe、配置文件、安装脚本打成 `meeting-client-setup.exe`。 |
| `build_server_linux_package.py` | 生成 Linux 服务端源码包 `build/meeting-server-linux.zip`。只打包服务端运行需要的 Python 文件，路径使用 Linux 兼容的 `/`。 |
| `deploy_server.py` | 通过 SSH 把 Linux 服务端源码包上传到服务器，写入 `config.ini`，注册 `meeting-server.service`，启动并做本机 RPC 验证。密码通过环境变量传入，不写入文件。 |
| `项目开发流程.md` | 原始项目开发流程文档。 |
| `会议室预约管理系统开发文档 (1).md` | 原始开发文档。 |
| `会议室预约管理系统产品需求文档（PRD）.md` | 原始产品需求文档。 |

### `meeting_room_system/`

| 文件 | 作用 |
| --- | --- |
| `meeting_room_system/__init__.py` | Python 包标记文件。 |
| `meeting_room_system/config.py` | 统一配置读取模块。负责判断运行目录、读取 `config.ini`、读取环境变量覆盖值，并返回服务端/客户端配置。 |

### `meeting_room_system/server/`

| 文件 | 作用 |
| --- | --- |
| `meeting_room_system/server/__init__.py` | 服务端子包标记文件。 |
| `meeting_room_system/server/app.py` | 服务端入口。读取服务端配置，创建 `MeetingRepository`、`MeetingService`、`RpcServer`，然后启动监听。 |
| `meeting_room_system/server/rpc_server.py` | Socket RPC 服务端。负责监听 TCP 端口、接收连接、读取长度前缀 JSON、调用业务服务、返回 JSON 响应。每个客户端连接用一个 daemon 线程处理。 |
| `meeting_room_system/server/service.py` | 业务服务层。包含登录、预约、查询、取消、可用会议室筛选、数据校验、冲突判断等所有业务规则。 |
| `meeting_room_system/server/repository.py` | SQLite 持久化层。负责建表、初始化会议室、用户保存、预约增删查、会议室查询、冲突查询。 |
| `meeting_room_system/server/models.py` | 数据模型层。定义 `Room`、`Meeting`、`TIME_FORMAT` 和默认会议室生成逻辑。 |

### `meeting_room_system/client/`

| 文件 | 作用 |
| --- | --- |
| `meeting_room_system/client/__init__.py` | 客户端子包标记文件。 |
| `meeting_room_system/client/app.py` | 客户端入口。创建 `MeetingRoomApp` 并进入 Tkinter 主循环。 |
| `meeting_room_system/client/rpc_client.py` | Socket RPC 客户端。读取客户端配置，连接服务端，发送长度前缀 JSON 请求，读取响应。 |
| `meeting_room_system/client/pages.py` | Tkinter 图形界面主体。包含登录页、普通用户主页、管理员主页、预约页、查询页、取消页、表格展示、日期时间选择控件、logo 加载和页面布局。 |

### `meeting_room_system/client/assets/`

| 文件 | 作用 |
| --- | --- |
| `logo.png` | 软件 logo，已处理为透明背景。用于窗口图标、页面标题、登录页左上角。 |
| `XDU.webp` | 学校 logo，已处理为透明背景。用于页面右上角和登录页底部。 |
| `logo.original.png` | 软件 logo 原始备份。 |
| `XDU.original.webp` | 学校 logo 原始备份。 |

### `src/`

| 文件 | 作用 |
| --- | --- |
| `src/server/server.py` | 兼容服务端入口。导入并调用 `meeting_room_system.server.app.main()`。PyInstaller 构建服务端 exe 时使用它。 |
| `src/client/client.py` | 兼容客户端入口。导入并调用 `meeting_room_system.client.app.main()`。PyInstaller 构建客户端 exe 时使用它。 |

### `tests/`

| 文件 | 作用 |
| --- | --- |
| `tests/test_service.py` | 服务层单元测试。使用临时 SQLite 数据库测试预约成功、会议室不存在、人数超限、时间格式错误、时间顺序错误、过去时间拒绝、同会议室冲突、不同会议室允许、相邻时间允许、取消权限、管理员取消、查询空闲会议室、查询全部预约等规则。 |

### `docs/`

| 文件 | 作用 |
| --- | --- |
| `docs/overview.md` | 项目概览文档。 |
| `docs/deployment.md` | 部署说明文档，包含 exe 构建、服务端部署、客户端部署、安装包和环境变量覆盖。 |

### `packaging/`

| 文件 | 作用 |
| --- | --- |
| `packaging/server-config.ini` | 服务端打包后的默认配置模板。`build_exe.ps1` 会复制到 `dist/server/config.ini`。 |
| `packaging/client-config.ini` | 客户端打包后的默认配置模板。当前默认连接 `47.108.143.209:8888`。`build_exe.ps1` 会复制到 `dist/client/config.ini`。 |
| `packaging/client-installer/install-client.cmd` | 客户端安装包启动脚本。IExpress 解压后先执行它，再调用 PowerShell 安装脚本。 |
| `packaging/client-installer/install-client.ps1` | 客户端安装逻辑。复制客户端 exe 到用户目录，首次安装写入 `config.ini`，创建桌面快捷方式、开始菜单快捷方式和卸载脚本。重复安装不会覆盖已有配置。 |

### `dist/`

`dist/` 是构建产物目录，不是手写源码。

| 文件或目录 | 作用 |
| --- | --- |
| `dist/server/meeting-server.exe` | Windows 服务端可执行文件。适用于 Windows 服务端部署。 |
| `dist/server/config.ini` | Windows 服务端运行配置。 |
| `dist/server/data/` | Windows 服务端默认数据库目录。 |
| `dist/client/meeting-client.exe` | Windows 客户端可执行文件。 |
| `dist/client/config.ini` | Windows 客户端运行配置。当前连接公网服务端 `47.108.143.209:8888`。 |

### `installer/`

| 文件 | 作用 |
| --- | --- |
| `installer/meeting-client-setup.exe` | 客户端安装包。由 `build_client_installer.ps1` 生成。安装后会创建桌面快捷方式和开始菜单快捷方式。 |

### `build/`

`build/` 是构建中间目录，通常不需要人工修改。

| 文件或目录 | 作用 |
| --- | --- |
| `build/spec/` | PyInstaller 生成的 spec 文件目录。 |
| `build/server/` | 服务端 exe 构建中间文件，例如分析结果、压缩包、警告日志。 |
| `build/client/` | 客户端 exe 构建中间文件。 |
| `build/client-installer/` | IExpress 安装包构建工作目录，包含临时复制的客户端 exe、配置文件、安装脚本和 `.sed` 配置。 |
| `build/meeting-server-linux.zip` | Linux 服务端源码部署包。 |
| `build/remote-server-package/` | 早期/临时远程部署打包工作目录。当前主要使用 `build_server_linux_package.py` 生成 Linux 包。 |

## 客户端界面逻辑

客户端主类是 `MeetingRoomApp`，继承自 `tk.Tk`。

启动流程：

1. `meeting_room_system/client/app.py` 调用 `MeetingRoomApp()`。
2. `MeetingRoomApp.__init__()` 创建 RPC 客户端、设置窗口标题和尺寸。
3. `_load_brand_assets()` 加载 `logo.png` 和 `XDU.webp`。
4. `_setup_style()` 设置 Tkinter/ttk 样式。
5. `show_login()` 显示登录页。

登录页：

- 软件 logo 放在窗口左上角。
- 登录框居中显示。
- 学校 logo 放在窗口底部居中。
- 输入用户名后调用 `login` action。

普通用户主页：

- 创建预约。
- 按 ID 查询。
- 按组织者查询。
- 按会议室查询。
- 查询空闲会议室。
- 取消预约。

管理员主页：

- 用户名为 `Admin` 时进入管理员模式。
- 可以查看全部预约。
- 可以查看全部会议室。
- 可以按组织者查询。
- 可以取消任意预约。

页面切换方式：

- `_clear()` 销毁当前 frame 并创建新 frame。
- `_scroll_page()` 创建带滚动条的页面容器。
- `_header()` 统一绘制页面标题、软件 logo、学校 logo、返回按钮和当前用户信息。

## 服务端运行逻辑

服务端入口是 `meeting_room_system/server/app.py`。

启动流程：

1. 调用 `server_settings()` 读取配置。
2. 创建 `MeetingRepository(db_path)`。
3. Repository 自动创建数据库目录、连接 SQLite、建表、初始化会议室。
4. 创建 `MeetingService(repository)`。
5. 创建 `RpcServer(service, host, port)`。
6. 调用 `serve_forever()` 持续监听 TCP 连接。

请求处理流程：

1. 客户端连接 TCP 端口。
2. 服务端读取 4 字节长度头。
3. 服务端读取 JSON payload。
4. 解析出 `action` 和 `data`。
5. 调用 `MeetingService.dispatch(action, data)`。
6. 服务层执行业务校验和数据库操作。
7. 服务端把响应 JSON 重新加长度头发送给客户端。

并发控制：

- RPC 层每个连接一个线程。
- 服务层预约操作使用 `threading.RLock()` 包住校验和写入，避免并发预约造成冲突漏判。
- Repository 层也使用 `RLock()` 保护 SQLite 连接。

## 构建 Windows exe

安装依赖：

```powershell
pip install -r requirements.txt
pip install -r requirements-build.txt
```

执行：

```powershell
.\build_exe.ps1
```

输出：

```text
dist/server/meeting-server.exe
dist/server/config.ini
dist/server/data/
dist/client/meeting-client.exe
dist/client/config.ini
```

客户端 exe 打包时会把 `meeting_room_system/client/assets` 一起打进去，保证 logo 可显示。

## 构建客户端安装包

先确保已经构建客户端 exe：

```powershell
.\build_exe.ps1
```

再构建安装包：

```powershell
.\build_client_installer.ps1
```

输出：

```text
installer/meeting-client-setup.exe
```

安装包行为：

1. 解压临时文件。
2. 执行 `install-client.cmd`。
3. `install-client.cmd` 调用 `install-client.ps1`。
4. 弹出安装位置选择窗口，默认位置是 `%LOCALAPPDATA%\Programs\MeetingRoomClient`。
5. 用户可以选择已有目录，也可以在选择窗口中新建目录。
6. 首次安装复制 `config.ini`。
7. 如果目标目录已有 `config.ini`，不会覆盖，避免覆盖用户已经设置好的服务端地址。
8. 创建桌面快捷方式。
9. 创建开始菜单快捷方式。
10. 创建卸载脚本和卸载快捷方式。
11. 安装完成后询问是否立即启动客户端。

## Windows 服务端部署

把下面整个目录复制到 Windows 服务器：

```text
dist/server
```

修改 `dist/server/config.ini`：

```ini
[server]
host = 0.0.0.0
port = 8888
db_path = data/meetings.db
```

启动：

```powershell
cd dist\server
.\meeting-server.exe
```

如果客户端无法连接，需要放行 Windows 防火墙 TCP 8888：

```powershell
New-NetFirewallRule -DisplayName "Meeting Server 8888" -Direction Inbound -Protocol TCP -LocalPort 8888 -Action Allow
```

## Linux 服务端部署

Linux 部署不使用 Windows 生成的 `meeting-server.exe`，而是部署 Python 源码并注册 systemd。

### 1. 构建 Linux 源码包

```powershell
python build_server_linux_package.py
```

输出：

```text
build/meeting-server-linux.zip
```

### 2. 配置 SSH 环境变量

不要把密码写入源码文件。部署脚本从环境变量读取服务器信息：

```powershell
$env:DEPLOY_HOST="服务器IP"
$env:DEPLOY_USER="用户名"
$env:DEPLOY_PASS="密码"
```

### 3. 执行部署

```powershell
python deploy_server.py
```

脚本会执行：

1. 连接服务器。
2. 创建 `/home/<用户>/meeting-room-server/data`。
3. 上传 `build/meeting-server-linux.zip`。
4. 解压服务端源码。
5. 写入服务端 `config.ini`。
6. 生成 `meeting-server.service`。
7. 复制到 `/etc/systemd/system/meeting-server.service`。
8. 执行 `systemctl daemon-reload`。
9. 启用并启动服务。
10. 尝试放行 UFW 8888。
11. 检查服务状态。
12. 在服务器本机发起一次 RPC 请求验证 `listRooms`。

### 4. 服务器管理命令

```bash
sudo systemctl status meeting-server.service
sudo systemctl restart meeting-server.service
sudo systemctl stop meeting-server.service
sudo journalctl -u meeting-server.service -n 100 --no-pager
```

### 5. 云服务器安全组

如果服务器本机验证成功，但外部客户端连不上，通常是云厂商安全组没有放行端口。

需要在云服务器控制台放行：

```text
协议：TCP
端口：8888
授权对象：0.0.0.0/0
```

更安全的做法是只放行固定办公网络出口 IP。

## 测试

运行全部单元测试：

```powershell
python -m unittest discover -s tests
```

当前测试覆盖重点：

- 成功预约。
- 会议室不存在。
- 人数超过容量。
- 时间格式错误。
- 开始时间晚于结束时间。
- 过去时间拒绝。
- 同会议室时间冲突。
- 不同会议室同时间允许。
- 相邻时间段允许。
- 普通用户取消自己的预约。
- 普通用户不能取消他人预约。
- 管理员可以取消任意预约。
- 查询不存在的预约 ID。
- 查询空闲会议室。
- 查询全部预约。

## 常见问题

### 客户端提示无法连接服务端

检查顺序：

1. 服务端进程是否启动。
2. 服务端是否监听 `0.0.0.0:8888` 或正确 IP。
3. 客户端 `config.ini` 的 `server_host` 是否正确。
4. 客户端机器是否能访问服务端端口：

```powershell
Test-NetConnection 服务器IP -Port 8888
```

5. Windows 防火墙或云服务器安全组是否放行 TCP 8888。

### 安装包安装后仍连接旧服务器

安装脚本为了保护用户配置，重复安装时不会覆盖已有：

```text
%LOCALAPPDATA%\Programs\MeetingRoomClient\config.ini
```

如果要改服务器地址，需要手动修改该文件，或者卸载后删除安装目录再重新安装。

### Linux 服务器服务启动失败

查看日志：

```bash
sudo journalctl -u meeting-server.service -n 100 --no-pager
```

常见原因：

- Python 不存在或路径不是 `/usr/bin/python3`。
- 端口 8888 被占用。
- 部署目录权限异常。
- `meeting_room_system` 源码没有正确解压。

### SQLite 数据库在哪里

Windows exe 默认：

```text
dist/server/data/meetings.db
```

Linux systemd 默认：

```text
/home/ddxd/meeting-room-server/data/meetings.db
```

实际位置由服务端 `config.ini` 的 `db_path` 决定。

## 开发建议

1. 改业务规则时优先修改 `meeting_room_system/server/service.py`。
2. 改数据库访问时修改 `meeting_room_system/server/repository.py`。
3. 改客户端界面时修改 `meeting_room_system/client/pages.py`。
4. 改通信方式时同时检查 `rpc_client.py` 和 `rpc_server.py`。
5. 改配置项时修改 `meeting_room_system/config.py`，并同步更新 `packaging/*.ini` 和 README。
6. 每次改业务逻辑后运行：

```powershell
python -m unittest discover -s tests
```

7. 每次重新发布 Windows 客户端安装包时执行：

```powershell
.\build_exe.ps1
.\build_client_installer.ps1
```

8. 每次重新部署 Linux 服务端时执行：

```powershell
python build_server_linux_package.py
python deploy_server.py
```

## 安全注意事项

- 不要把服务器密码写入 README、源码或提交记录。
- `deploy_server.py` 通过环境变量读取 SSH 密码，只适合内部临时部署。
- 正式服务器建议使用 SSH 密钥登录，并关闭弱密码登录。
- 公网开放 8888 时，建议限制来源 IP。
- 当前 RPC 协议没有 TLS 加密和用户密码认证，只适合内网或受控网络环境。如果要公网长期使用，应增加认证、加密和访问控制。
