# 部署说明

## 构建 exe

在项目根目录执行：

```powershell
pip install -r requirements.txt
pip install -r requirements-build.txt
.\build_exe.ps1
```

构建完成后会生成：

```text
dist/server/meeting-server.exe
dist/server/config.ini
dist/server/data/
dist/client/meeting-client.exe
dist/client/config.ini
```

## 服务端部署

把 `dist/server` 整个目录复制到服务端电脑。

配置 `dist/server/config.ini`：

```ini
[server]
host = 0.0.0.0
port = 8888
db_path = data/meetings.db
```

双击或在命令行启动：

```powershell
.\meeting-server.exe
```

如果其他电脑无法连接，需要在 Windows 防火墙中放行 TCP `8888` 端口。

## 客户端部署

把 `dist/client` 整个目录复制到客户端电脑。

配置 `dist/client/config.ini`，把 `server_host` 改成服务端电脑 IP：

```ini
[client]
server_host = 192.168.1.100
server_port = 8888
timeout = 5
```

双击启动：

```powershell
.\meeting-client.exe
```

也可以构建客户端安装包：

```powershell
.\build_client_installer.ps1
```

安装包会生成到：

```text
installer/meeting-client-setup.exe
```

安装包会弹出安装位置选择窗口，默认安装到当前用户目录：

```text
%LOCALAPPDATA%\Programs\MeetingRoomClient
```

用户可以选择已有目录，也可以新建目录。安装完成后会创建桌面快捷方式和开始菜单快捷方式，并询问是否立即启动客户端。第一次安装会写入默认 `config.ini`；重复安装到同一目录时会保留已有配置，避免覆盖已经设置好的服务端 IP。

## 环境变量覆盖

也可以用环境变量临时覆盖配置：

服务端：

```powershell
$env:MEETING_HOST="0.0.0.0"
$env:MEETING_PORT="8888"
$env:MEETING_DB="data/meetings.db"
.\meeting-server.exe
```

客户端：

```powershell
$env:MEETING_SERVER_HOST="192.168.1.100"
$env:MEETING_SERVER_PORT="8888"
.\meeting-client.exe
```
