import os
from openai import OpenAI


person_api_key = os.environ.get("OPENAI_API_KEY")
print("person_api_key: ", person_api_key)


client = OpenAI()

response = client.responses.create(
    model="gpt-4o",
    input="Write a one-sentence bedtime story about a unicorn."
)

print(response.output_text)
