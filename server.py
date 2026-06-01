#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器端代码
功能：实现RPC服务，处理客户端请求，实现会议室预约管理的核心业务逻辑
"""

import socket
import threading
import json
from datetime import datetime

# 全局变量
meeting_list = []  # 存储预约数据的列表
next_id = 1  # 自增预约ID


def is_conflict(room_name, start_time, end_time):
    """
    检查时间冲突
    :param room_name: 会议室名称
    :param start_time: 开始时间
    :param end_time: 结束时间
    :return: 是否存在冲突
    """
    for meeting in meeting_list:
        if meeting['roomName'] == room_name:
            existing_start = datetime.strptime(meeting['startTime'], '%Y-%m-%d %H:%M')
            existing_end = datetime.strptime(meeting['endTime'], '%Y-%m-%d %H:%M')
            new_start = datetime.strptime(start_time, '%Y-%m-%d %H:%M')
            new_end = datetime.strptime(end_time, '%Y-%m-%d %H:%M')
            # 冲突判定：新预约[s1,e1)与已有预约[s2,e2)满足e1 > s2 且 s1 < e2
            if new_end > existing_start and new_start < existing_end:
                return True
    return False


def book_meeting(data):
    """
    预约会议室
    :param data: 预约数据
    :return: 响应结果
    """
    global next_id
    
    # 解析参数
    organizer_name = data.get('organizerName')
    room_name = data.get('roomName')
    topic = data.get('topic')
    start_time = data.get('startTime')
    end_time = data.get('endTime')
    attendee_count = data.get('attendeeCount')
    
    # 数据合法性校验
    if not all([organizer_name, room_name, topic, start_time, end_time, attendee_count]):
        return {"success": False, "msg": "所有字段不能为空"}
    
    # 校验参与人数
    if not isinstance(attendee_count, int) or attendee_count <= 0:
        return {"success": False, "msg": "参与人数必须为大于0的整数"}
    
    # 校验时间格式
    try:
        start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M')
        end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M')
    except ValueError:
        return {"success": False, "msg": "时间格式错误，应为yyyy-MM-dd HH:mm"}
    
    # 校验时间逻辑
    if start_dt >= end_dt:
        return {"success": False, "msg": "开始时间必须早于结束时间"}
    
    if start_dt < datetime.now():
        return {"success": False, "msg": "开始时间不能早于当前时间"}
    
    # 时间冲突校验
    if is_conflict(room_name, start_time, end_time):
        return {"success": False, "msg": "该会议室在所选时间段已被预约"}
    
    # 新增预约
    meeting = {
        "meetingId": next_id,
        "organizerName": organizer_name,
        "roomName": room_name,
        "topic": topic,
        "startTime": start_time,
        "endTime": end_time,
        "attendeeCount": attendee_count
    }
    meeting_list.append(meeting)
    meeting_id = next_id
    next_id += 1
    
    return {"success": True, "msg": "预约成功", "meetingId": meeting_id}


def query_by_id(data):
    """
    按ID查询预约
    :param data: 查询数据
    :return: 响应结果
    """
    meeting_id = data.get('meetingId')
    
    if not isinstance(meeting_id, int):
        return {"success": False, "msg": "预约ID必须为整数"}
    
    for meeting in meeting_list:
        if meeting['meetingId'] == meeting_id:
            return {"success": True, "data": meeting}
    
    return {"success": False, "msg": "无此预约ID"}


def query_by_organizer(data):
    """
    按组织者查询预约
    :param data: 查询数据
    :return: 响应结果
    """
    organizer_name = data.get('organizerName')
    
    if not organizer_name:
        return {"success": False, "msg": "组织者姓名不能为空"}
    
    results = [meeting for meeting in meeting_list if meeting['organizerName'] == organizer_name]
    return {"success": True, "data": results}


def cancel_meeting(data):
    """
    取消预约
    :param data: 取消数据
    :return: 响应结果
    """
    meeting_id = data.get('meetingId')
    
    if not isinstance(meeting_id, int):
        return {"success": False, "msg": "预约ID必须为整数"}
    
    for i, meeting in enumerate(meeting_list):
        if meeting['meetingId'] == meeting_id:
            del meeting_list[i]
            return {"success": True, "msg": "取消成功"}
    
    return {"success": False, "msg": "无此预约ID，取消失败"}


def handle_client(conn):
    """
    处理单个客户端请求
    :param conn: 客户端连接
    """
    try:
        # 接收请求数据
        data = conn.recv(1024).decode('utf-8')
        if not data:
            return
        
        # 解析请求
        request = json.loads(data)
        action = request.get('action')
        
        # 处理不同类型的请求
        if action == 'book':
            response = book_meeting(request)
        elif action == 'queryById':
            response = query_by_id(request)
        elif action == 'queryByOrganizer':
            response = query_by_organizer(request)
        elif action == 'cancel':
            response = cancel_meeting(request)
        else:
            response = {"success": False, "msg": "未知操作"}
        
        # 返回响应
        conn.send(json.dumps(response).encode('utf-8'))
    except Exception as e:
        # 异常处理
        error_response = {"success": False, "msg": f"服务器错误: {str(e)}"}
        conn.send(json.dumps(error_response).encode('utf-8'))
    finally:
        conn.close()


def start_server():
    """
    启动服务器
    """
    # 创建socket服务端
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', 8888))
    server.listen(5)
    
    print("服务器启动，监听端口8888")
    
    while True:
        # 接收客户端连接
        conn, addr = server.accept()
        print(f"客户端 {addr} 连接")
        
        # 开启线程处理客户端请求
        client_thread = threading.Thread(target=handle_client, args=(conn,))
        client_thread.daemon = True
        client_thread.start()


if __name__ == "__main__":
    start_server()
