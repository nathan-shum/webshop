import google.generativeai as genai
import os
import dotenv

dotenv.load_dotenv()

if "GEMINI_API_KEY" in os.environ:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    print("Listing models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
else:
    print("GEMINI_API_KEY not found.")
