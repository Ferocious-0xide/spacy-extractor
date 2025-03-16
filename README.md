# spaCy PDF Extractor

A lightweight proof of concept application that uses spaCy to extract structured data from PDF documents. The application extracts named entities from PDFs and stores them in a PostgreSQL database.

## Features

- Simple web interface with drag-and-drop PDF uploads
- PDF text extraction using pdfplumber
- Named entity recognition with spaCy
- Structured data storage in PostgreSQL
- Progress tracking with Redis
- Minimal, lightweight design

## Technology Stack

- **Frontend**: HTML, CSS, JavaScript (no framework)
- **Backend**: Flask (Python)
- **NLP**: spaCy with en_core_web_sm model
- **PDF Processing**: pdfplumber
- **Database**: Heroku Postgres
- **Caching/Queue**: Heroku Redis
- **Deployment**: Heroku with Private Space (VPC)

## Project Structure

```
spacy-pdf-extractor/
├── Procfile                # Heroku deployment configuration
├── runtime.txt             # Python runtime specification
├── requirements.txt        # Python dependencies
├── app.py                  # Main Flask application
├── config.py               # Configuration and environment variables
├── pdf_processor.py        # PDF processing and NLP logic
├── database.py             # Database connectivity and queries
├── static/
│   └── css/
│       └── style.css       # Application styling
└── templates/
    ├── index.html          # Home page template
    └── results.html        # Results page template
```

## Deployment to Heroku

### Prerequisites

1. Heroku CLI installed
2. Git installed
3. Heroku account with access to Private Spaces
4. Heroku Postgres and Redis add-ons

### Steps

1. Clone this repository:
   ```
   git clone https://your-repository-url.git
   cd spacy-pdf-extractor
   ```

2. Login to Heroku:
   ```
   heroku login
   ```

3. Create a new Heroku app in your Private Space:
   ```
   heroku create app-name --space your-private-space
   ```

4. Add Heroku Postgres:
   ```
   heroku addons:create heroku-postgresql:hobby-dev
   ```

5. Add Heroku Redis:
   ```
   heroku addons:create heroku-redis:hobby-dev
   ```

6. Set a secret key for the application:
   ```
   heroku config:set SECRET_KEY=your-secure-random-key
   ```

7. Deploy the application:
   ```
   git push heroku main
   ```

8. Download the spaCy model:
   ```
   heroku run python -m spacy download en_core_web_sm
   ```

9. Open the application:
   ```
   heroku open
   ```

## Local Development

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Download the spaCy model:
   ```
   python -m spacy download en_core_web_sm
   ```

4. Create a `.env` file with the following variables:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/database_name
   REDIS_URL=redis://localhost:6379
   SECRET_KEY=development-key
   ```

5. Run the application:
   ```
   python app.py
   ```

## Customization Options

### Using a Different spaCy Model

To use a different spaCy model, modify the `pdf_processor.py` file:

```python
# Change from
nlp = spacy.load("en_core_web_sm")

# To a larger model with more accuracy
nlp = spacy.load("en_core_web_lg")
```

Remember to update `requirements.txt` and install the new model on Heroku.

### Adding Custom Entity Types

To extract custom entity types beyond spaCy's defaults, you can add a custom pipeline component:

```python
# In pdf_processor.py
custom_ner = spacy.blank("en")
# Define custom patterns...
nlp.add_pipe("entity_ruler").add_patterns(custom_patterns)
```

## Limitations and Future Improvements

This POC has several limitations that could be addressed in a production version:

1. No user authentication or multi-tenancy
2. Limited error handling and recovery
3. Basic PDF extraction that may struggle with complex layouts
4. No support for PDF tables or structured forms
5. Limited scalability for very large PDFs
6. No API for programmatic access

Future improvements could include:

1. Batch processing for multiple PDFs
2. Advanced PDF parsing with layout analysis
3. Custom entity training for domain-specific extraction
4. Document classification
5. Full-text search
6. API endpoints for integration
7. UI improvements with asynchronous updates