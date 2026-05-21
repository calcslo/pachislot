"""
特定日管理ツール - 合同営業日（天運総撃）・景品入荷日を管理するGUI
保存先: docs/ogiya/special_dates.json
"""
import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
import json
import os
from datetime import datetime, timedelta
import calendar

DATA_FILE = os.path.join(os.path.dirname(__file__), "docs", "ogiya", "special_dates.json")

CATEGORIES = {
    "tenun_dates":   {"label": "合同営業日（天運総撃）", "color": "#d4380d", "bg": "#fff2e8"},
    "restock_dates": {"label": "景品入荷日",              "color": "#096dd9", "bg": "#e6f7ff"},
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {k: [] for k in CATEGORIES}

def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


class CalendarWidget(tk.Frame):
    """月カレンダー表示＋クリックで日付選択"""
    WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]

    def __init__(self, master, on_select=None, **kw):
        super().__init__(master, **kw)
        self.on_select = on_select
        self._year = datetime.today().year
        self._month = datetime.today().month
        self._build()

    def _build(self):
        for w in self.winfo_children():
            w.destroy()

        # --- ナビゲーションバー ---
        nav = tk.Frame(self, bg="#1a1a2e")
        nav.pack(fill="x")
        tk.Button(nav, text="◀", command=self._prev, bg="#1a1a2e", fg="white",
                  relief="flat", cursor="hand2", font=("Segoe UI", 11)).pack(side="left", padx=4)
        tk.Label(nav, text=f"{self._year}年 {self._month}月",
                 bg="#1a1a2e", fg="white", font=("Segoe UI", 12, "bold")).pack(side="left", expand=True)
        tk.Button(nav, text="▶", command=self._next, bg="#1a1a2e", fg="white",
                  relief="flat", cursor="hand2", font=("Segoe UI", 11)).pack(side="right", padx=4)

        # --- 曜日ヘッダー ---
        grid = tk.Frame(self, bg="#f0f0f0")
        grid.pack(fill="x")
        for i, wd in enumerate(self.WEEKDAYS):
            clr = "#c0392b" if wd == "日" else "#2471a3" if wd == "土" else "#333"
            tk.Label(grid, text=wd, width=4, font=("Segoe UI", 9, "bold"),
                     fg=clr, bg="#f0f0f0").grid(row=0, column=i, padx=1, pady=2)

        # --- 日付セル ---
        cal = calendar.monthcalendar(self._year, self._month)
        today = datetime.today().date()
        for row, week in enumerate(cal, 1):
            for col, day in enumerate(week):
                if day == 0:
                    tk.Label(grid, text="", width=4, bg="#f0f0f0").grid(row=row, column=col)
                    continue
                date_obj = datetime(self._year, self._month, day).date()
                date_str = date_obj.strftime("%Y-%m-%d")
                is_today = (date_obj == today)
                bg_color, fg_color, bd = self._cell_color(date_str, col, is_today)
                btn = tk.Button(grid, text=str(day), width=4, height=1,
                                bg=bg_color, fg=fg_color,
                                font=("Segoe UI", 9, "bold" if is_today else "normal"),
                                relief="groove" if is_today else "flat",
                                bd=bd, cursor="hand2",
                                command=lambda ds=date_str: self._click(ds))
                btn.grid(row=row, column=col, padx=1, pady=1)

    def _cell_color(self, date_str, weekday_col, is_today):
        """日付の種別に応じたセル色を返す"""
        # 外部データ（AppからセットされるSpecialDates）を参照
        if hasattr(self, '_special_dates'):
            for key, info in CATEGORIES.items():
                if date_str in self._special_dates.get(key, []):
                    return info["color"], "white", 2
        bg = "#fffbeb" if is_today else "white"
        fg = "#c0392b" if weekday_col == 6 else "#2471a3" if weekday_col == 5 else "#222"
        return bg, fg, 0

    def set_special_dates(self, data):
        self._special_dates = data
        self._build()

    def _click(self, date_str):
        if self.on_select:
            self.on_select(date_str)

    def _prev(self):
        if self._month == 1:
            self._year -= 1; self._month = 12
        else:
            self._month -= 1
        self._build()

    def _next(self):
        if self._month == 12:
            self._year += 1; self._month = 1
        else:
            self._month += 1
        self._build()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("特定日管理ツール — 合同営業日・景品入荷日")
        self.geometry("860x660")
        self.configure(bg="#f5f6fa")
        self.resizable(True, True)

        self.data = load_data()
        # 古いキー名との互換性
        for k in CATEGORIES:
            if k not in self.data:
                self.data[k] = []

        self._build_ui()

    def _build_ui(self):
        # ========= タイトル =========
        hdr = tk.Frame(self, bg="#1a1a2e", height=56)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📅 特定日管理ツール",
                 bg="#1a1a2e", fg="white",
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=20, pady=12)

        # ========= メインエリア =========
        main = tk.Frame(self, bg="#f5f6fa")
        main.pack(fill="both", expand=True, padx=16, pady=12)

        # 左: カレンダー
        left = tk.Frame(main, bg="white", relief="flat",
                        highlightbackground="#e0e0e0", highlightthickness=1)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        tk.Label(left, text="カレンダー (クリックで日付選択)",
                 bg="white", fg="#555", font=("Segoe UI", 10)).pack(pady=(10, 4))
        self.cal = CalendarWidget(left, on_select=self._on_date_click, bg="white")
        self.cal.pack(padx=10, pady=6)
        self.cal.set_special_dates(self.data)

        # 凡例
        leg = tk.Frame(left, bg="white")
        leg.pack(pady=6)
        for key, info in CATEGORIES.items():
            tk.Label(leg, text="■", fg=info["color"], bg="white",
                     font=("Segoe UI", 11)).pack(side="left", padx=(6, 2))
            tk.Label(leg, text=info["label"], fg="#444", bg="white",
                     font=("Segoe UI", 9)).pack(side="left", padx=(0, 10))

        # 右: 操作パネル
        right = tk.Frame(main, bg="white", width=300,
                         highlightbackground="#e0e0e0", highlightthickness=1)
        right.pack(side="right", fill="both", padx=(8, 0))
        right.pack_propagate(False)

        # 選択日表示
        sf = tk.Frame(right, bg="#f0f4ff", pady=8)
        sf.pack(fill="x")
        tk.Label(sf, text="選択日:", bg="#f0f4ff", fg="#666",
                 font=("Segoe UI", 9)).pack(side="left", padx=10)
        self.selected_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        entry = ttk.Entry(sf, textvariable=self.selected_var, width=14,
                          font=("Segoe UI", 11))
        entry.pack(side="left", padx=4)

        # カテゴリ追加ボタン
        tk.Label(right, text="カテゴリを選んで登録", bg="white", fg="#333",
                 font=("Segoe UI", 10, "bold")).pack(pady=(14, 4))
        for key, info in CATEGORIES.items():
            btn = tk.Button(right, text=f"➕ {info['label']}",
                            bg=info["color"], fg="white",
                            font=("Segoe UI", 10, "bold"),
                            relief="flat", cursor="hand2", pady=8,
                            command=lambda k=key: self._add(k))
            btn.pack(fill="x", padx=14, pady=4)

        ttk.Separator(right, orient="horizontal").pack(fill="x", padx=14, pady=10)

        # リストビュー（タブ）
        notebook = ttk.Notebook(right)
        notebook.pack(fill="both", expand=True, padx=8, pady=4)

        self.listboxes = {}
        for key, info in CATEGORIES.items():
            frame = tk.Frame(notebook, bg="white")
            notebook.add(frame, text=info["label"])
            sb = tk.Scrollbar(frame)
            sb.pack(side="right", fill="y")
            lb = tk.Listbox(frame, yscrollcommand=sb.set, selectmode="single",
                            font=("Segoe UI", 10), bg="white",
                            selectbackground=info["color"],
                            activestyle="none", bd=0, highlightthickness=0)
            lb.pack(fill="both", expand=True)
            sb.config(command=lb.yview)
            self.listboxes[key] = lb
            self._refresh_list(key)
            # ダブルクリックで削除
            lb.bind("<Double-Button-1>", lambda e, k=key: self._delete(k))

        tk.Label(right, text="※ 一覧をダブルクリックで削除", bg="white",
                 fg="#aaa", font=("Segoe UI", 8)).pack(pady=4)

    def _on_date_click(self, date_str):
        self.selected_var.set(date_str)

    def _add(self, key):
        date_str = self.selected_var.get().strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("エラー", "日付の形式が正しくありません。\n(例: 2026-05-21)")
            return

        if date_str in self.data[key]:
            messagebox.showinfo("情報", f"「{date_str}」はすでに登録済みです。")
            return

        self.data[key].append(date_str)
        save_data(self.data)
        self._refresh_list(key)
        self.cal.set_special_dates(self.data)
        messagebox.showinfo("登録完了", f"✅ {CATEGORIES[key]['label']}\n{date_str} を追加しました。")

    def _delete(self, key):
        lb = self.listboxes[key]
        sel = lb.curselection()
        if not sel:
            return
        date_str = lb.get(sel[0])
        if messagebox.askyesno("削除確認", f"「{date_str}」を削除しますか？"):
            self.data[key].remove(date_str)
            save_data(self.data)
            self._refresh_list(key)
            self.cal.set_special_dates(self.data)

    def _refresh_list(self, key):
        lb = self.listboxes[key]
        lb.delete(0, tk.END)
        for d in sorted(self.data.get(key, []), reverse=True):
            lb.insert(tk.END, d)


if __name__ == "__main__":
    app = App()
    app.mainloop()
