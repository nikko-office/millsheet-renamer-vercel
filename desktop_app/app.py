import base64
import json
import os
import re
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import fitz  # PyMuPDF
import requests
from tkinterdnd2 import DND_FILES, TkinterDnD


APP_TITLE = "ミルシートPDF自動リネーム"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".millsheet-renamer")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
MODEL_NAME = "claude-sonnet-4-20250514"


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def sanitize_filename(name):
    name = name.replace("/", "_").replace("\\", "_")
    name = re.sub(r'[<>:"|?*]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def unique_path(path):
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while True:
        candidate = f"{base} ({i}){ext}"
        if not os.path.exists(candidate):
            return candidate
        i += 1


def pdf_to_images_base64(pdf_path, max_pages=2, scale=2.0):
    images = []
    doc = fitz.open(pdf_path)
    pages = min(max_pages, doc.page_count)
    for i in range(pages):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        png_bytes = pix.tobytes("png")
        images.append(base64.b64encode(png_bytes).decode("utf-8"))
    doc.close()
    return images


def build_prompt():
    return (
        "このPDFは鋼材検査証明書（ミルシート）です。\n"
        "以下の情報を正確に抽出してください：\n"
        "1. 発行日 (Date of Issue): YYYY.MM.DD形式または発行日付から抽出\n"
        "2. 規格: JIS G 3101 SS400 のような形式で、SS400の部分を抽出\n"
        "3. 寸法: 例「19.00X1,540XCOIL」のような形式（カンマを除去してxに統一）\n"
        "4. 鋼番 (Charge No.): 例「AE4652」\n"
        "5. 工事名 (Project Name): 【】で囲まれている場合があります\n"
        "6. メーカー名: 東京製鉄、JFEスチール、日本製鉄など\n\n"
        "必ず以下のJSON形式で回答してください（他のテキストは含めず、JSONのみ）:\n"
        "{\n"
        '  "date": "YYMMDD形式（例: 251125）",\n'
        '  "spec": "規格（例: SS400）",\n'
        '  "size": "寸法（例: 19.00x1540xCOIL）",\n'
        '  "charge_no": "鋼番（例: AE4652）",\n'
        '  "project": "工事名（例: ほぼゼロ）",\n'
        '  "maker": "メーカー名（例: 東京製鉄）"\n'
        "}"
    )


def call_claude(api_key, images_base64):
    content = []
    for img in images_base64:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img,
                },
            }
        )
    content.append({"type": "text", "text": build_prompt()})

    payload = {
        "model": MODEL_NAME,
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": content}],
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
    }

    resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"Claude API error: {resp.status_code} {resp.text}")

    data = resp.json()
    text_blocks = [c for c in data.get("content", []) if c.get("type") == "text"]
    if not text_blocks:
        raise RuntimeError("Claude response missing text content")

    text = text_blocks[0].get("text", "").strip()
    json_match = re.search(r"```json\s*(.*?)\s*```", text, re.S)
    if json_match:
        text = json_match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"JSON parse error: {exc}") from exc


def generate_filename(info):
    parts = [
        info.get("date") or "不明",
        info.get("spec") or "不明",
        info.get("size") or "不明",
        info.get("charge_no") or "不明",
        info.get("project") or "不明",
        info.get("maker") or "不明",
    ]
    filename = "_".join(parts) + ".pdf"
    return sanitize_filename(filename)


class App(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x600")
        self.configure(bg="#f5f6fa")
        self.files = []
        self.output_dir = ""

        self._build_ui()
        self._load_saved_key()

    def _build_ui(self):
        title = tk.Label(
            self,
            text=APP_TITLE,
            font=("Segoe UI", 18, "bold"),
            bg="#f5f6fa",
        )
        title.pack(pady=10)

        api_frame = tk.Frame(self, bg="#f5f6fa")
        api_frame.pack(fill="x", padx=20)
        tk.Label(
            api_frame,
            text="Claude API Key（必須）",
            font=("Segoe UI", 10, "bold"),
            bg="#f5f6fa",
        ).pack(anchor="w")
        self.api_key_var = tk.StringVar()
        api_entry = tk.Entry(api_frame, textvariable=self.api_key_var, show="*", width=60)
        api_entry.pack(fill="x", pady=5)

        drop_frame = tk.Frame(self, bg="#ffffff", bd=2, relief="groove")
        drop_frame.pack(fill="both", expand=True, padx=20, pady=10)
        drop_label = tk.Label(
            drop_frame,
            text="PDFファイルをドラッグ＆ドロップ\nまたはクリックで選択",
            font=("Segoe UI", 12),
            bg="#ffffff",
        )
        drop_label.pack(expand=True)

        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind("<<Drop>>", self._on_drop)
        drop_frame.bind("<Button-1>", lambda e: self._select_files())

        controls = tk.Frame(self, bg="#f5f6fa")
        controls.pack(fill="x", padx=20, pady=5)
        tk.Button(controls, text="PDF選択", command=self._select_files).pack(side="left")
        tk.Button(controls, text="出力先フォルダ", command=self._select_output_dir).pack(
            side="left", padx=5
        )
        tk.Button(controls, text="処理開始", command=self._start_processing).pack(
            side="right"
        )

        self.listbox = tk.Listbox(self, height=8)
        self.listbox.pack(fill="both", expand=False, padx=20, pady=10)

        self.status_var = tk.StringVar(value="待機中")
        status = tk.Label(self, textvariable=self.status_var, bg="#f5f6fa")
        status.pack(pady=5)

    def _load_saved_key(self):
        cfg = load_config()
        key = cfg.get("api_key", "")
        if key:
            self.api_key_var.set(key)

    def _save_key(self):
        key = self.api_key_var.get().strip()
        if key:
            cfg = load_config()
            cfg["api_key"] = key
            save_config(cfg)

    def _select_files(self):
        paths = filedialog.askopenfilenames(
            title="PDFを選択",
            filetypes=[("PDF Files", "*.pdf")],
        )
        self._add_files(paths)

    def _select_output_dir(self):
        path = filedialog.askdirectory(title="出力先フォルダを選択")
        if path:
            self.output_dir = path
            self.status_var.set(f"出力先: {path}")

    def _on_drop(self, event):
        paths = self._parse_drop_files(event.data)
        self._add_files(paths)

    def _parse_drop_files(self, data):
        files = self.tk.splitlist(data)
        paths = []
        for f in files:
            if os.path.isdir(f):
                for root, _, filenames in os.walk(f):
                    for name in filenames:
                        if name.lower().endswith(".pdf"):
                            paths.append(os.path.join(root, name))
            elif f.lower().endswith(".pdf"):
                paths.append(f)
        return paths

    def _add_files(self, paths):
        for p in paths:
            if p not in self.files:
                self.files.append(p)
                self.listbox.insert(tk.END, p)

    def _start_processing(self):
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("エラー", "Claude API Keyを入力してください。")
            return
        if not self.files:
            messagebox.showinfo("案内", "PDFファイルを追加してください。")
            return

        self._save_key()
        self.status_var.set("処理中...")
        thread = threading.Thread(target=self._process_files, args=(api_key,), daemon=True)
        thread.start()

    def _process_files(self, api_key):
        for idx, path in enumerate(self.files):
            self._set_list_status(idx, "処理中...")
            try:
                images_base64 = pdf_to_images_base64(path)
                info = call_claude(api_key, images_base64)
                new_name = generate_filename(info)
                target_dir = self.output_dir or os.path.dirname(path)
                target_path = unique_path(os.path.join(target_dir, new_name))
                shutil.move(path, target_path)
                self._set_list_status(idx, f"完了: {os.path.basename(target_path)}")
            except Exception as exc:
                self._set_list_status(idx, f"エラー: {exc}")

        self.status_var.set("完了")

    def _set_list_status(self, idx, message):
        def update():
            if idx < self.listbox.size():
                original = self.listbox.get(idx)
                self.listbox.delete(idx)
                self.listbox.insert(idx, f"{original}  ->  {message}")
        self.after(0, update)


if __name__ == "__main__":
    app = App()
    app.mainloop()
