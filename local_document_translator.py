#!/usr/bin/env python3
import os
import sys
import argparse
import urllib.request
import json
import re
from pypdf import PdfReader

# デフォルト設定
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

# 翻訳タスクのモデル優先順位リスト（優先度が高い順）
MODEL_PRIORITY = [
    "qwen2.5:32b",
    "qwen2.5:14b",
    "qwen3-coder-next:latest",
    "qwen3-coder:30b",
    "nemotron:latest",
    "deepseek-v4-pro:cloud",
    "llama3.2:3b",
    "gpt-oss:latest"
]

SYSTEM_PROMPT = """You are a professional, highly skilled English-to-Japanese translator.
Translate the input English text into natural, fluent, and contextual Japanese.
Follow these guidelines strictly:
- Maintain a professional, natural, and engaging tone. Avoid stiff, word-for-word translations.
- Translate technical terms accurately according to standard industry terminology.
- Preserve the paragraph structure and any formatting/placeholders if possible.
- Do not output any explanation, translator notes, or intro/outro. Output ONLY the translated Japanese text.
"""

def get_available_models() -> list:
    """ローカルの Ollama インスタンスから利用可能なモデルのリストを取得します。"""
    try:
        req = urllib.request.Request(OLLAMA_TAGS_URL, method="GET")
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode("utf-8"))
            return [model["name"] for model in data.get("models", [])]
    except Exception as e:
        print(f"警告: Ollama からモデルを取得できませんでした ({e})。Ollama が起動しているか確認してください。", file=sys.stderr)
        return []

def auto_detect_model() -> str:
    """優先順位リストに基づいて、利用可能な最適なモデルを検出します。"""
    available_models = get_available_models()
    if not available_models:
        return "qwen2.5:14b" # フォールバックのデフォルト
        
    for preferred_model in MODEL_PRIORITY:
        if preferred_model in available_models:
            print(f"自動検出された最適なモデル: {preferred_model}")
            return preferred_model
            
    # 優先モデルが見つからない場合、embedding モデル以外の最初のモデルを選択
    for model in available_models:
        if "embed" not in model.lower():
            print(f"自動検出されたフォールバックモデル: {model}")
            return model
            
    return available_models[0] if available_models else "qwen2.5:14b"

def extract_text_from_pdf(pdf_path: str) -> str:
    """pypdf を使用して PDF ファイルから生テキストを抽出します。"""
    print(f"PDFからテキストを抽出中: {pdf_path}")
    try:
        reader = PdfReader(pdf_path)
        pages_text = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                pages_text.append(text)
        return "\n\n--- PAGE BREAK ---\n\n".join(pages_text)
    except Exception as e:
        print(f"PDFの読み込みエラー {pdf_path}: {e}", file=sys.stderr)
        sys.exit(1)

def clean_extracted_text(text: str) -> str:
    """
    翻訳の準備として、PDF や元ファイルから抽出されたテキストをクリーンアップします。
    抽出時によくあるノイズを削除します:
    - 行番号 (例: 行の先頭/末尾)
    - ヘッダー/フッター (例: ページ番号)
    - 行をまたいでハイフネーションされた単語の修正
    - 段落の区切りを正規化し、改行を結合します。
    """
    print("抽出されたテキストをクリーンアップ中...")
    text = text.replace("--- PAGE BREAK ---", "")
    lines = text.splitlines()
    cleaned_lines = []
    
    for line in lines:
        l_str = line.strip()
        if not l_str:
            cleaned_lines.append("")
            continue
            
        l_str = re.sub(r'^\d{1,4}\s+', '', l_str)
        l_str = re.sub(r'\s+\d{1,4}$', '', l_str)
        
        if re.match(r'^-\s*\d+\s*-$', l_str) or re.match(r'^\[\d+\]$', l_str) or re.match(r'(?i)^page\s+\d+(\s+of\s+\d+)?$', l_str):
            continue
            
        cleaned_lines.append(l_str)
        
    text = "\n".join(cleaned_lines)
    text = re.sub(r'(\w+)-\s*\n\s*([a-zA-Z])', r'\1\2', text)
    
    paragraphs = text.split("\n\n")
    processed_paragraphs = []
    
    for para in paragraphs:
        para_clean = para.strip()
        if not para_clean:
            continue
        para_single_line = re.sub(r'(?<!\n)\n(?!\n)', ' ', para_clean)
        para_single_line = re.sub(r'[ \t]+', ' ', para_single_line)
        processed_paragraphs.append(para_single_line)
        
    return "\n\n".join(processed_paragraphs)

def split_text_into_chunks(text: str, max_chars: int = 1500) -> list:
    """長いテキストをチャンクに分割し、段落の境界を優先します。"""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_len = 0
    
    for para in paragraphs:
        para_len = len(para)
        if para_len > max_chars:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_len = 0
            
            sentences = re.split(r'(?<=[.!?])\s+', para)
            sub_chunk = []
            sub_len = 0
            for sentence in sentences:
                if sub_len + len(sentence) + 1 > max_chars:
                    if sub_chunk:
                        chunks.append(" ".join(sub_chunk))
                        sub_chunk = []
                        sub_len = 0
                    if len(sentence) > max_chars:
                        for i in range(0, len(sentence), max_chars):
                            chunks.append(sentence[i:i+max_chars])
                    else:
                        sub_chunk.append(sentence)
                        sub_len = len(sentence)
                else:
                    sub_chunk.append(sentence)
                    sub_len += len(sentence) + 1
            if sub_chunk:
                chunks.append(" ".join(sub_chunk))
        else:
            if current_len + para_len + 2 > max_chars:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [para]
                current_len = para_len
            else:
                current_chunk.append(para)
                current_len += para_len + 2
                
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
        
    return chunks

def translate_text(text: str, model: str) -> str:
    """ローカルの Ollama インスタンスを使用してテキストブロックを翻訳します。"""
    if not text.strip():
        return ""
    
    data = {
        "model": model,
        "prompt": text,
        "system": SYSTEM_PROMPT,
        "stream": False
    }
    
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode("utf-8"))
            return res_data.get("response", "").strip()
    except Exception as e:
        print(f"翻訳リクエスト中のエラー: {e}", file=sys.stderr)
        return "[エラー: 翻訳に失敗しました]"

def main():
    parser = argparse.ArgumentParser(
        description="ローカルのプライバシー重視翻訳ツール: PDF/テキストを抽出し、フォーマットをクリーンアップして、ローカルLLMで翻訳します。"
    )
    parser.add_argument("input_file", help="入力ファイルのパス (PDF または TXT)")
    parser.add_argument("-o", "--output", help="翻訳された出力テキストを保存するパス")
    parser.add_argument("-m", "--model", default="auto", help="使用する Ollama モデル。デフォルトは自動検出の 'auto'。")
    parser.add_argument("--save-clean-text", action="store_true", help="クリーンアップされた英語のテキストを最初にファイルに保存します")
    parser.add_argument("--chunk-size", type=int, default=1500, help="翻訳リクエストあたりの最大文字数 (デフォルト: 1500)")
    
    args = parser.parse_args()
    
    input_path = args.input_file
    if not os.path.exists(input_path):
        print(f"エラー: 入力ファイル '{input_path}' が見つかりません。", file=sys.stderr)
        sys.exit(1)
        
    # モデルの決定
    model = args.model
    if model.lower() == "auto":
        print("最適なモデルを自動検出中...")
        model = auto_detect_model()
        
    # 1. 抽出
    is_pdf = input_path.lower().endswith(".pdf")
    if is_pdf:
        raw_text = extract_text_from_pdf(input_path)
    else:
        try:
            with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()
        except Exception as e:
            print(f"ファイルの読み込みエラー {input_path}: {e}", file=sys.stderr)
            sys.exit(1)
            
    # 2. クリーンアップ
    cleaned_text = clean_extracted_text(raw_text)
    
    base_no_ext, _ = os.path.splitext(input_path)
    if args.save_clean_text:
        clean_text_path = f"{base_no_ext}_cleaned.txt"
        with open(clean_text_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)
        print(f"クリーンアップされた英語テキストを保存しました: {clean_text_path}")
        
    # 3. チャンク分割と翻訳
    chunks = split_text_into_chunks(cleaned_text, max_chars=args.chunk_size)
    total_chunks = len(chunks)
    print(f"翻訳のためにテキストを {total_chunks} 個のチャンクに分割しました（使用モデル: {model}）。")
    
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        print(f"  チャンク {i+1}/{total_chunks} ({len(chunk)} 文字) を翻訳中...")
        translated_chunk = translate_text(chunk, model)
        translated_chunks.append(translated_chunk)
        
    # 4. 結合
    translated_all = "\n\n".join(translated_chunks)
    
    output_path = args.output
    if not output_path:
        output_path = f"{base_no_ext}_ja.txt"
        
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(translated_all)
        print(f"\n成功しました！翻訳全体が次へ保存されました: {output_path}")
    except Exception as e:
        print(f"翻訳の保存エラー {output_path}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
