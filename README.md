![LocalDocTranslator Thumbnail](thumbnail_v2.jpg)

# LocalDocTranslator

LocalDocTranslator はプライバシーを重視したローカル環境で動作するドキュメント翻訳ツールです。PDF または TXT ファイルからテキストを抽出し、抽出時によく発生するノイズ（ページ番号、行番号、ハイフネーションなど）をクリーンアップします。また、[Ollama](https://ollama.com/) 経由で最適なローカルの大規模言語モデル（LLM）を自動検出し、非常に自然な日本語に翻訳します。

すべての処理はローカルで完結するため、**完全な機密性が保たれます。**

## 主な機能
- **ローカルでの PDF・テキスト処理:** データをクラウドに送信することなく抽出および翻訳を行います。
- **モデルの自動検出:** ローカルの Ollama インスタンスを自動的にチェックし、翻訳に最適な利用可能なモデル（例: `qwen2.5:14b`, `llama3.2` など）を選択します。
- **フォーマットのクリーンアップ:** ページ番号を削除し、行をまたぐハイフネーションされた単語を修正し、段落構造を維持しながら途切れた行を結合します。
- **スマートなチャンク分割:** 長いテキストを段落ごとに分割し、LLM のコンテキストウィンドウに収まるように処理した上で、自動的に全文を再構成します。

## 必須要件
- Python 3.8以上
- [Ollama](https://ollama.com/) がローカルでインストールされ、少なくとも1つのモデル（例: `ollama run qwen2.5:14b`）が実行可能であること

## インストール方法

1. このリポジトリをクローンします:
   ```bash
   git clone <YOUR_REPO_URL>
   cd LocalDocTranslator
   ```

2. 必要な Python パッケージをインストールします:
   ```bash
   pip install -r requirements.txt
   ```

3. スクリプトに実行権限を付与します:
   ```bash
   chmod +x local_document_translator.py
   ```

## 使い方

`.pdf` または `.txt` ファイルのパスを指定してスクリプトを実行します。このツールは **Windows, Mac, Linux** のすべてのOSで共通して動作します（特別な依存関係はなく標準のPython機能と `pypdf` を使用しています）。

**Mac / Linux の場合:**
```bash
./local_document_translator.py /path/to/your/document.pdf
```

**Windows の場合:**
```cmd
python local_document_translator.py C:\path\to\your\document.pdf
```

### オプション

- **`-m, --model`**: 使用する Ollama モデルを指定します。デフォルトは `auto` で、最適な利用可能なモデルが自動検出されます。
  **Mac / Linux:**
  ```bash
  ./local_document_translator.py document.pdf -m llama3.2:3b
  ```
  **Windows:**
  ```cmd
  python local_document_translator.py document.pdf -m llama3.2:3b
  ```
- **`-o, --output`**: 出力ファイルのパスを指定します。指定しない場合、`[元のファイル名]_ja.txt` として保存されます。
- **`--save-clean-text`**: 翻訳前のクリーンアップされた英語のテキストを保存します（テキスト抽出のデバッグに便利です）。
- **`--chunk-size`**: 翻訳チャンクあたりの最大文字数を調整します（デフォルト: 1500）。

## ワークフローの例
```bash
$ ./local_document_translator.py sample.pdf
最適なモデルを自動検出中...
自動検出された最適なモデル: qwen2.5:14b
PDFからテキストを抽出中: sample.pdf
抽出されたテキストをクリーンアップ中...
翻訳のためにテキストを 5 つのチャンクに分割しました（使用モデル: qwen2.5:14b）。
  チャンク 1/5 (1450 文字) を翻訳中...
  チャンク 2/5 (1300 文字) を翻訳中...
...
成功しました！翻訳全体が sample_ja.txt に保存されました
```
