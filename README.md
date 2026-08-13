# LocalDocTranslator

LocalDocTranslator is a privacy-first, locally-run document translation tool. It extracts text from PDF or TXT files, cleans up common extraction artifacts (like page numbers, line numbers, and hyphenations), automatically detects the optimal local Large Language Model (LLM) via [Ollama](https://ollama.com/), and translates the document into highly natural Japanese.

Since all processing is done locally, **complete confidentiality is maintained.**

## Features
- **Local PDF & Text Processing:** Extract and translate without sending data to the cloud.
- **Auto Model Detection:** Automatically checks your local Ollama instance and selects the best available model for translation (e.g., `qwen2.5:14b`, `llama3.2`).
- **Format Cleanup:** Removes page numbers, fixes split hyphenated words, and merges broken lines while maintaining paragraph structure.
- **Smart Chunking:** Splits long texts by paragraphs to fit within LLM context windows and automatically reconstructs the full document.

## Requirements
- Python 3.8+
- [Ollama](https://ollama.com/) installed and running locally with at least one model (e.g., `ollama run qwen2.5:14b`)

## Installation

1. Clone this repository:
   ```bash
   git clone <YOUR_REPO_URL>
   cd LocalDocTranslator
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Make the script executable:
   ```bash
   chmod +x local_document_translator.py
   ```

## Usage

Run the script by providing the path to a `.pdf` or `.txt` file:

```bash
./local_document_translator.py /path/to/your/document.pdf
```

### Options

- **`-m, --model`**: Specify an Ollama model to use. Defaults to `auto` which automatically detects the best available model.
  ```bash
  ./local_document_translator.py document.pdf -m llama3.2:3b
  ```
- **`-o, --output`**: Specify the output file path. If not provided, it saves as `[original_filename]_ja.txt`.
- **`--save-clean-text`**: Save the intermediate cleaned English text before translation (useful for debugging text extraction).
- **`--chunk-size`**: Adjust the maximum characters per translation chunk (default: 1500).

## Example Workflow
```bash
$ ./local_document_translator.py sample.pdf
Auto-detecting optimal model...
Auto-detected optimal model: qwen2.5:14b
Extracting text from PDF: sample.pdf
Cleaning extracted text...
Divided text into 5 chunks for translation (using model: qwen2.5:14b).
  Translating chunk 1/5 (1450 characters)...
  Translating chunk 2/5 (1300 characters)...
...
Success! Full translation saved to: sample_ja.txt
```
