import requests
import re
from openai import OpenAI
import os

HUNTER_API_KEY = os.getenv('HUNTER_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
API_URL = 'https://api.hunter.io/v2/domain-search'

client = OpenAI(api_key=OPENAI_API_KEY)

def parse_input_with_gpt(user_input):
    prompt = f"""
Extract the company domain and job title (if any) from the following search query.\n\nQuery: \"{user_input}\"\n\nReturn a JSON object with keys 'domain' and 'job_title'. If job title is not specified, set it to null.\n\nExamples:\n- Query: 'Find engineers at google.com'\n  Output: {{"domain": "google.com", "job_title": "engineer"}}\n- Query: 'Show people at netflix.com'\n  Output: {{"domain": "netflix.com", "job_title": null}}\n- Query: 'Find CEO at stripe.com'\n  Output: {{"domain": "stripe.com", "job_title": "CEO"}}\n\nQuery: '{user_input}'\nOutput:
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0
    )
    import json as pyjson
    text = response.choices[0].message.content
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return pyjson.loads(match.group(0))
        return pyjson.loads(text)
    except Exception as e:
        print(f"Could not parse GPT output: {text}")
        return {"domain": None, "job_title": None}

def domain_search(domain, job_title=None, limit=10):
    params = {
        'domain': domain,
        'api_key': HUNTER_API_KEY,
        'limit': limit
    }
    if job_title:
        params['position'] = job_title

    response = requests.get(API_URL, params=params)
    if response.status_code != 200:
        print(f"Error: {response.status_code} {response.text}")
        return None
    return response.json()

def print_people(data):
    emails = data.get('data', {}).get('emails', [])
    if not emails:
        print('No people found.')
        return
    print(f"Found {len(emails)} people:")
    for i, e in enumerate(emails, 1):
        name = f"{e.get('first_name', '')} {e.get('last_name', '')}".strip()
        print(f"{i}. {name} | {e.get('position', '')}")
        print(f"   Email: {e.get('value')}")
        print(f"   LinkedIn: {e.get('linkedin', '')}")
        print()

def main():
    print('Hunter.io Domain Search (with GPT input parsing)')
    user_input = input('Describe your search (e.g. "Find engineers at google.com"): ').strip()
    parsed = parse_input_with_gpt(user_input)
    domain = parsed.get('domain')
    job_title = parsed.get('job_title')
    if not domain:
        print('Could not extract a domain from your input.')
        return
    print(f"Searching for job title: {job_title} at domain: {domain}")
    data = domain_search(domain=domain, job_title=job_title)
    if data:
        print_people(data)

if __name__ == '__main__':
    main() 