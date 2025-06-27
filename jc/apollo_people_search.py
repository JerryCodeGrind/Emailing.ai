import os
import requests
import json

APOLLO_API_KEY = os.getenv('APOLLO_API_KEY')
API_URL = 'https://api.apollo.io/api/v1/mixed_people/search'


def people_search(
    person_titles=None,
    include_similar_titles=True,
    person_locations=None,
    person_seniorities=None,
    organization_locations=None,
    q_organization_domains_list=None,
    contact_email_status=None,
    organization_ids=None,
    organization_num_employees_ranges=None,
    q_keywords=None,
    page=1,
    per_page=10
):
    if not APOLLO_API_KEY:
        raise ValueError('APOLLO_API_KEY environment variable not set.')

    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'X-Api-Key': APOLLO_API_KEY
    }

    payload = {
        'page': page,
        'per_page': per_page,
        'include_similar_titles': include_similar_titles
    }
    if person_titles:
        payload['person_titles'] = person_titles
    if person_locations:
        payload['person_locations'] = person_locations
    if person_seniorities:
        payload['person_seniorities'] = person_seniorities
    if organization_locations:
        payload['organization_locations'] = organization_locations
    if q_organization_domains_list:
        payload['q_organization_domains_list'] = q_organization_domains_list
    if contact_email_status:
        payload['contact_email_status'] = contact_email_status
    if organization_ids:
        payload['organization_ids'] = organization_ids
    if organization_num_employees_ranges:
        payload['organization_num_employees_ranges'] = organization_num_employees_ranges
    if q_keywords:
        payload['q_keywords'] = q_keywords

    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        print(f"Error: {response.status_code} {response.text}")
        return None
    return response.json()


def print_contacts(data):
    contacts = data.get('contacts', [])
    if not contacts:
        print('No contacts found.')
        return
    print(f"Found {len(contacts)} contacts:")
    for i, c in enumerate(contacts, 1):
        print(f"{i}. {c.get('name')} | {c.get('title')} | {c.get('organization_name')}")
        print(f"   Email: {c.get('email')}")
        print(f"   LinkedIn: {c.get('linkedin_url')}")
        print(f"   Location: {c.get('city')}, {c.get('state')}, {c.get('country')}")
        print(f"   Phone: {c.get('sanitized_phone')}")
        print()


def main():
    print('Apollo People Search')
    print('Enter search filters (leave blank to skip):')
    titles = input('Job titles (comma separated): ').strip()
    locations = input('Person locations (comma separated): ').strip()
    seniorities = input('Person seniorities (comma separated, e.g. manager, director, c_suite): ').strip()
    org_domains = input('Organization domains (comma separated, e.g. apollo.io): ').strip()
    keywords = input('Keywords: ').strip()
    per_page = input('Results per page (default 10): ').strip()

    data = people_search(
        person_titles=[t.strip() for t in titles.split(',')] if titles else None,
        person_locations=[l.strip() for l in locations.split(',')] if locations else None,
        person_seniorities=[s.strip() for s in seniorities.split(',')] if seniorities else None,
        q_organization_domains_list=[d.strip() for d in org_domains.split(',')] if org_domains else None,
        q_keywords=keywords if keywords else None,
        per_page=int(per_page) if per_page.isdigit() else 10
    )
    if data:
        print_contacts(data)


if __name__ == '__main__':
    main() 