"""
Full content scraper for ArcGIS JavaScript SDK documentation.
Extracts complete documentation content, not just summaries.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set
import re
from dataclasses import dataclass
from datetime import datetime
import random

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ScrapedDocument:
    """Structure for scraped document data."""
    url: str
    title: str
    doc_type: str  # 'api_reference', 'guide', 'sample'
    content: str
    code_examples: List[str]
    metadata: Dict
    last_scraped: str


class ArcGISDocumentationScraper:
    """Comprehensive scraper for ArcGIS JavaScript SDK documentation."""
    
    def __init__(self):
        self.base_url = "https://developers.arcgis.com/javascript/latest/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.scraped_urls: Set[str] = set()
        self.documents: List[ScrapedDocument] = []
        self.stats = {
            'api_pages': 0,
            'guide_pages': 0,
            'sample_pages': 0,
            'total_content_chars': 0,
            'errors': []
        }
    
    def get_page_content(self, url: str, max_retries: int = 3) -> BeautifulSoup:
        """Fetch and parse page content with retries."""
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching: {url}")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                return soup
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(1, 3))
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    self.stats['errors'].append(f"Failed to fetch {url}: {e}")
                    return None
    
    def extract_api_reference_content(self, soup: BeautifulSoup, url: str) -> ScrapedDocument:
        """Extract full content from API reference pages."""
        
        # Get title
        title_elem = soup.find('h1') or soup.find('title')
        title = title_elem.get_text().strip() if title_elem else "Unknown API"
        
        # Extract main content - look for the main documentation container
        content_selectors = [
            '.main-content',
            '.api-reference-content', 
            '.documentation-content',
            'main',
            '.content'
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            # Fallback: get everything in body but exclude navigation
            main_content = soup.find('body')
            if main_content:
                # Remove navigation, footer, sidebar elements
                for elem in main_content.find_all(['nav', 'footer', 'aside', 'header']):
                    elem.decompose()
                for elem in main_content.find_all(class_=re.compile(r'nav|sidebar|footer|header|menu')):
                    elem.decompose()
        
        # Extract text content
        content_text = ""
        code_examples = []
        
        if main_content:
            # Extract code examples separately
            code_blocks = main_content.find_all(['pre', 'code'])
            for block in code_blocks:
                code_text = block.get_text().strip()
                if len(code_text) > 20:  # Only substantial code blocks
                    code_examples.append(code_text)
            
            # Clean up the content - remove script/style tags
            for elem in main_content.find_all(['script', 'style', 'noscript']):
                elem.decompose()
            
            # Get clean text content
            content_text = main_content.get_text(separator='\n', strip=True)
            
            # Clean up extra whitespace
            content_text = re.sub(r'\n\s*\n', '\n\n', content_text)
            content_text = re.sub(r' +', ' ', content_text)
        
        # Extract metadata
        metadata = {
            'class_name': self.extract_class_name(soup),
            'module_path': self.extract_module_path(soup),
            'since_version': self.extract_since_version(soup),
            'properties_count': len(soup.find_all(text=re.compile(r'Property.*Details', re.I))),
            'methods_count': len(soup.find_all(text=re.compile(r'Method.*Details', re.I))),
            'url_path': url.replace(self.base_url, ''),
            'scraped_at': datetime.now().isoformat()
        }
        
        return ScrapedDocument(
            url=url,
            title=title,
            doc_type='api_reference',
            content=content_text,
            code_examples=code_examples,
            metadata=metadata,
            last_scraped=datetime.now().isoformat()
        )
    
    def extract_sample_content(self, soup: BeautifulSoup, url: str) -> ScrapedDocument:
        """Extract full content from sample pages."""
        
        # Get title
        title_elem = soup.find('h1') or soup.find('title')
        title = title_elem.get_text().strip() if title_elem else "Unknown Sample"
        
        # Look for sample-specific content areas
        content_areas = [
            '.sample-content',
            '.sample-description', 
            '.tutorial-content',
            'main',
            '.content'
        ]
        
        full_content = ""
        code_examples = []
        
        # Try to find the main content area
        main_area = None
        for selector in content_areas:
            main_area = soup.select_one(selector)
            if main_area:
                break
        
        if not main_area:
            main_area = soup.find('body')
        
        if main_area:
            # Remove navigation and non-content elements
            for elem in main_area.find_all(['nav', 'footer', 'aside', 'header']):
                elem.decompose()
            
            # Extract all code examples (JavaScript, HTML, CSS)
            code_selectors = [
                'pre code',
                '.highlight pre',
                '.code-sample',
                '.javascript',
                '.html',
                '.css',
                'pre'
            ]
            
            for selector in code_selectors:
                for code_elem in main_area.select(selector):
                    code_text = code_elem.get_text().strip()
                    if len(code_text) > 50:  # Substantial code blocks
                        code_examples.append(code_text)
            
            # Look for embedded CodePen/JSFiddle links
            iframe_links = main_area.find_all('iframe')
            for iframe in iframe_links:
                src = iframe.get('src', '')
                if 'codepen' in src or 'jsfiddle' in src:
                    code_examples.append(f"Interactive example: {src}")
            
            # Extract description and tutorial text
            description_selectors = [
                '.sample-description',
                '.description',
                '.overview',
                'p',
                '.tutorial-step'
            ]
            
            description_parts = []
            for selector in description_selectors:
                for elem in main_area.select(selector):
                    text = elem.get_text().strip()
                    if len(text) > 30:
                        description_parts.append(text)
            
            full_content = '\n\n'.join(description_parts)
            
            # If we didn't get much content, extract everything
            if len(full_content) < 200:
                for elem in main_area.find_all(['script', 'style']):
                    elem.decompose()
                full_content = main_area.get_text(separator='\n', strip=True)
        
        # Clean up content
        full_content = re.sub(r'\n\s*\n', '\n\n', full_content)
        full_content = re.sub(r' +', ' ', full_content)
        
        metadata = {
            'sample_type': self.extract_sample_type(soup),
            'technologies_used': self.extract_technologies(soup),
            'difficulty_level': self.extract_difficulty(soup),
            'code_examples_count': len(code_examples),
            'url_path': url.replace(self.base_url, ''),
            'scraped_at': datetime.now().isoformat()
        }
        
        return ScrapedDocument(
            url=url,
            title=title,
            doc_type='sample',
            content=full_content,
            code_examples=code_examples,
            metadata=metadata,
            last_scraped=datetime.now().isoformat()
        )
    
    def extract_guide_content(self, soup: BeautifulSoup, url: str) -> ScrapedDocument:
        """Extract full content from guide/tutorial pages."""
        
        # Get title
        title_elem = soup.find('h1') or soup.find('title')
        title = title_elem.get_text().strip() if title_elem else "Unknown Guide"
        
        # Look for guide-specific content
        content_selectors = [
            '.guide-content',
            '.tutorial-content',
            '.documentation-content',
            'article',
            'main',
            '.content'
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.find('body')
        
        full_content = ""
        code_examples = []
        
        if main_content:
            # Remove non-content elements
            for elem in main_content.find_all(['nav', 'footer', 'aside', 'header']):
                elem.decompose()
            
            # Extract code examples
            for code_elem in main_content.find_all(['pre', 'code']):
                code_text = code_elem.get_text().strip()
                if len(code_text) > 30:
                    code_examples.append(code_text)
            
            # Extract step-by-step content
            steps = []
            
            # Look for numbered steps or sections
            step_selectors = [
                '.step',
                '.tutorial-step', 
                'h2', 'h3', 'h4',
                '.section'
            ]
            
            for selector in step_selectors:
                for elem in main_content.select(selector):
                    # Get the element and its following content
                    step_content = []
                    step_content.append(elem.get_text().strip())
                    
                    # Get following paragraphs until next step
                    next_elem = elem.find_next_sibling()
                    while next_elem and next_elem.name not in ['h1', 'h2', 'h3', 'h4']:
                        if next_elem.name in ['p', 'div', 'ul', 'ol']:
                            text = next_elem.get_text().strip()
                            if text:
                                step_content.append(text)
                        next_elem = next_elem.find_next_sibling()
                    
                    if step_content:
                        steps.append('\n'.join(step_content))
            
            # If no structured steps found, get all content
            if not steps:
                for elem in main_content.find_all(['script', 'style']):
                    elem.decompose()
                full_content = main_content.get_text(separator='\n', strip=True)
            else:
                full_content = '\n\n'.join(steps)
        
        # Clean up content
        full_content = re.sub(r'\n\s*\n', '\n\n', full_content)
        full_content = re.sub(r' +', ' ', full_content)
        
        metadata = {
            'guide_type': self.extract_guide_type(soup),
            'prerequisites': self.extract_prerequisites(soup),
            'estimated_time': self.extract_time_estimate(soup),
            'steps_count': len(code_examples),
            'url_path': url.replace(self.base_url, ''),
            'scraped_at': datetime.now().isoformat()
        }
        
        return ScrapedDocument(
            url=url,
            title=title,
            doc_type='guide',
            content=full_content,
            code_examples=code_examples,
            metadata=metadata,
            last_scraped=datetime.now().isoformat()
        )
    
    def discover_api_reference_urls(self) -> List[str]:
        """Discover all API reference page URLs."""
        api_urls = []
        
        # Start with the main API reference page
        api_index_url = urljoin(self.base_url, "api-reference/")
        soup = self.get_page_content(api_index_url)
        
        if soup:
            # Look for links to individual API pages
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/api-reference/' in href and href.endswith('.html'):
                    full_url = urljoin(self.base_url, href)
                    api_urls.append(full_url)
        
        logger.info(f"Discovered {len(api_urls)} API reference URLs")
        return list(set(api_urls))  # Remove duplicates
    
    def discover_sample_urls(self) -> List[str]:
        """Discover all sample page URLs."""
        sample_urls = []
        
        # Start with sample code index
        samples_index_url = urljoin(self.base_url, "sample-code/")
        soup = self.get_page_content(samples_index_url)
        
        if soup:
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/sample-code/' in href and href != '/sample-code/':
                    full_url = urljoin(self.base_url, href)
                    sample_urls.append(full_url)
        
        logger.info(f"Discovered {len(sample_urls)} sample URLs")
        return list(set(sample_urls))
    
    def discover_guide_urls(self) -> List[str]:
        """Discover all guide/tutorial URLs."""
        guide_urls = []
        
        # Common guide sections
        guide_sections = [
            "get-started/",
            "tutorials/", 
            "programming-patterns/",
            "visualization/",
            "maps-2d/",
            "scenes-3d/",
            "layers/",
            "query/",
            "edit/"
        ]
        
        for section in guide_sections:
            section_url = urljoin(self.base_url, section)
            soup = self.get_page_content(section_url)
            
            if soup:
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    # Look for guide-like URLs
                    if any(guide_path in href for guide_path in [
                        '/get-started/', '/tutorials/', '/programming-patterns/',
                        '/visualization/', '/maps-2d/', '/scenes-3d/', '/layers/',
                        '/query/', '/edit/'
                    ]):
                        full_url = urljoin(self.base_url, href)
                        guide_urls.append(full_url)
        
        logger.info(f"Discovered {len(guide_urls)} guide URLs")
        return list(set(guide_urls))
    
    def scrape_all_content(self, max_pages_per_type: int = None) -> Dict:
        """Scrape all documentation content."""
        
        logger.info("Starting comprehensive ArcGIS documentation scraping...")
        
        # Discover all URLs
        api_urls = self.discover_api_reference_urls()
        sample_urls = self.discover_sample_urls()
        guide_urls = self.discover_guide_urls()
        
        # Limit if specified (for testing)
        if max_pages_per_type:
            api_urls = api_urls[:max_pages_per_type]
            sample_urls = sample_urls[:max_pages_per_type]
            guide_urls = guide_urls[:max_pages_per_type]
        
        logger.info(f"Will scrape: {len(api_urls)} API, {len(sample_urls)} samples, {len(guide_urls)} guides")
        
        # Scrape API reference pages
        logger.info("Scraping API reference pages...")
        for url in api_urls:
            if url not in self.scraped_urls:
                soup = self.get_page_content(url)
                if soup:
                    doc = self.extract_api_reference_content(soup, url)
                    self.documents.append(doc)
                    self.stats['api_pages'] += 1
                    self.stats['total_content_chars'] += len(doc.content)
                    self.scraped_urls.add(url)
                    
                    # Rate limiting
                    time.sleep(random.uniform(0.5, 1.5))
        
        # Scrape sample pages
        logger.info("Scraping sample pages...")
        for url in sample_urls:
            if url not in self.scraped_urls:
                soup = self.get_page_content(url)
                if soup:
                    doc = self.extract_sample_content(soup, url)
                    self.documents.append(doc)
                    self.stats['sample_pages'] += 1
                    self.stats['total_content_chars'] += len(doc.content)
                    self.scraped_urls.add(url)
                    
                    time.sleep(random.uniform(0.5, 1.5))
        
        # Scrape guide pages
        logger.info("Scraping guide pages...")
        for url in guide_urls:
            if url not in self.scraped_urls:
                soup = self.get_page_content(url)
                if soup:
                    doc = self.extract_guide_content(soup, url)
                    self.documents.append(doc)
                    self.stats['guide_pages'] += 1
                    self.stats['total_content_chars'] += len(doc.content)
                    self.scraped_urls.add(url)
                    
                    time.sleep(random.uniform(0.5, 1.5))
        
        # Generate summary
        summary = {
            'total_pages': len(self.documents),
            'api_reference_pages': self.stats['api_pages'],
            'guide_pages': self.stats['guide_pages'],
            'sample_pages': self.stats['sample_pages'],
            'total_content_characters': self.stats['total_content_chars'],
            'average_content_length': self.stats['total_content_chars'] // len(self.documents) if self.documents else 0,
            'scrape_date': datetime.now().isoformat(),
            'errors_count': len(self.stats['errors']),
            'errors': self.stats['errors'][:10]  # First 10 errors
        }
        
        logger.info(f"Scraping complete! {summary}")
        return summary
    
    def save_to_json(self, output_dir: str = "data/scraped/"):
        """Save scraped content to JSON files."""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Separate by document type
        api_docs = [doc for doc in self.documents if doc.doc_type == 'api_reference']
        sample_docs = [doc for doc in self.documents if doc.doc_type == 'sample']
        guide_docs = [doc for doc in self.documents if doc.doc_type == 'guide']
        
        # Convert to JSON-serializable format
        def doc_to_dict(doc):
            return {
                'url': doc.url,
                'title': doc.title,
                'doc_type': doc.doc_type,
                'content': doc.content,
                'code_examples': doc.code_examples,
                'metadata': doc.metadata,
                'last_scraped': doc.last_scraped
            }
        
        # Save API reference
        if api_docs:
            api_file = output_path / "api_reference_full.json"
            with open(api_file, 'w', encoding='utf-8') as f:
                json.dump([doc_to_dict(doc) for doc in api_docs], f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(api_docs)} API docs to {api_file}")
        
        # Save samples
        if sample_docs:
            sample_file = output_path / "samples_full.json"
            with open(sample_file, 'w', encoding='utf-8') as f:
                json.dump([doc_to_dict(doc) for doc in sample_docs], f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(sample_docs)} sample docs to {sample_file}")
        
        # Save guides
        if guide_docs:
            guide_file = output_path / "guides_full.json"
            with open(guide_file, 'w', encoding='utf-8') as f:
                json.dump([doc_to_dict(doc) for doc in guide_docs], f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(guide_docs)} guide docs to {guide_file}")
        
        # Save summary
        summary_file = output_path / "scrape_summary_full.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_pages': len(self.documents),
                'api_reference_pages': len(api_docs),
                'guide_pages': len(guide_docs), 
                'sample_pages': len(sample_docs),
                'total_content_chars': self.stats['total_content_chars'],
                'scrape_date': datetime.now().isoformat(),
                'errors': self.stats['errors']
            }, f, indent=2)
        
        logger.info(f"Scraping complete! Files saved to {output_path}")
    
    # Helper methods for metadata extraction
    def extract_class_name(self, soup):
        """Extract class name from API documentation."""
        class_elem = soup.find(text=re.compile(r'class|Class'))
        return class_elem.strip() if class_elem else None
    
    def extract_module_path(self, soup):
        """Extract module import path."""
        import_elem = soup.find('code', text=re.compile(r'@arcgis/core'))
        return import_elem.get_text().strip() if import_elem else None
    
    def extract_since_version(self, soup):
        """Extract 'since version' information."""
        since_elem = soup.find(text=re.compile(r'Since.*ArcGIS.*JavaScript'))
        return since_elem.strip() if since_elem else None
    
    def extract_sample_type(self, soup):
        """Extract sample type/category."""
        # Logic to determine sample type from content
        return "code_sample"
    
    def extract_technologies(self, soup):
        """Extract technologies used in sample."""
        return []
    
    def extract_difficulty(self, soup):
        """Extract difficulty level."""
        return "intermediate"
    
    def extract_guide_type(self, soup):
        """Extract guide type."""
        return "tutorial"
    
    def extract_prerequisites(self, soup):
        """Extract prerequisites."""
        return []
    
    def extract_time_estimate(self, soup):
        """Extract time estimate."""
        return None


def main():
    """Main function to run the scraper."""
    scraper = ArcGISDocumentationScraper()
    
    # Full scraping - no limits
    summary = scraper.scrape_all_content()
    
    # Save results
    scraper.save_to_json()
    
    print("Full content scraping completed!")
    print(f"Total pages: {summary['total_pages']}")
    print(f"Total content: {summary['total_content_characters']:,} characters")
    print(f"Average content length: {summary['average_content_length']:,} characters")


if __name__ == "__main__":
    main()