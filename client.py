#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户端代码
功能：实现GUI界面，处理用户交互，与服务器端通信
风格：Google Material Design
"""

import tkinter as tk
from tkinter import messagebox
import json
import socket
import os
from PIL import Image, ImageTk


# ==================== Google Material Design 色彩系统 ====================
COLORS = {
    "primary": "#4285F4",
    "primary_dark": "#3367D6",
    "primary_light": "#8AB4F8",
    "secondary": "#34A853",
    "secondary_dark": "#2D9249",
    "error": "#EA4335",
    "error_dark": "#D93025",
    "warning": "#FBBC05",
    "surface": "#FFFFFF",
    "background": "#F8F9FA",
    "on_primary": "#FFFFFF",
    "on_surface": "#202124",
    "on_surface_variant": "#5F6368",
    "outline": "#DADCE0",
    "outline_variant": "#E8EAED",
    "card_shadow": "#00000012",
    "ripple": "#1A73E8",
}

FONT_FAMILY = "Segoe UI"
FONT_FAMILY_CN = "微软雅黑"


class ClientApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("会议室预约管理系统")
        self.root.geometry("480x680")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["background"])

        self.current_frame = None
        self.bg_photo = None
        self._load_background()

        self.show_login_page()
        self.root.mainloop()

    def _load_background(self):
        bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "background.png")
        if os.path.exists(bg_path):
            img = Image.open(bg_path)
            img = img.resize((480, 680), Image.LANCZOS)
            overlay = Image.new("RGBA", img.size, (248, 249, 250, 210))
            img = img.convert("RGBA")
            img = Image.alpha_composite(img, overlay)
            img = img.convert("RGB")
            self.bg_photo = ImageTk.PhotoImage(img)

    def _create_page(self):
        if self.current_frame:
            self.current_frame.destroy()

        frame = tk.Frame(self.root, bg=COLORS["background"])
        frame.pack(fill=tk.BOTH, expand=True)

        if self.bg_photo:
            bg_label = tk.Label(frame, image=self.bg_photo, bg=COLORS["background"])
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.current_frame = frame
        return frame

    # ==================== Material 组件工厂 ====================
    def _make_card(self, parent, **kwargs):
        card = tk.Frame(
            parent, bg=COLORS["surface"],
            highlightbackground=COLORS["outline_variant"],
            highlightthickness=1,
            padx=24, pady=20,
            **kwargs
        )
        return card

    def _make_headline(self, parent, text, size=24):
        lbl = tk.Label(
            parent, text=text,
            font=(FONT_FAMILY_CN, size, "bold"),
            fg=COLORS["on_surface"], bg=parent.cget("bg")
        )
        return lbl

    def _make_subtitle(self, parent, text, size=12):
        lbl = tk.Label(
            parent, text=text,
            font=(FONT_FAMILY, size),
            fg=COLORS["on_surface_variant"], bg=parent.cget("bg")
        )
        return lbl

    def _make_body(self, parent, text, size=11, fg=None):
        lbl = tk.Label(
            parent, text=text,
            font=(FONT_FAMILY_CN, size),
            fg=fg or COLORS["on_surface"], bg=parent.cget("bg")
        )
        return lbl

    def _make_filled_button(self, parent, text, command, color=None, width=20):
        bg = color or COLORS["primary"]
        btn = tk.Button(
            parent, text=text, command=command,
            font=(FONT_FAMILY_CN, 11, "bold"),
            fg=COLORS["on_primary"], bg=bg,
            activebackground=COLORS["primary_dark"], activeforeground=COLORS["on_primary"],
            relief=tk.FLAT, bd=0, cursor="hand2",
            width=width, height=1,
            pady=8
        )
        return btn

    def _make_outlined_button(self, parent, text, command, width=12):
        btn = tk.Button(
            parent, text=text, command=command,
            font=(FONT_FAMILY_CN, 10),
            fg=COLORS["primary"], bg=COLORS["surface"],
            activebackground=COLORS["outline_variant"], activeforeground=COLORS["primary_dark"],
            relief=tk.FLAT, bd=1, cursor="hand2",
            width=width, height=1,
            highlightbackground=COLORS["outline"],
            highlightthickness=1,
            pady=6
        )
        return btn

    def _make_text_button(self, parent, text, command, fg=None):
        btn = tk.Button(
            parent, text=text, command=command,
            font=(FONT_FAMILY_CN, 10),
            fg=fg or COLORS["error"], bg=parent.cget("bg"),
            activebackground=parent.cget("bg"), activeforeground=COLORS["error_dark"],
            relief=tk.FLAT, bd=0, cursor="hand2",
            pady=4
        )
        return btn

    def _make_entry(self, parent, var, placeholder="", width=28):
        entry_frame = tk.Frame(parent, bg=COLORS["surface"])
        entry = tk.Entry(
            entry_frame, textvariable=var,
            font=(FONT_FAMILY_CN, 11),
            fg=COLORS["on_surface"], bg=COLORS["surface"],
            insertbackground=COLORS["primary"],
            relief=tk.FLAT, bd=0,
            width=width
        )
        entry.pack(side=tk.TOP, fill=tk.X, pady=(4, 0))
        underline = tk.Frame(entry_frame, bg=COLORS["outline"], height=1)
        underline.pack(side=tk.TOP, fill=tk.X, pady=(0, 0))
        return entry_frame, entry

    def _make_field(self, parent, label_text, var, width=28):
        field_frame = tk.Frame(parent, bg=COLORS["surface"])
        label = tk.Label(
            field_frame, text=label_text,
            font=(FONT_FAMILY_CN, 10),
            fg=COLORS["on_surface_variant"], bg=COLORS["surface"],
            anchor=tk.W
        )
        label.pack(side=tk.TOP, fill=tk.X)
        entry = tk.Entry(
            field_frame, textvariable=var,
            font=(FONT_FAMILY_CN, 12),
            fg=COLORS["on_surface"], bg=COLORS["surface"],
            insertbackground=COLORS["primary"],
            relief=tk.FLAT, bd=0,
            width=width
        )
        entry.pack(side=tk.TOP, fill=tk.X, pady=(2, 0))
        underline = tk.Frame(field_frame, bg=COLORS["outline"], height=1)
        underline.pack(side=tk.TOP, fill=tk.X)
        return field_frame, entry

    def _make_icon_button(self, parent, icon_text, command, bg=None):
        btn = tk.Button(
            parent, text=icon_text, command=command,
            font=(FONT_FAMILY, 14),
            fg=COLORS["on_surface_variant"], bg=bg or parent.cget("bg"),
            activebackground=COLORS["outline_variant"], activeforeground=COLORS["on_surface"],
            relief=tk.FLAT, bd=0, cursor="hand2",
            width=3, height=1, pady=0
        )
        return btn

    # ==================== 登录页面 ====================
    def show_login_page(self):
        page = self._create_page()

        top_area = tk.Frame(page, bg=COLORS["primary"], height=200)
        top_area.pack(fill=tk.X)
        top_area.pack_propagate(False)

        google_logo = tk.Label(
            top_area, text="G",
            font=(FONT_FAMILY, 48, "bold"),
            fg=COLORS["on_primary"], bg=COLORS["primary"]
        )
        google_logo.pack(pady=(40, 5))

        title = tk.Label(
            top_area, text="会议室预约管理系统",
            font=(FONT_FAMILY_CN, 16, "bold"),
            fg=COLORS["on_primary"], bg=COLORS["primary"]
        )
        title.pack(pady=(0, 5))

        subtitle = tk.Label(
            top_area, text="Conference Room Booking",
            font=(FONT_FAMILY, 10),
            fg=COLORS["primary_light"], bg=COLORS["primary"]
        )
        subtitle.pack()

        card = self._make_card(page)
        card.place(relx=0.5, y=230, anchor=tk.N)

        field_frame = tk.Frame(card, bg=COLORS["surface"])
        field_frame.pack(fill=tk.X, pady=(0, 20))

        field_label = tk.Label(
            field_frame, text="用户名",
            font=(FONT_FAMILY_CN, 10),
            fg=COLORS["on_surface_variant"], bg=COLORS["surface"],
            anchor=tk.W
        )
        field_label.pack(side=tk.TOP, fill=tk.X)

        self.username_var = tk.StringVar()
        self.username_entry = tk.Entry(
            field_frame, textvariable=self.username_var,
            font=(FONT_FAMILY_CN, 14),
            fg=COLORS["on_surface"], bg=COLORS["surface"],
            insertbackground=COLORS["primary"],
            relief=tk.FLAT, bd=0, width=24
        )
        self.username_entry.pack(side=tk.TOP, fill=tk.X, pady=(2, 0))
        self.username_entry.bind("<Return>", lambda event: self.login())

        self.login_underline = tk.Frame(field_frame, bg=COLORS["outline"], height=2)
        self.login_underline.pack(side=tk.TOP, fill=tk.X)

        self.login_tip = tk.Label(
            card, text="",
            font=(FONT_FAMILY_CN, 9),
            fg=COLORS["error"], bg=COLORS["surface"],
            anchor=tk.W
        )
        self.login_tip.pack(fill=tk.X, pady=(4, 8))

        login_btn = self._make_filled_button(card, "登  录", self.login, width=24)
        login_btn.pack(pady=(4, 0))

    def login(self):
        username = self.username_var.get().strip()
        if not username:
            self.login_tip.config(text="请输入用户名")
            self.login_underline.config(bg=COLORS["error"])
            return
        self.login_tip.config(text="")
        self.login_underline.config(bg=COLORS["outline"])
        self.show_main_page()

    # ==================== 主界面 ====================
    def show_main_page(self):
        page = self._create_page()

        app_bar = tk.Frame(page, bg=COLORS["primary"], height=64)
        app_bar.pack(fill=tk.X)
        app_bar.pack_propagate(False)

        back_btn = self._make_icon_button(app_bar, "←", self.show_login_page, bg=COLORS["primary"])
        back_btn.config(fg=COLORS["on_primary"])
        back_btn.pack(side=tk.LEFT, padx=8)

        app_title = tk.Label(
            app_bar, text="会议室预约系统",
            font=(FONT_FAMILY_CN, 14, "bold"),
            fg=COLORS["on_primary"], bg=COLORS["primary"]
        )
        app_title.pack(side=tk.LEFT, padx=8)

        content = tk.Frame(page, bg=page.cget("bg"))
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        welcome = tk.Label(
            content, text="欢迎使用",
            font=(FONT_FAMILY_CN, 20, "bold"),
            fg=COLORS["on_surface"], bg=content.cget("bg")
        )
        welcome.pack(anchor=tk.W, pady=(8, 2))

        welcome_sub = tk.Label(
            content, text="请选择您需要的操作",
            font=(FONT_FAMILY_CN, 11),
            fg=COLORS["on_surface_variant"], bg=content.cget("bg")
        )
        welcome_sub.pack(anchor=tk.W, pady=(0, 16))

        buttons_data = [
            ("预约会议室", self.show_book_page, COLORS["secondary"], "📋"),
            ("按ID查询", self.show_query_id_page, COLORS["primary"], "🔍"),
            ("按组织者查询", self.show_query_organizer_page, "#7B1FA2", "👥"),
            ("取消预约", self.show_cancel_page, COLORS["error"], "✕"),
        ]

        for text, command, color, icon in buttons_data:
            card = self._make_card(content)
            card.pack(fill=tk.X, pady=6)

            btn_frame = tk.Frame(card, bg=COLORS["surface"])
            btn_frame.pack(fill=tk.X)

            icon_label = tk.Label(
                btn_frame, text=icon,
                font=(FONT_FAMILY, 18),
                fg=color, bg=COLORS["surface"],
                width=3
            )
            icon_label.pack(side=tk.LEFT, padx=(0, 12))

            text_frame = tk.Frame(btn_frame, bg=COLORS["surface"])
            text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

            btn_label = tk.Label(
                text_frame, text=text,
                font=(FONT_FAMILY_CN, 13, "bold"),
                fg=COLORS["on_surface"], bg=COLORS["surface"],
                anchor=tk.W
            )
            btn_label.pack(anchor=tk.W)

            btn_desc = tk.Label(
                text_frame, text=self._get_btn_desc(text),
                font=(FONT_FAMILY_CN, 9),
                fg=COLORS["on_surface_variant"], bg=COLORS["surface"],
                anchor=tk.W
            )
            btn_desc.pack(anchor=tk.W)

            arrow = tk.Label(
                btn_frame, text="›",
                font=(FONT_FAMILY, 20),
                fg=COLORS["on_surface_variant"], bg=COLORS["surface"]
            )
            arrow.pack(side=tk.RIGHT)

            for widget in [card, btn_frame, icon_label, text_frame, btn_label, btn_desc, arrow]:
                widget.bind("<Button-1>", lambda e, cmd=command: cmd())
                widget.configure(cursor="hand2")

        exit_btn = self._make_text_button(content, "退出登录", self.exit_app)
        exit_btn.pack(pady=(16, 8))

    def _get_btn_desc(self, text):
        desc_map = {
            "预约会议室": "选择会议室并填写预约信息",
            "按ID查询": "通过预约编号查询预约详情",
            "按组织者查询": "查看某组织者的所有预约",
            "取消预约": "取消已有的预约记录",
        }
        return desc_map.get(text, "")

    # ==================== 预约会议室页面 ====================
    def show_book_page(self):
        page = self._create_page()
        self._build_app_bar(page, "预约会议室")

        scroll_area = tk.Frame(page, bg=page.cget("bg"))
        scroll_area.pack(fill=tk.BOTH, expand=True, padx=20, pady=8)

        card = self._make_card(scroll_area)
        card.pack(fill=tk.X, pady=(8, 0))

        fields = [
            ("组织者姓名", "organizer_var"),
            ("会议室名称", "room_var"),
            ("会议主题", "topic_var"),
            ("开始时间  yyyy-MM-dd HH:mm", "start_var"),
            ("结束时间  yyyy-MM-dd HH:mm", "end_var"),
            ("参与人数", "attendee_var"),
        ]

        self.book_vars = {}
        self.book_entries = []
        for label_text, var_name in fields:
            var = tk.StringVar()
            self.book_vars[var_name] = var
            field_frame, entry = self._make_field(card, label_text, var, width=28)
            field_frame.pack(fill=tk.X, pady=6)
            self.book_entries.append(entry)

        self.organizer_var = self.book_vars["organizer_var"]
        self.room_var = self.book_vars["room_var"]
        self.topic_var = self.book_vars["topic_var"]
        self.start_var = self.book_vars["start_var"]
        self.end_var = self.book_vars["end_var"]
        self.attendee_var = self.book_vars["attendee_var"]

        self.book_tip = tk.Label(
            card, text="",
            font=(FONT_FAMILY_CN, 9),
            fg=COLORS["error"], bg=COLORS["surface"],
            anchor=tk.W
        )
        self.book_tip.pack(fill=tk.X, pady=(4, 0))

        btn_area = tk.Frame(scroll_area, bg=scroll_area.cget("bg"))
        btn_area.pack(fill=tk.X, pady=(16, 8))

        book_btn = self._make_filled_button(btn_area, "确认预约", self.book_meeting, color=COLORS["secondary"], width=16)
        book_btn.pack(side=tk.LEFT, padx=(0, 12))

        back_btn = self._make_outlined_button(btn_area, "返回", self.show_main_page, width=10)
        back_btn.pack(side=tk.LEFT)

    # ==================== 按ID查询页面 ====================
    def show_query_id_page(self):
        page = self._create_page()
        self._build_app_bar(page, "按ID查询")

        content = tk.Frame(page, bg=page.cget("bg"))
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=8)

        card = self._make_card(content)
        card.pack(fill=tk.X, pady=(8, 0))

        self.query_id_var = tk.StringVar()
        field_frame, entry = self._make_field(card, "预约ID", self.query_id_var, width=28)
        field_frame.pack(fill=tk.X, pady=6)

        query_btn = self._make_filled_button(card, "查  询", self.query_by_id, width=24)
        query_btn.pack(pady=(12, 0))

        result_card = self._make_card(content)
        result_card.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        result_title = tk.Label(
            result_card, text="查询结果",
            font=(FONT_FAMILY_CN, 11, "bold"),
            fg=COLORS["on_surface"], bg=COLORS["surface"],
            anchor=tk.W
        )
        result_title.pack(fill=tk.X, pady=(0, 8))

        self.result_listbox = tk.Listbox(
            result_card, font=(FONT_FAMILY_CN, 10),
            width=36, height=8,
            bg=COLORS["background"], fg=COLORS["on_surface"],
            selectbackground=COLORS["primary"], selectforeground=COLORS["on_primary"],
            relief=tk.FLAT, bd=0,
            highlightthickness=1,
            highlightbackground=COLORS["outline_variant"],
            activestyle="none"
        )
        self.result_listbox.pack(fill=tk.BOTH, expand=True)

        self.query_id_tip = tk.Label(
            content, text="",
            font=(FONT_FAMILY_CN, 9),
            fg=COLORS["error"], bg=content.cget("bg"),
            anchor=tk.W
        )
        self.query_id_tip.pack(fill=tk.X, pady=(4, 0))

        btn_area = tk.Frame(content, bg=content.cget("bg"))
        btn_area.pack(fill=tk.X, pady=(12, 8))

        back_btn = self._make_outlined_button(btn_area, "返回", self.show_main_page, width=10)
        back_btn.pack(side=tk.LEFT)

    # ==================== 按组织者查询页面 ====================
    def show_query_organizer_page(self):
        page = self._create_page()
        self._build_app_bar(page, "按组织者查询")

        content = tk.Frame(page, bg=page.cget("bg"))
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=8)

        card = self._make_card(content)
        card.pack(fill=tk.X, pady=(8, 0))

        self.query_organizer_var = tk.StringVar()
        field_frame, entry = self._make_field(card, "组织者姓名", self.query_organizer_var, width=28)
        field_frame.pack(fill=tk.X, pady=6)

        query_btn = self._make_filled_button(card, "查  询", self.query_by_organizer, color="#7B1FA2", width=24)
        query_btn.pack(pady=(12, 0))

        result_card = self._make_card(content)
        result_card.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        result_title = tk.Label(
            result_card, text="查询结果",
            font=(FONT_FAMILY_CN, 11, "bold"),
            fg=COLORS["on_surface"], bg=COLORS["surface"],
            anchor=tk.W
        )
        result_title.pack(fill=tk.X, pady=(0, 8))

        self.result_listbox = tk.Listbox(
            result_card, font=(FONT_FAMILY_CN, 10),
            width=36, height=8,
            bg=COLORS["background"], fg=COLORS["on_surface"],
            selectbackground="#7B1FA2", selectforeground=COLORS["on_primary"],
            relief=tk.FLAT, bd=0,
            highlightthickness=1,
            highlightbackground=COLORS["outline_variant"],
            activestyle="none"
        )
        self.result_listbox.pack(fill=tk.BOTH, expand=True)

        self.query_organizer_tip = tk.Label(
            content, text="",
            font=(FONT_FAMILY_CN, 9),
            fg=COLORS["error"], bg=content.cget("bg"),
            anchor=tk.W
        )
        self.query_organizer_tip.pack(fill=tk.X, pady=(4, 0))

        btn_area = tk.Frame(content, bg=content.cget("bg"))
        btn_area.pack(fill=tk.X, pady=(12, 8))

        back_btn = self._make_outlined_button(btn_area, "返回", self.show_main_page, width=10)
        back_btn.pack(side=tk.LEFT)

    # ==================== 取消预约页面 ====================
    def show_cancel_page(self):
        page = self._create_page()
        self._build_app_bar(page, "取消预约")

        content = tk.Frame(page, bg=page.cget("bg"))
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=8)

        card = self._make_card(content)
        card.pack(fill=tk.X, pady=(40, 0))

        warn_icon = tk.Label(
            card, text="⚠",
            font=(FONT_FAMILY, 32),
            fg=COLORS["warning"], bg=COLORS["surface"]
        )
        warn_icon.pack(pady=(0, 8))

        warn_text = tk.Label(
            card, text="取消预约后将无法恢复，请确认预约ID",
            font=(FONT_FAMILY_CN, 10),
            fg=COLORS["on_surface_variant"], bg=COLORS["surface"]
        )
        warn_text.pack(pady=(0, 16))

        self.cancel_id_var = tk.StringVar()
        field_frame, entry = self._make_field(card, "预约ID", self.cancel_id_var, width=28)
        field_frame.pack(fill=tk.X, pady=6)

        self.cancel_tip = tk.Label(
            card, text="",
            font=(FONT_FAMILY_CN, 9),
            fg=COLORS["error"], bg=COLORS["surface"],
            anchor=tk.W
        )
        self.cancel_tip.pack(fill=tk.X, pady=(4, 0))

        btn_area = tk.Frame(card, bg=COLORS["surface"])
        btn_area.pack(fill=tk.X, pady=(16, 0))

        cancel_btn = self._make_filled_button(btn_area, "确认取消", self.cancel_meeting, color=COLORS["error"], width=14)
        cancel_btn.pack(side=tk.LEFT, padx=(0, 12))

        back_btn = self._make_outlined_button(btn_area, "返回", self.show_main_page, width=10)
        back_btn.pack(side=tk.LEFT)

    # ==================== App Bar 构建器 ====================
    def _build_app_bar(self, parent, title_text):
        app_bar = tk.Frame(parent, bg=COLORS["primary"], height=56)
        app_bar.pack(fill=tk.X)
        app_bar.pack_propagate(False)

        back_btn = self._make_icon_button(app_bar, "←", self.show_main_page, bg=COLORS["primary"])
        back_btn.config(fg=COLORS["on_primary"], font=(FONT_FAMILY, 16))
        back_btn.pack(side=tk.LEFT, padx=8)

        title = tk.Label(
            app_bar, text=title_text,
            font=(FONT_FAMILY_CN, 14, "bold"),
            fg=COLORS["on_primary"], bg=COLORS["primary"]
        )
        title.pack(side=tk.LEFT, padx=8)

        exit_btn = self._make_icon_button(app_bar, "✕", self.exit_app, bg=COLORS["primary"])
        exit_btn.config(fg=COLORS["on_primary"], font=(FONT_FAMILY, 12))
        exit_btn.pack(side=tk.RIGHT, padx=8)

    # ==================== RPC请求模块 ====================
    def request(self, data):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', 8888))
            sock.send(json.dumps(data).encode('utf-8'))
            response = sock.recv(4096).decode('utf-8')
            sock.close()
            return json.loads(response)
        except Exception:
            messagebox.showerror("连接失败", "无法连接服务器，请确认server.py已启动")
            return None

    # ==================== 业务逻辑 ====================
    def book_meeting(self):
        organizer = self.organizer_var.get().strip()
        room = self.room_var.get().strip()
        topic = self.topic_var.get().strip()
        start = self.start_var.get().strip()
        end = self.end_var.get().strip()
        attendee = self.attendee_var.get().strip()

        if not all([organizer, room, topic, start, end, attendee]):
            self.book_tip.config(text="请填写所有字段")
            return

        try:
            attendee_count = int(attendee)
            if attendee_count <= 0:
                raise ValueError
        except ValueError:
            self.book_tip.config(text="参与人数必须为大于0的整数")
            return

        data = {
            "action": "book",
            "organizerName": organizer,
            "roomName": room,
            "topic": topic,
            "startTime": start,
            "endTime": end,
            "attendeeCount": attendee_count
        }

        response = self.request(data)
        if response:
            if response["success"]:
                messagebox.showinfo("预约成功", f"预约成功！预约ID: {response['meetingId']}")
                self.organizer_var.set("")
                self.room_var.set("")
                self.topic_var.set("")
                self.start_var.set("")
                self.end_var.set("")
                self.attendee_var.set("")
                self.book_tip.config(text="")
            else:
                self.book_tip.config(text=response["msg"])

    def query_by_id(self):
        id_str = self.query_id_var.get().strip()
        if not id_str:
            self.query_id_tip.config(text="请输入预约ID")
            return

        try:
            meeting_id = int(id_str)
        except ValueError:
            self.query_id_tip.config(text="预约ID必须为整数")
            return

        data = {"action": "queryById", "meetingId": meeting_id}

        response = self.request(data)
        if response:
            if response["success"]:
                self.result_listbox.delete(0, tk.END)
                meeting = response["data"]
                self.result_listbox.insert(tk.END, f"预约ID: {meeting['meetingId']}")
                self.result_listbox.insert(tk.END, f"组织者: {meeting['organizerName']}")
                self.result_listbox.insert(tk.END, f"会议室: {meeting['roomName']}")
                self.result_listbox.insert(tk.END, f"主  题: {meeting['topic']}")
                self.result_listbox.insert(tk.END, f"开始时间: {meeting['startTime']}")
                self.result_listbox.insert(tk.END, f"结束时间: {meeting['endTime']}")
                self.result_listbox.insert(tk.END, f"参与人数: {meeting['attendeeCount']}")
                self.query_id_tip.config(text="")
            else:
                self.query_id_tip.config(text=response["msg"])
                self.result_listbox.delete(0, tk.END)

    def query_by_organizer(self):
        organizer = self.query_organizer_var.get().strip()
        if not organizer:
            self.query_organizer_tip.config(text="请输入组织者姓名")
            return

        data = {"action": "queryByOrganizer", "organizerName": organizer}

        response = self.request(data)
        if response:
            if response["success"]:
                self.result_listbox.delete(0, tk.END)
                meetings = response["data"]
                if not meetings:
                    self.result_listbox.insert(tk.END, "无预约记录")
                else:
                    for meeting in meetings:
                        self.result_listbox.insert(tk.END, f"ID: {meeting['meetingId']}, 会议室: {meeting['roomName']}")
                        self.result_listbox.insert(tk.END, f"主题: {meeting['topic']}, 时间: {meeting['startTime']} - {meeting['endTime']}")
                        self.result_listbox.insert(tk.END, "")
                self.query_organizer_tip.config(text="")
            else:
                self.query_organizer_tip.config(text=response["msg"])
                self.result_listbox.delete(0, tk.END)

    def cancel_meeting(self):
        id_str = self.cancel_id_var.get().strip()
        if not id_str:
            self.cancel_tip.config(text="请输入预约ID")
            return

        try:
            meeting_id = int(id_str)
        except ValueError:
            self.cancel_tip.config(text="预约ID必须为整数")
            return

        data = {"action": "cancel", "meetingId": meeting_id}

        response = self.request(data)
        if response:
            if response["success"]:
                messagebox.showinfo("取消成功", "预约已成功取消")
                self.cancel_id_var.set("")
                self.cancel_tip.config(text="")
            else:
                self.cancel_tip.config(text=response["msg"])

    def exit_app(self):
        if messagebox.askyesno("确认退出", "确定要退出登录吗？"):
            self.show_login_page()


if __name__ == "__main__":
    ClientApp()
