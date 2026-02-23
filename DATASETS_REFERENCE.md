# Datasets Reference Guide

A comprehensive reference of publicly available datasets for training sentiment analysis models across different domains.

## Quick Reference Table

| Dataset | Domain | Size | Format | License | Best For |
|---------|--------|------|--------|---------|----------|
| Amazon Reviews | E-commerce | 130M+ | JSON | Free | Product sentiment |
| MIMIC-III | Healthcare | 2M+ notes | CSV | Credentialed | Medical triage |
| Twitter Sentiment140 | Social Media | 1.6M | CSV | Free | Brand monitoring |
| Glassdoor Reviews | HR/Employment | 67k | CSV | Academic use | Employee feedback |
| GitHub Issues | Software Dev | Billions | JSON | Public | Bug/feature triage |
| CFPB Complaints | Finance | 3M+ | JSON | Public | Banking issues |
| Yelp Dataset | Reviews | 8M | JSON | Free | Business reviews |
| Reddit Comments | General | Billions | JSON | Free | Community sentiment |
| Stack Overflow | Education/Tech | 10M+ | XML | CC BY-SA | Technical Q&A |
| IMDB Reviews | General | 50k | Text | Free | Binary sentiment |

---

## Healthcare & Medical Datasets

### 1. MIMIC-III Clinical Database
- **Description**: De-identified health data from ICU patients
- **Size**: 2+ million clinical notes, 58,000+ hospital admissions
- **Access**: Requires CITI training certification
- **URL**: https://physionet.org/content/mimiciii/
- **Use Cases**: Patient feedback triage, symptom classification
- **Format**: CSV files with clinical notes
- **License**: PhysioNet Credentialed Health Data License

### 2. MedDialog Dataset
- **Description**: Doctor-patient conversation transcripts
- **Size**: 3.66 million conversations
- **Access**: Public GitHub repository
- **URL**: https://github.com/UCSD-AI4H/Medical-Dialogue-System
- **Use Cases**: Medical question answering, intent classification
- **Format**: JSON with dialogue turns
- **License**: Research use

### 3. Drug Reviews (Drugs.com)
- **Description**: Patient reviews and ratings of medications
- **Size**: 215,000+ reviews
- **Access**: UCI Machine Learning Repository
- **URL**: https://archive.ics.uci.edu/ml/datasets/Drug+Review+Dataset+%28Drugs.com%29
- **Use Cases**: Adverse reaction detection, treatment effectiveness
- **Format**: TSV with ratings and text
- **License**: CC BY 4.0

### 4. PubMed Abstracts
- **Description**: Medical literature abstracts
- **Size**: 30+ million abstracts
- **Access**: Public via NCBI API
- **URL**: https://pubmed.ncbi.nlm.nih.gov/
- **Use Cases**: Medical terminology, clinical language models
- **Format**: XML, JSON via API
- **License**: Public domain

---

## Financial Services Datasets

### 1. Consumer Financial Protection Bureau (CFPB) Complaints
- **Description**: Consumer complaints about financial products
- **Size**: 3+ million complaints
- **Access**: Public API and downloads
- **URL**: https://www.consumerfinance.gov/data-research/consumer-complaints/
- **Use Cases**: Banking complaint classification, fraud detection
- **Format**: JSON, CSV
- **License**: Public domain

### 2. Financial PhraseBank
- **Description**: Financial news sentences with sentiment annotations
- **Size**: 4,840 sentences from financial news
- **Access**: ResearchGate
- **URL**: https://www.researchgate.net/publication/251231364_FinancialPhraseBank-v10
- **Use Cases**: Financial sentiment analysis, investment queries
- **Format**: Text files
- **License**: Creative Commons

### 3. Twitter Financial News Sentiment
- **Description**: Tweets about stocks and companies with sentiment
- **Size**: 11,000+ tweets
- **Access**: Kaggle
- **URL**: https://www.kaggle.com/datasets/sulphatet/twitter-financial-news
- **Use Cases**: Real-time financial sentiment, market analysis
- **Format**: CSV
- **License**: CC0: Public Domain

### 4. SEC EDGAR Filings
- **Description**: Public company financial reports
- **Size**: Millions of filings
- **Access**: Public SEC API
- **URL**: https://www.sec.gov/edgar/searchedgar/companysearch.html
- **Use Cases**: Financial document analysis, risk assessment
- **Format**: HTML, XML
- **License**: Public domain

---

## Education & Learning Datasets

### 1. Stack Overflow Questions
- **Description**: Programming questions and answers
- **Size**: 10+ million questions
- **Access**: Stack Exchange Data Dump
- **URL**: https://archive.org/details/stackexchange
- **Use Cases**: Technical question classification, educational support
- **Format**: XML
- **License**: CC BY-SA 4.0

### 2. EdX Discussion Forums
- **Description**: Student discussions from online courses
- **Size**: 290,000+ posts
- **Access**: Stanford SNAP
- **URL**: http://snap.stanford.edu/data/
- **Use Cases**: Student inquiry routing, learning analytics
- **Format**: JSON
- **License**: Academic research

### 3. Coursera Course Reviews
- **Description**: Student reviews and feedback on courses
- **Size**: Varies (requires scraping with permission)
- **Access**: Coursera API (restricted)
- **Use Cases**: Course evaluation analysis, feedback classification
- **Format**: JSON via API
- **License**: Restricted

---

## Social Media Datasets

### 1. Twitter Sentiment140
- **Description**: Tweets annotated with sentiment (positive/negative)
- **Size**: 1.6 million tweets
- **Access**: Kaggle
- **URL**: https://www.kaggle.com/datasets/kazanova/sentiment140
- **Use Cases**: Brand monitoring, crisis detection
- **Format**: CSV
- **License**: Free for research

### 2. Reddit Comments Corpus
- **Description**: Reddit comments from all subreddits
- **Size**: Billions of comments (2005-present)
- **Access**: Pushshift API, Academic Torrents
- **URL**: https://files.pushshift.io/reddit/
- **Use Cases**: Community sentiment, discussion analysis
- **Format**: JSONL (compressed)
- **License**: Research use

### 3. YouTube Comments Dataset
- **Description**: Comments from YouTube videos
- **Size**: Varies by collection
- **Access**: YouTube Data API (quota limits)
- **URL**: https://developers.google.com/youtube/v3
- **Use Cases**: Video feedback analysis, content moderation
- **Format**: JSON via API
- **License**: Google API Terms

---

## E-commerce & Retail Datasets

### 1. Amazon Customer Reviews
- **Description**: Product reviews across all categories
- **Size**: 130+ million reviews
- **Access**: AWS Open Data Registry
- **URL**: https://s3.amazonaws.com/amazon-reviews-pds/readme.html
- **Use Cases**: Product review classification, quality complaints
- **Format**: TSV, Parquet
- **License**: Free for research and commercial use

### 2. Yelp Open Dataset
- **Description**: Business reviews, user data, and check-ins
- **Size**: 8 million reviews, 200k+ businesses
- **Access**: Yelp Dataset Challenge
- **URL**: https://www.yelp.com/dataset
- **Use Cases**: Restaurant/business review analysis, local sentiment
- **Format**: JSON
- **License**: Academic use only

### 3. Best Buy Product Reviews
- **Description**: Electronics product reviews
- **Size**: Varies (requires web scraping)
- **Access**: Best Buy API (restricted)
- **Use Cases**: Electronics product sentiment
- **Format**: JSON
- **License**: Restricted

---

## Legal & Compliance Datasets

### 1. CaseHOLD (Case Holdings on Legal Decisions)
- **Description**: Legal case citations and holdings
- **Size**: 53,000+ cases
- **Access**: GitHub
- **URL**: https://github.com/reglab/casehold
- **Use Cases**: Legal question classification, case analysis
- **Format**: JSON
- **License**: Open source

### 2. Multi-Legal Pile
- **Description**: Large corpus of legal documents
- **Size**: 256GB of legal text
- **Access**: HuggingFace Datasets
- **URL**: https://huggingface.co/datasets/pile-of-law/pile-of-law
- **Use Cases**: Legal language models, compliance analysis
- **Format**: JSON
- **License**: Research use

### 3. EU GDPR Guidelines
- **Description**: Privacy and data protection documentation
- **Size**: Regulatory documents
- **Access**: Official EU websites
- **URL**: https://gdpr.eu/
- **Use Cases**: Compliance inquiry classification
- **Format**: HTML, PDF
- **License**: Public domain

---

## Human Resources Datasets

### 1. Glassdoor Company Reviews
- **Description**: Employee reviews of companies
- **Size**: 67,000+ reviews
- **Access**: Kaggle
- **URL**: https://www.kaggle.com/datasets/davidgauthier/glassdoor-job-reviews
- **Use Cases**: Employee feedback analysis, HR complaint detection
- **Format**: CSV
- **License**: CC0: Public Domain

### 2. Indeed Job Reviews
- **Description**: Employer and job reviews
- **Size**: Varies (requires scraping)
- **Access**: Web scraping (check terms of service)
- **Use Cases**: Workplace sentiment, culture analysis
- **Format**: HTML
- **License**: Restricted

---

## General Sentiment Analysis Datasets

### 1. Stanford Sentiment Treebank (SST)
- **Description**: Movie reviews with fine-grained sentiment labels
- **Size**: 11,855 sentences
- **Access**: Stanford NLP
- **URL**: https://nlp.stanford.edu/sentiment/
- **Use Cases**: Baseline sentiment model training
- **Format**: Text files
- **License**: Research use

### 2. IMDB Movie Reviews
- **Description**: Binary sentiment classification (positive/negative)
- **Size**: 50,000 reviews
- **Access**: Stanford AI Lab
- **URL**: https://ai.stanford.edu/~amaas/data/sentiment/
- **Use Cases**: Binary sentiment training, general classification
- **Format**: Text files
- **License**: Free for research

### 3. Sentiment140 (Twitter)
- **Description**: Tweets with emoticon-based labels
- **Size**: 1.6 million tweets
- **Access**: Kaggle
- **URL**: https://www.kaggle.com/datasets/kazanova/sentiment140
- **Use Cases**: Short-form text sentiment, social media
- **Format**: CSV
- **License**: Research use

---

## Specialized Datasets

### 1. Mental Health (Reddit)
- **Description**: Posts from mental health subreddits
- **Size**: Millions of posts
- **Access**: Pushshift API
- **URL**: https://pushshift.io/
- **Use Cases**: Mental health support classification ⚠️ *Sensitive*
- **Format**: JSON
- **License**: Research use with ethical considerations

### 2. Crisis Text Line Data
- **Description**: De-identified crisis conversation data
- **Size**: Limited public release
- **Access**: Research partnerships only
- **URL**: https://www.crisistextline.org/crisis-trends/
- **Use Cases**: Crisis detection, support routing ⚠️ *High sensitivity*
- **Format**: Aggregated statistics
- **License**: Highly restricted

### 3. Government 311 Service Requests
- **Description**: Citizen service requests and complaints
- **Size**: Millions of requests (varies by city)
- **Access**: City open data portals
- **URLs**: 
  - NYC: https://data.cityofnewyork.us/
  - Chicago: https://data.cityofchicago.org/
  - Boston: https://data.boston.gov/
- **Use Cases**: Public service triage, infrastructure complaints
- **Format**: CSV, JSON
- **License**: Open data

---

## Data Collection Best Practices

### Ethical Considerations
1. **Privacy**: Always de-identify personal information
2. **Consent**: Ensure data collection complies with terms of service
3. **Bias**: Be aware of demographic and language biases in datasets
4. **Sensitivity**: Extra care for medical, mental health, and legal data

### Data Quality Checklist
- [ ] Balanced class distribution
- [ ] Representative sample of use cases
- [ ] Proper train/validation/test split (70/15/15 or 80/10/10)
- [ ] De-duplicated entries
- [ ] Cleaned and normalized text
- [ ] Consistent annotation guidelines
- [ ] Inter-annotator agreement measured (if manual labels)

### Annotation Guidelines
1. **Clear Definitions**: Document what each label means
2. **Edge Cases**: Define how to handle ambiguous cases
3. **Multiple Annotators**: Use at least 2-3 annotators per sample
4. **Gold Standard**: Create reference examples
5. **Regular Calibration**: Periodic consistency checks

---

## Data Augmentation Techniques

### 1. Back Translation
Translate to another language and back to increase diversity:
```python
# English → German → English
"This product is broken" → "Dieses Produkt ist kaputt" → "This product is broken"
```

### 2. Synonym Replacement
Replace words with synonyms:
```python
"This is terrible" → "This is awful"
"Not working" → "Not functioning"
```

### 3. Paraphrasing with GPT
Use language models to rephrase:
```python
Original: "How do I reset my password?"
Augmented: "What's the process for password reset?"
```

### 4. Adding Noise
Simulate typos and variations:
```python
"broken" → "borken", "brokn", "brkn"
```

---

## Pre-trained Models by Domain

### General Purpose
- **DistilBERT**: `distilbert-base-uncased-finetuned-sst-2-english`
- **RoBERTa**: `cardiffnlp/twitter-roberta-base-sentiment`
- **BERT**: `bert-base-uncased`

### Domain-Specific
- **Finance**: `ProsusAI/finbert`, `yiyanghkust/finbert-tone`
- **Healthcare**: `emilyalsentzer/Bio_ClinicalBERT`
- **Legal**: `nlpaueb/legal-bert-base-uncased`
- **Customer Service**: `cardiffnlp/twitter-roberta-base-sentiment-latest`

### Multilingual
- **mBERT**: `bert-base-multilingual-cased`
- **XLM-RoBERTa**: `xlm-roberta-base`

---

## Dataset Licensing Summary

| License Type | Can Use For | Restrictions |
|--------------|-------------|--------------|
| Public Domain | Commercial, Research | None |
| CC0 | Commercial, Research | None |
| CC BY | Commercial, Research | Attribution required |
| CC BY-SA | Commercial, Research | Share-alike required |
| Academic Only | Research | No commercial use |
| API Terms | Per ToS | Rate limits, restrictions |
| Credentialed | Research (with approval) | Ethics training, approval needed |

---

## Additional Resources

### Dataset Repositories
- **Kaggle**: https://www.kaggle.com/datasets
- **HuggingFace Datasets**: https://huggingface.co/datasets
- **UCI ML Repository**: https://archive.ics.uci.edu/ml/
- **Google Dataset Search**: https://datasetsearch.research.google.com/
- **Papers with Code**: https://paperswithcode.com/datasets
- **AWS Open Data**: https://registry.opendata.aws/

### Tools for Data Collection
- **Scrapy**: Web scraping framework
- **Beautiful Soup**: HTML parsing
- **Selenium**: Browser automation
- **PRAW**: Reddit API wrapper
- **Tweepy**: Twitter API wrapper
- **Pushshift**: Reddit archive API

### Annotation Tools
- **Label Studio**: https://labelstud.io/
- **Prodigy**: https://prodi.gy/
- **Doccano**: https://github.com/doccano/doccano
- **Amazon Mechanical Turk**: https://www.mturk.com/
- **Scale AI**: https://scale.com/

---

## Next Steps

1. **Choose Your Domain**: Select the most relevant niche use case
2. **Find Datasets**: Use this guide to locate appropriate data
3. **Prepare Data**: Clean, label, and format for training
4. **Adapt Model**: Fine-tune using domain-specific data
5. **Evaluate**: Test on held-out validation set
6. **Deploy**: Integrate into the sentiment analysis application
7. **Monitor**: Track performance and collect feedback

For implementation details, see [NICHE_USE_CASES.md](NICHE_USE_CASES.md) and the main [README.md](README.md).

---

**Last Updated**: February 2026  
**Version**: 1.0  
**Maintained by**: Sinbad Adjuik
