import requests
import time
from typing import List, Dict, Optional
import os
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    email: str = ""
    phone: str = ""
    linkedin_url: str = ""
    job_title: str = ""
    company: str = ""
    location: str = ""

class LeadGenerationSystem:
    """
    A system that can find people based on criteria and get their contact info.
    Supports multiple APIs for different use cases.
    """
    
    def __init__(self):
        # API keys from environment variables
        self.apollo_api_key = os.getenv('APOLLO_API_KEY')
        self.hunter_api_key = os.getenv('HUNTER_API_KEY')
        self.clado_api_key = os.getenv('CLADO_API_KEY')
        self.proxycurl_api_key = os.getenv('PROXYCURL_API_KEY')
        
    def search_people_apollo(self, criteria: Dict) -> List[Person]:
        """
        Search for people using Apollo.io API
        
        Args:
            criteria: Dict with search parameters like:
                - job_titles: List of job titles
                - company_names: List of company names
                - locations: List of locations
                - keywords: List of keywords
                - limit: Number of results (default: 25)
        
        Returns:
            List of Person objects with contact information
        """
        if not self.apollo_api_key:
            raise ValueError("Apollo API key not found. Set APOLLO_API_KEY environment variable.")
        
        url = "https://api.apollo.io/v1/mixed_people/search"
        
        headers = {
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json',
            'X-Api-Key': self.apollo_api_key
        }
        
        # Build search payload
        payload = {
            "page": 1,
            "per_page": criteria.get('limit', 25)
        }
        
        # Add search criteria
        if 'job_titles' in criteria:
            payload['person_titles'] = criteria['job_titles']
        if 'company_names' in criteria:
            payload['organization_names'] = criteria['company_names']
        if 'locations' in criteria:
            payload['person_locations'] = criteria['locations']
        if 'keywords' in criteria:
            payload['q_keywords'] = ' '.join(criteria['keywords'])
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            people = []
            
            for person_data in data.get('people', []):
                person = Person(
                    name=person_data.get('name', ''),
                    email=person_data.get('email', ''),
                    phone=person_data.get('phone', ''),
                    linkedin_url=person_data.get('linkedin_url', ''),
                    job_title=person_data.get('title', ''),
                    company=person_data.get('organization', {}).get('name', ''),
                    location=person_data.get('city', '')
                )
                people.append(person)
            
            return people
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Apollo API error: {str(e)}")
    
    def search_people_hunter(self, domain: str, job_title: str = None) -> List[Person]:
        """
        Find people at a specific company domain using Hunter.io
        
        Args:
            domain: Company domain (e.g., "google.com")
            job_title: Optional job title filter
        
        Returns:
            List of Person objects
        """
        if not self.hunter_api_key:
            raise ValueError("Hunter API key not found. Set HUNTER_API_KEY environment variable.")
        
        url = "https://api.hunter.io/v2/domain-search"
        
        params = {
            'domain': domain,
            'api_key': self.hunter_api_key,
            'limit': 25
        }
        
        if job_title:
            params['type'] = 'personal'
            params['seniority'] = job_title
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            people = []
            
            for email_data in data.get('data', {}).get('emails', []):
                person = Person(
                    name=f"{email_data.get('first_name', '')} {email_data.get('last_name', '')}".strip(),
                    email=email_data.get('value', ''),
                    job_title=email_data.get('position', ''),
                    company=data.get('data', {}).get('organization', ''),
                    linkedin_url=email_data.get('linkedin', '')
                )
                people.append(person)
            
            return people
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Hunter API error: {str(e)}")
    
    def enrich_with_clado(self, people: List[Person]) -> List[Person]:
        """
        Enrich existing people data with more contact info using Clado
        
        Args:
            people: List of Person objects with LinkedIn URLs or emails
        
        Returns:
            Enhanced List of Person objects
        """
        if not self.clado_api_key:
            print("Warning: Clado API key not found. Skipping enrichment.")
            return people
        
        headers = {
            "Authorization": f"Bearer {self.clado_api_key}",
            "Content-Type": "application/json"
        }
        
        enriched_people = []
        
        for person in people:
            try:
                # Try to enrich with LinkedIn URL first
                if person.linkedin_url:
                    params = {'linkedin_url': person.linkedin_url}
                elif person.email:
                    params = {'email': person.email}
                else:
                    enriched_people.append(person)
                    continue
                
                response = requests.get(
                    "https://search.clado.ai/api/enrich/contacts",
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    contacts = data.get('data', [{}])[0].get('contacts', [])
                    
                    # Update person with new contact info
                    for contact in contacts:
                        if contact['type'] == 'email' and not person.email:
                            person.email = contact['value']
                        elif contact['type'] == 'phone' and not person.phone:
                            person.phone = contact['value']
                
                enriched_people.append(person)
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"Error enriching {person.name}: {e}")
                enriched_people.append(person)
        
        return enriched_people
    
    def search_by_natural_language(self, query: str) -> List[Person]:
        """
        Parse natural language query and search for people
        
        Args:
            query: Natural language query like "People working in FAANG"
        
        Returns:
            List of Person objects
        """
        query_lower = query.lower()
        people = []
        
        # FAANG companies
        if 'faang' in query_lower:
            faang_companies = ['Meta', 'Apple', 'Amazon', 'Netflix', 'Google']
            criteria = {
                'company_names': faang_companies,
                'limit': 50
            }
            
            if self.apollo_api_key:
                try:
                    people = self.search_people_apollo(criteria)
                except Exception as e:
                    print(f"Apollo search failed: {e}")
            
            # Also try Hunter for each FAANG domain
            faang_domains = ['meta.com', 'apple.com', 'amazon.com', 'netflix.com', 'google.com']
            for domain in faang_domains:
                try:
                    if self.hunter_api_key:
                        domain_people = self.search_people_hunter(domain)
                        people.extend(domain_people)
                except Exception as e:
                    print(f"Hunter search for {domain} failed: {e}")
        
        # Generic job title search
        elif any(title in query_lower for title in ['engineer', 'developer', 'manager', 'director', 'ceo', 'cto']):
            job_titles = []
            if 'engineer' in query_lower or 'developer' in query_lower:
                job_titles = ['Software Engineer', 'Senior Software Engineer', 'Developer']
            elif 'manager' in query_lower:
                job_titles = ['Engineering Manager', 'Product Manager', 'Manager']
            elif 'director' in query_lower:
                job_titles = ['Director', 'Engineering Director']
            elif 'ceo' in query_lower:
                job_titles = ['CEO', 'Chief Executive Officer']
            elif 'cto' in query_lower:
                job_titles = ['CTO', 'Chief Technology Officer']
            
            criteria = {
                'job_titles': job_titles,
                'limit': 25
            }
            
            if self.apollo_api_key:
                try:
                    people = self.search_people_apollo(criteria)
                except Exception as e:
                    print(f"Apollo search failed: {e}")
        
        # Enrich results with additional contact info
        if people and self.clado_api_key:
            people = self.enrich_with_clado(people)
        
        return people

def print_people_results(people: List[Person]):
    """Pretty print the search results"""
    if not people:
        print("No people found.")
        return
    
    print(f"\n=== FOUND {len(people)} PEOPLE ===\n")
    
    for i, person in enumerate(people, 1):
        print(f"{i}. {person.name}")
        if person.email:
            print(f"   📧 Email: {person.email}")
        if person.phone:
            print(f"   📱 Phone: {person.phone}")
        if person.job_title:
            print(f"   💼 Title: {person.job_title}")
        if person.company:
            print(f"   🏢 Company: {person.company}")
        if person.location:
            print(f"   📍 Location: {person.location}")
        if person.linkedin_url:
            print(f"   🔗 LinkedIn: {person.linkedin_url}")
        print()

def main():
    """
    Main interactive function
    """
    print("=== Lead Generation System ===")
    print("This system can find people based on your criteria!")
    print("\nRequired API Keys (set as environment variables):")
    print("- APOLLO_API_KEY (for general people search)")
    print("- HUNTER_API_KEY (for company domain search)")
    print("- CLADO_API_KEY (for contact enrichment)")
    print("\nAt least one API key is required to work.\n")
    
    system = LeadGenerationSystem()
    
    # Check available APIs
    available_apis = []
    if system.apollo_api_key:
        available_apis.append("Apollo")
    if system.hunter_api_key:
        available_apis.append("Hunter")
    if system.clado_api_key:
        available_apis.append("Clado")
    
    if not available_apis:
        print("❌ No API keys found! Please set at least one API key as environment variable.")
        return
    
    print(f"✅ Available APIs: {', '.join(available_apis)}")
    
    while True:
        print("\n" + "="*50)
        print("Enter your search criteria:")
        print("Examples:")
        print("- 'People working in FAANG'")
        print("- 'Software engineers at Google'")
        print("- 'CTOs in San Francisco'")
        print("- 'Marketing managers'")
        print("\nOr type 'quit' to exit")
        
        query = input("\nYour search: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not query:
            print("Please enter a search query!")
            continue
        
        try:
            print(f"\n🔍 Searching for: {query}")
            print("Please wait...")
            
            people = system.search_by_natural_language(query)
            print_people_results(people)
            
            if people:
                # Option to export results
                export = input("\nWould you like to export results to CSV? (y/n): ").strip().lower()
                if export == 'y':
                    import csv
                    filename = f"leads_{int(time.time())}.csv"
                    
                    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                        fieldnames = ['name', 'email', 'phone', 'job_title', 'company', 'location', 'linkedin_url']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        
                        writer.writeheader()
                        for person in people:
                            writer.writerow({
                                'name': person.name,
                                'email': person.email,
                                'phone': person.phone,
                                'job_title': person.job_title,
                                'company': person.company,
                                'location': person.location,
                                'linkedin_url': person.linkedin_url
                            })
                    
                    print(f"✅ Results exported to {filename}")
        
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()