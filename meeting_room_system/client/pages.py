"""Tkinter client UI."""

import calendar
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk

from .rpc_client import RpcClient


ROOM_OPTIONS = [
    f"{floor}层10人{index}"
    for floor in range(1, 7)
    for index in range(1, 4)
] + [
    f"{floor}层5人{index}"
    for floor in range(1, 7)
    for index in range(1, 3)
]


class MeetingRoomApp(tk.Tk):
    def __init__(self, client=None):
        super().__init__()
        self.client = client or RpcClient()
        self.title("会议室预约管理系统")
        self.geometry("860x620")
        self.minsize(560, 420)
        self.current_user = ""
        self.is_admin = False
        self.current_frame = None
        self.result_table = None
        self.room_table = None
        self._setup_style()
        self.show_login()

    def _setup_style(self):
        self.configure(bg="#f6f8fa")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f6f8fa")
        style.configure("Card.TFrame", background="#ffffff", relief="flat")
        style.configure("TLabel", background="#f6f8fa", foreground="#24292f", font=("Microsoft YaHei UI", 10))
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 18, "bold"))
        style.configure("Muted.TLabel", foreground="#57606a")
        style.configure("TButton", font=("Microsoft YaHei UI", 10), padding=(10, 6))
        style.configure("Primary.TButton", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Treeview", rowheight=26, font=("Microsoft YaHei UI", 9))
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 9, "bold"))

    def _clear(self):
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = ttk.Frame(self)
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        return self.current_frame

    def _scroll_page(self):
        shell = self._clear()
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(0, weight=1)

        canvas = tk.Canvas(shell, bg="#f6f8fa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(shell, orient=tk.VERTICAL, command=canvas.yview)
        content = ttk.Frame(canvas)
        content_id = canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        def sync_scroll(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def sync_width(event):
            canvas.itemconfigure(content_id, width=event.width)

        def on_mousewheel(event):
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-event.delta / 120), "units")

        def bind_mousewheel(_event):
            canvas.bind_all("<MouseWheel>", on_mousewheel)

        def unbind_mousewheel(_event):
            canvas.unbind_all("<MouseWheel>")

        content.bind("<Configure>", sync_scroll)
        canvas.bind("<Configure>", sync_width)
        canvas.bind("<Enter>", bind_mousewheel)
        canvas.bind("<Leave>", unbind_mousewheel)
        content.bind("<Enter>", bind_mousewheel)
        content.bind("<Leave>", unbind_mousewheel)

        inner = ttk.Frame(content, padding=(24, 20, 24, 20))
        inner.pack(fill=tk.BOTH, expand=True)
        return inner

    def _card(self, parent, padding=18):
        card = ttk.Frame(parent, style="Card.TFrame", padding=padding)
        card.columnconfigure(1, weight=1)
        return card

    def _home_command(self):
        return self.show_admin_main if self.is_admin else self.show_main

    def _header(self, parent, title, show_back=False, back_command=None):
        header = ttk.Frame(parent)
        header.pack(fill=tk.X, pady=(0, 16))
        ttk.Label(header, text=title, style="Title.TLabel").pack(side=tk.LEFT)
        if show_back:
            ttk.Button(header, text="返回", command=back_command or self._home_command()).pack(side=tk.RIGHT, padx=(8, 0))
        if self.current_user:
            name = f"管理员：{self.current_user}" if self.is_admin else f"当前用户：{self.current_user}"
            ttk.Label(header, text=name, style="Muted.TLabel").pack(side=tk.RIGHT, padx=(8, 0))

    def _text_field(self, parent, row, label, variable):
        ttk.Label(parent, text=label, background="#ffffff", wraplength=220).grid(row=row, column=0, sticky=tk.W, pady=7)
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky=tk.EW, pady=7, padx=(12, 0))
        return entry

    def _room_field(self, parent, row, variable):
        ttk.Label(parent, text="会议室", background="#ffffff", wraplength=220).grid(row=row, column=0, sticky=tk.W, pady=7)
        combo = ttk.Combobox(parent, textvariable=variable, values=ROOM_OPTIONS, state="readonly")
        combo.current(0)
        combo.grid(row=row, column=1, sticky=tk.EW, pady=7, padx=(12, 0))
        return combo

    def _default_datetime(self, offset_minutes):
        now = datetime.now() + timedelta(minutes=offset_minutes)
        minute = ((now.minute + 4) // 5) * 5
        if minute >= 60:
            now = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            now = now.replace(minute=minute, second=0, microsecond=0)
        return now

    def _datetime_picker(self, parent, row, label, default_time):
        ttk.Label(parent, text=label, background="#ffffff", wraplength=220).grid(row=row, column=0, sticky=tk.W, pady=7)

        picker = tk.Frame(parent, bg="#ffffff")
        picker.grid(row=row, column=1, sticky=tk.EW, pady=7, padx=(12, 0))
        for column in range(10):
            picker.columnconfigure(column, weight=1 if column in (0, 2, 4, 6, 8) else 0)

        current_year = datetime.now().year
        vars_ = {
            "year": tk.StringVar(value=f"{default_time.year:04d}"),
            "month": tk.StringVar(value=f"{default_time.month:02d}"),
            "day": tk.StringVar(value=f"{default_time.day:02d}"),
            "hour": tk.StringVar(value=f"{default_time.hour:02d}"),
            "minute": tk.StringVar(value=f"{default_time.minute:02d}"),
        }

        year_combo = ttk.Combobox(picker, textvariable=vars_["year"], values=[str(year) for year in range(current_year, current_year + 6)], width=6, state="readonly")
        month_combo = ttk.Combobox(picker, textvariable=vars_["month"], values=[f"{month:02d}" for month in range(1, 13)], width=4, state="readonly")
        day_combo = ttk.Combobox(picker, textvariable=vars_["day"], values=[], width=4, state="readonly")
        hour_combo = ttk.Combobox(picker, textvariable=vars_["hour"], values=[f"{hour:02d}" for hour in range(24)], width=4, state="readonly")
        minute_combo = ttk.Combobox(picker, textvariable=vars_["minute"], values=[f"{minute:02d}" for minute in range(0, 60, 5)], width=4, state="readonly")

        def update_days(*_args):
            try:
                year = int(vars_["year"].get())
                month = int(vars_["month"].get())
            except ValueError:
                return
            max_day = calendar.monthrange(year, month)[1]
            days = [f"{day:02d}" for day in range(1, max_day + 1)]
            day_combo.configure(values=days)
            if vars_["day"].get() not in days:
                vars_["day"].set(days[-1])

        vars_["year"].trace_add("write", update_days)
        vars_["month"].trace_add("write", update_days)
        update_days()

        widgets = [
            (year_combo, "年"),
            (month_combo, "月"),
            (day_combo, "日"),
            (hour_combo, "时"),
            (minute_combo, "分"),
        ]
        for index, (combo, suffix) in enumerate(widgets):
            combo.grid(row=0, column=index * 2, sticky=tk.EW)
            ttk.Label(picker, text=suffix, background="#ffffff").grid(row=0, column=index * 2 + 1, padx=(2, 8 if index < len(widgets) - 1 else 0))

        return vars_

    def _datetime_value(self, vars_):
        return f"{vars_['year'].get()}-{vars_['month'].get()}-{vars_['day'].get()} {vars_['hour'].get()}:{vars_['minute'].get()}"

    def _request(self, action, data=None):
        try:
            return self.client.request(action, data)
        except Exception as exc:
            messagebox.showerror("连接失败", f"无法连接服务器，请先启动服务端。\n{exc}")
            return None

    def show_login(self):
        frame = self._clear()
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        card = ttk.Frame(frame, style="Card.TFrame", padding=32)
        card.grid(row=0, column=0, sticky="n", padx=24, pady=(80, 24))
        card.columnconfigure(0, weight=1)

        ttk.Label(card, text="会议室预约管理系统", style="Title.TLabel", background="#ffffff").grid(row=0, column=0, sticky="w")
        ttk.Label(card, text="输入用户名后进入系统", style="Muted.TLabel", background="#ffffff").grid(row=1, column=0, sticky="w", pady=(4, 20))

        self.login_name = tk.StringVar()
        ttk.Label(card, text="用户名", background="#ffffff").grid(row=2, column=0, sticky="w")
        entry = ttk.Entry(card, textvariable=self.login_name)
        entry.grid(row=3, column=0, sticky="ew", pady=(4, 16))
        entry.bind("<Return>", lambda _event: self.login())
        ttk.Button(card, text="登录", style="Primary.TButton", command=self.login).grid(row=4, column=0, sticky="ew")
        entry.focus_set()

    def login(self):
        username = self.login_name.get().strip()
        if not username:
            messagebox.showwarning("输入错误", "用户名不能为空")
            return
        response = self._request("login", {"username": username})
        if response and response["success"]:
            self.current_user = username
            self.is_admin = username == "Admin"
            self.show_admin_main() if self.is_admin else self.show_main()
        elif response:
            messagebox.showerror("登录失败", response["msg"])

    def logout(self):
        if messagebox.askyesno("确认退出", "确定要退出当前登录吗？"):
            self.current_user = ""
            self.is_admin = False
            self.show_login()

    def show_main(self):
        self.is_admin = False
        frame = self._scroll_page()
        self._header(frame, "会议室预约")
        actions = ttk.Frame(frame)
        actions.pack(fill=tk.BOTH, expand=True)

        items = [
            ("预约会议室", "创建新的会议室预约", self.show_book),
            ("按 ID 查询", "根据预约编号查看详情", self.show_query_id),
            ("按组织者查询", "查看某个组织者的所有预约", self.show_query_organizer),
            ("按会议室查询", "查看某个会议室的预约记录", self.show_query_room),
            ("查询空闲会议室", "按时间段筛选可用会议室", self.show_available),
            ("取消预约", "根据预约编号删除预约", self.show_cancel),
        ]
        for index, (title, desc, command) in enumerate(items):
            card = self._card(actions)
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=8, pady=8)
            ttk.Label(card, text=title, font=("Microsoft YaHei UI", 13, "bold"), background="#ffffff").pack(anchor=tk.W)
            ttk.Label(card, text=desc, style="Muted.TLabel", background="#ffffff", wraplength=300).pack(anchor=tk.W, pady=(4, 12))
            ttk.Button(card, text="进入", command=command).pack(anchor=tk.E)
        for column in range(2):
            actions.columnconfigure(column, weight=1, uniform="actions")

        ttk.Button(frame, text="退出登录", command=self.logout).pack(anchor=tk.E, pady=(8, 0))

    def show_admin_main(self):
        self.is_admin = True
        frame = self._scroll_page()
        self._header(frame, "管理员控制台")
        actions = ttk.Frame(frame)
        actions.pack(fill=tk.BOTH, expand=True)

        items = [
            ("全部预约", "查看系统内所有预约记录", self.show_admin_meetings),
            ("全部会议室", "查看系统内所有会议室", self.show_admin_rooms),
            ("按组织者查询", "快速查看指定组织者预约", self.show_query_organizer),
            ("取消预约", "根据ID删除任意预约", self.show_cancel),
        ]
        for index, (title, desc, command) in enumerate(items):
            card = self._card(actions)
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=8, pady=8)
            ttk.Label(card, text=title, font=("Microsoft YaHei UI", 13, "bold"), background="#ffffff").pack(anchor=tk.W)
            ttk.Label(card, text=desc, style="Muted.TLabel", background="#ffffff", wraplength=300).pack(anchor=tk.W, pady=(4, 12))
            ttk.Button(card, text="进入", command=command).pack(anchor=tk.E)
        for column in range(2):
            actions.columnconfigure(column, weight=1, uniform="actions")

        ttk.Button(frame, text="退出登录", command=self.logout).pack(anchor=tk.E, pady=(8, 0))

    def show_book(self):
        frame = self._scroll_page()
        self._header(frame, "预约会议室", show_back=True)
        form = self._card(frame)
        form.pack(fill=tk.X)

        self.book_vars = {
            "organizer": tk.StringVar(value=self.current_user),
            "room": tk.StringVar(),
            "topic": tk.StringVar(),
            "count": tk.StringVar(),
        }
        self.book_start_vars = self._datetime_picker(form, 0, "开始时间", self._default_datetime(30))
        self._room_field(form, 1, self.book_vars["room"])
        self._text_field(form, 2, "会议主题", self.book_vars["topic"])
        self.book_end_vars = self._datetime_picker(form, 3, "结束时间", self._default_datetime(90))
        self._text_field(form, 4, "参与人数", self.book_vars["count"])

        buttons = ttk.Frame(frame)
        buttons.pack(fill=tk.X, pady=14)
        ttk.Button(buttons, text="提交预约", style="Primary.TButton", command=self.book).pack(side=tk.LEFT)

    def book(self):
        data = {
            "organizerName": self.book_vars["organizer"].get(),
            "roomName": self.book_vars["room"].get(),
            "topic": self.book_vars["topic"].get(),
            "startTime": self._datetime_value(self.book_start_vars),
            "endTime": self._datetime_value(self.book_end_vars),
            "attendeeCount": self.book_vars["count"].get(),
        }
        response = self._request("bookMeeting", data)
        if not response:
            return
        if response["success"]:
            messagebox.showinfo("预约成功", f"预约成功，ID：{response['data']['meetingId']}")
            self.show_main()
        else:
            messagebox.showerror("预约失败", response["msg"])

    def show_query_id(self):
        frame = self._scroll_page()
        self._header(frame, "按 ID 查询", show_back=True)
        query = self._card(frame)
        query.pack(fill=tk.X)
        self.query_id_var = tk.StringVar()
        ttk.Label(query, text="预约ID", background="#ffffff").pack(anchor=tk.W)
        ttk.Entry(query, textvariable=self.query_id_var).pack(fill=tk.X, pady=(4, 12))
        ttk.Button(query, text="查询", command=self.query_id).pack(anchor=tk.E)
        self._create_result_table(frame)

    def query_id(self):
        response = self._request("queryByID", {"meetingId": self.query_id_var.get()})
        self._show_meetings([response["data"]["meeting"]] if response and response["success"] else [])
        if response and not response["success"]:
            messagebox.showerror("查询失败", response["msg"])

    def show_query_organizer(self):
        frame = self._scroll_page()
        self._header(frame, "按组织者查询", show_back=True)
        query = self._card(frame)
        query.pack(fill=tk.X)
        self.query_org_var = tk.StringVar(value=self.current_user)
        ttk.Label(query, text="组织者", background="#ffffff").pack(anchor=tk.W)
        ttk.Entry(query, textvariable=self.query_org_var).pack(fill=tk.X, pady=(4, 12))
        ttk.Button(query, text="查询", command=self.query_organizer).pack(anchor=tk.E)
        self._create_result_table(frame)

    def query_organizer(self):
        response = self._request("queryByOrganizer", {"organizerName": self.query_org_var.get()})
        self._show_meetings(response["data"]["meetings"] if response and response["success"] else [])
        if response and not response["success"]:
            messagebox.showerror("查询失败", response["msg"])

    def show_query_room(self):
        frame = self._scroll_page()
        self._header(frame, "按会议室查询", show_back=True)
        query = self._card(frame)
        query.pack(fill=tk.X)
        self.query_room_var = tk.StringVar(value=ROOM_OPTIONS[0])
        ttk.Label(query, text="会议室", background="#ffffff").pack(anchor=tk.W)
        ttk.Combobox(query, textvariable=self.query_room_var, values=ROOM_OPTIONS, state="readonly").pack(fill=tk.X, pady=(4, 12))
        ttk.Button(query, text="查询", command=self.query_room).pack(anchor=tk.E)
        self._create_result_table(frame)

    def query_room(self):
        response = self._request("queryByRoom", {"roomName": self.query_room_var.get()})
        self._show_meetings(response["data"]["meetings"] if response and response["success"] else [])
        if response and not response["success"]:
            messagebox.showerror("查询失败", response["msg"])

    def show_available(self):
        frame = self._scroll_page()
        self._header(frame, "查询空闲会议室", show_back=True)
        query = self._card(frame)
        query.pack(fill=tk.X)
        self.available_count_var = tk.StringVar()
        self.available_start_vars = self._datetime_picker(query, 0, "开始时间", self._default_datetime(30))
        self.available_end_vars = self._datetime_picker(query, 1, "结束时间", self._default_datetime(90))
        self._text_field(query, 2, "参与人数", self.available_count_var)
        ttk.Button(query, text="查询", command=self.query_available).grid(row=3, column=1, sticky=tk.E, pady=(10, 0))
        self._create_room_table(frame)

    def query_available(self):
        data = {
            "startTime": self._datetime_value(self.available_start_vars),
            "endTime": self._datetime_value(self.available_end_vars),
            "attendeeCount": self.available_count_var.get(),
        }
        response = self._request("queryAvailableRooms", data)
        self.room_table.delete(*self.room_table.get_children())
        if response and response["success"]:
            for room in response["data"]["rooms"]:
                self.room_table.insert("", tk.END, values=(room["roomName"], room["floor"], room["capacity"]))
        elif response:
            messagebox.showerror("查询失败", response["msg"])

    def show_cancel(self):
        frame = self._scroll_page()
        self._header(frame, "取消预约", show_back=True)
        card = self._card(frame)
        card.pack(fill=tk.X)
        self.cancel_id_var = tk.StringVar()
        ttk.Label(card, text="预约ID", background="#ffffff").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(card, textvariable=self.cancel_id_var).grid(row=0, column=1, sticky=tk.EW, padx=(12, 0))
        ttk.Button(card, text="取消预约", command=self.cancel).grid(row=1, column=1, sticky=tk.E, pady=(12, 0))
        card.columnconfigure(1, weight=1)
        self._create_result_table(frame)
        self.refresh_cancel_list()

    def cancel(self):
        response = self._request(
            "cancelMeeting",
            {
                "meetingId": self.cancel_id_var.get(),
                "requesterName": self.current_user,
                "isAdmin": self.is_admin,
            },
        )
        if response and response["success"]:
            messagebox.showinfo("取消成功", response["msg"])
            self.refresh_cancel_list()
            self._home_command()()
        elif response:
            messagebox.showerror("取消失败", response["msg"])

    def refresh_cancel_list(self):
        if self.is_admin:
            response = self._request("listAllMeetings", {})
            meetings = response["data"]["meetings"] if response and response["success"] else []
        else:
            response = self._request("queryByOrganizer", {"organizerName": self.current_user})
            meetings = response["data"]["meetings"] if response and response["success"] else []

        self._show_meetings(meetings)
        if response and not response["success"]:
            if response.get("code") == "UNKNOWN_ACTION":
                messagebox.showerror("查询失败", "服务端版本过旧，请重启 server.py 后再试")
            else:
                messagebox.showerror("查询失败", response["msg"])

    def show_admin_meetings(self):
        frame = self._scroll_page()
        self._header(frame, "全部预约", show_back=True, back_command=self.show_admin_main)
        query = self._card(frame)
        query.pack(fill=tk.X)
        ttk.Label(query, text="显示系统内所有预约记录", background="#ffffff").pack(anchor=tk.W)
        ttk.Button(query, text="刷新", command=self.refresh_admin_meetings).pack(anchor=tk.E, pady=(12, 0))
        self._create_result_table(frame)
        self.refresh_admin_meetings()

    def refresh_admin_meetings(self):
        response = self._request("listAllMeetings", {})
        if response and response["success"]:
            self._show_meetings(response["data"]["meetings"])
            return
        self._show_meetings([])
        if response and response.get("code") == "UNKNOWN_ACTION":
            messagebox.showerror("查询失败", "服务端版本过旧，请重启 server.py 后再试")
        elif response:
            messagebox.showerror("查询失败", response["msg"])

    def show_admin_rooms(self):
        frame = self._scroll_page()
        self._header(frame, "全部会议室", show_back=True, back_command=self.show_admin_main)
        query = self._card(frame)
        query.pack(fill=tk.X)
        ttk.Label(query, text="显示系统内所有会议室", background="#ffffff").pack(anchor=tk.W)
        ttk.Button(query, text="刷新", command=self.refresh_admin_rooms).pack(anchor=tk.E, pady=(12, 0))
        self._create_room_table(frame)
        self.refresh_admin_rooms()

    def refresh_admin_rooms(self):
        response = self._request("listRooms", {})
        self.room_table.delete(*self.room_table.get_children())
        if response and response["success"]:
            for room in response["data"]["rooms"]:
                self.room_table.insert("", tk.END, values=(room["roomName"], room["floor"], room["capacity"]))
        elif response:
            messagebox.showerror("查询失败", response["msg"])

    def _create_result_table(self, parent):
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(14, 0))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        self.result_table = ttk.Treeview(table_frame, columns=("id", "organizer", "room", "topic", "start", "end", "count"), show="headings", height=8)
        y_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.result_table.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.result_table.xview)
        self.result_table.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        headings = [
            ("id", "ID", 56),
            ("organizer", "组织者", 100),
            ("room", "会议室", 120),
            ("topic", "主题", 160),
            ("start", "开始", 140),
            ("end", "结束", 140),
            ("count", "人数", 70),
        ]
        for key, label, width in headings:
            self.result_table.heading(key, text=label)
            self.result_table.column(key, width=width, minwidth=width, anchor=tk.CENTER, stretch=True)

        self.result_table.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

    def _create_room_table(self, parent):
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(14, 0))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        self.room_table = ttk.Treeview(table_frame, columns=("roomName", "floor", "capacity"), show="headings", height=8)
        y_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.room_table.yview)
        self.room_table.configure(yscrollcommand=y_scroll.set)
        for key, label, width in [
            ("roomName", "会议室", 180),
            ("floor", "楼层", 80),
            ("capacity", "容量", 80),
        ]:
            self.room_table.heading(key, text=label)
            self.room_table.column(key, width=width, minwidth=width, anchor=tk.CENTER, stretch=True)
        self.room_table.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")

    def _show_meetings(self, meetings):
        self.result_table.delete(*self.result_table.get_children())
        for meeting in meetings:
            self.result_table.insert(
                "",
                tk.END,
                values=(
                    meeting["meetingId"],
                    meeting["organizerName"],
                    meeting["roomName"],
                    meeting["topic"],
                    meeting["startTime"],
                    meeting["endTime"],
                    meeting["attendeeCount"],
                ),
            )

