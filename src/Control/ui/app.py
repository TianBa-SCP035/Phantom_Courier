import customtkinter as ctk
import sys

# ── 全局色板（薰衣草配色）────────────────────────────
C_SIDEBAR    = "#7468B5"   # 薰衣草紫（中色调，白字可读）
C_SIDEBAR_HV = "#8478C5"   # 悬停浅紫
C_SIDEBAR_AC = "#A898E0"   # 激活高亮紫
C_SIDEBAR_T  = "#D8D0FF"   # 侧边栏文字（淡丁香）
C_SIDEBAR_TA = "#FFFFFF"   # 激活文字
C_BG         = "#F3F0FF"   # 极淡薰衣草背景
C_CARD       = "#FFFFFF"   # 卡片白
C_BORDER     = "#DDD5FF"   # 淡紫边框
C_ACCENT     = "#6D4AE8"   # 深紫强调
C_YELLOW     = "#F59E0B"   # 强调黄
C_SUCCESS    = "#059669"   # 翠绿
C_ERROR      = "#DC2626"   # 红
C_WARNING    = "#D97706"   # 橙
C_TEXT       = "#1A1060"   # 深紫黑
C_TEXT2      = "#6B7280"   # 中灰


def app_font(size=13, weight="normal", family="Microsoft YaHei UI"):
    return ctk.CTkFont(family=family, size=size, weight=weight)


class ControlApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")

        self.title("Phantom Courier — 控制面板")
        self.geometry("1200x760")
        self.minsize(960, 620)
        self.configure(fg_color=C_BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        from config_manager import ConfigManager
        from service_manager import ServiceManager
        from data_manager import DataManager
        self.config_manager = ConfigManager()
        self.service_manager = ServiceManager()
        self.data_manager = DataManager()

        self._nav_btns = {}
        self._current = None
        self._build_sidebar()
        self._build_content()
        self.show_view("dashboard")

    # ── 侧边栏 ────────────────────────────────────────
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color=C_SIDEBAR)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_columnconfigure(0, weight=1)
        sb.grid_rowconfigure(5, weight=1)

        # 品牌区
        brand = ctk.CTkFrame(sb, fg_color="transparent")
        brand.grid(row=0, column=0, pady=(28, 16), padx=20, sticky="ew")
        ctk.CTkLabel(brand, text="👽 Phantom Courier", font=app_font(16, "bold"),
                     text_color="white").pack(anchor="w")
        ctk.CTkLabel(brand, text="文件监控 · 自动传输",
                     font=app_font(11), text_color="#6A9DD4").pack(anchor="w", pady=(3, 0))

        ctk.CTkFrame(sb, height=1, fg_color="#9D90DF").grid(
            row=1, column=0, sticky="ew", padx=18, pady=(0, 12))

        # 导航按钮
        nav = [
            ("dashboard", "🖥   仪表盘"),
            ("config",    "⚙   参数配置"),
            ("logs",      "📋  日志与记录"),
        ]
        for i, (key, label) in enumerate(nav):
            btn = ctk.CTkButton(
                sb, text=label, anchor="w", height=44, corner_radius=10,
                font=app_font(14), fg_color="transparent",
                text_color=C_SIDEBAR_T, hover_color=C_SIDEBAR_HV,
                command=lambda k=key: self.show_view(k)
            )
            btn.grid(row=3 + i, column=0, sticky="ew", padx=12, pady=3)
            self._nav_btns[key] = btn

        # 底部
        ft = ctk.CTkFrame(sb, fg_color="transparent")
        ft.grid(row=5, column=0, sticky="sew", padx=16, pady=14)
        ctk.CTkLabel(ft, text="© 2026 Phantom Courier",
                     font=app_font(10), text_color="#3A5E8A").pack(anchor="w")

    # ── 内容区 ────────────────────────────────────────
    def _build_content(self):
        self._content = ctk.CTkFrame(self, corner_radius=0, fg_color=C_BG)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        from ui.dashboard import DashboardView
        from ui.config_view import ConfigView
        from ui.logs_view import LogsView
        self._views = {
            "dashboard": DashboardView(self._content, self),
            "config":    ConfigView(self._content, self),
            "logs":      LogsView(self._content, self),
        }
        for v in self._views.values():
            v.grid(row=0, column=0, sticky="nsew")
            v.grid_remove()

    def show_view(self, key: str):
        if self._current == key:
            return
        for k, btn in self._nav_btns.items():
            if k == key:
                btn.configure(fg_color=C_SIDEBAR_AC, text_color=C_SIDEBAR_TA)
            else:
                btn.configure(fg_color="transparent", text_color=C_SIDEBAR_T)
        if self._current:
            self._views[self._current].grid_remove()
        self._current = key
        self._views[key].grid()
        if hasattr(self._views[key], 'on_show'):
            self._views[key].on_show()

    def _on_close(self):
        self.service_manager.stop_standalone()
        self.destroy()
        sys.exit(0)
