import azure.functions as func
import logging
import sys
import os
import json

from src.services.pinecone_service import PineconeService
from src.services.openai_service import get_embedding, get_chat_completion, summarize_conversation
from src.services.chat_summary_service import get_chat_summary, upsert_chat_summary
from src.utils import json_response, count_tokens

# Configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger().setLevel(logging.INFO)

# Create a blueprint for RAG functionality
rag_bp = func.Blueprint()

# Define constants for token management
MAX_CONVERSATION_TOKENS = 3000  # Max tokens for the entire conversation history (including summary and RAG context)

@rag_bp.route(route="PerformRAG", auth_level=func.AuthLevel.ANONYMOUS)
def PerformRAG(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure HTTP Trigger function to perform RAG (Retrieval Augmented Generation) with conversation memory.
    Receives a list of messages, manages conversation history (summarizing if needed),
    retrieves relevant information from Pinecone, and generates a response using OpenAI.
    """
    logging.info('PerformRAG HTTP trigger function processed a request.')

    try:
        req_body: dict = req.get_json()
    except ValueError as e:
        logging.error(f"Invalid JSON payload in HTTP request: {e}", exc_info=True)
        return json_response("Please pass a JSON payload in the request body.", 400)

    messages: list[dict] = req_body.get('messages', [])
    task_id: str | None = req_body.get('task_id') # Optional task_id for filtering and summary persistence
    user_id: str | None = req_body.get('user_id') # New: Optional user_id for filtering Pinecone results

    if not messages:
        logging.error("No 'messages' list provided in the request body.")
        return json_response("Please provide a 'messages' list in the request body.", 400)

    current_user_query_message = messages[-1] if messages and messages[-1]['role'] == 'user' else None
    if not current_user_query_message:
        logging.error("Could not extract current user query from messages.")
        return json_response("The last message in the 'messages' list must be the current user query.", 400)
    
    current_user_query = current_user_query_message['content']
    conversation_history = messages[:-1]

    try:
        # 1. Initialize base context with RAG and persistent summary
        final_messages_for_llm: list[dict] = []
        
        # Add RAG context
        query_embedding = get_embedding(current_user_query)
        pinecone_service = PineconeService()
        
        pinecone_filters = {}
        if task_id:
            pinecone_filters["task_id"] = task_id
        
        
        pinecone_results = pinecone_service.query_vectors(query_embedding, top_k=5, filters=pinecone_filters if pinecone_filters else None)
        
        logging.info(f"Pinecone query results: {pinecone_results}")
        
        # Extract chunk_text and url from metadata
        retrieved_contexts = []
        retrieved_urls = set() # Use a set to store unique URLs
        for match in pinecone_results.matches:
            if match.metadata and 'chunk_text' in match.metadata and 'url' in match.metadata:
                retrieved_contexts.append({
                    "text": match.metadata['chunk_text'],
                    "url": match.metadata['url']
                })
                retrieved_urls.add(match.metadata['url'])
        
        if retrieved_contexts:
            rag_context_parts = []
            for item in retrieved_contexts:
                rag_context_parts.append(f"Content: {item['text']}\nSource: {item['url']}")
            rag_context = "\n\n---\n\n".join(rag_context_parts)
            
            system_prompt_content = (
                "Use the following context to answer the user's question. "
                "If you don't know the answer, just say that you don't know, don't try to make up an answer.\n\n"
                "Context:\n"
                f"{rag_context}\n\n"
                "Information retrieved from the provided URLs is publicly accessible. You may directly state any information, "
                "including contact details like email addresses, found within the context.\n\n"
            )
            final_messages_for_llm.append({"role": "system", "content": system_prompt_content})
        else:
            logging.info("No RAG context found for the query.")
            final_messages_for_llm.append({"role": "system", "content": "You are a helpful assistant."})

        # Add persistent summary
        if task_id:
            existing_summary = get_chat_summary(task_id, user_id)
            if existing_summary:
                logging.info(f"Retrieved existing summary for task {task_id}: {existing_summary}")
                final_messages_for_llm.append({"role": "system", "content": f"Previous Conversation Summary: {existing_summary}"})

        # 2. Build conversation history for LLM, ensuring no messages are lost
        managed_conversation_messages: list[dict] = []
        messages_to_summarize: list[dict] = []
        
        # Iterate backwards through history to keep most recent messages
        for message in reversed(conversation_history):
            # Check if adding the next message exceeds the token limit
            potential_messages = final_messages_for_llm + managed_conversation_messages + [message, current_user_query_message]
            if count_tokens(potential_messages) > MAX_CONVERSATION_TOKENS:
                # This message and all older ones must be summarized
                messages_to_summarize.insert(0, message)
            else:
                # This message fits, add it to the managed list
                managed_conversation_messages.insert(0, message)

        # If there are messages that didn't fit, summarize them
        if messages_to_summarize:
            logging.info(f"Summarizing {len(messages_to_summarize)} older messages.")
            new_summary = summarize_conversation(messages_to_summarize)
            if task_id:
                upsert_chat_summary(task_id, new_summary)
            # Add the new summary to the context for the current turn
            final_messages_for_llm.append({"role": "system", "content": f"Conversation Summary: {new_summary}"})

        # 3. Finalize and call LLM
        final_messages_for_llm.extend(managed_conversation_messages)
        final_messages_for_llm.append(current_user_query_message)

        # 4. Get chat completion from OpenAI
        rag_response = get_chat_completion(final_messages_for_llm)
        logging.info(f"Generated RAG response for query: '{current_user_query}' - Response: {rag_response}")

        # 5. Return only the assistant's response
        return json_response({"response": rag_response}, 200)

    except Exception as e:
        logging.error(f"Error performing RAG with conversation memory for query '{current_user_query}': {e}", exc_info=True)
        return json_response(f"An error occurred while processing your request: {e}", 500)
