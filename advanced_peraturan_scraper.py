"""
Advanced Indonesian Legal Documents Scraper
Scraper canggih untuk mengunduh dokumen hukum Indonesia dari peraturan.go.id
dengan fitur:
1. Preservasi nama file asli dari Content-Disposition headers
2. Struktur folder terorganisir berdasarkan jenis/tahun/nomor
3. Filter pencarian berdasarkan jenis peraturan/tahun/nomor/status
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
from typing import Dict, List, Optional, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AdvancedPeraturanScraper:
    def __init__(self, base_url: str = "https://peraturan.go.id", config_path: str = "config.json"):
        self.base_url = base_url
        self.session = None
        self.config = self.load_config(config_path)
        self.download_count = 0
        self.success_count = 0
        self.error_count = 0
        self.downloaded_files = []
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using default config")
            return {
                "regulation_types": {
                    "UU": "Undang-Undang",
                    "PP": "Peraturan Pemerintah",
                    "PERPRES": "Peraturan Presiden",
                    "PERMEN": "Peraturan Menteri",
                    "PERDA": "Peraturan Daerah"
                },
                "base_dir": "Peraturan-RI",
                "demo_mode": false,
                "max_concurrent": 5
            }
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=300, use_dns_cache=True)
        timeout = aiohttp.ClientTimeout(total=300, connect=60)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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
    """Main function for testing the scraper with new features"""
    
    async with AdvancedPeraturanScraper() as scraper:
        print("=== Advanced Indonesian Legal Documents Scraper ===")
        print("Features:")
        print("1. Original filename preservation from Content-Disposition headers")
        print("2. Organized folder structure: /Peraturan-RI/{TYPE}/{YEAR}/Nomor {X}/")
        print("3. Only downloads active (Berlaku) regulations")
        print("4. Uses specific search URL format for peraturan.go.id")
        print()
        
        # Example 1: Scrape specific UU for 2024
        print("Example 1: Scraping UU (Undang-Undang) for 2024...")
        result1 = await scraper.scrape_regulations(
            regulation_type="UU",
            year="2024",
            status="Berlaku",
            max_results=5
        )
        print(f"UU 2024 results: {json.dumps(result1, indent=2, ensure_ascii=False)}")
        print()
        
        # Example 2: Scrape specific regulation by number
        print("Example 2: Scraping UU Nomor 1 for 2024...")
        result2 = await scraper.scrape_regulations(
            regulation_type="UU",
            year="2024",
            number="1",
            status="Berlaku",
            max_results=1
        )
        print(f"UU No. 1/2024 results: {json.dumps(result2, indent=2, ensure_ascii=False)}")
        print()
        
        # Example 3: Comprehensive scrape (commented out for demo)
        # print("Example 3: Comprehensive scrape of all active regulations...")
        # comprehensive_result = await scraper.scrape_all_active_regulations(
        #     years=["2023", "2024"],
        #     regulation_types=["UU", "PP"],
        #     max_results_per_search=3
        # )
        # print(f"Comprehensive results summary: Downloaded {comprehensive_result['total_downloaded']} files")
        
        # Show final statistics
        stats = scraper.get_stats()
        print(f"Final statistics: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        

if __name__ == "__main__":
    asyncio.run(main())
