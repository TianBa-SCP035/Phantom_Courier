import customtkinter as ctk
from ui.app import (C_BG, C_CARD, C_BORDER, C_TEXT, C_TEXT2,
                    C_SUCCESS, C_ERROR, C_WARNING, C_ACCENT, C_YELLOW, C_SIDEBAR, app_font)


def _card(master, **kw):
    return ctk.CTkFrame(master, fg_color=C_CARD, border_width=1,
                        border_color=C_BORDER, corner_radius=14, **kw)


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=C_BG)
        self.app = app
        self._loading = False
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_header()
        self._build_service_panels()
        self._build_stats()
        self._tick()

    def on_show(self):
        self._refresh()

    # ── 顶部标题 ──────────────────────────────────────
    def _build_header(self):
        hf = ctk.CTkFrame(self, fg_color="transparent")
        hf.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 8))
        hf.grid_columnconfigure(0, weight=1)
        tf = ctk.CTkFrame(hf, fg_color="transparent")
        tf.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(tf, text="仪表盘", font=app_font(24, "bold"), text_color=C_TEXT).pack(anchor="w")
        ctk.CTkLabel(tf, text="服务运行状态监控 · 快捷启停操作",
                     font=app_font(12), text_color=C_TEXT2).pack(anchor="w")

    # ── 服务控制面板 ──────────────────────────────────
    def _build_service_panels(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew", padx=28, pady=(8, 8))
        row.grid_columnconfigure((0, 1), weight=1)
        self._build_standalone_card(row)
        self._build_winsvc_card(row)

    def _build_standalone_card(self, parent):
        card = _card(parent)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        card.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top, text="💻  便携独立运行", font=app_font(15, "bold"), text_color=C_TEXT).grid(row=0, column=0, sticky="w")
        self._lbl_sa = ctk.CTkLabel(top, text="● 检测中…", font=app_font(13, "bold"), text_color=C_TEXT2)
        self._lbl_sa.grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(card, text="启动为伴随进程 · 面板关闭时自动终止\n适合开发调试或临时运行",
                     font=app_font(12), text_color=C_TEXT2, justify="left"
                     ).grid(row=1, column=0, sticky="w", padx=20, pady=(6, 14))

        bf = ctk.CTkFrame(card, fg_color="transparent")
        bf.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        bf.grid_columnconfigure((0, 1), weight=1)
        self._btn_sa_start = ctk.CTkButton(
            bf, text="▶  启动", height=38, corner_radius=8, font=app_font(13, "bold"),
            fg_color="#D1FAE5", text_color="#065F46", hover_color="#A7F3D0",
            command=self._start_sa)
        self._btn_sa_start.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self._btn_sa_stop = ctk.CTkButton(
            bf, text="■  停止", height=38, corner_radius=8, font=app_font(13, "bold"),
            fg_color="#FEE2E2", text_color="#991B1B", hover_color="#FECACA",
            command=self._stop_sa)
        self._btn_sa_stop.grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _build_winsvc_card(self, parent):
        card = _card(parent)
        card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        card.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top, text="⚙  Windows 系统服务", font=app_font(15, "bold"), text_color=C_TEXT).grid(row=0, column=0, sticky="w")
        self._lbl_ws = ctk.CTkLabel(top, text="● 检测中…", font=app_font(13, "bold"), text_color=C_TEXT2)
        self._lbl_ws.grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(card, text="注册为 Windows 后台服务 · 开机自动启动\n适合服务器长期无人值守运行",
                     font=app_font(12), text_color=C_TEXT2, justify="left"
                     ).grid(row=1, column=0, sticky="w", padx=20, pady=(6, 14))

        bf = ctk.CTkFrame(card, fg_color="transparent")
        bf.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        bf.grid_columnconfigure((0, 1, 2, 3), weight=1)

        def ws_btn(text, bg, fg, hv, cmd):
            return ctk.CTkButton(bf, text=text, height=38, corner_radius=8,
                                 font=app_font(12, "bold"), fg_color=bg,
                                 text_color=fg, hover_color=hv, command=cmd)

        self._btn_ws_start   = ws_btn("▶ 启动", "#D1FAE5", "#065F46", "#A7F3D0", self._start_ws)
        self._btn_ws_stop    = ws_btn("■ 停止", "#FEE2E2", "#991B1B", "#FECACA", self._stop_ws)
        self._btn_ws_install = ws_btn("⊕ 安装", "#DBEAFE", "#1E40AF", "#BFDBFE", self._install_ws)
        self._btn_ws_remove  = ws_btn("🗑 卸载", "#FEF3C7", "#92400E", "#FDE68A", self._remove_ws)
        for col, btn in enumerate([self._btn_ws_start, self._btn_ws_stop,
                                    self._btn_ws_install, self._btn_ws_remove]):
            btn.grid(row=0, column=col, sticky="ew", padx=2)

    # ── 统计卡片 ──────────────────────────────────────
    def _build_stats(self):
        sf = ctk.CTkFrame(self, fg_color="transparent")
        sf.grid(row=2, column=0, sticky="nsew", padx=28, pady=(8, 24))
        sf.grid_columnconfigure((0, 1, 2, 3), weight=1)
        sf.grid_rowconfigure(0, weight=1)

        card_cfg = [
            ("uploaded_files",  "✅  成功上传",    "#D1FAE5", C_SUCCESS, "#065F46", "uploaded.json"),
            ("failed_files",    "❌  传输失败",    "#FEE2E2", C_ERROR,   "#991B1B", "failed.json"),
            ("monitored_dirs",  "📂  已记录目录",  "#EDE9FE", C_ACCENT,  "#5B21B6", "dirs.json"),
            ("gating_calls",    "🔬  Gating 调用", "#CCFBF1", "#0D9488", "#065F50", "gating_records.json"),
        ]
        self._stat_labels = {}
        for col, (key, title, bg, num_c, txt_c, jf) in enumerate(card_cfg):
            card = ctk.CTkFrame(sf, fg_color=C_CARD, border_width=1,
                                border_color=C_BORDER, corner_radius=14)
            card.grid(row=0, column=col, sticky="nsew", padx=5)
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkFrame(card, height=4, fg_color=num_c, corner_radius=0
                         ).grid(row=0, column=0, sticky="ew")
            ctk.CTkLabel(card, text=title, font=app_font(12), text_color=C_TEXT2
                         ).grid(row=1, column=0, pady=(16, 4))
            lbl = ctk.CTkLabel(card, text="—", font=app_font(44, "bold", "Segoe UI"), text_color=num_c)
            lbl.grid(row=2, column=0, pady=(0, 8))
            self._stat_labels[key] = lbl
            ctk.CTkButton(card, text="查看明细 →", height=30, corner_radius=6,
                          font=app_font(12), fg_color=bg, text_color=txt_c, hover_color=bg,
                          command=lambda f=jf: self._show_detail(f)
                          ).grid(row=3, column=0, padx=16, pady=(0, 18), sticky="ew")

    # ── 刷新逻辑 ──────────────────────────────────────
    def _refresh(self):
        s = self.app.service_manager.get_status_info()
        sa = s.get("standalone_running", False)
        ws = s.get("win_service_running", False)
        wi = s.get("win_service_installed", False)

        self._lbl_sa.configure(text="● 运行中" if sa else "● 已停止",
                               text_color=C_SUCCESS if sa else C_ERROR)
        self._btn_sa_start.configure(state="disabled" if sa or ws else "normal")
        self._btn_sa_stop.configure(state="normal" if sa and not ws else "disabled")

        if not wi:
            self._lbl_ws.configure(text="○ 未安装", text_color=C_TEXT2)
            for b in [self._btn_ws_start, self._btn_ws_stop, self._btn_ws_remove]:
                b.configure(state="disabled")
            self._btn_ws_install.configure(state="normal")
        else:
            self._lbl_ws.configure(text="● 运行中" if ws else "● 已停止",
                                   text_color=C_SUCCESS if ws else C_ERROR)
            self._btn_ws_start.configure(state="disabled" if ws else "normal")
            self._btn_ws_stop.configure(state="normal" if ws else "disabled")
            self._btn_ws_install.configure(state="disabled")
            self._btn_ws_remove.configure(state="disabled" if ws else "normal")

        stats = self.app.data_manager.get_stats()
        for k, lbl in self._stat_labels.items():
            lbl.configure(text=str(stats.get(k, 0)))

    def _tick(self):
        self._refresh()
        self.after(2000, self._tick)

    def _show_detail(self, json_file):
        from ui.data_viewer import DataViewer
        data = self.app.data_manager.get_raw_data(json_file)
        DataViewer(self.winfo_toplevel(), json_file, data)

    def _set_loading(self, loading: bool):
        self._loading = loading
        state = "disabled" if loading else "normal"
        self._btn_sa_start.configure(state=state)
        self._btn_sa_stop.configure(state=state)
        self._btn_ws_start.configure(state=state)
        self._btn_ws_stop.configure(state=state)
        self._btn_ws_install.configure(state=state)
        self._btn_ws_remove.configure(state=state)

    def _start_sa(self):
        if self._loading:
            return
        self._set_loading(True)
        ok = self.app.service_manager.start_standalone()
        self.after(1000, lambda: self._after_operation(ok, "Windows服务正在运行，无法启动前台版本。"))

    def _stop_sa(self):
        if self._loading:
            return
        self._set_loading(True)
        self.app.service_manager.stop_standalone()
        self.after(1000, lambda: self._after_operation(True, ""))

    def _start_ws(self):
        if self._loading:
            return
        from tkinter import messagebox
        self._set_loading(True)
        ok = self.app.service_manager.start_win_service()
        self.after(1000, lambda: self._after_operation(ok, "启动服务失败，请检查权限。"))

    def _stop_ws(self):
        if self._loading:
            return
        from tkinter import messagebox
        self._set_loading(True)
        ok = self.app.service_manager.stop_win_service()
        self.after(1000, lambda: self._after_operation(ok, "停止服务失败，请检查权限。"))

    def _install_ws(self):
        if self._loading:
            return
        from tkinter import messagebox
        self._set_loading(True)
        ok = self.app.service_manager.install_win_service()
        self.after(1000, lambda: self._after_operation(ok, "UAC 授权被取消，无法完成安装。"))

    def _remove_ws(self):
        if self._loading:
            return
        from tkinter import messagebox
        self._set_loading(True)
        ok = self.app.service_manager.uninstall_win_service()
        self.after(1000, lambda: self._after_operation(ok, "UAC 授权被取消，无法完成卸载。"))

    def _after_operation(self, ok, error_msg):
        from tkinter import messagebox
        self._set_loading(False)
        if not ok and error_msg:
            messagebox.showerror("失败", error_msg)
        self._refresh()
