"""
data_viewer.py — 数据明细弹窗 + 共享的记录格式化渲染工具

    configure_record_tags(tk_text)  — 配置颜色 tag
    render_records(tk_text, filename, data) — 将 JSON 数据渲染为带色彩的文本

DataViewer 弹窗（仪表盘「查看明细」使用）
"""
import customtkinter as ctk
import os
from ui.app import C_BG, C_CARD, C_BORDER, C_TEXT, C_TEXT2, C_ACCENT, app_font


# ── 共享工具函数 ──────────────────────────────────────────────────────────────

def configure_record_tags(tk_text):
    """在 tk.Text 底层 widget 上配置所有颜色/字体 tag"""
    F = "Microsoft YaHei UI"
    M = "Consolas"
    tk_text.tag_config("hdr_ok",      foreground="#059669", font=(F, 12, "bold"))
    tk_text.tag_config("hdr_fail",    foreground="#DC2626", font=(F, 12, "bold"))
    tk_text.tag_config("hdr_warn",    foreground="#D97706", font=(F, 12, "bold"))
    tk_text.tag_config("hdr_dir",     foreground="#7C3AED", font=(F, 12, "bold"))
    tk_text.tag_config("hdr_gate",    foreground="#0D9488", font=(F, 12, "bold"))
    tk_text.tag_config("filename",    foreground="#1C1044", font=(F, 12, "bold"))
    tk_text.tag_config("path",        foreground="#94A3B8", font=(F, 11))
    tk_text.tag_config("meta",        foreground="#6B7280", font=(M, 11))
    tk_text.tag_config("dest",        foreground="#374151", font=(M, 11))
    tk_text.tag_config("status_ok",   foreground="#059669", font=(M, 11, "bold"))
    tk_text.tag_config("status_fail", foreground="#DC2626", font=(M, 11, "bold"))
    tk_text.tag_config("sep",         foreground="#DDD6FE", font=(M, 9))


def render_records(tk_text, filename: str, data: dict):
    """将记录数据格式化渲染到 tk.Text widget（极快，无 widget 创建开销）"""
    tk_text.configure(state="normal")
    tk_text.delete("1.0", "end")

    if not data:
        tk_text.insert("end", "\n  （暂无记录）\n", "meta")
        tk_text.configure(state="disabled")
        return

    sep = "  " + "─" * 70 + "\n"

    if filename == "uploaded.json":
        for path, rec in data.items():
            dests = rec.get("destinations", {})
            all_ok = all(d.get("status") == "success" for d in dests.values()) if dests else False
            icon, htag = ("✅", "hdr_ok") if all_ok else ("⚠ ", "hdr_warn")
            name  = os.path.basename(path)
            size  = _human_size(rec.get("size", 0))
            tk_text.insert("end", f"\n  {icon}  ", htag)
            tk_text.insert("end", f"{name}", "filename")
            tk_text.insert("end", f"  ({size})\n", "meta")
            tk_text.insert("end", f"     {path}\n", "path")
            for dest in dests.values():
                proto = dest.get("protocol", "?").upper()
                ip    = dest.get("ip", dest.get("host", "?"))
                tgt   = dest.get("target_path", "")
                stat  = dest.get("status", "?")
                utime = dest.get("upload_time", "")
                stag  = "status_ok" if stat == "success" else "status_fail"
                tk_text.insert("end", f"     {proto}  {ip}  →  {tgt}\n", "dest")
                tk_text.insert("end", f"     [{stat}]", stag)
                tk_text.insert("end", f"  {utime}\n", "meta")
            tk_text.insert("end", sep, "sep")

    elif filename == "failed.json":
        for path, rec in data.items():
            name = os.path.basename(path)
            size = _human_size(rec.get("size", 0))
            tk_text.insert("end", f"\n  ❌  ", "hdr_fail")
            tk_text.insert("end", f"{name}", "filename")
            tk_text.insert("end", f"  ({size})\n", "meta")
            tk_text.insert("end", f"     {path}\n", "path")
            tk_text.insert("end", f"     重试: {rec.get('retry_count', 0)} 次  "
                                  f"最后失败: {rec.get('last_fail_time', '—')}\n", "meta")
            err = rec.get("error", "")
            if err:
                tk_text.insert("end", f"     错误: {err}\n", "status_fail")
            tk_text.insert("end", sep, "sep")

    elif filename == "dirs.json":
        for path, rec in data.items():
            name = os.path.basename(path) or path
            tk_text.insert("end", f"\n  📂  ", "hdr_dir")
            tk_text.insert("end", f"{name}\n", "filename")
            tk_text.insert("end", f"     {path}\n", "path")
            tk_text.insert("end", f"     最后扫描: {rec.get('last_scan_time', '—')}\n", "meta")
            tk_text.insert("end", sep, "sep")

    elif filename == "gating_records.json":
        for path, rec in data.items():
            name   = os.path.basename(path) or path
            status = rec.get("status", "?")
            stag   = "status_ok" if status == "success" else "hdr_warn"
            tk_text.insert("end", f"\n  🔬  ", "hdr_gate")
            tk_text.insert("end", f"{name}  ", "filename")
            tk_text.insert("end", f"[{status.upper()}]", stag)
            tk_text.insert("end", "\n", "meta")
            tk_text.insert("end", f"     {path}\n", "path")
            result_n = len(rec.get("result_paths", []))
            tk_text.insert("end", f"     调用时间: {rec.get('call_time', '—')}  "
                                  f"结果文件: {result_n} 个\n", "meta")
            tk_text.insert("end", sep, "sep")

    tk_text.configure(state="disabled")


def _human_size(b):
    b = float(b) if b else 0.0
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


# ── 弹窗 ──────────────────────────────────────────────────────────────────────

class DataViewer(ctk.CTkToplevel):
    """仪表盘「查看明细」弹窗 — 带颜色的格式化文本展示"""

    TITLES = {
        "uploaded.json":       "成功上传记录",
        "failed.json":         "传输失败记录",
        "dirs.json":           "已记录目录",
        "gating_records.json": "Gating 调用记录",
    }

    def __init__(self, master, filename: str, data: dict):
        super().__init__(master)
        title = self.TITLES.get(filename, filename)
        self.title(f"明细查看 — {title}")
        self.geometry("900x580")
        
        # Windows 透明色在一些系统下会导致穿模，且居中坐标受多屏幕影响，因此移除特殊样式
        self.configure(fg_color=C_BORDER)  # base
        self.overrideredirect(True)

        self.grab_set()
        self.focus()

        # 主容器：利用自身背景做1px边框
        main_frame = ctk.CTkFrame(self, fg_color=C_BG, corner_radius=0, border_width=0)
        main_frame.pack(fill="both", expand=True, padx=1, pady=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Header
        hf = ctk.CTkFrame(main_frame, fg_color=C_CARD, border_width=0, corner_radius=0)
        hf.grid(row=0, column=0, sticky="ew")
        hf.grid_columnconfigure(0, weight=1)
        lbl_title = ctk.CTkLabel(hf, text=title, font=app_font(16, "bold"), text_color=C_TEXT)
        lbl_title.grid(row=0, column=0, sticky="w", padx=20, pady=(14, 2))
        
        lbl_count = ctk.CTkLabel(hf, text=f"共 {len(data)} 条记录", font=app_font(11), text_color=C_TEXT2)
        lbl_count.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 12))
        
        ctk.CTkButton(hf, text="✕ 关闭", width=76, height=30, corner_radius=7,
                      font=app_font(12), fg_color="#F1F5F9", text_color=C_TEXT2,
                      hover_color="#E2E8F0", command=self.destroy
                      ).grid(row=0, column=1, rowspan=2, sticky="e", padx=20)

        # 使自定义标题栏支持拖拽
        self._offset_x = 0
        self._offset_y = 0

        def start_move(event):
            self._offset_x = event.x
            self._offset_y = event.y

        def do_move(event):
            x = self.winfo_x() + event.x - self._offset_x
            y = self.winfo_y() + event.y - self._offset_y
            self.geometry(f"+{x}+{y}")

        hf.bind("<ButtonPress-1>", start_move)
        hf.bind("<B1-Motion>", do_move)
        lbl_title.bind("<ButtonPress-1>", start_move)
        lbl_title.bind("<B1-Motion>", do_move)
        lbl_count.bind("<ButtonPress-1>", start_move)
        lbl_count.bind("<B1-Motion>", do_move)

        # Record display
        tb = ctk.CTkTextbox(main_frame, font=ctk.CTkFont(family="Microsoft YaHei UI", size=12),
                             wrap="none", corner_radius=0,
                             fg_color="#FAFCFF", border_width=0)
        tb.grid(row=1, column=0, sticky="nsew", padx=1, pady=(0, 1))
        # 数据倒序显示（最新记录在最前）
        data_disp = dict(reversed(list(data.items())))
        configure_record_tags(tb._textbox)
        render_records(tb._textbox, filename, data_disp)
