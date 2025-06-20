# generate_sql.py

from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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")  # 🔁 Replace with your key

def generate_sql_from_nl(prompt, model="deepseek/deepseek-r1-0528:free"):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content
