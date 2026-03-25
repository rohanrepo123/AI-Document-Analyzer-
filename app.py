from unittest import result
from wsgiref import headers

from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
from textblob import TextBlob
import pytesseract
from PIL import Image
import os
import re 
import numpy as np
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import re
from nltk.stem import PorterStemmer
from textblob import TextBlob
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

documents = []
faiss_index = None

# NEW imports
import fitz  # PyMuPDF (for PDFs)
from keybert import KeyBERT

kw_model = KeyBERT()
from docx import Document  # for DOCX

research_paper = False
abstract_c = ""
app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Set Tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def build_index():
    global faiss_index, documents

    import json
    try:
        with open("data.json", "r") as f:
            db = json.load(f)
    except:
        db = []

    documents = db
    vectors = []

    for doc in db:
        vec = model.encode(doc["text"])
        vectors.append(vec)

    if vectors:
        dim = len(vectors[0])
        faiss_index = faiss.IndexFlatL2(dim)
        faiss_index.add(np.array(vectors))


@app.route('/')
def index():
    return render_template('docUpload.html')

@app.route('/uploads', methods=['POST'])
def upload():
    import os 
    if 'file' not in request.files:
        return jsonify({"text": "No file uploaded"})

    file = request.files['file']

    if file.filename == "":
        return jsonify({"text": "Empty filename"})

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    
    text = ""
    True_text = ""
    image = True
    try:
        filename = file.filename.lower()

        # ================= IMAGE =================
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            img = Image.open(filepath).convert("RGB")
            text = pytesseract.image_to_string(img)

        # ================= PDF =================
        elif filename.endswith('.pdf'):
            doc = fitz.open(filepath)
            for page in doc:
                page_text = page.get_text()
                image = False

                # If no text (scanned PDF), use OCR
                if not page_text.strip():
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    page_text = pytesseract.image_to_string(img)

                text += page_text + "\n"

        # ================= DOCX =================
        elif filename.endswith('.docx'):
            doc = Document(filepath)
            for para in doc.paragraphs:
                text += para.text + "\n"
            image = False
        else:
            text = "Unsupported file type"

    except Exception as e:
        text = "Error: " + str(e)
    # print(text)
        # =====================Text Preprocessing=====================

    # def htmlTag(text):
    #     clean = re.compile('<.*?>')
    #     return re.sub(clean, '', text)
    
    # def emoji(text):
    #     emoji_pattern = re.compile("["
    #                             u"\U0001F600-\U0001F64F"  # emoticons
    #                             u"\U0001F300-\U0001F5FF"  # symbols & pictographs
    #                             u"\U0001F680-\U0001F6FF"  # transport & map symbols
    #                             u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
    #                             "]+", flags=re.UNICODE)
    #     return emoji_pattern.sub(r'', text)
    
    # def removeSpecial(text):
    #     return re.sub(r'[^A-Za-z0-9\s]+', '', text)
    
    # ======================FOR Images======================
    true_text = text
    def removeExtraSpaces(text):
        return re.sub(r'\s+', ' ', text).strip()
    
    def clean_text(text):
        text = text.strip()
        text = text.replace("\n", " ")
        text = text.replace("â‚¹", "₹")
        text = text.replace("â€“", "-")
        text = text.replace("â€œ", '"')
        text = text.replace("â€", '"')
        # fix encoding issues
        text = text.encode('utf-8', 'ignore').decode('utf-8')
        return text
    import re
    def basic_clean(text):
        
        text = text.strip()
        text = text.replace("\n", " ")
        text = re.sub(r'\s+', ' ', text)
        return text

    def fix_common_ocr_errors(text):
        replacements = {
        "0": "O",   # sometimes needed carefully
        "1": "l",
        "|": "I",
        "5": "S",
        "€": "₹"}
        for wrong, correct in replacements.items():
            text = text.replace(wrong, correct)
        return text

    def protect_numbers(text):
        return re.sub(r'\bO\b', '0', text)
    
    def remove_noise(text):
        text = re.sub(r'[^a-zA-Z0-9₹.,:/\- ]', '', text)
        return text

    from textblob import TextBlob

    def correct_spelling(text):
        return str(TextBlob(text).correct())

    def clean_ocr_text(text):
        text = removeExtraSpaces(text)
        # text = basic_clean(text)
        text = remove_noise(text)
        text = fix_common_ocr_errors(text)
        text = protect_numbers(text)
        text = clean_text(text)
        text = correct_spelling(text)
        return text
    
    if image:
        text = clean_ocr_text(text)
    else:
        text = basic_clean(text)

    # print("Cleaned Text:", text_c)
    
    # =====================Skip intro===============================

    def extract_abstract(text):
        match = re.search(r'abstract(.*?)(introduction|1\.)', text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()   
        return text[:1100]   
     
    import re

    def remove_references(text):
        keywords = ["future scope", "refrences", "refrence"]
        text_lower = text.lower()

        for kw in keywords:
            if kw in text_lower:
                if kw == "future scope":
                    match = re.search(r'future scope(.*?)(refrences|refrence\.)',
                                    text, re.IGNORECASE | re.DOTALL)
                    if match:
                        return match.start()

                match = re.search(f'{kw}(.*)', text, re.IGNORECASE | re.DOTALL)
                if match:                    
                    return text[:-match.start()] 
        return text
                

    def check_research_paper(text):
            global research_paper
            count = 0
            keywords = ["abstract", "introduction", "conclusion"]
            count = sum(1 for kw in keywords if kw in text.lower())
            for i in keywords:
                if i in text.lower():
                    count +=1
            if count >2:
                research_paper = True
                print(count)
            else:
                research_paper= False
            
    def remove_intro(text):
        global research_paper
        count =0
        keywords = ["abstract", "introduction", "conclusion"]
        count = sum(1 for kw in keywords if kw in text.lower())
        # print(count)
        if count == 3:
            abstract_c = extract_abstract(text)
            text = remove_references(text)
            return text,abstract_c  
        return text,0  # Return the original text unchanged
    
      # Return the original text unchanged
    def extract_keywords(text):
        keywords = kw_model.extract_keywords(text, top_n=5)
        return [kw[0] for kw in keywords]

    keywords = extract_keywords(text)

    # ======================Text Summarization=====================

    import os
    from huggingface_hub import InferenceClient
    import dotenv
    dotenv.load_dotenv()
    # text = "This was the third time the U.S. has temporarily waived sanctions in about two weeks. The U.S. had previously eased sanctions on Russian oil and on Friday (March 20, 2026) issued a general license allowing the sale of Iranian crude oil and petroleum products loaded on vessels as of March 20 to April 19, according to the license posted to the Treasury Department's website."
    # text = 'This was the third time the U.S. has temporarily waived sanctions in about two weeks.'
    def summarize_research_paper(text):
        # text = text[:-2000]
        client = InferenceClient(
            provider="hf-inference",
            api_key=os.environ["HF_TOKEN"],
        )
        
        result = client.summarization(
            text,
        #     model="google/pegasus-xsum",
        #     model="allenai/led-base-16384-ms2",
        #     model="google/flan-t5-base",
        model = 'sshleifer/distilbart-cnn-12-6'
        )
        # Text generation as summarization for long documents
        # result = client.text_generation(
        # f"Summarize the following document:\n{text}",
        # model="google/flan-t5-base")

        print("Research Paper")
    
        return result.summary_text
    
    def summarize_general(text):
        client = InferenceClient(
            provider="hf-inference",
            api_key=os.environ["HF_TOKEN"],
        )

        result = client.summarization(
            text,
            model="facebook/bart-large-cnn",
        )
        print("Normal Paper")
    
        return result.summary_text
    # print("Summary:\n")
    # print(summary)
    # ===================NER Recognition=======================
        
    # hh = 'https://huggingface.co/dbmdz/bert-large-cased-finetuned-conll03-english'
    
    # text = remove_intro(text)

    def ner_recognition(text):
        import os
        from huggingface_hub import InferenceClient
        client = InferenceClient(
            provider="hf-inference",
            api_key=os.environ["HF_TOKEN"],
        )

        result = client.token_classification(
            text,
            model="Jean-Baptiste/roberta-large-ner-english",
        )

        # print(summary)
        # print("Summary:\n")
        print("\nNamed Entities:\n")
        ner = {}

        current_word = ""
        current_label = ""

        for i in result:
            word = i['word']
            label = i['entity_group']

            # Handle subwords (##)
            if word.startswith("##"):
                current_word += word[2:]
            else:
                if current_word:
                    if current_label not in ner:
                        ner[current_label] = []
                    ner[current_label].append(current_word)

                current_word = word
                current_label = label

        # Add last word
        if current_word:
            if current_label not in ner:
                ner[current_label] = []
            ner[current_label].append(current_word)
        return ner 
    summary_abstract =""

    check_research_paper(text)

    print(research_paper)
    if research_paper:
        text1, abstract_c = remove_intro(text)
        # print("Abstract Summary:\n",abstract_c)
    
        ttxt = text1[:2000]
        summary = summarize_research_paper(ttxt)
        # print("Abstract Summary:\n",summary)
        summary_abstract = summarize_research_paper(abstract_c)
        # print("Abstract Summary:\n",summary_abstract)
    else:
        summary = summarize_general(text[:2000])
    
    ner = ner_recognition(text)
    # ====================Keyword Parser======================
    save_data = {
    "filename": file.filename,
    "text": text,
    "summary": summary,
    "abstract": summary_abstract,
    "entities": ner,
    "keywords": keywords
}

    import json
    try:
        with open("data.json", "r") as f:
            db = json.load(f)
    except:
        db = []

    db.append(save_data)

    with open("data.json", "w") as f:
        json.dump(db, f, indent=4)
    build_index()

    # text1 = ''
    return jsonify({
        "filename": file.filename,
        "Doc": text,
        "Summary": summary,
        "Abstract": summary_abstract if research_paper else "N/A",
        "NER": ner,
        "url": f"http://127.0.0.1:5001/uploads/{file.filename}"
    })

@app.route('/search')
def search():
    query = request.args.get('q')

    import json
    try:
        with open("data.json", "r") as f:
            db = json.load(f)
    except:
        return jsonify({"results": []})

    results = []

    for doc in db:
        if query.lower() in doc["text"].lower():
            results.append({
                "filename": doc["filename"],
                "summary": doc["summary"],
                "text": doc["text"],
                "abstract": doc.get("abstract", ""),
                "entities": doc.get("entities", {})
            })
    return jsonify({"results": results})

@app.route('/doc')
def get_doc():
    name = request.args.get('name')

    import json
    with open("data.json", "r") as f:
        db = json.load(f)
    print("Requested:", name)

    for doc in db:
        if doc["filename"] == name:
            return jsonify(doc)

    return jsonify({"error": "Not found"})

faiss_index = None

@app.route('/semantic_search')
def semantic_search():
    query = request.args.get('q')

    global faiss_index, documents

    if not query:
        return jsonify({"results": []})

    if faiss_index is None:
        build_index()

    q_vec = model.encode([query])

    D, I = faiss_index.search(np.array(q_vec), k=3)

    results = []

    for idx in I[0]:
        if idx < len(documents):
            doc = documents[idx]
            results.append({
                "filename": doc["filename"],
                "summary": doc["summary"]
            })

    return jsonify({"results": results})

if __name__ == '__main__':
    app.run(debug=True, port=5001)