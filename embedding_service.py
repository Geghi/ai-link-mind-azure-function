import logging
import uuid
from openai_service import get_embedding
from scraped_pages_service import insert_text_chunk_with_embedding
from pinecone_service import PineconeService

def process_and_embed_text(scraped_page_id: str, user_id: str, page_text_content: str, task_id: str, url: str) -> None:
    """
    Processes text content by chunking it, generating embeddings, and storing them.

    Args:
        scraped_page_id (str): The ID of the scraped page.
        user_id (str): The ID of the user associated with the content.
        page_text_content (str): The extracted text content of the page.
        task_id (str): The ID of the scraping task.
        url (str): The URL of the page being processed.
    """
    logging.info(f"Starting chunking and embedding for {url}.")

    # Simple chunking for demonstration. A more robust solution would handle sentence boundaries, etc.
    chunk_size = 500 # words
    overlap_size = 100 # words
    words = page_text_content.split()
    
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += (chunk_size - overlap_size)
        # Ensure we don't go past the end if overlap makes us
        if i >= len(words) and (len(words) - (i - (chunk_size - overlap_size))) < chunk_size:
            break

    pinecone_service = PineconeService()
    vectors_to_upload = []

    for i, chunk in enumerate(chunks):
        try:
            embedding = get_embedding(chunk)
            chunk_id = insert_text_chunk_with_embedding(scraped_page_id, user_id, chunk, embedding) # Pass user_id
            if chunk_id:
                logging.info(f"Inserted chunk {i+1}/{len(chunks)} for {url} into Supabase with chunk_id {chunk_id}.")
                
                vector = {
                    "id": str(chunk_id),
                    "values": embedding,
                    "metadata": {
                        "task_id": task_id,
                        "url": url,
                        "chunk_text": chunk
                    }
                }
                vectors_to_upload.append(vector)
            else:
                logging.error(f"Failed to insert chunk {i+1}/{len(chunks)} for {url} into Supabase.")

        except Exception as e:
            logging.error(f"Error generating or inserting embedding for chunk {i+1} of {url}: {e}", exc_info=True)

    if vectors_to_upload:
        try:
            pinecone_service.upload_vectors(vectors_to_upload)
            logging.info(f"Successfully uploaded {len(vectors_to_upload)} vectors to Pinecone for {url}.")
        except Exception as e:
            logging.error(f"Error uploading vectors to Pinecone for {url}: {e}", exc_info=True)
    
    logging.info(f"Finished chunking and embedding for {url}.")
