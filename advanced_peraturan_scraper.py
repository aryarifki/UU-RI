"""
Complete Indonesian Legal Documents Scraper
Scraper lengkap untuk mengunduh SEMUA dokumen PDF dari peraturan.go.id
dengan fitur:
1. Download semua file PDF dari semua kategori peraturan
2. Preservasi nama file asli dari Content-Disposition headers
3. Struktur folder terorganisir berdasarkan jenis/tahun/nomor
4. Crawler untuk menemukan semua halaman dan link PDF
5. Retry mechanism untuk koneksi yang gagal
"""

import asyncio
import aiohttp
import json
import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, quote, unquote
from bs4 import BeautifulSoup
import logging
from typing import Dict, List, Optional, Tuple, Set
import time
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('peraturan_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CompletePeraturanScraper:
    def __init__(self, base_url: str = "https://peraturan.go.id", config_path: str = "config.json"):
        self.base_url = base_url
        self.session = None
        self.config = self.load_config(config_path)
        self.download_count = 0
        self.success_count = 0
        self.error_count = 0
        self.downloaded_files = []
        self.visited_urls: Set[str] = set()
        self.found_pdfs: Set[str] = set()
        self.processed_regulations: Set[str] = set()
        self.max_concurrent = self.config.get("max_concurrent", 10)
        self.request_delay = self.config.get("request_delay", 1.0)
        self.retry_attempts = self.config.get("retry_attempts", 3)
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        default_config = {
            "regulation_types": {
                "UU": "Undang-Undang",
                "PERPPU": "Peraturan Pemerintah Pengganti Undang-Undang", 
                "PP": "Peraturan Pemerintah",
                "PERPRES": "Peraturan Presiden",
                "PERMEN": "Peraturan Menteri",
                "PERDA": "Peraturan Daerah",
                "PERBAN": "Peraturan Bank Indonesia",
                "TAPMPR": "Ketetapan MPR",
                "PERMENKUMHAM": "Peraturan Menteri Hukum dan HAM",
                "PERMENDAGRI": "Peraturan Menteri Dalam Negeri",
                "PERMENKEU": "Peraturan Menteri Keuangan",
                "PERMENKES": "Peraturan Menteri Kesehatan",
                "PERMENDIKBUD": "Peraturan Menteri Pendidikan dan Kebudayaan",
                "PERMENAKER": "Peraturan Menteri Ketenagakerjaan",
                "PERMENAG": "Peraturan Menteri Agama"
            },
            "base_dir": "Peraturan-RI-Complete",
            "demo_mode": False,
            "max_concurrent": 10,
            "request_delay": 1.0,
            "retry_attempts": 3,
            "years_range": list(range(1945, 2026)),  # Dari kemerdekaan sampai sekarang
            "download_all_types": True,
            "follow_pagination": True,
            "crawl_depth": 5
        }
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                default_config.update(loaded_config)
                return default_config
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using default config")
            return default_config
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(
            limit=50, 
            ttl_dns_cache=300, 
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        timeout = aiohttp.ClientTimeout(total=300, connect=60)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'id,en-US;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def extract_filename_from_content_disposition(self, content_disposition: str) -> Optional[str]:
        """
        Extract filename from Content-Disposition header
        Supports both 'filename=' and 'filename*=' formats
        Prioritizes original server filename with minimal sanitization
        """
        if not content_disposition:
            return None
        
        # First try filename*= (RFC 6266 - supports encoded filenames)
        filename_star_match = re.search(r"filename\*=(?:UTF-8'')?([^;]+)", content_disposition)
        if filename_star_match:
            encoded_filename = filename_star_match.group(1)
            try:
                # URL decode the filename
                decoded_filename = unquote(encoded_filename)
                return decoded_filename.strip('"')
            except Exception as e:
                logger.warning(f"Failed to decode filename*: {e}")
        
        # Then try regular filename=
        filename_match = re.search(r'filename="?([^";]+)"?', content_disposition)
        if filename_match:
            filename = filename_match.group(1)
            return filename.strip('"')
        
        return None
    
    def clean_filename(self, filename: str, minimal_cleaning: bool = True) -> str:
        """
        Clean filename for filesystem compatibility
        With minimal_cleaning=True, preserves most characters including parentheses, commas
        """
        if minimal_cleaning:
            # Only replace truly problematic characters for filesystems
            # Preserve parentheses, commas, periods, spaces, and most punctuation
            cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
        else:
            # More aggressive cleaning (old behavior)
            cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove leading/trailing whitespace
        cleaned = cleaned.strip()
        
        # Limit length but preserve extension
        if len(cleaned) > 255:
            name, ext = os.path.splitext(cleaned)
            cleaned = name[:255-len(ext)] + ext
            
        return cleaned
    
    def build_search_url(self, regulation_type: str, year: Optional[str] = None, 
                        number: Optional[str] = None, status: str = "Berlaku") -> str:
        """
        Build search URL for peraturan.go.id using the exact format specified:
        https://peraturan.go.id/cari?PeraturanSearch%5Btentang%5D=&PeraturanSearch%5Bnomor%5D=(input nomor Peraturan)&PeraturanSearch%5Btahun%5D=(input tahun Peraturan)&PeraturanSearch%5Bjenis_peraturan_id%5D=&PeraturanSearch%5Bpemrakarsa_id%5D=&PeraturanSearch%5Bstatus%5D=Berlaku
        """
        # Base search URL exactly as specified
        search_url = f"{self.base_url}/cari?"
        
        params = []
        
        # 1. tentang parameter - always empty as per your specification
        params.append("PeraturanSearch%5Btentang%5D=")
        
        # 2. nomor parameter - use provided number or empty
        if number:
            params.append(f"PeraturanSearch%5Bnomor%5D={str(number)}")
        else:
            params.append("PeraturanSearch%5Bnomor%5D=")
        
        # 3. tahun parameter - use provided year or empty
        if year:
            params.append(f"PeraturanSearch%5Btahun%5D={str(year)}")
        else:
            params.append("PeraturanSearch%5Btahun%5D=")
        
        # 4. jenis_peraturan_id parameter - use type mapping or empty
        type_mapping = {
            "UU": "1",
            "PERPPU": "2", 
            "PP": "3",
            "PERPRES": "4",
            "PERMEN": "5",
            "PERDA": "6"
        }
        
        if regulation_type and regulation_type in type_mapping:
            params.append(f"PeraturanSearch%5Bjenis_peraturan_id%5D={type_mapping[regulation_type]}")
        else:
            params.append("PeraturanSearch%5Bjenis_peraturan_id%5D=")
        
        # 5. pemrakarsa_id parameter - always empty as per your specification
        params.append("PeraturanSearch%5Bpemrakarsa_id%5D=")
        
        # 6. status parameter - default: Berlaku (exactly as specified)
        params.append(f"PeraturanSearch%5Bstatus%5D={status}")
        
        final_url = search_url + "&".join(params)
        logger.info(f"Built search URL: {final_url}")
        return final_url
    
    def create_folder_structure(self, regulation_type: str, year: str, number: str) -> Path:
        """
        Create organized folder structure: /Peraturan-RI/{TYPE}/{YEAR}/Nomor {X}/
        """
        base_dir = Path(self.config.get("base_dir", "Peraturan-RI"))
        
        # Clean and format folder names
        clean_type = re.sub(r'[<>:"/\\|?*]', '', regulation_type)
        clean_year = re.sub(r'[<>:"/\\|?*]', '', str(year))
        clean_number = re.sub(r'[<>:"/\\|?*]', '', str(number))
        
        folder_path = base_dir / clean_type / clean_year / f"Nomor {clean_number}"
        
        # Create directories if they don't exist
        folder_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created folder structure: {folder_path}")
        return folder_path
    
    async def fetch_search_results(self, url: str) -> List[Dict]:
        """Fetch and parse search results from peraturan.go.id"""
        try:
            logger.info(f"Fetching search results from: {url}")
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"HTTP {response.status} error for URL: {url}")
                    return []
                
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Parse search results - this depends on the actual HTML structure
                results = []
                
                # Look for regulation links/entries
                # This is a generic parser - might need adjustment based on actual site structure
                regulation_links = soup.find_all('a', href=re.compile(r'/peraturan/view/'))
                
                for link in regulation_links:
                    href = link.get('href')
                    title = link.get_text(strip=True)
                    
                    if href and title:
                        full_url = urljoin(self.base_url, href)
                        results.append({
                            'title': title,
                            'url': full_url,
                            'href': href
                        })
                
                logger.info(f"Found {len(results)} regulations")
                return results
                
        except Exception as e:
            logger.error(f"Error fetching search results: {e}")
            return []
    
    async def extract_download_links(self, regulation_url: str) -> List[Dict]:
        """Extract download links from a regulation page"""
        try:
            logger.info(f"Extracting download links from: {regulation_url}")
            
            async with self.session.get(regulation_url) as response:
                if response.status != 200:
                    logger.error(f"HTTP {response.status} error for regulation page: {regulation_url}")
                    return []
                
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                download_links = []
                
                # Look for download links - common patterns
                download_selectors = [
                    'a[href*="download"]',
                    'a[href$=".pdf"]',
                    'a[href$=".doc"]',
                    'a[href$=".docx"]',
                    '.download-link a',
                    '.btn-download'
                ]
                
                for selector in download_selectors:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get('href')
                        if href:
                            full_url = urljoin(self.base_url, href)
                            download_links.append({
                                'url': full_url,
                                'text': link.get_text(strip=True),
                                'type': self.get_file_type(href)
                            })
                
                # Remove duplicates
                unique_links = []
                seen_urls = set()
                for link in download_links:
                    if link['url'] not in seen_urls:
                        unique_links.append(link)
                        seen_urls.add(link['url'])
                
                logger.info(f"Found {len(unique_links)} download links")
                return unique_links
                
        except Exception as e:
            logger.error(f"Error extracting download links: {e}")
            return []
    
    def get_file_type(self, url: str) -> str:
        """Determine file type from URL"""
        url_lower = url.lower()
        if '.pdf' in url_lower:
            return 'pdf'
        elif '.doc' in url_lower:
            return 'doc'
        elif '.docx' in url_lower:
            return 'docx'
        else:
            return 'unknown'
    
    async def download_file(self, download_url: str, folder_path: Path, 
                          regulation_info: Dict) -> bool:
        """Download a file and save it with original filename from Content-Disposition"""
        try:
            logger.info(f"Downloading file from: {download_url}")
            
            if self.config.get("demo_mode", True):
                logger.info("DEMO MODE: Would download file but skipping actual download")
                return True
            
            async with self.session.get(download_url) as response:
                if response.status != 200:
                    logger.error(f"HTTP {response.status} error downloading: {download_url}")
                    return False
                
                # PRIORITY 1: Try to get original filename from Content-Disposition header
                content_disposition = response.headers.get('Content-Disposition', '')
                original_filename = self.extract_filename_from_content_disposition(content_disposition)
                
                if original_filename:
                    logger.info(f"Using original server filename: {original_filename}")
                else:
                    # PRIORITY 2: Fallback to URL-based filename 
                    parsed_url = urlparse(download_url)
                    url_filename = os.path.basename(parsed_url.path)
                    
                    if url_filename and '.' in url_filename:
                        original_filename = unquote(url_filename)
                        logger.info(f"Using URL-based filename: {original_filename}")
                    else:
                        # PRIORITY 3: Generate filename based on regulation info
                        file_ext = self.get_file_extension_from_content_type(
                            response.headers.get('Content-Type', '')
                        )
                        # Use regulation title for filename
                        title = regulation_info.get('title', 'document')
                        original_filename = f"{title}{file_ext}"
                        logger.info(f"Generated filename from title: {original_filename}")
                
                # Clean filename with minimal sanitization to preserve original format
                safe_filename = self.clean_filename(original_filename, minimal_cleaning=True)
                file_path = folder_path / safe_filename
                
                # Check if file already exists
                if file_path.exists():
                    logger.info(f"File already exists, skipping: {safe_filename}")
                    return True
                
                # Download and save file
                content = await response.read()
                
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                logger.info(f"Successfully downloaded: {safe_filename}")
                self.downloaded_files.append({
                    'original_url': download_url,
                    'saved_path': str(file_path),
                    'original_filename': original_filename,
                    'safe_filename': safe_filename,
                    'size_bytes': len(content)
                })
                
                return True
                
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return False
    
    def get_file_extension_from_content_type(self, content_type: str) -> str:
        """Get file extension from Content-Type header"""
        content_type_map = {
            'application/pdf': '.pdf',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'text/plain': '.txt',
            'text/html': '.html'
        }
        return content_type_map.get(content_type.lower(), '.pdf')  # Default to PDF

    async def discover_all_regulation_pages(self) -> List[str]:
        """
        Discover all regulation pages by crawling the website
        Returns list of URLs to regulation detail pages
        """
        logger.info("Starting comprehensive discovery of all regulation pages...")
        
        discovered_urls = set()
        
        # 1. Discover through main categories
        await self._discover_by_categories(discovered_urls)
        
        # 2. Discover through year-based searches
        await self._discover_by_years(discovered_urls)
        
        # 3. Discover through alphabetical searches
        await self._discover_by_alphabetical(discovered_urls)
        
        # 4. Discover through sitemap if available
        await self._discover_by_sitemap(discovered_urls)
        
        logger.info(f"Total discovered regulation pages: {len(discovered_urls)}")
        return list(discovered_urls)
    
    async def _discover_by_categories(self, discovered_urls: set):
        """Discover regulations by browsing all categories"""
        logger.info("Discovering regulations by categories...")
        
        # URLs to explore for different regulation types
        category_urls = [
            f"{self.base_url}/peraturan",
            f"{self.base_url}/uu",
            f"{self.base_url}/pp", 
            f"{self.base_url}/perpres",
            f"{self.base_url}/permen",
            f"{self.base_url}/perda"
        ]
        
        for category_url in category_urls:
            try:
                await self._crawl_category_pages(category_url, discovered_urls)
                await asyncio.sleep(self.request_delay)
            except Exception as e:
                logger.error(f"Error discovering category {category_url}: {e}")
    
    async def _discover_by_years(self, discovered_urls: set):
        """Discover regulations by searching through all years"""
        logger.info("Discovering regulations by years...")
        
        years = self.config.get("years_range", list(range(1945, 2026)))
        regulation_types = list(self.config["regulation_types"].keys())
        
        for year in years:
            for reg_type in regulation_types:
                try:
                    search_url = self.build_comprehensive_search_url(
                        regulation_type=reg_type, 
                        year=str(year)
                    )
                    await self._crawl_search_results(search_url, discovered_urls)
                    await asyncio.sleep(self.request_delay)
                except Exception as e:
                    logger.error(f"Error discovering {reg_type} {year}: {e}")
    
    async def _discover_by_alphabetical(self, discovered_urls: set):
        """Discover regulations by alphabetical browsing"""
        logger.info("Discovering regulations alphabetically...")
        
        # Try browsing alphabetically
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            try:
                search_url = f"{self.base_url}/cari?PeraturanSearch%5Btentang%5D={letter}"
                await self._crawl_search_results(search_url, discovered_urls)
                await asyncio.sleep(self.request_delay)
            except Exception as e:
                logger.error(f"Error discovering letter {letter}: {e}")
    
    async def _discover_by_sitemap(self, discovered_urls: set):
        """Try to discover regulations through sitemap"""
        logger.info("Attempting to discover through sitemap...")
        
        sitemap_urls = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemap_index.xml",
            f"{self.base_url}/robots.txt"
        ]
        
        for sitemap_url in sitemap_urls:
            try:
                await self._parse_sitemap(sitemap_url, discovered_urls)
            except Exception as e:
                logger.error(f"Error parsing sitemap {sitemap_url}: {e}")
    
    async def _crawl_category_pages(self, category_url: str, discovered_urls: set):
        """Crawl category pages to find regulation links"""
        try:
            async with self.session.get(category_url) as response:
                if response.status != 200:
                    return
                
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Find all regulation links
                regulation_links = soup.find_all('a', href=re.compile(r'/peraturan/view/'))
                
                for link in regulation_links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        discovered_urls.add(full_url)
                
                # Look for pagination links
                pagination_links = soup.find_all('a', href=re.compile(r'page=\d+'))
                for link in pagination_links:
                    href = link.get('href')
                    if href:
                        next_page_url = urljoin(self.base_url, href)
                        if next_page_url not in self.visited_urls:
                            self.visited_urls.add(next_page_url)
                            await self._crawl_category_pages(next_page_url, discovered_urls)
                            await asyncio.sleep(self.request_delay)
                            
        except Exception as e:
            logger.error(f"Error crawling category page {category_url}: {e}")
    
    async def _crawl_search_results(self, search_url: str, discovered_urls: set):
        """Crawl search results to find regulation links"""
        try:
            if search_url in self.visited_urls:
                return
            
            self.visited_urls.add(search_url)
            
            async with self.session.get(search_url) as response:
                if response.status != 200:
                    return
                
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Find regulation links
                regulation_links = soup.find_all('a', href=re.compile(r'/peraturan/view/'))
                
                for link in regulation_links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        discovered_urls.add(full_url)
                
                # Follow pagination
                next_links = soup.find_all('a', string=re.compile(r'Next|Selanjutnya|»'))
                for next_link in next_links:
                    href = next_link.get('href')
                    if href:
                        next_url = urljoin(self.base_url, href)
                        if next_url not in self.visited_urls:
                            await self._crawl_search_results(next_url, discovered_urls)
                            await asyncio.sleep(self.request_delay)
                            
        except Exception as e:
            logger.error(f"Error crawling search results {search_url}: {e}")
    
    async def _parse_sitemap(self, sitemap_url: str, discovered_urls: set):
        """Parse sitemap XML to find regulation URLs"""
        try:
            async with self.session.get(sitemap_url) as response:
                if response.status != 200:
                    return
                
                content = await response.text()
                
                # Look for regulation URLs in sitemap
                url_pattern = re.compile(r'<loc>(.*?peraturan/view/.*?)</loc>')
                matches = url_pattern.findall(content)
                
                for match in matches:
                    discovered_urls.add(match)
                    
        except Exception as e:
            logger.error(f"Error parsing sitemap {sitemap_url}: {e}")
    
    def build_comprehensive_search_url(self, regulation_type: str = None, year: str = None, 
                                     number: str = None, status: str = None) -> str:
        """
        Build comprehensive search URL for discovering all regulations
        """
        search_url = f"{self.base_url}/cari?"
        params = []
        
        params.append("PeraturanSearch%5Btentang%5D=")
        
        if number:
            params.append(f"PeraturanSearch%5Bnomor%5D={str(number)}")
        else:
            params.append("PeraturanSearch%5Bnomor%5D=")
        
        if year:
            params.append(f"PeraturanSearch%5Btahun%5D={str(year)}")
        else:
            params.append("PeraturanSearch%5Btahun%5D=")
        
        # Type mapping for comprehensive search
        type_mapping = {
            "UU": "1", "PERPPU": "2", "PP": "3", "PERPRES": "4", 
            "PERMEN": "5", "PERDA": "6", "PERBAN": "7", "TAPMPR": "8",
            "PERMENKUMHAM": "9", "PERMENDAGRI": "10", "PERMENKEU": "11",
            "PERMENKES": "12", "PERMENDIKBUD": "13", "PERMENAKER": "14",
            "PERMENAG": "15"
        }
        
        if regulation_type and regulation_type in type_mapping:
            params.append(f"PeraturanSearch%5Bjenis_peraturan_id%5D={type_mapping[regulation_type]}")
        else:
            params.append("PeraturanSearch%5Bjenis_peraturan_id%5D=")
        
        params.append("PeraturanSearch%5Bpemrakarsa_id%5D=")
        
        if status:
            params.append(f"PeraturanSearch%5Bstatus%5D={status}")
        else:
            params.append("PeraturanSearch%5Bstatus%5D=")
        
        return search_url + "&".join(params)
    
    async def extract_all_pdf_links(self, regulation_url: str) -> List[Dict]:
        """
        Extract ALL PDF download links from a regulation page
        More comprehensive than the basic version
        """
        try:
            if regulation_url in self.processed_regulations:
                return []
            
            self.processed_regulations.add(regulation_url)
            
            logger.info(f"Extracting PDF links from: {regulation_url}")
            
            async with self.session.get(regulation_url) as response:
                if response.status != 200:
                    logger.error(f"HTTP {response.status} error for regulation page: {regulation_url}")
                    return []
                
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                pdf_links = []
                
                # Comprehensive PDF link detection
                pdf_selectors = [
                    'a[href*=".pdf"]',
                    'a[href*="download"]',
                    'a[href*="file"]',
                    'a[href*="document"]',
                    'a[href*="lampiran"]',
                    '.download-link a',
                    '.btn-download',
                    '.file-download',
                    '.pdf-link',
                    '.document-link',
                    'a[title*="PDF"]',
                    'a[title*="Download"]',
                    'a[title*="File"]'
                ]
                
                for selector in pdf_selectors:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get('href')
                        if href and ('.pdf' in href.lower() or 'download' in href.lower()):
                            full_url = urljoin(self.base_url, href)
                            if full_url not in self.found_pdfs:
                                self.found_pdfs.add(full_url)
                                pdf_links.append({
                                    'url': full_url,
                                    'text': link.get_text(strip=True),
                                    'type': 'pdf',
                                    'source_page': regulation_url
                                })
                
                # Also look for embedded PDFs or iframe sources
                iframes = soup.find_all('iframe', src=re.compile(r'\.pdf', re.I))
                for iframe in iframes:
                    src = iframe.get('src')
                    if src:
                        full_url = urljoin(self.base_url, src)
                        if full_url not in self.found_pdfs:
                            self.found_pdfs.add(full_url)
                            pdf_links.append({
                                'url': full_url,
                                'text': 'Embedded PDF',
                                'type': 'pdf',
                                'source_page': regulation_url
                            })
                
                logger.info(f"Found {len(pdf_links)} PDF links on page")
                return pdf_links
                
        except Exception as e:
            logger.error(f"Error extracting PDF links: {e}")
            return []
    
    async def download_all_pdfs_from_website(self) -> Dict:
        """
        Main method to download ALL PDFs from the entire website
        """
        logger.info("=== Starting COMPLETE PDF download from peraturan.go.id ===")
        start_time = time.time()
        
        try:
            # Step 1: Discover all regulation pages
            logger.info("Step 1: Discovering all regulation pages...")
            all_regulation_urls = await self.discover_all_regulation_pages()
            
            if not all_regulation_urls:
                logger.warning("No regulation pages discovered!")
                return {
                    'total_pages_found': 0,
                    'total_pdfs_found': 0,
                    'total_downloaded': 0,
                    'total_errors': 0,
                    'duration_seconds': time.time() - start_time
                }
            
            logger.info(f"Discovered {len(all_regulation_urls)} regulation pages")
            
            # Step 2: Extract all PDF links from all pages
            logger.info("Step 2: Extracting all PDF links...")
            all_pdf_links = []
            
            # Process in batches to avoid overwhelming the server
            batch_size = self.max_concurrent
            for i in range(0, len(all_regulation_urls), batch_size):
                batch_urls = all_regulation_urls[i:i+batch_size]
                
                # Process batch concurrently
                tasks = []
                for url in batch_urls:
                    tasks.append(self.extract_all_pdf_links(url))
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, list):
                        all_pdf_links.extend(result)
                    elif isinstance(result, Exception):
                        logger.error(f"Error in batch processing: {result}")
                        self.error_count += 1
                
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(all_regulation_urls)-1)//batch_size + 1}")
                await asyncio.sleep(self.request_delay)
            
            logger.info(f"Found total {len(all_pdf_links)} PDF links")
            
            # Step 3: Download all PDFs
            logger.info("Step 3: Downloading all PDFs...")
            download_tasks = []
            
            for pdf_link in all_pdf_links:
                # Create appropriate folder structure
                folder_path = self._create_folder_for_pdf(pdf_link)
                
                task = self.download_pdf_with_retry(
                    pdf_link['url'], 
                    folder_path, 
                    pdf_link
                )
                download_tasks.append(task)
            
            # Process downloads in batches
            download_batch_size = self.max_concurrent // 2  # Smaller batches for downloads
            for i in range(0, len(download_tasks), download_batch_size):
                batch_tasks = download_tasks[i:i+download_batch_size]
                
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for result in batch_results:
                    if result is True:
                        self.success_count += 1
                    elif isinstance(result, Exception):
                        logger.error(f"Download error: {result}")
                        self.error_count += 1
                    else:
                        self.error_count += 1
                
                logger.info(f"Downloaded batch {i//download_batch_size + 1}/{(len(download_tasks)-1)//download_batch_size + 1}")
                await asyncio.sleep(self.request_delay)
            
            end_time = time.time()
            duration = end_time - start_time
            
            summary = {
                'total_pages_found': len(all_regulation_urls),
                'total_pdfs_found': len(all_pdf_links),
                'total_downloaded': self.success_count,
                'total_errors': self.error_count,
                'duration_seconds': duration,
                'duration_formatted': f"{duration//3600:.0f}h {(duration%3600)//60:.0f}m {duration%60:.1f}s",
                'downloaded_files': self.downloaded_files.copy(),
                'unique_pdfs_found': len(self.found_pdfs)
            }
            
            logger.info("=== COMPLETE PDF DOWNLOAD FINISHED ===")
            logger.info(f"Total regulation pages: {summary['total_pages_found']}")
            logger.info(f"Total PDF links found: {summary['total_pdfs_found']}")
            logger.info(f"Successfully downloaded: {summary['total_downloaded']}")
            logger.info(f"Errors: {summary['total_errors']}")
            logger.info(f"Duration: {summary['duration_formatted']}")
            
            return summary
            
        except Exception as e:
            logger.error(f"Critical error in download_all_pdfs_from_website: {e}")
            return {
                'error': str(e),
                'total_downloaded': self.success_count,
                'total_errors': self.error_count + 1,
                'duration_seconds': time.time() - start_time
            }
    
    def _create_folder_for_pdf(self, pdf_link: Dict) -> Path:
        """Create appropriate folder structure for PDF"""
        base_dir = Path(self.config.get("base_dir", "Peraturan-RI-Complete"))
        
        # Try to extract regulation info from source page URL
        source_url = pdf_link.get('source_page', '')
        
        # Extract regulation type, year, number from URL or text
        reg_type, year, number = self._extract_regulation_info(source_url, pdf_link.get('text', ''))
        
        if reg_type and year and number:
            folder_path = base_dir / reg_type / year / f"Nomor {number}"
        elif reg_type and year:
            folder_path = base_dir / reg_type / year / "Lainnya"
        elif reg_type:
            folder_path = base_dir / reg_type / "Lainnya"
        else:
            folder_path = base_dir / "Uncategorized"
        
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path
    
    def _extract_regulation_info(self, source_url: str, text: str) -> Tuple[str, str, str]:
        """Extract regulation type, year, and number from URL or text"""
        reg_type = None
        year = None
        number = None
        
        # Try to extract from URL
        url_parts = source_url.split('/')
        for part in url_parts:
            if part.upper() in self.config["regulation_types"]:
                reg_type = part.upper()
                break
        
        # Extract year (4-digit number)
        year_match = re.search(r'\b(19|20)\d{2}\b', source_url + ' ' + text)
        if year_match:
            year = year_match.group(0)
        
        # Extract number
        number_patterns = [
            r'(?:Nomor|No\.?)\s*(\d+)',
            r'(\d+)\s*(?:Tahun|Year)',
            r'/(\d+)/'
        ]
        
        for pattern in number_patterns:
            match = re.search(pattern, source_url + ' ' + text, re.IGNORECASE)
            if match:
                number = match.group(1)
                break
        
        return reg_type or "Unknown", year or "Unknown", number or "Unknown"
    
    async def download_pdf_with_retry(self, download_url: str, folder_path: Path, 
                                    pdf_info: Dict) -> bool:
        """Download PDF with retry mechanism"""
        for attempt in range(self.retry_attempts):
            try:
                success = await self.download_file(download_url, folder_path, pdf_info)
                if success:
                    return True
                    
            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed for {download_url}: {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error(f"Failed to download after {self.retry_attempts} attempts: {download_url}")
        return False
    
    async def scrape_all_active_regulations(self, years: List[str] = None, 
                                          regulation_types: List[str] = None,
                                          max_results_per_search: int = 50) -> Dict:
        """
        Scrape all active (Berlaku) regulations for specified years and types
        This is the main method to get only active regulations
        """
        if not years:
            years = ["2020", "2021", "2022", "2023", "2024", "2025"]
        
        if not regulation_types:
            regulation_types = ["UU", "PERPPU", "PP", "PERPRES", "PERMEN"]
        
        logger.info(f"Starting comprehensive scrape for active regulations")
        logger.info(f"Years: {years}")
        logger.info(f"Types: {regulation_types}")
        
        all_results = {}
        total_downloaded = 0
        total_errors = 0
        
        for reg_type in regulation_types:
            logger.info(f"Processing regulation type: {reg_type}")
            type_results = {}
            
            for year in years:
                logger.info(f"Processing {reg_type} for year {year}")
                
                try:
                    result = await self.scrape_regulations(
                        regulation_type=reg_type,
                        year=year,
                        status="Berlaku",  # Only active regulations
                        max_results=max_results_per_search
                    )
                    
                    type_results[year] = result
                    total_downloaded += result.get('downloaded', 0)
                    total_errors += result.get('errors', 0)
                    
                    # Add delay between requests to be respectful
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing {reg_type} {year}: {e}")
                    type_results[year] = {'error': str(e)}
                    total_errors += 1
            
            all_results[reg_type] = type_results
            
            # Add delay between regulation types
            await asyncio.sleep(3)
        
        summary = {
            'total_downloaded': total_downloaded,
            'total_errors': total_errors,
            'results_by_type': all_results,
            'downloaded_files': self.downloaded_files.copy()
        }
        
        logger.info(f"Comprehensive scrape completed. Downloaded: {total_downloaded}, Errors: {total_errors}")
        return summary
    
    async def scrape_regulations(self, regulation_type: str, year: Optional[str] = None,
                               number: Optional[str] = None, status: str = "Berlaku",
                               max_results: int = 10) -> Dict:
        """
        Main scraping method for individual regulation type/year combinations
        """
        try:
            logger.info(f"Starting scrape for {regulation_type} regulations")
            
            # Build search URL
            search_url = self.build_search_url(regulation_type, year, number, status)
            
            # Fetch search results
            search_results = await self.fetch_search_results(search_url)
            
            if not search_results:
                logger.warning("No search results found")
                return {
                    'regulation_type': regulation_type,
                    'total_found': 0,
                    'processed': 0,
                    'downloaded': 0,
                    'errors': 0,
                    'files': []
                }
            
            # Limit results if specified
            if max_results > 0:
                search_results = search_results[:max_results]
            
            logger.info(f"Processing {len(search_results)} regulations")
            
            processed_count = 0
            downloaded_count = 0
            error_count = 0
            
            for result in search_results:
                try:
                    processed_count += 1
                    logger.info(f"Processing regulation {processed_count}/{len(search_results)}: {result['title']}")
                    
                    # Extract year and number from title or URL for folder structure
                    reg_year = year if year else self.extract_year_from_title(result['title'])
                    reg_number = number if number else self.extract_number_from_title(result['title'])
                    
                    if not reg_year or not reg_number:
                        logger.warning(f"Could not extract year/number from: {result['title']}")
                        reg_year = reg_year or "Unknown"
                        reg_number = reg_number or "Unknown"
                    
                    # Create folder structure
                    folder_path = self.create_folder_structure(regulation_type, reg_year, reg_number)
                    
                    # Extract download links from regulation page
                    download_links = await self.extract_download_links(result['url'])
                    
                    if not download_links:
                        logger.warning(f"No download links found for: {result['title']}")
                        continue
                    
                    # Download files
                    for link in download_links:
                        success = await self.download_file(
                            link['url'], 
                            folder_path, 
                            {
                                'title': result['title'],
                                'regulation_type': regulation_type,
                                'year': reg_year,
                                'number': reg_number
                            }
                        )
                        
                        if success:
                            downloaded_count += 1
                        else:
                            error_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing regulation: {e}")
                    error_count += 1
                    continue
            
            summary = {
                'regulation_type': regulation_type,
                'total_found': len(search_results),
                'processed': processed_count,
                'downloaded': downloaded_count,
                'errors': error_count,
                'files': self.downloaded_files.copy()
            }
            
            logger.info(f"Scraping completed. Downloaded: {downloaded_count}, Errors: {error_count}")
            return summary
            
        except Exception as e:
            logger.error(f"Error in scrape_regulations: {e}")
            return {
                'regulation_type': regulation_type,
                'total_found': 0,
                'processed': 0,
                'downloaded': 0,
                'errors': 1,
                'files': [],
                'error': str(e)
            }
    
    def extract_year_from_title(self, title: str) -> Optional[str]:
        """Extract year from regulation title"""
        # Look for 4-digit year
        year_match = re.search(r'\b(19|20)\d{2}\b', title)
        return year_match.group(0) if year_match else None
    
    def extract_number_from_title(self, title: str) -> Optional[str]:
        """Extract regulation number from title"""
        # Look for "Nomor X" or "No. X" patterns
        number_patterns = [
            r'(?:Nomor|No\.?)\s*(\d+)',
            r'(\d+)\s*(?:Tahun|Year)',
            r'/(\d+)/'
        ]
        
        for pattern in number_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def get_stats(self) -> Dict:
        """Get scraping statistics"""
        return {
            'total_downloads': self.download_count,
            'successful_downloads': self.success_count,
            'failed_downloads': self.error_count,
            'downloaded_files': len(self.downloaded_files)
        }


# Main function for testing
async def main():
    """Main function to download ALL PDFs from peraturan.go.id"""
    
    async with CompletePeraturanScraper() as scraper:
        print("=== COMPLETE Indonesian Legal Documents PDF Downloader ===")
        print("This will download ALL PDF files from peraturan.go.id")
        print("Features:")
        print("1. Comprehensive website crawling to find all regulation pages")
        print("2. Extracts ALL PDF links from every regulation page")
        print("3. Preserves original filenames from Content-Disposition headers")
        print("4. Organized folder structure by regulation type/year/number")
        print("5. Retry mechanism for failed downloads")
        print("6. Progress monitoring and logging")
        print()
        
        # Ask for confirmation before starting massive download
        response = input("This will download potentially thousands of PDF files. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Download cancelled.")
            return
        
        print("Starting comprehensive download...")
        print("This may take several hours depending on the number of files.")
        print("Check peraturan_scraper.log for detailed progress.")
        print()
        
        # Start the complete download process
        result = await scraper.download_all_pdfs_from_website()
        
        print("\n=== DOWNLOAD COMPLETE ===")
        print(f"Total regulation pages found: {result.get('total_pages_found', 0)}")
        print(f"Total PDF links found: {result.get('total_pdfs_found', 0)}")
        print(f"Successfully downloaded: {result.get('total_downloaded', 0)}")
        print(f"Errors encountered: {result.get('total_errors', 0)}")
        print(f"Duration: {result.get('duration_formatted', 'Unknown')}")
        print(f"Files saved in: {scraper.config.get('base_dir', 'Peraturan-RI-Complete')}")
        
        # Save summary to file
        summary_file = f"download_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Summary saved to: {summary_file}")


# Convenience functions for specific use cases
async def download_by_regulation_type(regulation_types: List[str] = None, years: List[str] = None):
    """Download PDFs for specific regulation types and years"""
    async with CompletePeraturanScraper() as scraper:
        if not regulation_types:
            regulation_types = ["UU", "PP", "PERPRES"]
        
        if not years:
            years = ["2020", "2021", "2022", "2023", "2024", "2025"]
        
        logger.info(f"Downloading PDFs for types: {regulation_types}, years: {years}")
        
        # Override config for specific search
        scraper.config["regulation_types"] = {k: v for k, v in scraper.config["regulation_types"].items() if k in regulation_types}
        scraper.config["years_range"] = [int(y) for y in years]
        
        result = await scraper.download_all_pdfs_from_website()
        return result


async def download_recent_regulations(days_back: int = 30):
    """Download regulations from recent days"""
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    async with CompletePeraturanScraper() as scraper:
        # This would require additional implementation to filter by date
        # For now, download recent years
        current_year = end_date.year
        years = [str(current_year), str(current_year - 1)]
        
        scraper.config["years_range"] = [int(y) for y in years]
        
        result = await scraper.download_all_pdfs_from_website()
        return result
        

if __name__ == "__main__":
    asyncio.run(main())
