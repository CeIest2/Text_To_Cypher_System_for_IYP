import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

load_dotenv()

lf = Langfuse()
lf_handler = CallbackHandler()

def get_llm(mode: str = "smart") -> ChatGoogleGenerativeAI:
    """Factory to load the requested Gemini model."""
    configs = {
        "fast": {"model": "gemini-2.5-flash-lite", "temp": 0.0},
        "smart": {"model": "gemini-2.5-flash", "temp": 0.2},
        "reasoning": {"model": "gemini-2.0-flash-thinking-exp", "temp": 0.0},
        "report": {"model": "gemini-3-pro-preview", "temp": 0.3}
    }
    cfg = configs.get(mode, configs["smart"])
    
    return ChatGoogleGenerativeAI(
        model=cfg["model"],
        temperature=cfg["temp"],
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

def ask_structured(llm: ChatGoogleGenerativeAI, prompt_name: str, variables: dict, output_schema):
    prompt = lf.get_prompt(prompt_name).get_langchain_prompt()
    chain = prompt | llm.with_structured_output(output_schema)
    return chain.invoke(variables, config={"callbacks": [lf_handler]})


if __name__ == "__main__":
    from pydantic import BaseModel, Field
    
    class TestResponse(BaseModel):
        translated_text: str = Field(description="The text translated to French")

    test_llm = get_llm("fast")
    print("Testing Langfuse Prompt + Structured Output...")
    
    try:
        result = ask_structured(
            llm=test_llm,
            prompt_name="test_translator", 
            variables={"text": "Hello, how are you?"},
            output_schema=TestResponse
        )
        print(f"✅ Success! Translation: {result.translated_text}")
    except Exception as e:
        print(f"❌ Error: Make sure 'test_translator' exists in Langfuse UI. Details: {e}")