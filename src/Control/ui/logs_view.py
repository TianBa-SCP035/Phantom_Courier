"""
logs_view.py — 日志与记录视图

子页：
  📄 运行日志   — 实时追踪，级别过滤，颜色高亮
  ✅ 上传记录   ─┐
  ❌ 失败记录   ─┤ 使用 data_viewer.render_records() 文本渲染
  📂 目录记录   ─┤ （替代原卡片 widget 方案，解决卡顿问题）
  🔬 Gating记录 ─┘
"""
import customtkinter as ctk
import os
import json
from ui.app import (C_BG, C_CARD, C_BORDER, C_TEXT, C_TEXT2, C_ACCENT, app_font)


class LogsView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=C_BG)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._auto_follow   = True
        self._auto_refresh  = True
        self._log_size      = 0
        self._active_sub    = "log"
        self._data_counter  = 0   # 计数器：30 × 1s = 30s 自动刷新数据记录

        self._build_header()
        self._build_sub_nav()
        self._build_panes()
        self._tick()

    def on_show(self):
        self._switch_sub(self._active_sub)

    # ── 顶部标题 ──────────────────────────────────────
    def _build_header(self):
        hf = ctk.CTkFrame(self, fg_color="transparent")
        hf.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 4))
        hf.grid_columnconfigure(0, weight=1)
        tf = ctk.CTkFrame(hf, fg_color="transparent")
        tf.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(tf, text="日志与记录", font=app_font(24, "bold"), text_color=C_TEXT).pack(anchor="w")
        ctk.CTkLabel(tf, text="实时运行日志 · 上传 · 失败 · 目录 · Gating 记录",
                     font=app_font(12), text_color=C_TEXT2).pack(anchor="w")

    # ── 子页导航 ──────────────────────────────────────
    def _build_sub_nav(self):
        nf = ctk.CTkFrame(self, fg_color="transparent")
        nf.grid(row=1, column=0, sticky="ew", padx=28, pady=(4, 0))
        self._sub_btns = {}
        items = [
            ("log",      "📄 运行日志"),
            ("uploaded", "✅ 上传记录"),
            ("failed",   "❌ 失败记录"),
            ("dirs",     "📂 目录记录"),
            ("gating",   "🔬 Gating记录"),
        ]
        for key, label in items:
            btn = ctk.CTkButton(
                nf, text=label, height=32, corner_radius=7, font=app_font(12),
                fg_color="#EDE9FE", text_color=C_TEXT2, hover_color="#DDD6FE",
                command=lambda k=key: self._switch_sub(k))
            btn.pack(side="left", padx=(0, 6))
            self._sub_btns[key] = btn

    def _switch_sub(self, key: str):
        self._active_sub = key
        for k, btn in self._sub_btns.items():
            btn.configure(fg_color=C_ACCENT if k == key else "#EDE9FE",
                          text_color="#FFFFFF" if k == key else C_TEXT2)
        for k, frame in self._panes.items():
            frame.grid() if k == key else frame.grid_remove()

        if key == "log":
            self._load_log()
        elif key == "uploaded":
            self._load_data("uploaded.json", self._pane_uploaded)
        elif key == "failed":
            self._load_data("failed.json", self._pane_failed)
        elif key == "dirs":
            self._load_data("dirs.json", self._pane_dirs)
        elif key == "gating":
            self._load_data("gating_records.json", self._pane_gating)

    # ── 构建各面板 ────────────────────────────────────
    def _build_panes(self):
        self._pane_log      = self._build_log_pane()
        self._pane_uploaded = self._build_data_pane()
        self._pane_failed   = self._build_data_pane()
        self._pane_dirs     = self._build_data_pane()
        self._pane_gating   = self._build_data_pane()
        self._panes = {
            "log":      self._pane_log,
            "uploaded": self._pane_uploaded,
            "failed":   self._pane_failed,
            "dirs":     self._pane_dirs,
            "gating":   self._pane_gating,
        }
        for f in self._panes.values():
            f.grid(row=2, column=0, sticky="nsew", padx=28, pady=(6, 24))
            f.grid_remove()

        self._switch_sub("log")

    # ── 日志面板 ──────────────────────────────────────
    def _build_log_pane(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        # 控制栏
        cf = ctk.CTkFrame(frame, fg_color=C_CARD, border_width=1,
                           border_color=C_BORDER, corner_radius=10)
        cf.grid(row=0, column=0, sticky="ew", pady=(4, 6))
        cf.grid_columnconfigure(4, weight=1)

        ctk.CTkLabel(cf, text="级别过滤：", font=app_font(12), text_color=C_TEXT2
                     ).grid(row=0, column=0, padx=(12, 4), pady=8)
        self._level_var = ctk.StringVar(value="全部")
        ctk.CTkOptionMenu(cf, variable=self._level_var,
                          values=["全部", "DEBUG", "INFO", "WARNING", "ERROR"],
                          width=110, height=30, corner_radius=7, font=app_font(12),
                          fg_color="#FAFCFF", button_color="#F1F5F9", button_hover_color="#E2E8F0",
                          text_color=C_TEXT, dropdown_fg_color="#FAFCFF", dropdown_text_color=C_TEXT,
                          command=lambda _: self._load_log()
                          ).grid(row=0, column=1, padx=4, pady=8)

        # 日志文本区
        self._log_textbox = ctk.CTkTextbox(
            frame, font=ctk.CTkFont(family="Consolas", size=13),
            wrap="none", corner_radius=10,
            fg_color="#FAFCFF", border_width=1, border_color=C_BORDER)
        self._log_textbox.grid(row=1, column=0, sticky="nsew")

        # 颜色 tag
        tk_t = self._log_textbox._textbox
        tk_t.tag_config("ERROR",    foreground="#DC2626")
        tk_t.tag_config("CRITICAL", foreground="#9B1C1C", font=("Consolas", 13, "bold"))
        tk_t.tag_config("WARNING",  foreground="#D97706")
        tk_t.tag_config("INFO",     foreground="#0369A1")
        tk_t.tag_config("DEBUG",    foreground="#94A3B8")
        tk_t.tag_config("DEFAULT",  foreground="#374151")
        return frame

    # ── 数据记录通用面板（文本渲染，无卡片 widget）────
    def _build_data_pane(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        # 工具栏
        cf = ctk.CTkFrame(frame, fg_color=C_CARD, border_width=1,
                           border_color=C_BORDER, corner_radius=10)
        cf.grid(row=0, column=0, sticky="ew", pady=(4, 6))
        cf.grid_columnconfigure(0, weight=1)
        lbl = ctk.CTkLabel(cf, text="", font=app_font(11), text_color=C_TEXT2)
        lbl.grid(row=0, column=0, sticky="w", padx=14, pady=8)
        frame._refresh_lbl = lbl
        
        # 自动刷新开关
        auto_sw = ctk.CTkSwitch(cf, text="自动刷新", variable=ctk.BooleanVar(value=True),
                                font=app_font(11), text_color=C_TEXT2, progress_color="#89B4EA")
        auto_sw.grid(row=0, column=1, sticky="e", padx=(0, 12), pady=8)
        frame._auto_sw = auto_sw

        # JSON 文本显示区（单个 widget，无卡片创建开销）
        tb = ctk.CTkTextbox(frame, font=ctk.CTkFont(family="Consolas", size=12),
                             wrap="none", corner_radius=10,
                             fg_color="#FAFCFF", border_width=1, border_color=C_BORDER)
        tb.grid(row=1, column=0, sticky="nsew")
        frame._tb = tb
        return frame

    # ── 日志加载 ──────────────────────────────────────
    def _get_log_path(self) -> str:
        cfg = self.app.config_manager.get_config()
        log_file = cfg.get("logging", {}).get("log_file", "service.log")
        return self.app.data_manager.get_log_path(log_file)

    def _load_log(self):
        path = self._get_log_path()
        if not path or not os.path.exists(path):
            return
        try:
            filt = self._level_var.get()
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            if filt != "全部":
                lines = [l for l in lines if filt in l.upper()]

            tk_t = self._log_textbox._textbox
            tk_t.configure(state="normal")
            tk_t.delete("1.0", "end")
            for line in lines:
                tk_t.insert("end", line, _log_tag(line))
            tk_t.configure(state="disabled")

            if self._auto_follow:
                self._log_textbox.see("end")
            self._log_size = os.path.getsize(path)
        except Exception:
            pass

    # ── 数据记录加载（原始 JSON 显示）────────────────
    def _load_data(self, filename: str, pane):
        data = self.app.data_manager.get_raw_data(filename)
        pane._refresh_lbl.configure(text=f"共 {len(data)} 条记录  ·  每 30 秒自动刷新")
        tk_t = pane._tb._textbox
        tk_t.configure(state="normal")
        tk_t.delete("1.0", "end")
        tk_t.insert("end", json.dumps(data, indent=2, ensure_ascii=False) if data else "（暂无记录）")
        tk_t.configure(state="disabled")
        tk_t.see("end")

    # ── tick：日志实时追踪 + 数据记录 30s 自动刷新 ────
    def _tick(self):
        # ① 日志文件增量追踪（1.5s 间隔，几乎实时）
        if self._active_sub == "log" and self._auto_follow:
            path = self._get_log_path()
            if path and os.path.exists(path):
                try:
                    cur = os.path.getsize(path)
                    if cur > self._log_size:
                        filt = self._level_var.get()
                        tk_t = self._log_textbox._textbox
                        tk_t.configure(state="normal")
                        with open(path, 'r', encoding='utf-8') as f:
                            f.seek(self._log_size)
                            for line in f:
                                if filt == "全部" or filt in line.upper():
                                    tk_t.insert("end", line, _log_tag(line))
                        tk_t.configure(state="disabled")
                        self._log_textbox.see("end")
                        self._log_size = cur
                    elif cur < self._log_size:
                        self._load_log()   # 日志轮转，重新全量加载
                except Exception:
                    pass

        # ② 数据记录 30s 自动刷新（读文件不影响 Service 写入，就算最坏情况读到半截 JSON 也只是跳过本次）
        self._data_counter += 1
        if self._data_counter >= 30 and self._active_sub != "log":
            self._data_counter = 0
            # 检查自动刷新开关
            auto_refresh = self._pane_uploaded._auto_sw.get() if self._active_sub == "uploaded" else \
                          self._pane_failed._auto_sw.get() if self._active_sub == "failed" else \
                          self._pane_dirs._auto_sw.get() if self._active_sub == "dirs" else \
                          self._pane_gating._auto_sw.get() if self._active_sub == "gating" else True
            if auto_refresh:
                self._switch_sub(self._active_sub)

        self.after(1000, self._tick)


# ── 模块级辅助 ────────────────────────────────────────
def _log_tag(line: str) -> str:
    u = line.upper()
    if "CRITICAL" in u: return "CRITICAL"
    if "ERROR"    in u: return "ERROR"
    if "WARNING"  in u: return "WARNING"
    if "INFO"     in u: return "INFO"
    if "DEBUG"    in u: return "DEBUG"
    return "DEFAULT"
