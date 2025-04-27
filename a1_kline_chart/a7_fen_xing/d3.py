from google import genai
import os

person_api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=person_api_key)

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=["今天星期几？"]
)
print(response.text)