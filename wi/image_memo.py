"""
image_memo.py - 바탕화면 이미지 메모 GUI 프로그램
- 메모 추가, 수정, 삭제, 크기 조절, 위치 정렬
- Unsplash 배경 키워드 검색 및 Google Fonts 글씨체 연동 (200줄 이하 준수)
"""
import tkinter as tk
from tkinter import messagebox, ttk
from wallpaper import load_memos, save_memos, update_wallpaper, get_screen_size
from api_service import get_available_fonts, fetch_font_file, fetch_unsplash_background

class MemoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("바탕화면 이미지 메모")
        self.root.geometry("450x520")
        self.root.configure(bg="#212529")
        self.memos = load_memos()

        tk.Label(root, text="📌 바탕화면 이미지 메모", font=("맑은 고딕", 14, "bold"), fg="#FFEB3B", bg="#212529").pack(pady=10)
        fl = tk.Frame(root, bg="#212529")
        fl.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        sb = tk.Scrollbar(fl)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = tk.Listbox(fl, font=("맑은 고딕", 10), yscrollcommand=sb.set, bg="#2B3035", fg="#F8F9FA", selectbackground="#F59E0B", selectforeground="#000", height=10)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=self.listbox.yview)

        bf = tk.Frame(root, bg="#212529")
        bf.pack(fill=tk.X, padx=15, pady=10)
        bst = {"font": ("맑은 고딕", 10, "bold"), "bd": 0, "cursor": "hand2", "pady": 6}
        btn_data = [
            ("➕ 새 메모 추가", "#10B981", lambda: self.open_memo_window(), 0, 0),
            ("✏️ 메모 수정", "#3B82F6", lambda: self.open_memo_window(self.get_selected_index()), 0, 1),
            ("🗑️ 메모 삭제", "#EF4444", self.delete_memo, 1, 0),
            ("📏 메모 크기", "#6366F1", self.open_resize_window, 1, 1),
            ("📐 위치 정렬", "#F59E0B", self.open_arrange_window, 2, 0),
            ("🔄 바탕화면 갱신", "#8B5CF6", self.apply_wallpaper, 2, 1)
        ]
        for t, c, cmd, r, col in btn_data:
            tk.Button(bf, text=t, bg=c, fg="white", command=cmd, **bst).grid(row=r, column=col, padx=3, pady=3, sticky="ew")
        bf.grid_columnconfigure((0, 1), weight=1)
        self.refresh_listbox()

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for i, m in enumerate(self.memos):
            first = m.get("text", "").split("\n")[0].strip() or "(빈 메모)"
            tag = f" [{m.get('font_family', '기본')[:4]}|{m.get('bg_keyword', '노랑')[:4]}]"
            self.listbox.insert(tk.END, f"[{i+1}] {first[:16]} ({m['width']}x{m['height']}){tag}")

    def get_selected_index(self):
        sel = self.listbox.curselection()
        return sel[0] if sel else None

    def apply_wallpaper(self):
        save_memos(self.memos)
        update_wallpaper(self.memos)
        messagebox.showinfo("완료", "바탕화면이 성공적으로 설정되었습니다!")

    def open_memo_window(self, edit_idx=None):
        is_edit = edit_idx is not None
        if is_edit and (edit_idx < 0 or edit_idx >= len(self.memos)):
            messagebox.showwarning("선택 오류", "수정할 메모를 목록에서 선택해주세요.")
            return
        memo = self.memos[edit_idx] if is_edit else {}
        win = tk.Toplevel(self.root)
        win.title("메모 수정" if is_edit else "새 메모 추가")
        win.geometry("380x420")
        win.configure(bg="#212529")

        tk.Label(win, text="📝 메모 내용:", font=("맑은 고딕", 10, "bold"), fg="#FFEB3B", bg="#212529").pack(anchor="w", padx=15, pady=(8, 2))
        tbox = tk.Text(win, font=("맑은 고딕", 10), height=6, bg="#FFFDE7", fg="#212529")
        tbox.pack(fill=tk.BOTH, expand=True, padx=15, pady=2)
        if is_edit: tbox.insert("1.0", memo.get("text", ""))

        tk.Label(win, text="🖼️ 배경 키워드 (Unsplash API, 예: paper, sky):", font=("맑은 고딕", 9, "bold"), fg="#E2E8F0", bg="#212529").pack(anchor="w", padx=15, pady=(8, 2))
        ekw = tk.Entry(win, font=("맑은 고딕", 10), bg="#2B3035", fg="white", insertbackground="white")
        ekw.pack(fill=tk.X, padx=15, pady=2)
        if is_edit: ekw.insert(0, memo.get("bg_keyword", ""))

        tk.Label(win, text="🔤 글씨체 (Google Fonts API):", font=("맑은 고딕", 9, "bold"), fg="#E2E8F0", bg="#212529").pack(anchor="w", padx=15, pady=(8, 2))
        fonts = get_available_fonts()
        fcombo = ttk.Combobox(win, values=fonts, state="readonly", font=("맑은 고딕", 9))
        fcombo.set(memo.get("font_family") if is_edit and memo.get("font_family") in fonts else fonts[0])
        fcombo.pack(fill=tk.X, padx=15, pady=2)

        def save():
            txt = tbox.get("1.0", tk.END).strip()
            if not txt:
                messagebox.showwarning("입력 필요", "메모 내용을 입력하세요.", parent=win)
                return
            kw, ffamily = ekw.get().strip(), fcombo.get()
            btn_save.config(text="⏳ 다운로드 중...", state=tk.DISABLED)
            win.update()
            bg_p = fetch_unsplash_background(kw, memo.get("width", 260), memo.get("height", 180)) if kw else ""
            f_p = fetch_font_file(ffamily) if ffamily else ""
            data = {"text": txt, "bg_keyword": kw, "bg_image_path": bg_p, "font_family": ffamily, "font_path": f_p}
            if is_edit:
                memo.update(data)
            else:
                idx = len(self.memos)
                self.memos.append({"id": idx + 1, "x": 80 + (idx * 40) % 500, "y": 80 + (idx * 40) % 300, "width": 260, "height": 180, **data})
            self.refresh_listbox()
            self.apply_wallpaper()
            win.destroy()

        btn_save = tk.Button(win, text="저장 및 바탕화면 적용", font=("맑은 고딕", 10, "bold"), bg="#10B981", fg="white", command=save, bd=0, pady=6)
        btn_save.pack(fill=tk.X, padx=15, pady=12)

    def delete_memo(self):
        idx = self.get_selected_index()
        if idx is None:
            messagebox.showwarning("선택 오류", "삭제할 메모를 목록에서 선택해주세요.")
            return
        if messagebox.askyesno("삭제 확인", f"선택한 메모 {idx+1}번을 삭제할까요?"):
            self.memos.pop(idx)
            self.refresh_listbox()
            self.apply_wallpaper()

    def open_resize_window(self):
        idx = self.get_selected_index()
        if idx is None:
            messagebox.showwarning("선택 오류", "크기를 조절할 메모를 선택해주세요.")
            return
        memo = self.memos[idx]
        win = tk.Toplevel(self.root)
        win.title("메모 크기 조절")
        win.geometry("320x240")
        win.configure(bg="#212529")
        tk.Label(win, text=f"메모 #{idx+1} 크기 설정", font=("맑은 고딕", 10, "bold"), fg="#FFEB3B", bg="#212529").pack(pady=6)
        sw = tk.Scale(win, from_=150, to=600, orient=tk.HORIZONTAL, label="가로 크기 (Width)", bg="#2B3035", fg="white", highlightthickness=0, length=240)
        sw.set(memo["width"])
        sh = tk.Scale(win, from_=100, to=500, orient=tk.HORIZONTAL, label="세로 크기 (Height)", bg="#2B3035", fg="white", highlightthickness=0, length=240)
        sh.set(memo["height"])
        sw.pack(pady=3); sh.pack(pady=3)

        def save_size():
            memo["width"], memo["height"] = sw.get(), sh.get()
            self.refresh_listbox(); self.apply_wallpaper(); win.destroy()
        tk.Button(win, text="크기 적용 및 바탕화면 설정", font=("맑은 고딕", 10, "bold"), bg="#3B82F6", fg="white", command=save_size, bd=0, pady=6).pack(fill=tk.X, padx=20, pady=10)

    def open_arrange_window(self):
        if not self.memos:
            messagebox.showwarning("안내", "정렬할 메모가 없습니다.")
            return
        win = tk.Toplevel(self.root)
        win.title("메모 위치 드래그 정렬")
        win.geometry("640x440")
        win.configure(bg="#212529")
        sw, sh = get_screen_size()
        cw, ch = 600, int(600 * (sh / sw))
        rx, ry = sw / cw, sh / ch

        tk.Label(win, text="💡 메모지를 마우스로 드래그하여 배치한 뒤 적용하세요.", font=("맑은 고딕", 10), fg="#FFEB3B", bg="#212529").pack(pady=6)
        canvas = tk.Canvas(win, width=cw, height=ch, bg="#121212", highlightthickness=1, highlightbackground="#495057")
        canvas.pack(pady=5)
        drag = {"item": None, "x": 0, "y": 0, "idx": None}

        for i, m in enumerate(self.memos):
            x1, y1 = m["x"] / rx, m["y"] / ry
            x2, y2 = (m["x"] + m["width"]) / rx, (m["y"] + m["height"]) / ry
            canvas.create_rectangle(x1, y1, x2, y2, fill="#FFEB3B", outline="#F59E0B", width=2, tags=(f"memo_{i}", "memo_obj", f"rect_{i}"))
            snip = (m["text"].split("\n")[0][:10] or "메모")
            canvas.create_text(x1 + 6, y1 + 8, text=f"#{i+1} {snip}", anchor="nw", font=("맑은 고딕", 8, "bold"), fill="#212529", tags=(f"memo_{i}", "memo_obj"))

        def on_press(e):
            c = canvas.find_withtag("current")
            if c:
                for t in canvas.gettags(c[0]):
                    if t.startswith("memo_") and not t.startswith("memo_obj"):
                        drag["idx"], drag["item"], drag["x"], drag["y"] = int(t.split("_")[1]), t, e.x, e.y
                        break
        def on_motion(e):
            if drag["item"]:
                canvas.move(drag["item"], e.x - drag["x"], e.y - drag["y"])
                drag["x"], drag["y"] = e.x, e.y
        def on_release(e):
            if drag["item"]:
                c = canvas.coords(f"rect_{drag['idx']}")
                if c and len(c) >= 4:
                    self.memos[drag['idx']]["x"], self.memos[drag['idx']]["y"] = max(0, int(c[0] * rx)), max(0, int(c[1] * ry))
                drag["item"] = None
        canvas.tag_bind("memo_obj", "<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_motion)
        canvas.bind("<ButtonRelease-1>", on_release)

        def save_pos():
            for i, m in enumerate(self.memos):
                c = canvas.coords(f"rect_{i}")
                if c and len(c) >= 4:
                    m["x"], m["y"] = max(0, int(c[0] * rx)), max(0, int(c[1] * ry))
            self.apply_wallpaper()
            win.destroy()
        tk.Button(win, text="위치 적용 및 바탕화면 설정", font=("맑은 고딕", 10, "bold"), bg="#10B981", fg="white", command=save_pos, bd=0, pady=6).pack(pady=8)

if __name__ == "__main__":
    root = tk.Tk()
    app = MemoApp(root)
    root.mainloop()
