import json
import os
import uuid
from glob import glob
from app.llm_client import LlamaEdgeClient
from app.vector_store import QdrantStore
import logging

PROJECT_COLLECTION = "project_examples"
ERROR_COLLECTION = "error_examples"
PROJECT_DATA_PATH = "data/project_examples/*.json"
ERROR_DATA_PATH = "data/error_examples/*.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_examples(vector_store, llm_client, collection_name, file_pattern, text_key):
    """Load examples into vector database"""
    # Ensure collections exist
    vector_store.create_collection(collection_name)
    
    example_files = glob(file_pattern)
    
    # Collect all embeddings and metadata first
    embeddings = []
    metadata = []
    
    for file_path in example_files:
        with open(file_path, 'r') as f:
            example = json.load(f)
        
        # Get embedding for query or error
        try:
            embedding = llm_client.get_embeddings([example[text_key]])[0]
            embeddings.append(embedding)
            metadata.append(example)
            logger.info(f"Loaded {collection_name[:-1]} example: {example[text_key][:50]}...")
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
    
    # Insert all documents in a single batch
    if embeddings:
        vector_store.insert_documents(collection_name, embeddings, metadata)

def load_project_examples():
    """Load project examples into vector database"""
    vector_store = QdrantStore()
    llm_client = LlamaEdgeClient()
    
    load_examples(vector_store, llm_client, PROJECT_COLLECTION, PROJECT_DATA_PATH, "query")

def load_error_examples():
    """Load compiler error examples into vector database"""
    vector_store = QdrantStore()
    llm_client = LlamaEdgeClient()
    
    load_examples(vector_store, llm_client, ERROR_COLLECTION, ERROR_DATA_PATH, "error")

def load_conversion_examples():
    """Load Python → Rust conversion examples into vector database."""
    from pathlib import Path
    
    logger.info("Loading conversion examples...")
    
    vector_store = QdrantStore()
    llm_client = LlamaEdgeClient()
    
    # Create collection if it doesn't exist
    try:
        vector_store.create_collection("conversion_examples")
    except Exception as e:
        logger.info(f"Collection might already exist: {e}")
    
    # Check if already loaded
    count = vector_store.count("conversion_examples")
    if count > 0:
        logger.info(f"Conversion examples already loaded ({count} items)")
        return
    
    # Load from data/conversion_examples/python_to_rust/
    examples_dir = Path("data/conversion_examples/python_to_rust")
    
    if not examples_dir.exists():
        logger.warning(f"{examples_dir} not found, skipping conversion examples")
        return
    
    json_files = list(examples_dir.glob("*.json"))
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                example = json.load(f)
            
            # Use python_code as embedding query
            query_text = example.get("python_code", "")
            if not query_text:
                continue
            
            # Generate embedding
            embeddings = llm_client.get_embeddings([query_text])
            if embeddings and len(embeddings) > 0:
                # Format example for storage
                example_text = f"""Python Code:
{example.get('python_code', '')}

Rust Code:
{example.get('rust_code', '')}

Explanation:
{example.get('explanation', '')}

Patterns: {', '.join(example.get('patterns', []))}
"""
                
                # Add to vector store
                vector_store.add_item(
                    "conversion_examples",
                    embeddings[0],
                    {"example": example_text, **example}
                )
                
                logger.info(f"  Loaded: {json_file.name}")
        
        except Exception as e:
            logger.error(f"  Error loading {json_file.name}: {e}")
    
    final_count = vector_store.count("conversion_examples")
    logger.info(f"Loaded {final_count} conversion examples")


if __name__ == "__main__":
    load_project_examples()
    load_error_examples()
    load_conversion_examples()
