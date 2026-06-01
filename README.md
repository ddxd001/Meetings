# 会议室预约管理系统

这是按 `项目开发流程.md` 改造后的版本，使用 Python 标准库实现：

- 服务端：Socket RPC、多线程、SQLite。
- 客户端：Tkinter GUI。
- 数据库：首次启动自动创建 `meeting_room_system/data/meetings.db`，并初始化 6 层会议室数据。
- 测试：`unittest`。

## 运行

启动服务端：

```powershell
python -m meeting_room_system.server.app
```

启动客户端：

```powershell
python -m meeting_room_system.client.app
```

## 功能

- 预约会议室。
- 按 ID 查询预约。
- 按组织者查询预约。
- 按会议室查询预约记录。
- 按时间段查询空闲会议室。
- 取消预约。

## 业务规则

- 会议室必须存在。
- 参与人数不能超过会议室容量。
- 时间格式为 `yyyy-MM-dd HH:mm`。
- 开始时间必须早于结束时间。
- 不能预约过去时间。
- 同一会议室同一时间段不能冲突。
- 不同会议室允许同一时间段预约。
- 同一会议室首尾相接不算冲突。

## 测试

```powershell
python -m unittest discover -s tests
```

