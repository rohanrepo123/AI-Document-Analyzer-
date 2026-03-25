# 🤖 AI Document Analyzer

An end-to-end NLP system that extracts, analyzes, and searches documents using OCR, transformer models, and semantic search.

---

## 🚀 Features

* 📤 Upload documents (PDF, DOCX, Images)
* 🔍 OCR-based text extraction (Tesseract)
* 🧠 Automatic text summarization (Hugging Face models)
* 🏷️ Named Entity Recognition (NER)
* 🔑 Keyword extraction (KeyBERT)
* 📄 Smart logic to detect research paper 
* 🔎 Keyword-based search
* ⚡ Semantic search using FAISS + Sentence Transformers
* 📄 Document viewer with detailed insights

---

## 🧠 Tech Stack

* **Backend:** Flask (Python)
* **Frontend:** HTML, CSS, JavaScript
* **NLP Models:**
  * Hugging Face Transformers
  * Sentence Transformers
* **OCR:** Tesseract
* **Vector Search:** FAISS
* **Keyword Extraction:** KeyBERT

---

## 🏗️ System Architecture

```
Upload → Extract Text → Clean → Summarize → NER → Keywords → Store → Index → Search
```

---

## 📂 Supported File Types

* 📄 PDF (including scanned PDFs via OCR)
* 📝 DOCX
* 🖼️ Images (PNG, JPG, JPEG)

---

## 🔍 Search Capabilities

### 1. Keyword Search

* Matches exact terms in documents

### 2. Semantic Search (AI)

* Uses embeddings to find meaning-based matches
* Powered by Sentence Transformers + FAISS

---

## ⚙️ Installation

```bash
git clone https://github.com/your-username/ai-document-analyzer.git
cd ai-document-analyzer
pip install -r requirements.txt
```

---

## ▶️ Run the Project

```bash
python app.py
```

Open in browser:

```
http://127.0.0.1:5001
```

---

## 🔐 Environment Setup

Create `.env` file:

```
HF_TOKEN=your_huggingface_api_key
```

---

## 📊 Example Output

```json
{
  "summary": "This paper proposes...",
  "entities": {
    "ORG": ["Google"],
    "PER": ["John Doe"]
  },
  "keywords": ["deep learning", "computer vision"]
}
```

---

## 🧠 Key Highlights

* Handles **research papers + real-world documents**
* Combines **NLP + IR (Information Retrieval)**
* Supports **hybrid search (keyword + semantic)**

---

## 🎯 Future Improvements

* 🔥 Hybrid search (BM25 + FAISS)
* 🔥 Reranking models (Cross-Encoder)
* 🔥 Entity highlighting in UI
* 🔥 User authentication & dashboard

---

## 👨‍💻 Author

Rohan
(IIIT Nagpur)

---

## ⭐ If you like this project, give it a star!
