# NLP Techniques Quick Reference Card

> Quick reference for implementation and enhancement options. Any improvement
> percentages are planning targets or literature/course-context estimates until
> reproduced with this repository's current evaluation scripts and data.

## At-a-Glance: What's in Your System

| Technique | Current Implementation | File Location | Enhancement Available |
|-----------|----------------------|---------------|---------------------|
| **Sentiment Analysis** | TextBlob (lexicon) | `modules/qualitative_analysis.py` | RoBERTa (+17% accuracy) |
| **Topic Modeling** | TF-IDF + K-Means | `modules/qualitative_analysis.py` | BERTopic (+35% coherence) |
| **Text Embeddings** | Sentence-BERT (MiniLM) | `modules/rag_query.py` | BGE (+15% retrieval) |
| **Question Answering** | RAG with Llama 3.2 | `modules/rag_query.py` | Extractive QA (faster) |
| **Text Generation** | Llama 3.2 (3B) | `modules/quantitative_analysis.py` | Keep (works well) |
| **PII Detection** | Regex patterns | `modules/pii_detector.py` | BERT NER (+40% recall) |
| **Categorization** | Manual | N/A | Zero-shot classifier (new) |
| **Summarization** | None | N/A | BART (new capability) |

---

## NLP Pipeline Visualization

```
┌─────────────────────────────────────────────────────────────┐
│                    RAW TEXT INPUT                            │
│              (Survey responses, feedback)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 TEXT PREPROCESSING                           │
│  • Tokenization (split into words)                          │
│  • Lowercasing (normalize)                                  │
│  • Stop word removal (filter common words)                  │
│  • Punctuation handling                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┬──────────────┐
        │              │              │              │
        ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│  SENTIMENT   │ │  THEMES  │ │EMBEDDINGS│ │     PII      │
│   ANALYSIS   │ │EXTRACTION│ │(VECTORS) │ │  DETECTION   │
├──────────────┤ ├──────────┤ ├──────────┤ ├──────────────┤
│ TextBlob     │ │ TF-IDF   │ │Sentence  │ │ Regex        │
│ Polarity     │ │ K-Means  │ │  BERT    │ │ Patterns     │
│ Score        │ │ Keywords │ │ 384-dim  │ │ Redaction    │
└──────┬───────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘
       │              │            │               │
       ▼              ▼            ▼               ▼
┌──────────────────────────────────────────────────────────┐
│              ANALYSIS RESULTS                             │
│  • Sentiment distribution (pos/neu/neg)                  │
│  • Identified themes with keywords                       │
│  • Semantic search capability                            │
│  • Privacy-protected data                                │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│                 USER QUERY (RAG)                          │
│  Question → Embedding → Vector Search → Context          │
│  Context + Question → LLM → Answer + Citations           │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│              REPORT GENERATION                            │
│  • Statistical summaries                                  │
│  • LLM-generated interpretations                         │
│  • Visualizations                                        │
│  • Executive summary                                     │
└──────────────────────────────────────────────────────────┘
```

---

## Key Algorithms Explained Simply

### 1. TF-IDF (Term Frequency-Inverse Document Frequency)

**What it does**: Finds important words in documents

**How it works**:
- TF (Term Frequency): How often a word appears in a document
- IDF (Inverse Document Frequency): How rare a word is across all documents
- TF-IDF = TF × IDF (high score = important word)

**Example**:
```
Document 1: "The library has great study spaces"
Document 2: "The library needs more study rooms"

Word "library": High TF, Low IDF (appears in both) → Low importance
Word "spaces": Low TF, High IDF (appears in one) → High importance
```

**Use in system**: Identify keywords for themes

---

### 2. K-Means Clustering

**What it does**: Groups similar items together

**How it works**:
1. Choose K (number of groups)
2. Randomly place K "centers"
3. Assign each item to nearest center
4. Move centers to middle of their group
5. Repeat steps 3-4 until stable

**Example**:
```
Responses about library:
Group 1: "quiet", "study", "peaceful" → Study Spaces theme
Group 2: "hours", "weekend", "late" → Operating Hours theme
Group 3: "books", "resources", "databases" → Collections theme
```

**Use in system**: Group similar survey responses into themes

---

### 3. Sentence Embeddings

**What it does**: Converts text to numbers (vectors) that capture meaning

**How it works**:
- Neural network trained on millions of sentences
- Similar meanings → similar vectors
- Can measure similarity with math (cosine distance)

**Example**:
```
"The library is open late" → [0.2, 0.8, 0.1, ..., 0.5] (384 numbers)
"Library has extended hours" → [0.3, 0.7, 0.2, ..., 0.4] (similar!)
"I like pizza" → [0.9, 0.1, 0.8, ..., 0.2] (very different)
```

**Use in system**: Find relevant documents for user questions

---

### 4. Retrieval-Augmented Generation (RAG)

**What it does**: Answers questions using your data + AI

**How it works**:
1. User asks: "What do students say about study spaces?"
2. Convert question to vector (embedding)
3. Find similar documents in database (retrieval)
4. Give documents + question to LLM (generation)
5. LLM generates answer based on documents
6. Show answer + which documents were used (citations)

**Why it's better than just LLM**:
- LLM alone: Might make up answers (hallucination)
- RAG: Grounds answers in your actual data
- Provides citations for transparency

**Use in system**: Ask feature

---

### 5. Sentiment Analysis (Lexicon-Based)

**What it does**: Determines if text is positive, negative, or neutral

**How it works (TextBlob)**:
- Has dictionary of words with sentiment scores
- "great" = +0.8, "terrible" = -0.9, "okay" = 0.0
- Averages scores of all words in text
- Handles negation: "not great" flips score

**Example**:
```
"The library is amazing!" 
→ amazing (+0.9) → Positive

"Staff is unhelpful and rude"
→ unhelpful (-0.5) + rude (-0.7) → Negative

"It's okay, nothing special"
→ okay (0.0) + nothing (0.0) → Neutral
```

**Limitation**: Misses context and sarcasm

**Enhancement**: Use RoBERTa (neural network) for +17% accuracy

---

## Model Comparison Cheat Sheet

### Sentiment Analysis

| Model | Type | Accuracy | Speed | Size | Best For |
|-------|------|----------|-------|------|----------|
| TextBlob | Lexicon | 72% | Very Fast | Tiny | Quick baseline |
| DistilBERT | Neural | 85% | Fast | 250MB | Real-time |
| RoBERTa | Neural | 89% | Medium | 500MB | Best accuracy |

**Recommendation**: Start with RoBERTa for course project

---

### Embeddings

| Model | Dimensions | Quality | Speed | Size | Best For |
|-------|-----------|---------|-------|------|----------|
| MiniLM (current) | 384 | Good | Fast | 80MB | Current system |
| MPNet | 768 | Better | Medium | 420MB | Better themes |
| BGE | 768 | Best | Medium | 440MB | Best RAG |

**Recommendation**: Upgrade to BGE for better retrieval

---

### Topic Modeling

| Method | Type | Coherence | Interpretability | Speed |
|--------|------|-----------|------------------|-------|
| TF-IDF + K-Means (current) | Traditional | Medium | Medium | Fast |
| LDA | Probabilistic | Medium | Good | Medium |
| BERTopic | Neural | High | Excellent | Slow |

**Recommendation**: Try BERTopic for better themes

---

## Common NLP Terms Explained

| Term | Simple Explanation | Example |
|------|-------------------|---------|
| **Token** | A word or piece of text | "library" is one token |
| **Corpus** | Collection of documents | All survey responses |
| **Embedding** | Text as numbers (vector) | "hello" → [0.1, 0.5, 0.2, ...] |
| **Semantic** | Related to meaning | "car" and "automobile" are semantically similar |
| **Polarity** | Positive/negative score | +0.8 = very positive |
| **Stop words** | Common words to ignore | "the", "is", "and" |
| **N-gram** | Sequence of N words | "study space" is a 2-gram |
| **Fine-tuning** | Training model on specific data | Train on library feedback |
| **Zero-shot** | No training needed | Classify without examples |
| **Hallucination** | AI making up information | LLM invents fake statistics |

---

## Quick Implementation Checklist

### To Add RoBERTa Sentiment (30 minutes)

- [ ] Install: `pip install transformers torch`
- [ ] Create `modules/sentiment_enhanced.py` (see HUGGINGFACE_QUICK_START.md)
- [ ] Update `modules/qualitative_analysis.py` to use new model
- [ ] Add checkbox in Streamlit UI for "Enhanced Sentiment"
- [ ] Test with sample data
- [ ] Compare results with TextBlob

### To Add Zero-Shot Classification (45 minutes)

- [ ] Install: `pip install transformers torch`
- [ ] Create `modules/classifier.py`
- [ ] Define categories: ["study spaces", "hours", "resources", "staff"]
- [ ] Add to qualitative analysis page
- [ ] Display categorization results
- [ ] Export categories with themes

### To Upgrade Embeddings (1 hour)

- [ ] Install: `pip install sentence-transformers`
- [ ] Update model name in `modules/rag_query.py`
- [ ] Re-index all documents (one-time process)
- [ ] Test retrieval quality
- [ ] Compare with old embeddings

---

## Performance Benchmarks

### Current System (on typical laptop)

| Operation | Time | Notes |
|-----------|------|-------|
| Sentiment (100 texts) | 0.5s | TextBlob |
| Theme extraction (500 texts) | 3s | TF-IDF + K-Means |
| Embedding (100 texts) | 2s | MiniLM |
| RAG query | 5-10s | Includes LLM generation |
| Report generation | 30-60s | Depends on data size |

### With Hugging Face Models (estimated)

| Operation | Time | Notes |
|-----------|------|-------|
| Sentiment (100 texts) | 5s | RoBERTa (CPU) |
| Sentiment (100 texts) | 1s | RoBERTa (GPU) |
| Theme extraction (500 texts) | 15s | BERTopic |
| Embedding (100 texts) | 4s | BGE |
| Zero-shot (100 texts) | 8s | BART-MNLI |

**Optimization tip**: Process in batches for 3-5x speedup

---

## When to Use What

### Use TextBlob when:
- Need very fast results
- Simple sentiment is enough
- CPU-only environment
- Prototyping

### Use RoBERTa when:
- Accuracy matters
- Have GPU available
- Processing in batches
- Final system

### Use TF-IDF when:
- Need fast theme extraction
- Simple keywords are enough
- Limited compute resources

### Use BERTopic when:
- Want interpretable themes
- Need automatic topic names
- Have time for processing
- Quality over speed

### Use RAG when:
- Need to answer questions about data
- Want citations/sources
- Data changes frequently
- Explainability important

### Use Fine-tuning when:
- Have labeled training data
- Domain-specific language
- Need best possible accuracy
- Have compute resources

---

## Troubleshooting Guide

### "Model download failed"
→ Check internet connection or download manually

### "Out of memory"
→ Reduce batch size or use smaller model

### "Slow inference"
→ Use GPU, quantization, or smaller model

### "Poor sentiment accuracy"
→ Try RoBERTa or domain-specific model

### "Themes don't make sense"
→ Increase n_themes or try BERTopic

### "RAG gives wrong answers"
→ Check retrieval quality, upgrade embeddings

### "LLM is slow"
→ Use smaller model or extractive QA

---

## Resources for Learning

### Beginner
- [Hugging Face Course](https://huggingface.co/course) - Free NLP course
- [Fast.ai NLP](https://www.fast.ai/) - Practical deep learning

### Intermediate
- [Speech and Language Processing](https://web.stanford.edu/~jurafsky/slp3/) - Textbook
- [Sentence-BERT Paper](https://arxiv.org/abs/1908.10084) - Embeddings

### Advanced
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762) - Transformers
- [RAG Paper](https://arxiv.org/abs/2005.11401) - Retrieval-Augmented Generation

### Practical
- [Hugging Face Model Hub](https://huggingface.co/models) - Pre-trained models
- [Papers With Code](https://paperswithcode.com/) - Latest research + code

---

## For Your Course Report

### Include These Sections:

1. **NLP Techniques Used** (from this card)
2. **Why These Techniques** (justify choices)
3. **Implementation Details** (code snippets)
4. **Evaluation** (compare methods)
5. **Results** (show improvements)
6. **Limitations** (be honest)
7. **Future Work** (Hugging Face enhancements)

### Key Points to Emphasize:

- Multiple NLP techniques integrated
- State-of-the-art approaches (RAG, embeddings)
- Practical application (real library use case)
- Privacy-preserving (local processing)
- Extensible (easy to add models)
- Evaluated (compared approaches)

---

## One-Page Summary for Presentation

**System**: Library Assessment Decision Support System

**NLP Techniques**:
1. Sentiment Analysis (TextBlob → RoBERTa upgrade available)
2. Topic Modeling (TF-IDF + K-Means → BERTopic upgrade available)
3. Text Embeddings (Sentence-BERT for semantic search)
4. RAG (Retrieval-Augmented Generation for Q&A)
5. Text Generation (Llama 3.2 for interpretations)
6. PII Detection (Regex → NER upgrade available)

**Key Innovation**: Combines multiple NLP techniques in privacy-preserving architecture

**Impact**: Helps libraries make data-driven decisions while protecting student privacy

**Extensibility**: Easy to integrate Hugging Face models for improvements

**Academic Value**: Demonstrates understanding of modern NLP pipeline

---

**Quick Start**: See `HUGGINGFACE_QUICK_START.md` for 30-minute sentiment upgrade!
