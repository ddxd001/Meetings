# 会议室预约管理系统概要设计

## 架构

项目采用客户端/服务器架构：

- `meeting_room_system/server`：业务规则、SQLite 数据存储、RPC 服务端。
- `meeting_room_system/client`：Tkinter 图形客户端、RPC 客户端。
- `tests`：服务层自动化测试。

## 模块职责

- `models.py`：会议室和预约数据结构。
- `repository.py`：SQLite 表结构、会议室初始化、预约读写。
- `service.py`：预约、查询、取消、空闲会议室查询等业务规则。
- `rpc_server.py`：长度前缀 JSON RPC 通信。
- `rpc_client.py`：客户端 RPC 请求封装。
- `pages.py`：Tkinter 页面和交互逻辑。

## 通信协议

请求格式：

```json
{
  "action": "bookMeeting",
  "data": {
    "roomName": "1层10人1",
    "topic": "项目讨论",
    "startTime": "2099-06-02 10:00",
    "endTime": "2099-06-02 11:00",
    "attendeeCount": 6
  }
}
```

响应格式：

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

