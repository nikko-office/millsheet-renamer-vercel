# ミルシートPDF自動リネーム（デスクトップ版）

Claude API を使って、PDF（ミルシート）から情報を抽出し、  
`発行日_規格_寸法_鋼番_工事名_メーカー名.pdf` の形式で自動リネームします。

## 使い方（開発環境）

1. Python 3.10 以上をインストール
2. 依存関係をインストール

```
pip install -r requirements.txt
```

3. 起動

```
python app.py
```

## EXE化（Windows）

1. PyInstaller をインストール

```
pip install pyinstaller
```

2. exe を作成

```
pyinstaller --onefile --windowed --name MillsheetRenamer app.py
```

3. `dist/MillsheetRenamer.exe` を起動

## 操作方法

- Claude API Key を入力
- PDF をドラッグ＆ドロップ or クリックで選択
- 「処理開始」でリネーム実行
- 出力先フォルダを指定しない場合、元のフォルダに保存されます

## 注意

- API Key はローカルに保存されます（`%USERPROFILE%\.millsheet-renamer\config.json`）
- PDF は Claude API に送信されます
