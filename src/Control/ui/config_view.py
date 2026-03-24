import customtkinter as ctk
from tkinter import filedialog, messagebox
from ui.app import (C_BG, C_CARD, C_BORDER, C_TEXT, C_TEXT2,
                    C_ACCENT, C_SUCCESS, C_ERROR, app_font)


# ── 密码验证弹窗 ────────────────────────────────────────────────────────────────
class PasswordDialog(ctk.CTkToplevel):
    """密码验证弹窗"""

    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success
        self.password_var = ctk.StringVar()
        self._build_ui()
        self.grab_set()
        self.focus()

    def _build_ui(self):
        self.title("密码验证")
        self.geometry("320x160")
        self.resizable(False, False)
        self.configure(fg_color=C_BG)
        self.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(self, text="请输入密码以保存配置：",
                             font=app_font(13), text_color=C_TEXT)
        label.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))

        entry = ctk.CTkEntry(self, textvariable=self.password_var, show="*",
                             font=app_font(13), height=36, corner_radius=7)
        entry.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 16))
        entry.bind("<Return>", lambda e: self._verify())

        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 20))
        bf.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(bf, text="取消", height=36, corner_radius=8, font=app_font(13),
                      fg_color="#F1F5F9", text_color=C_TEXT2, hover_color="#E2E8F0",
                      command=self.destroy).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(bf, text="确认", height=36, corner_radius=8, font=app_font(13, "bold"),
                      fg_color=C_ACCENT, text_color="white", hover_color="#1D4ED8",
                      command=self._verify).grid(row=0, column=1, sticky="ew", padx=(8, 0))

    def _verify(self):
        if self.password_var.get() == "tianba":
            self.on_success()
            self.destroy()
        else:
            messagebox.showerror("密码错误", "密码不正确，请重试。", parent=self)
            self.password_var.set("")


# ── 目标编辑弹窗 ──────────────────────────────────────────────────────────────
class DestinationDialog(ctk.CTkToplevel):
    """新增 / 编辑单条传输目标的弹窗"""

    SFTP_FIELDS = [("host", "服务器地址"), ("port", "端口 (默认 22)"),
                   ("username", "用户名"), ("password", "密码"),
                   ("target_path", "目标路径")]
    SMB_FIELDS  = [("server_ip", "服务器 IP"), ("server_port", "端口 (默认 139)"),
                   ("username", "用户名"), ("password", "密码"),
                   ("share_name", "共享名称"), ("target_path", "目标路径")]

    def __init__(self, master, on_confirm, existing: dict = None):
        super().__init__(master)
        self.on_confirm = on_confirm
        self.existing   = existing or {}
        self.result     = None
        self._entries   = {}

        self.title("编辑传输目标")
        self.geometry("480x400")
        self.resizable(False, False)
        self.grab_set()
        self.focus()
        self.configure(fg_color=C_BG)
        self.grid_columnconfigure(0, weight=1)

        # 协议选择
        pf = ctk.CTkFrame(self, fg_color="transparent")
        pf.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 4))
        ctk.CTkLabel(pf, text="协议类型：", font=app_font(13), text_color=C_TEXT).pack(side="left")
        self._proto_var = ctk.StringVar(value=self.existing.get("protocol", "sftp").upper())
        for p in ("SFTP", "SMB"):
            ctk.CTkRadioButton(pf, text=p, variable=self._proto_var, value=p,
                               font=app_font(13), text_color=C_TEXT,
                               command=self._refresh_fields).pack(side="left", padx=8)

        # 字段容器
        self._field_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._field_frame.grid(row=1, column=0, sticky="nsew", padx=24, pady=4)
        self._field_frame.grid_columnconfigure(1, weight=1)
        self._refresh_fields()

        # 按钮
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.grid(row=2, column=0, sticky="ew", padx=24, pady=(12, 20))
        bf.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(bf, text="取消", height=36, corner_radius=8, font=app_font(13),
                      fg_color="#F1F5F9", text_color=C_TEXT2, hover_color="#E2E8F0",
                      command=self.destroy).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(bf, text="确认保存", height=36, corner_radius=8, font=app_font(13, "bold"),
                      fg_color=C_ACCENT, text_color="white", hover_color="#1D4ED8",
                      command=self._confirm).grid(row=0, column=1, sticky="ew", padx=(8, 0))

    def _refresh_fields(self):
        for w in self._field_frame.winfo_children():
            w.destroy()
        self._entries.clear()
        proto = self._proto_var.get()
        fields = self.SFTP_FIELDS if proto == "SFTP" else self.SMB_FIELDS
        self.geometry(f"480x{200 + len(fields)*46}")
        for i, (key, label) in enumerate(fields):
            ctk.CTkLabel(self._field_frame, text=label + "：", font=app_font(12), text_color=C_TEXT2,
                         width=140, anchor="e").grid(row=i, column=0, sticky="e", padx=(0, 8), pady=5)
            show = "*" if key == "password" else None
            entry = ctk.CTkEntry(self._field_frame, font=app_font(13), show=show, height=34, corner_radius=7)
            entry.insert(0, str(self.existing.get(key, "")))
            entry.grid(row=i, column=1, sticky="ew", pady=5)
            self._entries[key] = entry

    def _confirm(self):
        proto = self._proto_var.get().lower()
        data = {"protocol": proto}
        for key, entry in self._entries.items():
            val = entry.get().strip()
            # 自动转整数
            if key in ("port", "server_port") and val:
                try:
                    val = int(val)
                except ValueError:
                    messagebox.showerror("格式错误", f"{key} 必须为整数。", parent=self)
                    return
            data[key] = val
        self.on_confirm(data)
        self.destroy()


# ── 配置主视图 ────────────────────────────────────────────────────────────────
class ConfigView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=C_BG)
        self.app = app
        self._dest_list = []   # 当前 destinations 数据
        self._dest_rows = []   # UI 行组件列表
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_tabs()

    def on_show(self):
        self._load()

    # ── 顶部 ──────────────────────────────────────────
    def _build_header(self):
        hf = ctk.CTkFrame(self, fg_color="transparent")
        hf.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 8))
        hf.grid_columnconfigure(0, weight=1)
        tf = ctk.CTkFrame(hf, fg_color="transparent")
        tf.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(tf, text="参数配置", font=app_font(24, "bold"), text_color=C_TEXT).pack(anchor="w")
        ctk.CTkLabel(tf, text="修改后点击「保存配置」，需重启服务方可生效",
                     font=app_font(12), text_color=C_TEXT2).pack(anchor="w")
        ctk.CTkButton(hf, text="💾  保存配置", width=110, height=36, corner_radius=8,
                      font=app_font(13, "bold"), fg_color=C_ACCENT, text_color="white",
                      hover_color="#5A38D8", command=self._save
                      ).grid(row=0, column=1, sticky="e")

    # ── Tabs ──────────────────────────────────────────
    def _build_tabs(self):
        self._tabs = ctk.CTkTabview(self, corner_radius=12,
                                    fg_color=C_CARD,
                                    segmented_button_fg_color="#EDE9FF",
                                    segmented_button_selected_color=C_ACCENT,
                                    segmented_button_selected_hover_color="#5A38D8",
                                    segmented_button_unselected_color="#EDE9FF",
                                    segmented_button_unselected_hover_color="#DDD5FF",
                                    text_color=C_TEXT)
        # 设置 Tab 标签字体
        try:
            self._tabs._segmented_button.configure(font=app_font(15))
        except Exception:
            pass
        self._tabs.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))
        for t in ["扫描设置", "过滤设置", "上传目标", "Gating 设置", "稳定性设置", "日志设置"]:
            self._tabs.add(t)
        self._build_scan_tab(self._tabs.tab("扫描设置"))
        self._build_filter_tab(self._tabs.tab("过滤设置"))
        self._build_upload_tab(self._tabs.tab("上传目标"))
        self._build_gating_tab(self._tabs.tab("Gating 设置"))
        self._build_stability_tab(self._tabs.tab("稳定性设置"))
        self._build_log_tab(self._tabs.tab("日志设置"))

    # ─── 扫描设置 ─────────────────────────────────────
    def _build_scan_tab(self, p):
        p.grid_columnconfigure(1, weight=1)
        
        self._root_path_list = []
        
        # 路径列表标题
        hf = ctk.CTkFrame(p, fg_color="transparent")
        hf.grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(8, 6))
        hf.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hf, text="监控根目录列表", font=app_font(14, "bold"), text_color=C_TEXT).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(hf, text="＋  添加目录", height=32, corner_radius=8, font=app_font(12, "bold"),
                      fg_color="#DBEAFE", text_color="#1E40AF", hover_color="#BFDBFE",
                      command=self._add_root_path).grid(row=0, column=1, sticky="e")

        # 可滚动路径列表容器
        self._root_scroll = ctk.CTkScrollableFrame(p, fg_color="#F5F9FF",
                                                    border_width=1, border_color=C_BORDER,
                                                    corner_radius=10)
        self._root_scroll.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=14, pady=(0, 12))
        self._root_scroll.grid_columnconfigure(0, weight=1)
        self._root_empty_label = ctk.CTkLabel(self._root_scroll, text="暂无监控目录，点击「添加目录」新增",
                                              font=app_font(12), text_color=C_TEXT2)
        self._root_empty_label.grid(row=0, column=0, pady=20)
        
        # 分隔线
        ctk.CTkFrame(p, height=1, fg_color=C_BORDER).grid(row=2, column=0, columnspan=2, sticky="ew", padx=14, pady=8)
        
        # 扫描间隔和开关放在一个容器中
        opt_f = ctk.CTkFrame(p, fg_color="transparent")
        opt_f.grid(row=3, column=0, columnspan=2, sticky="ew", padx=14, pady=(4, 8))
        opt_f.grid_columnconfigure(0, weight=1)
        
        # 扫描间隔
        self._interval_var = self._labeled_entry(opt_f, "扫描间隔（秒）：", 0, default="1800", width=100, compact=True)
        
        # 三个开关放在一行
        sw_f = ctk.CTkFrame(opt_f, fg_color="transparent")
        sw_f.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        sw_f.grid_columnconfigure((0, 1, 2), weight=1)
        
        self._recursive_var    = self._labeled_switch(sw_f, "递归扫描子文件夹", 0, compact=True)
        self._always_scan_var  = self._labeled_switch(sw_f, "总是扫描文件", 1, compact=True)
        self._upload_first_var = self._labeled_switch(sw_f, "首次运行上传", 2, compact=True)

    # ─── 过滤设置 ─────────────────────────────────────
    def _build_filter_tab(self, p):
        p.grid_columnconfigure(1, weight=1)
        opts = ["黑名单 (排除)", "白名单 (仅包含)"]
        self._folder_mode_var    = self._labeled_option(p, "文件夹过滤模式：", 0, opts)
        self._incl_folders_var   = self._labeled_entry(p, "包含的文件夹（逗号分隔）：", 1)
        self._excl_folders_var   = self._labeled_entry(p, "排除的文件夹（逗号分隔）：", 2)
        ctk.CTkFrame(p, height=1, fg_color=C_BORDER).grid(row=3, column=0, columnspan=2, sticky="ew", padx=14, pady=10)
        self._file_mode_var      = self._labeled_option(p, "文件过滤模式：", 4, opts)
        self._incl_patterns_var  = self._labeled_entry(p, "包含的正则（逗号分隔）：", 5)
        self._excl_patterns_var  = self._labeled_entry(p, "排除的正则（逗号分隔）：", 6)
        self._excl_hidden_var    = self._labeled_switch(p, "排除隐藏文件（. 开头）", 7)

    def _build_upload_tab(self, p):
        p.grid_columnconfigure(1, weight=1)
        p.grid_rowconfigure(2, weight=1)
        
        # 顶部控制行：开关和重试次数并排
        row_f = ctk.CTkFrame(p, fg_color="transparent")
        row_f.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=16)

        self._upload_enabled_var = ctk.BooleanVar()
        sw = ctk.CTkSwitch(row_f, text="启用文件上传", variable=self._upload_enabled_var, 
                           font=app_font(13), text_color=C_TEXT, progress_color="#89B4EA")
        sw.pack(side="left", padx=(10, 30))
        
        ctk.CTkLabel(row_f, text="失败重试次数：", font=app_font(12), text_color=C_TEXT2).pack(side="left")
        self._retry_count_var = ctk.StringVar(value="2")
        ctk.CTkEntry(row_f, textvariable=self._retry_count_var, font=app_font(13), 
                     height=30, width=60, corner_radius=7).pack(side="left", padx=4)

        # 目标列表标题
        hf = ctk.CTkFrame(p, fg_color="transparent")
        hf.grid(row=1, column=0, columnspan=2, sticky="ew", padx=14, pady=(4, 4))
        hf.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hf, text="传输目标列表", font=app_font(14, "bold"), text_color=C_TEXT).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(hf, text="＋  添加目标", height=32, corner_radius=8, font=app_font(12, "bold"),
                      fg_color="#DBEAFE", text_color="#1E40AF", hover_color="#BFDBFE",
                      command=self._add_destination).grid(row=0, column=1, sticky="e")

        # 可滚动目标列表容器
        self._dest_scroll = ctk.CTkScrollableFrame(p, fg_color="#F5F9FF",
                                                    border_width=1, border_color=C_BORDER,
                                                    corner_radius=10)
        self._dest_scroll.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=14, pady=(0, 14))
        self._dest_scroll.grid_columnconfigure(0, weight=1)
        self._empty_label = ctk.CTkLabel(self._dest_scroll, text="暂无传输目标，点击「添加目标」新增",
                                          font=app_font(12), text_color=C_TEXT2)
        self._empty_label.grid(row=0, column=0, pady=20)

    # ─── Gating ───────────────────────────────────────
    def _build_gating_tab(self, p):
        p.grid_columnconfigure(1, weight=1)
        self._gating_enabled_var = self._labeled_switch(p, "启用 Gating 自动调用", 0)
        self._gating_exe_var     = self._labeled_entry(p, "Gating.exe 路径：", 1, default="Gating.exe")
        self._gating_ext_var     = self._labeled_entry(p, "触发文件后缀：", 2, default=".fcs")
        ctk.CTkLabel(p, text="※ 当文件夹内所有文件均为该后缀时自动触发",
                     font=app_font(11), text_color=C_TEXT2).grid(row=3, column=1, sticky="w", padx=14, pady=(0, 8))

    # ─── 稳定性 ───────────────────────────────────────
    def _build_stability_tab(self, p):
        p.grid_columnconfigure(1, weight=1)
        self._stab_count_var    = self._labeled_entry(p, "采样次数：", 0, default="3", width=80)
        self._stab_interval_var = self._labeled_entry(p, "采样间隔（秒）：", 1, default="1", width=80)
        self._stab_round_var    = self._labeled_entry(p, "判别轮数：", 2, default="2", width=80)
        ctk.CTkLabel(p, text="※ 文件大小和修改时间在 N 次采样中均不变才视为稳定",
                     font=app_font(11), text_color=C_TEXT2).grid(row=3, column=1, sticky="w", padx=14, pady=(4, 8))

    # ─── 日志 ─────────────────────────────────────────
    def _build_log_tab(self, p):
        p.grid_columnconfigure(1, weight=1)
        self._log_level_var = self._labeled_option(p, "日志级别：", 0, ["DEBUG", "INFO", "WARNING", "ERROR"])
        self._log_file_var  = self._labeled_entry(p, "日志文件名：", 1, default="service.log")
        ctk.CTkFrame(p, height=1, fg_color=C_BORDER).grid(row=2, column=0, columnspan=2, sticky="ew", padx=14, pady=10)
        self._upload_record_var = self._labeled_entry(p, "上传记录文件名：", 3, default="uploaded.json")
        self._failed_record_var = self._labeled_entry(p, "失败记录文件名：", 4, default="failed.json")
        self._dir_record_var    = self._labeled_entry(p, "文件夹记录文件名：", 5, default="dirs.json")
        self._gating_record_var = self._labeled_entry(p, "Gating 记录文件名：", 6, default="gating_records.json")

    # ── 辅助构建函数 ──────────────────────────────────
    def _label(self, parent, text, row, col=0):
        ctk.CTkLabel(parent, text=text, font=app_font(12), text_color=C_TEXT2,
                     width=200, anchor="e").grid(row=row, column=col, sticky="e", padx=(14, 8), pady=8)

    def _labeled_entry(self, parent, label, row, default="", width=None, compact=False):
        if not compact:
            self._label(parent, label, row)
            var = ctk.StringVar(value=default)
            kw = {"width": width} if width else {}
            e = ctk.CTkEntry(parent, textvariable=var, font=app_font(13), height=34, corner_radius=7, **kw)
            e.grid(row=row, column=1, sticky="ew" if not width else "w", padx=14, pady=8)
        else:
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.grid(row=row, column=0, sticky="w", padx=4, pady=4)
            ctk.CTkLabel(f, text=label, font=app_font(12), text_color=C_TEXT2).pack(side="left", padx=(0, 4))
            var = ctk.StringVar(value=default)
            kw = {"width": width} if width else {}
            e = ctk.CTkEntry(f, textvariable=var, font=app_font(12), height=28, corner_radius=6, **kw)
            e.pack(side="left", padx=0)
        return var

    def _labeled_switch(self, parent, label, row, compact=False):
        if not compact:
            ctk.CTkLabel(parent, text="", width=200).grid(row=row, column=0)  # placeholder
            var = ctk.BooleanVar()
            ctk.CTkSwitch(parent, text=label, variable=var, font=app_font(13), text_color=C_TEXT, progress_color="#89B4EA"
                          ).grid(row=row, column=1, sticky="w", padx=14, pady=8)
        else:
            var = ctk.BooleanVar()
            ctk.CTkSwitch(parent, text=label, variable=var, font=app_font(12), text_color=C_TEXT, progress_color="#89B4EA"
                          ).grid(row=row, column=0, sticky="w", padx=4, pady=8)
        return var

    def _labeled_option(self, parent, label, row, values):
        self._label(parent, label, row)
        var = ctk.StringVar(value=values[0])
        ctk.CTkOptionMenu(parent, variable=var, values=values,
                          font=app_font(13), width=160, height=32, corner_radius=7,
                          fg_color="#FAFCFF", button_color="#F1F5F9", button_hover_color="#E2E8F0",
                          text_color=C_TEXT, dropdown_fg_color="#FAFCFF", dropdown_text_color=C_TEXT
                          ).grid(row=row, column=1, sticky="w", padx=14, pady=8)
        return var

    def _add_root_path(self):
        path = filedialog.askdirectory(title="选择监控目录")
        if path:
            self._root_path_list.append(path)
            self._render_root_paths()

    def _render_root_paths(self):
        for w in self._root_scroll.winfo_children():
            w.destroy()
        if not self._root_path_list:
            self._root_empty_label = ctk.CTkLabel(self._root_scroll, text="暂无监控目录，点击「添加目录」新增",
                                                  font=app_font(12), text_color=C_TEXT2)
            self._root_empty_label.grid(row=0, column=0, pady=20)
            return
        for i, path in enumerate(self._root_path_list):
            self._render_root_path_row(i, path)

    def _render_root_path_row(self, idx, path):
        row_f = ctk.CTkFrame(self._root_scroll, fg_color=C_CARD,
                              border_width=1, border_color=C_BORDER, corner_radius=10)
        row_f.grid(row=idx, column=0, sticky="ew", padx=4, pady=4)
        row_f.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(row_f, text=path, font=app_font(12), text_color=C_TEXT,
                     anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        bf = ctk.CTkFrame(row_f, fg_color="transparent")
        bf.grid(row=0, column=1, padx=8)
        ctk.CTkButton(bf, text="✕ 删除", width=64, height=28, corner_radius=6,
                      font=app_font(11), fg_color="#FEF2F2", text_color=C_ERROR,
                      hover_color="#FEE2E2",
                      command=lambda i=idx: self._delete_root_path(i)).pack(side="left", padx=2)

    def _delete_root_path(self, idx):
        self._root_path_list.pop(idx)
        self._render_root_paths()

    # ── Destinations 编辑 ─────────────────────────────
    def _render_destinations(self):
        for w in self._dest_scroll.winfo_children():
            w.destroy()
        self._dest_rows.clear()
        if not self._dest_list:
            self._empty_label = ctk.CTkLabel(self._dest_scroll,
                                              text="暂无传输目标，点击「添加目标」新增",
                                              font=app_font(12), text_color=C_TEXT2)
            self._empty_label.grid(row=0, column=0, pady=20)
            return
        for i, dest in enumerate(self._dest_list):
            self._render_dest_row(i, dest)

    def _render_dest_row(self, idx, dest):
        proto = dest.get("protocol", "?").upper()
        if proto == "SFTP":
            info = f"{dest.get('host','?')}:{dest.get('port',22)}  →  {dest.get('target_path','')}"
            badge_bg, badge_tc = "#DBEAFE", "#1E40AF"
        else:
            info = f"{dest.get('server_ip','?')}  [{dest.get('share_name','')}]  →  {dest.get('target_path','')}"
            badge_bg, badge_tc = "#FEF3C7", "#92400E"

        row_f = ctk.CTkFrame(self._dest_scroll, fg_color=C_CARD,
                              border_width=1, border_color=C_BORDER, corner_radius=10)
        row_f.grid(row=idx, column=0, sticky="ew", padx=4, pady=4)
        row_f.grid_columnconfigure(1, weight=1)

        # 协议徽标
        ctk.CTkLabel(row_f, text=f" {proto} ", font=app_font(11, "bold"),
                     fg_color=badge_bg, text_color=badge_tc, corner_radius=5
                     ).grid(row=0, column=0, padx=(10, 8), pady=10)
        ctk.CTkLabel(row_f, text=info, font=app_font(12), text_color=C_TEXT,
                     anchor="w").grid(row=0, column=1, sticky="ew")

        # 操作按钮
        bf = ctk.CTkFrame(row_f, fg_color="transparent")
        bf.grid(row=0, column=2, padx=8)
        ctk.CTkButton(bf, text="✏ 编辑", width=64, height=28, corner_radius=6,
                      font=app_font(11), fg_color="#EFF6FF", text_color=C_ACCENT,
                      hover_color="#DBEAFE",
                      command=lambda i=idx: self._edit_destination(i)).pack(side="left", padx=2)
        ctk.CTkButton(bf, text="✕ 删除", width=64, height=28, corner_radius=6,
                      font=app_font(11), fg_color="#FEF2F2", text_color=C_ERROR,
                      hover_color="#FEE2E2",
                      command=lambda i=idx: self._delete_destination(i)).pack(side="left", padx=2)

    def _add_destination(self):
        def on_confirm(data):
            self._dest_list.append(data)
            self._render_destinations()
        DestinationDialog(self.winfo_toplevel(), on_confirm)

    def _edit_destination(self, idx):
        def on_confirm(data):
            self._dest_list[idx] = data
            self._render_destinations()
        DestinationDialog(self.winfo_toplevel(), on_confirm, existing=self._dest_list[idx])

    def _delete_destination(self, idx):
        self._dest_list.pop(idx)
        self._render_destinations()

    # ── 加载 / 保存 ────────────────────────────────────
    def _load(self):
        c = self.app.config_manager.get_config()
        sc = c.get("scan", {})
        fc = c.get("filter", {})
        uc = c.get("upload", {})
        gc = c.get("gating", {})
        stc = c.get("stability", {})
        lc = c.get("logging", {})

        self._root_path_list = list(sc.get("root_paths", []))
        self._render_root_paths()
        self._interval_var.set(str(sc.get("interval", 1800)))
        self._recursive_var.set(sc.get("recursive", True))
        self._always_scan_var.set(sc.get("always_scan_files", False))
        self._upload_first_var.set(uc.get("upload_on_first_run", True))

        self._folder_mode_var.set("黑名单 (排除)" if fc.get("folder_mode", "blacklist") == "blacklist" else "白名单 (仅包含)")
        self._incl_folders_var.set(", ".join(fc.get("include_folders", [])))
        self._excl_folders_var.set(", ".join(fc.get("exclude_folders", [])))
        self._file_mode_var.set("黑名单 (排除)" if fc.get("file_mode", "blacklist") == "blacklist" else "白名单 (仅包含)")
        self._incl_patterns_var.set(", ".join(fc.get("include_patterns", [])))
        self._excl_patterns_var.set(", ".join(fc.get("exclude_patterns", [])))
        self._excl_hidden_var.set(fc.get("exclude_hidden", True))

        self._upload_enabled_var.set(uc.get("enabled", True))
        self._retry_count_var.set(str(uc.get("retry_count", 2)))
        self._dest_list = list(uc.get("destinations", []))
        self._render_destinations()

        self._gating_enabled_var.set(gc.get("enabled", False))
        self._gating_exe_var.set(gc.get("exe_path", "Gating.exe"))
        self._gating_ext_var.set(gc.get("file_extension", ".fcs"))

        self._stab_count_var.set(str(stc.get("file_check_count", 3)))
        self._stab_interval_var.set(str(stc.get("file_check_interval", 1)))
        self._stab_round_var.set(str(stc.get("file_check_round", 2)))

        self._log_level_var.set(lc.get("level", "INFO"))
        self._log_file_var.set(lc.get("log_file", "service.log"))
        
        sc = c.get("storage", {})
        self._upload_record_var.set(sc.get("upload_record_file", "uploaded.json"))
        self._failed_record_var.set(sc.get("failed_record_file", "failed.json"))
        self._dir_record_var.set(sc.get("dir_record_file", "dirs.json"))
        self._gating_record_var.set(sc.get("gating_record_file", "gating_records.json"))

    def _save(self):
        PasswordDialog(self.winfo_toplevel(), self._do_save)

    def _do_save(self):
        try:
            c = self.app.config_manager.get_config()
            c["scan"]["root_paths"] = self._root_path_list
            c["scan"]["interval"] = int(self._interval_var.get())
            c["scan"]["recursive"] = self._recursive_var.get()
            c["scan"]["always_scan_files"] = self._always_scan_var.get()
            c["upload"]["upload_on_first_run"] = self._upload_first_var.get()
            c["filter"]["folder_mode"] = "blacklist" if "黑名单" in self._folder_mode_var.get() else "whitelist"
            c["filter"]["include_folders"] = [x.strip() for x in self._incl_folders_var.get().split(",") if x.strip()]
            c["filter"]["exclude_folders"] = [x.strip() for x in self._excl_folders_var.get().split(",") if x.strip()]
            c["filter"]["file_mode"] = "blacklist" if "黑名单" in self._file_mode_var.get() else "whitelist"
            c["filter"]["include_patterns"] = [x.strip() for x in self._incl_patterns_var.get().split(",") if x.strip()]
            c["filter"]["exclude_patterns"] = [x.strip() for x in self._excl_patterns_var.get().split(",") if x.strip()]
            c["filter"]["exclude_hidden"] = self._excl_hidden_var.get()
            c["upload"]["enabled"] = self._upload_enabled_var.get()
            c["upload"]["retry_count"] = int(self._retry_count_var.get())
            c["upload"]["destinations"] = self._dest_list
            c["gating"]["enabled"] = self._gating_enabled_var.get()
            c["gating"]["exe_path"] = self._gating_exe_var.get().strip()
            c["gating"]["file_extension"] = self._gating_ext_var.get().strip()
            c["stability"]["file_check_count"] = int(self._stab_count_var.get())
            c["stability"]["file_check_interval"] = int(self._stab_interval_var.get())
            c["stability"]["file_check_round"] = int(self._stab_round_var.get())
            c["logging"]["level"] = self._log_level_var.get()
            c["logging"]["log_file"] = self._log_file_var.get().strip()
            c["storage"]["upload_record_file"] = self._upload_record_var.get().strip()
            c["storage"]["failed_record_file"] = self._failed_record_var.get().strip()
            c["storage"]["dir_record_file"] = self._dir_record_var.get().strip()
            c["storage"]["gating_record_file"] = self._gating_record_var.get().strip()
            if not self.app.config_manager.update_config(c):
                messagebox.showerror("错误", "写入配置文件失败。")
        except Exception as e:
            messagebox.showerror("格式错误", f"输入有误：\n{e}")
