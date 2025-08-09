#!/usr/bin/env python3
"""
Practical script for scraping active Indonesian regulations
with proper filename preservation and organized folder structure.

Usage examples:
1. Scrape all UU (Undang-Undang) for 2024: python scrape_active_regulations.py --type UU --year 2024
2. Scrape specific regulation: python scrape_active_regulations.py --type UU --year 2024 --number 1
3. Scrape multiple types for recent years: python scrape_active_regulations.py --comprehensive
"""

import asyncio
import argparse
import json
from advanced_peraturan_scraper import AdvancedPeraturanScraper

async def scrape_specific_regulation(reg_type: str, year: str, number: str = None, max_results: int = 10):
    """Scrape specific regulation type/year/number"""
    async with AdvancedPeraturanScraper() as scraper:
        print(f"Scraping {reg_type} for year {year}" + (f" number {number}" if number else ""))
        print(f"Only downloading active (Berlaku) regulations")
        print(f"Files will be saved with original names in: Peraturan-RI/{reg_type}/{year}/Nomor X/")
        print()
        
        result = await scraper.scrape_regulations(
            regulation_type=reg_type,
            year=year,
            number=number,
            status="Berlaku",
            max_results=max_results
        )
        
        print("Results:")
        print(f"- Found: {result.get('total_found', 0)} regulations")
        print(f"- Downloaded: {result.get('downloaded', 0)} files")
        print(f"- Errors: {result.get('errors', 0)}")
        
        if result.get('files'):
            print("\nDownloaded files:")
            for file_info in result['files']:
                print(f"- {file_info.get('safe_filename', 'Unknown')} ({file_info.get('size_bytes', 0)} bytes)")
        
        return result

async def scrape_comprehensive():
    """Scrape multiple regulation types for recent years"""
    async with AdvancedPeraturanScraper() as scraper:
        print("Comprehensive scraping of active regulations")
        print("Types: UU, PERPPU, PP, PERPRES, PERMEN")
        print("Years: 2022, 2023, 2024, 2025")
        print("Status: Only Berlaku (Active)")
        print()
        
        result = await scraper.scrape_all_active_regulations(
            years=["2022", "2023", "2024", "2025"],
            regulation_types=["UU", "PERPPU", "PP", "PERPRES", "PERMEN"],
            max_results_per_search=20
        )
        
        print("Comprehensive Results:")
        print(f"- Total Downloaded: {result.get('total_downloaded', 0)} files")
        print(f"- Total Errors: {result.get('total_errors', 0)}")
        
        # Show breakdown by type
        for reg_type, type_results in result.get('results_by_type', {}).items():
            total_for_type = sum(year_result.get('downloaded', 0) 
                               for year_result in type_results.values() 
                               if isinstance(year_result, dict))
            print(f"- {reg_type}: {total_for_type} files")
        
        return result

def main():
    parser = argparse.ArgumentParser(description="Scrape active Indonesian regulations")
    parser.add_argument("--type", help="Regulation type (UU, PERPPU, PP, PERPRES, PERMEN)")
    parser.add_argument("--year", help="Year to scrape")
    parser.add_argument("--number", help="Specific regulation number")
    parser.add_argument("--max-results", type=int, default=10, help="Maximum results per search")
    parser.add_argument("--comprehensive", action="store_true", 
                       help="Run comprehensive scrape of all types for recent years")
    
    args = parser.parse_args()
    
    if args.comprehensive:
        print("Starting comprehensive scrape...")
        result = asyncio.run(scrape_comprehensive())
    elif args.type and args.year:
        print(f"Starting specific scrape...")
        result = asyncio.run(scrape_specific_regulation(
            args.type, args.year, args.number, args.max_results
        ))
    else:
        print("Please specify either --comprehensive or both --type and --year")
        print("Examples:")
        print("  python scrape_active_regulations.py --type UU --year 2024")
        print("  python scrape_active_regulations.py --type UU --year 2024 --number 1")
        print("  python scrape_active_regulations.py --comprehensive")
        return
    
    # Save results to file
    output_file = "scraping_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed results saved to: {output_file}")

if __name__ == "__main__":
    main()
