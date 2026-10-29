"""
image_memo.py - 바탕화면 이미지 메모 GUI 프로그램
- 메모 추가, 삭제, 크기 조절(슬라이더), 위치 정렬(드래그) 인터페이스
- 윈도우 바탕화면 반영 및 실시간 적용 (200줄 이내)
"""
import tkinter as tk
from tkinter import messagebox
from wallpaper import load_memos, save_memos, update_wallpaper, get_screen_size

class MemoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("바탕화면 이미지 메모")
        self.root.geometry("400x500")
        self.root.configure(bg="#212529")
        self.memos = load_memos()

        tk.Label(root, text="📌 바탕화면 이미지 메모", font=("맑은 고딕", 14, "bold"), fg="#FFEB3B", bg="#212529").pack(pady=10)

        frame_list = tk.Frame(root, bg="#212529")
        frame_list.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        self.scrollbar = tk.Scrollbar(frame_list)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = tk.Listbox(frame_list, font=("맑은 고딕", 10), yscrollcommand=self.scrollbar.set,
                                  bg="#2B3035", fg="#F8F9FA", selectbackground="#F59E0B", selectforeground="#000000", height=10)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.listbox.yview)

        btn_frame = tk.Frame(root, bg="#212529")
        btn_frame.pack(fill=tk.X, padx=15, pady=10)
        b_style = {"font": ("맑은 고딕", 10, "bold"), "bd": 0, "cursor": "hand2", "pady": 6}
        tk.Button(btn_frame, text="➕ 메모 추가", bg="#10B981", fg="white", command=self.open_add_window, **b_style).grid(row=0, column=0, padx=3, pady=3, sticky="ew")
        tk.Button(btn_frame, text="🗑️ 메모 삭제", bg="#EF4444", fg="white", command=self.delete_memo, **b_style).grid(row=0, column=1, padx=3, pady=3, sticky="ew")
        tk.Button(btn_frame, text="📏 메모 크기", bg="#3B82F6", fg="white", command=self.open_resize_window, **b_style).grid(row=1, column=0, padx=3, pady=3, sticky="ew")
        tk.Button(btn_frame, text="📐 위치 정렬", bg="#F59E0B", fg="white", command=self.open_arrange_window, **b_style).grid(row=1, column=1, padx=3, pady=3, sticky="ew")
        tk.Button(btn_frame, text="🔄 바탕화면 즉시 갱신", bg="#6366F1", fg="white", command=self.apply_wallpaper, **b_style).grid(row=2, column=0, columnspan=2, padx=3, pady=4, sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        self.refresh_listbox()

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for i, m in enumerate(self.memos):
            first_line = m["text"].split("\n")[0].strip() or "(빈 메모)"
            self.listbox.insert(tk.END, f"[{i+1}] {first_line[:20]} ({m['width']}x{m['height']})")

    def get_selected_index(self):
        sel = self.listbox.curselection()
        return sel[0] if sel else None

    def apply_wallpaper(self):
        save_memos(self.memos)
        update_wallpaper(self.memos)
        messagebox.showinfo("완료", "바탕화면이 성공적으로 설정되었습니다!")

    def open_add_window(self):
        win = tk.Toplevel(self.root)
        win.title("새 메모 추가")
        win.geometry("320x290")
        win.configure(bg="#212529")
        tk.Label(win, text="메모 내용 입력:", font=("맑은 고딕", 10, "bold"), fg="#FFEB3B", bg="#212529").pack(anchor="w", padx=15, pady=8)
        text_box = tk.Text(win, font=("맑은 고딕", 10), height=7, bg="#FFFDE7", fg="#212529")
        text_box.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        text_box.focus_set()

        def save_new():
            content = text_box.get("1.0", tk.END).strip()
            if not content:
                messagebox.showwarning("입력 필요", "메모 내용을 입력하세요.", parent=win)
                return
            idx = len(self.memos)
            self.memos.append({
                "id": idx + 1, "text": content,
                "x": 80 + (idx * 40) % 500, "y": 80 + (idx * 40) % 300,
                "width": 260, "height": 180
            })
            self.refresh_listbox()
            self.apply_wallpaper()
            win.destroy()

        tk.Button(win, text="추가 및 바탕화면 적용", font=("맑은 고딕", 10, "bold"), bg="#10B981", fg="white", command=save_new, bd=0, pady=6).pack(fill=tk.X, padx=15, pady=10)

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
            messagebox.showwarning("선택 오류", "크기를 조절할 메모를 목록에서 먼저 선택해주세요.")
            return
        memo = self.memos[idx]
        win = tk.Toplevel(self.root)
        win.title("메모 크기 조절")
        win.geometry("320x250")
        win.configure(bg="#212529")

        tk.Label(win, text=f"메모 #{idx+1} 크기 설정 (슬라이더 조절)", font=("맑은 고딕", 10, "bold"), fg="#FFEB3B", bg="#212529").pack(pady=8)
        tk.Label(win, text="가로 크기 (Width)", fg="white", bg="#212529").pack()
        scale_w = tk.Scale(win, from_=150, to=600, orient=tk.HORIZONTAL, bg="#2B3035", fg="white", highlightthickness=0, length=240)
        scale_w.set(memo["width"])
        scale_w.pack(pady=2)

        tk.Label(win, text="세로 크기 (Height)", fg="white", bg="#212529").pack()
        scale_h = tk.Scale(win, from_=100, to=500, orient=tk.HORIZONTAL, bg="#2B3035", fg="white", highlightthickness=0, length=240)
        scale_h.set(memo["height"])
        scale_h.pack(pady=2)

        def save_size():
            memo["width"], memo["height"] = scale_w.get(), scale_h.get()
            self.refresh_listbox()
            self.apply_wallpaper()
            win.destroy()

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

        tk.Label(win, text="💡 노란 메모지를 마우스로 드래그하여 배치한 뒤 적용하세요.", font=("맑은 고딕", 10), fg="#FFEB3B", bg="#212529").pack(pady=6)
        canvas = tk.Canvas(win, width=cw, height=ch, bg="#121212", highlightthickness=1, highlightbackground="#495057")
        canvas.pack(pady=5)
        drag = {"item": None, "x": 0, "y": 0, "idx": None}

        for i, m in enumerate(self.memos):
            x1, y1 = m["x"] / rx, m["y"] / ry
            x2, y2 = (m["x"] + m["width"]) / rx, (m["y"] + m["height"]) / ry
            canvas.create_rectangle(x1, y1, x2, y2, fill="#FFEB3B", outline="#F59E0B", width=2, tags=(f"memo_{i}", "memo_obj", f"rect_{i}"))
            snippet = (m["text"].split("\n")[0][:10] or "메모")
            canvas.create_text(x1 + 6, y1 + 8, text=f"#{i+1} {snippet}", anchor="nw", font=("맑은 고딕", 8, "bold"), fill="#212529", tags=(f"memo_{i}", "memo_obj"))

        def on_press(event):
            clicked = canvas.find_withtag("current")
            if clicked:
                for t in canvas.gettags(clicked[0]):
                    if t.startswith("memo_") and not t.startswith("memo_obj"):
                        drag["idx"], drag["item"] = int(t.split("_")[1]), t
                        drag["x"], drag["y"] = event.x, event.y
                        break

        def on_motion(event):
            if drag["item"]:
                dx, dy = event.x - drag["x"], event.y - drag["y"]
                canvas.move(drag["item"], dx, dy)
                drag["x"], drag["y"] = event.x, event.y

        def on_release(event):
            if drag["item"]:
                c = canvas.coords(f"rect_{drag['idx']}")
                if c and len(c) >= 4:
                    self.memos[drag['idx']]["x"], self.memos[drag['idx']]["y"] = max(0, int(c[0] * rx)), max(0, int(c[1] * ry))
                drag["item"] = None

        canvas.tag_bind("memo_obj", "<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_motion)
        canvas.bind("<ButtonRelease-1>", on_release)

        def save_positions():
            for i, m in enumerate(self.memos):
                c = canvas.coords(f"rect_{i}")
                if c and len(c) >= 4:
                    m["x"], m["y"] = max(0, int(c[0] * rx)), max(0, int(c[1] * ry))
            self.apply_wallpaper()
            win.destroy()

        tk.Button(win, text="위치 적용 및 바탕화면 설정", font=("맑은 고딕", 10, "bold"), bg="#10B981", fg="white", command=save_positions, bd=0, pady=6).pack(pady=8)

if __name__ == "__main__":
    root = tk.Tk()
    app = MemoApp(root)
    root.mainloop()
