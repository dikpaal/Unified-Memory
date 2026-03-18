import json
from google import genai
from google.genai import types
from typing import List
from backend.prompts.prompts import SYSTEM_PROMPT_SUMMARIZE_CONVERSATION_GEMINI, SYSTEM_PROMPT_GENERATE_MEMORY_GEMINI, SYSTEM_PROMPT_COMPARE_MEMORY_FOR_UPDATE
from pydantic import BaseModel

from backend.models.models import Summary, Memory, Memories
from backend.db.kv_store import KVStore

class Gemini:
    """
    Uses Gemini to generate summary and memory
    """
    
    def __init__(self) -> None:
        self.client = genai.Client()

    def summarize(self, messages) -> str:
        
        formatted_messages = self._format_conversation(messages=messages)
        
        response = self.client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=formatted_messages,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT_SUMMARIZE_CONVERSATION_GEMINI,
                max_output_tokens=1024,
                temperature=0.0,
                response_mime_type='application/json',
                response_schema=Summary,
            ),
        )
        raw_summary = response.candidates[0].content.parts[0].text
        cleaned_summary = json.loads(raw_summary)

        return cleaned_summary.get('summary', '')

    def generate_memories(self, messages) -> List[str]:

        formatted_messages = self._format_conversation(messages=messages)

        response = self.client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=formatted_messages,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT_GENERATE_MEMORY_GEMINI,
                max_output_tokens=2000,
                temperature=0.0,
                response_mime_type='application/json',
                response_schema=Memories,
            ),
        )
        raw_memories = response.candidates[0].content.parts[0].text
        cleaned_memories = json.loads(raw_memories)

        return cleaned_memories.get('memories', '')

    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for text using Google's embedding model
        """

        response = self.client.models.embed_content(
            model='gemini-embedding-2-preview',
            contents=text
        )

        return response.embeddings[0].values
    
    def remove_memories_already_present_in_database(self, kv_store: KVStore, memories: List[str]) -> List[str]:
        """
        Remove memories from `memories` that are already present in database
        """
        
        updated_memories = []
        
        for memory in memories:
            embedding = self.embed_text(memory)
            
            # don't add if similar memory exists
            retrieved_memory = kv_store.perform_vector_search(embedding=embedding, top_k=1, threshold=0.9)
            
            if retrieved_memory:
                continue
            
            updated_memories.append(memory)
        
        return updated_memories    
    
    def update_memories(self, new_memories: List[str], memories: List[str]) -> List[str]:
        """
        Compares `new_memories` with `memories` and outputs updated memories
        """

        formatted_memories = self._format_memories(new_memories=new_memories, memories=memories)
        response = self.client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=formatted_memories,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT_COMPARE_MEMORY_FOR_UPDATE,
                max_output_tokens=4000,
                temperature=0.5,
                response_mime_type='application/json',
                response_schema=Memories,
            ),
        )

        raw_memory = response.candidates[0].content.parts[0].text
        cleaned_memory = json.loads(raw_memory)

        return cleaned_memory.get('memories', '')

    def _format_memories(self, new_memories, memories) -> str:

        """
        Formats the memories in a single string
        """

        final_memories = 'NEW MEMORIES:'
        for new_mem in new_memories:
            final_memories += f'\n- {new_mem}'

        final_memories += '\n\nEXISTING MEMORIES:'
        for memory in memories:
            final_memories += f'\n- {memory}'

        return final_memories
        
    
    def _format_conversation(self, messages) -> str:
        
        """
        Formats the conversation history in a single string
        """
        
        
        final_conversation_history = ""
        
        for message in messages:
            final_conversation_history += f'\n{message['role']}: {message['content']}\n'
        
        return final_conversation_history
        
    def close_client(self) -> None:
        """
        Close the client to free up resources
        """
        
        self.client.close()
        

if __name__ == "__main__":
    summarizer = Gemini()
    # messages = [
    #     {"role": 'user', "content": 'my name is Dikpaal'},         
    #     {"role": 'assistant', "content": 'Nice to meet you, Dikpaal! 👋\nThat’s a strong name…pretty cool imagery.\nHow can I help you today? 🚀'},
    #     {"role": 'user', "content": 'I love python'},         
    #     {"role": 'assistant', "content": '🚀'}
    # ]
    
    # print(type(summarizer.generate_memories(messages)[0]))
    
    import numpy as np
    
    embedding_1 = summarizer.embed_text("User is straight")
    embedding_2 = summarizer.embed_text("User likes cats")
    embedding_3 = summarizer.embed_text("User is insightful")
    embedding_4 = summarizer.embed_text("User is deep")
    
    new_embedding = summarizer.embed_text("User dislikes cats")
    
    print(np.dot(new_embedding, embedding_2) / (np.linalg.norm(new_embedding) * np.linalg.norm(embedding_2)))