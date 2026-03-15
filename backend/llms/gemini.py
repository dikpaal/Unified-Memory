import json
from google import genai
from google.genai import types
from backend.prompts.prompts import SYSTEM_PROMPT_SUMMARIZE_CONVERSATION_GEMINI, SYSTEM_PROMPT_GENERATE_MEMORY_GEMINI
from pydantic import BaseModel

from backend.models.models import Summary, Memories

class GeminiGenerator:
    """
    Given messages from a conversation, generates a summary
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

    def generate_memory(self, messages) -> str:
        
        formatted_messages = self._format_conversation(messages=messages)
        
        response = self.client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=formatted_messages,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT_GENERATE_MEMORY_GEMINI,
                max_output_tokens=1024,
                temperature=0.0,
                response_mime_type='application/json',
                response_schema=Memories,
            ),
        )
        raw_memory = response.candidates[0].content.parts[0].text
        cleaned_memory = json.loads(raw_memory)

        return cleaned_memory.get('memories', '')
        
    
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
        

# if __name__ == "__main__":
#     summarizer = GeminiGenerator()
#     messages = [
#         {"role": 'user', "content": 'my name is Dikpaal'},         
#         {"role": 'assistant', "content": 'Nice to meet you, Dikpaal! 👋\nThat’s a strong name…pretty cool imagery.\nHow can I help you today? 🚀'},
#         {"role": 'user', "content": 'I love python'},         
#         {"role": 'assistant', "content": '🚀'}
#     ]
    
#     print(type(summarizer.generate_memory(messages)))