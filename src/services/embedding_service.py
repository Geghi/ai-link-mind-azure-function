import logging
from src.services.openai_service import get_embedding
from src.services.pinecone_service import PineconeService
from src.services.vector_service import VectorService

class EmbeddingService:
    """
    A service class for processing and embedding text content.
    """

    def __init__(self):
        self.pinecone_service = PineconeService()
        self.vector_service = VectorService()

    def get_text_chunks(self, text: str) -> list[str]:
        """
        Splits text into chunks of a specified size with overlap.
        """
        chunk_size = 500  # words
        overlap_size = 100  # words
        words = text.split()
        
        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
            i += (chunk_size - overlap_size)
            if i >= len(words) and (len(words) - (i - (chunk_size - overlap_size))) < chunk_size:
                break
        return chunks

    def process_and_embed_text(self, scraped_page_id: str, user_id: str, page_text_content: str, task_id: str, url: str) -> None:
        """
        Processes text content by chunking it, generating embeddings, and storing them.
        """
        logging.info(f"Starting chunking and embedding for {url}.")

        chunks = self.get_text_chunks(page_text_content)
        vectors_to_upload = []

        for i, chunk in enumerate(chunks):
            try:
                embedding = get_embedding(chunk)
                if embedding:
                    chunk_id = self.vector_service.insert_text_chunk_with_embedding(scraped_page_id, user_id, chunk, embedding)
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
                else:
                    logging.error(f"Failed to generate embedding for chunk {i+1}/{len(chunks)} for {url}.")

            except Exception as e:
                logging.error(f"Error processing chunk {i+1} of {url}: {e}", exc_info=True)

        if vectors_to_upload:
            try:
                self.pinecone_service.upload_vectors(vectors_to_upload)
                logging.info(f"Successfully uploaded {len(vectors_to_upload)} vectors to Pinecone for {url}.")
            except Exception as e:
                logging.error(f"Error uploading vectors to Pinecone for {url}: {e}", exc_info=True)
        
        logging.info(f"Finished chunking and embedding for {url}.")
