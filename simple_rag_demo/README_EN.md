# 🤖 Mini RAG Demonstrator with the LLMaaS API

This project is a Python script designed as an educational tool to clearly and visually illustrate the functioning of a **RAG (Retrieval-Augmented Generation)** architecture.

It relies exclusively on the **Cloud Temple LLMaaS API** and standard Python libraries, without the complexity of Docker containers or external vector databases. The vectors are simply stored in memory, making it ideal for understanding the fundamental mechanics of RAG.

---

## 📖 Key Concepts Demonstrated

This script highlights the fundamental steps of the RAG process:

1.  **📚 Document Corpus**: Uses articles from the French Constitution as a knowledge base.
2.  **🧠 Embedding**: Vectorizes the corpus and the user's question using the `granite-embedding:278m` model.
3.  **🔍 Similarity Search**: Compares the question to the documents using two metrics (Cosine Similarity and Euclidean Distance) to find the most relevant context.
4.  **✍️ Augmented Generation**: Sends the question and the found context to a generation model (`mistral-small3.2:24b`) to obtain a factual and contextual answer.

For a detailed explanation of these concepts, consult our guide: **[Understanding RAG: Embedding and Vector Distance](../../doc/llmaas/rag_explained.md)**.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- A valid LLMaaS API token.

### 1. Installation

Navigate to the root of this folder (`examples/simple-rag-demo`) and run the following commands:

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create the .env file from the example
cp .env.example .env
```

### 2. Configuration

Open the `.env` file you just created and enter your LLMaaS API key:

```dotenv
# .env
LLMAAS_API_KEY="your_personal_token_here"
LLMAAS_BASE_URL="https://api.ai.cloud-temple.com/v1"
```

### 3. Execution

Simply run the script from your terminal:

```bash
python rag_demo.py
```

The script will guide you through the different steps. For an even more detailed view showing the payloads sent to the API, use the `--payload` option:

```bash
python rag_demo.py --payload
```

---

## 📊 Example Output

Here is what the script's execution looks like when you ask a question:

  <!-- Replace with a real screenshot if possible -->

```
╭────────────────────────────────── Welcome ───────────────────────────────────╮
│  RAG (Retrieval-Augmented Generation) Demonstrator                           │
│  Using the French Constitution as a knowledge base                           │
╰────────────────────────────────────────────────────────────────────────────────╯
╭────────────────────────────────────────────────────────────────────────────────╮
│ STEP 1: Corpus Vectorization                                                   │
│ Each article is converted into a numerical vector (embedding).                 │
╰────────────────────────────────────────────────────────────────────────────────╯
   => 11 documents vectorized successfully.

╭────────────────────────────────────────────────────────────────────────────────╮
│ STEP 2: User Question                                                          │
│ Ask a question about the Constitution.                                         │
╰────────────────────────────────────────────────────────────────────────────────╯
Your question > who appoints the prime minister?

╭────────────────────────────────────────────────────────────────────────────────╮
│ STEP 3: Question Vectorization                                                 │
│ The question is converted into a vector to be compared with the corpus.        │
╰────────────────────────────────────────────────────────────────────────────────╯
   => Question vectorized successfully.

╭────────────────────────────────────────────────────────────────────────────────╮
│ STEP 4: Similarity Search (Retrieval)                                          │
│ The question vector is compared to all corpus vectors.                         │
╰────────────────────────────────────────────────────────────────────────────────╯
                                Proximity Calculation
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Article (excerpt)            ┃ Cosine Similarity ↑  ┃ Euclidean Distance ↓ ┃ Choice (by Cosine)  ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ Article 8: The President of  │               0.7511 │                 0.6912 │         ✅          │
│ the Republic appoints the... │                      │                        │                     │
│ ...                          │                  ... │                    ... │                     │
└──────────────────────────────┴──────────────────────┴────────────────────────┴─────────────────────┘
   => The document with the highest cosine similarity score is chosen...

   => Relevant document found:
╭────────────────────────────────────────────────────────────────────────────────╮
│ Article 8: The President of the Republic appoints the Prime Minister. He may   │
│ terminate his functions upon the presentation by the latter of the...          │
╰────────────────────────────────────────────────────────────────────────────────╯
╭────────────────────────────────────────────────────────────────────────────────╮
│ STEP 5: Augmented Generation                                                   │
│ Building an enriched prompt and sending it to the generation model.            │
╰────────────────────────────────────────────────────────────────────────────────╯
   => Final prompt sent to the generation model:
  1 Answer in French the question: "who appoints the prime minister?", using...
╭────────────────────────────────────────────────────────────────────────────────╮
│ STEP 6: Displaying the Final Answer                                            │
╰────────────────────────────────────────────────────────────────────────────────╯
╭─ Model's Final Answer ─────────────────────────────────────────────────────────╮
│                                                                                │
│  According to the provided text, it is the President of the Republic who       │
│  appoints the Prime Minister.                                                  │
│                                                                                │
╰────────────────────────────────────────────────────────────────────────────────╯
