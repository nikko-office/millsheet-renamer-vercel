# ミルシートPDF自動リネームツール - Vercel版

Claude APIを使用して、ミルシート（鋼材検査証明書）PDFを自動でリネームするWebアプリケーションです。

## 🚀 Vercelでデプロイする方法

### 前提条件
- GitHubアカウント
- Vercelアカウント（GitHubでログイン可能）

### 手順

#### 1. GitHubリポジトリを作成

1. https://github.com/new にアクセス
2. リポジトリ名: `millsheet-renamer-vercel`
3. Public を選択
4. 「Create repository」をクリック

#### 2. ファイルをアップロード

以下のファイルをリポジトリにアップロード：

```
millsheet-renamer-vercel/
├── api/
│   └── extract.js          # サーバーレス関数
├── public/
│   └── index.html          # フロントエンド
├── vercel.json             # Vercel設定
├── package.json            # パッケージ情報
└── README.md               # このファイル
```

**アップロード方法:**
1. リポジトリページで「Add file」→「Upload files」
2. すべてのファイルをドラッグ&ドロップ
3. 「Commit changes」をクリック

**重要**: フォルダ構造を保つこと！
- `api/extract.js` は `api` フォルダに
- `public/index.html` は `public` フォルダに

#### 3. Vercelにデプロイ

1. https://vercel.com/ にアクセス
2. 「Sign Up」→「Continue with GitHub」でログイン
3. 「New Project」をクリック
4. GitHubリポジトリ `millsheet-renamer-vercel` を選択
5. 「Import」をクリック
6. 設定はデフォルトのまま「Deploy」をクリック

#### 4. デプロイ完了！

数分後、以下のようなURLでアクセス可能：
```
https://millsheet-renamer-vercel.vercel.app/
```

---

## 📋 プロジェクト構成

### `/api/extract.js`
- サーバーレス関数（Node.js）
- Claude APIを呼び出してPDFから情報を抽出
- CORSヘッダーを設定してブラウザからのアクセスを許可

### `/public/index.html`
- フロントエンドUI
- PDFをアップロード
- サーバーレス関数 `/api/extract` を呼び出し
- 結果を表示してダウンロード

### `/vercel.json`
- Vercel設定ファイル
- ルーティング設定
- ビルド設定

---

## 🎯 使い方

1. デプロイされたURLにアクセス
2. Claude API Keyを入力（https://console.anthropic.com/ から取得）
3. PDFファイルをドラッグ&ドロップ
4. 自動で情報が抽出されます
5. ダウンロードボタンでリネーム済みファイルを保存

---

## 💰 料金

### Vercel
- **Hobby プラン**: 無料
- サーバーレス関数: 月100,000リクエストまで無料

### Claude API
- Claude Sonnet 4使用
- ミルシート1枚あたり約0.5〜2円（従量課金）

---

## 🔒 セキュリティ

- API Keyはサーバーレス関数経由で処理
- PDFはClaude APIにのみ送信
- Vercelのサーバーレス関数は自動的にHTTPSで保護

---

## 🛠️ ローカル開発

```bash
# Vercel CLIをインストール
npm install -g vercel

# プロジェクトをクローン
git clone https://github.com/あなたのユーザー名/millsheet-renamer-vercel.git
cd millsheet-renamer-vercel

# ローカルサーバーを起動
vercel dev

# http://localhost:3000 でアクセス
```

---

## 📝 生成されるファイル名

```
発行日_規格_寸法_鋼番_工事名_メーカー名.pdf
```

例：`251125_SS400_19.00x1540xCOIL_AE4652_ほぼゼロ_東京製鉄.pdf`

---

## ❓ トラブルシューティング

### Q: デプロイに失敗する
A: フォルダ構造が正しいか確認してください
- `api/extract.js`
- `public/index.html`

### Q: API呼び出しでエラーが出る
A: API Keyが正しいか確認してください

### Q: 404 Not Found
A: `vercel.json` が正しくアップロードされているか確認

---

## 🎉 完成

これで完全に動作するWebアプリケーションが完成です！

---

Made with ❤️ using Claude API and Vercel
