import os
import spacy
import pdfplumber
import json
from database import save_extracted_entities, update_document_status, redis_client

# Load spaCy model
# We'll use the smaller model to keep the app lightweight
nlp = spacy.load("en_core_web_sm")

def process_pdf(file_path, document_id):
    """
    Process a PDF file using spaCy to extract entities
    and convert to structured data
    """
    try:
        # Extract text from PDF
        all_entities = []
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                # Process text with spaCy
                doc = nlp(text)
                
                # Extract entities
                page_entities = []
                for ent in doc.ents:
                    entity = {
                        'type': ent.label_,
                        'text': ent.text,
                        'confidence': get_entity_confidence(ent),
                        'page_num': page_num + 1,
                        'position': {
                            'start': ent.start_char,
                            'end': ent.end_char
                        }
                    }
                    page_entities.append(entity)
                
                # Add all entities from this page
                all_entities.extend(page_entities)
                
                # Save in batches to avoid large transactions
                if len(all_entities) >= 100:
                    save_extracted_entities(document_id, all_entities)
                    all_entities = []
                    
                # Use Redis for progress tracking if available
                if redis_client:
                    progress = int((page_num + 1) / len(pdf.pages) * 100)
                    redis_client.set(f"pdf_progress:{document_id}", progress)
        
        # Save any remaining entities
        if all_entities:
            save_extracted_entities(document_id, all_entities)
            
        # Update document status to complete
        update_document_status(document_id, "complete")
        
        # Remove the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # Clear Redis progress key
        if redis_client:
            redis_client.delete(f"pdf_progress:{document_id}")
            
        return True
    except Exception as e:
        print(f"Error processing PDF: {e}")
        update_document_status(document_id, "error")
        
        # Clear Redis progress key
        if redis_client:
            redis_client.delete(f"pdf_progress:{document_id}")
            
        return False

def get_entity_confidence(entity):
    """
    Calculate a confidence score for the entity
    This is a simplified version - in a real app you might use the entity._.score
    or a more sophisticated approach
    """
    # For this POC we'll use a simple heuristic
    # Longer entities tend to be more reliable
    length_factor = min(len(entity.text) / 20, 1.0)
    
    # Some entity types are more reliable than others
    type_factors = {
        'PERSON': 0.9,
        'ORG': 0.85,
        'GPE': 0.9,
        'DATE': 0.95,
        'MONEY': 0.95,
        'PERCENT': 0.95,
        'TIME': 0.9,
        'QUANTITY': 0.85,
        'CARDINAL': 0.7,
        'ORDINAL': 0.8,
        'PRODUCT': 0.7,
        'EVENT': 0.7,
        'WORK_OF_ART': 0.6,
        'LAW': 0.8,
        'LANGUAGE': 0.9,
        'FAC': 0.7,
        'NORP': 0.8,
        'LOC': 0.8
    }
    
    type_factor = type_factors.get(entity.label_, 0.6)
    
    # Combine factors for a confidence score
    confidence = (length_factor * 0.3) + (type_factor * 0.7)
    
    return round(confidence, 2)