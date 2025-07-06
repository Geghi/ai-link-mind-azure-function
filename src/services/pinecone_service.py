import os
from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any
import logging


class PineconeService:
    def __init__(self):
        """
        Initializes the Pinecone service client.
        - Connects to Pinecone using the API key from environment variables.
        - Checks if the specified index exists.
        - If the index does not exist, it creates a new serverless index with cosine similarity
          and a dimension of 1536, suitable for OpenAI's text-embedding-ada-002 model.
        """
        self.api_key = os.environ["PINECONE_API_KEY"]
        self.index_name = os.environ.get("PINECONE_INDEX_NAME", "ai-link-mind")
        
        pc = Pinecone(api_key=self.api_key)
        
        if not pc.has_index(self.index_name):
            pc.create_index(
                name=self.index_name,
                dimension=1536, # OpenAI's text-embedding-ada-002 model dimension
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )

        self.index = pc.Index(self.index_name)

    def upload_vectors(self, vectors: List[Dict[str, Any]]):
        """
        Uploads vectors to the Pinecone index.
        Each vector dictionary should have 'id', 'values', and 'metadata'.
        """
        self.index.upsert(vectors=vectors)
        logging.info(self.index.describe_index_stats())

    def query_vectors(self, query_embedding: List[float], top_k: int = 3, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Queries the Pinecone index with a given embedding and optional metadata filters.

        Args:
            query_embedding (List[float]): The embedding of the query.
            top_k (int): The number of top results to return.
            filters (Dict[str, Any], optional): A dictionary of metadata filters.
                                                E.g., {"task_id": "some_task_id"}. Defaults to None.
        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing the query results.
        """
        return self.index.query(vector=query_embedding, top_k=top_k, include_metadata=True, filter=filters)
