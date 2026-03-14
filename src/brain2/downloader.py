"""
Unified downloader module for academic papers.
Supports arXiv and Semantic Scholar with configuration-based topics.

Usage:
    python -m src.brain2.downloader
"""

import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import arxiv
    import requests
    from src.brain2.db_utils import add_paper_to_db, get_existing_papers
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    print("Please install required packages: pip install arxiv requests")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ArxivDownloader:
    """Downloader for arXiv.org papers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.settings = config.get('settings', {})
        self.topics = config.get('topics', [])
        self.batch_size = self.settings.get('batch_size', 50)
        self.delay_seconds = self.settings.get('delay_seconds', 3)
        self.date_filter_days = self.settings.get('date_filter_days', 365)
        self.data_dir = Path(self.settings.get('data_dir', 'data/pdf'))
        
    def search_topic(self, topic: Dict[str, str]) -> List[arxiv.Result]:
        """Search arXiv for a specific topic."""
        keywords = topic.get('keywords', [])
        categories = topic.get('categories', [])
        exclude_terms = topic.get('exclude_terms', [])
        
        # Build search query
        query_parts = []
        for keyword in keywords:
            query_parts.append(f'all:{keyword}')
        
        if not query_parts:
            return []
            
        search_query = ' OR '.join(query_parts)
        
        # Build category filter
        cat_filter = None
        if categories:
            cat_filter = arxiv.SortCriterion.Relevance
            
        # Date filter
        start_date = datetime.now() - timedelta(days=self.date_filter_days)
        
        try:
            search = arxiv.Search(
                query=search_query,
                max_results=self.batch_size,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            results = []
            for result in search.results():
                # Check date filter
                if result.published < start_date:
                    continue
                    
                # Check exclude terms
                title_lower = result.title.lower()
                abstract_lower = result.summary.lower()
                exclude = False
                for term in exclude_terms:
                    if term.lower() in title_lower or term.lower() in abstract_lower:
                        exclude = True
                        break
                        
                if not exclude:
                    results.append(result)
                    
            return results
            
        except Exception as e:
            logger.error(f"Error searching arXiv for topic {topic.get('name')}: {e}")
            return []
    
    def download_paper(self, paper: arxiv.Result) -> Optional[str]:
        """Download a single paper."""
        try:
            # Create filename
            safe_title = "".join(c for c in paper.title if c.isalnum() or c in ' -_')[:50]
            filename = f"{safe_title}_{paper.authors[0].last_name if paper.authors else 'unknown'}_{paper.published.strftime('%Y%m%d')}.pdf"
            filepath = self.data_dir / filename
            
            # Download
            paper.download_pdf(filename=str(filepath))
            logger.info(f"Downloaded: {paper.title[:50]}...")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error downloading paper {paper.title}: {e}")
            return None
    
    def run(self) -> Dict[str, int]:
        """Run download for all topics."""
        stats = {'found': 0, 'downloaded': 0, 'skipped': 0, 'errors': 0}
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Get existing papers to avoid duplicates
        existing_titles = get_existing_papers()
        
        for topic in self.topics:
            topic_name = topic.get('name', 'unknown')
            logger.info(f"Searching arXiv for topic: {topic_name}")
            
            papers = self.search_topic(topic)
            stats['found'] += len(papers)
            
            for paper in papers:
                # Check if already exists
                if paper.title in existing_titles:
                    stats['skipped'] += 1
                    continue
                
                # Download
                filepath = self.download_paper(paper)
                if filepath:
                    # Add to database
                    try:
                        add_paper_to_db(
                            title=paper.title,
                            authors=[str(a) for a in paper.authors],
                            filepath=filepath,
                            source='arxiv',
                            url=paper.entry_id,
                            published_date=paper.published,
                            abstract=paper.summary,
                            topics=[topic_name]
                        )
                        stats['downloaded'] += 1
                    except Exception as e:
                        logger.error(f"Error adding paper to DB: {e}")
                        stats['errors'] += 1
                else:
                    stats['errors'] += 1
                    
                # Delay to respect rate limits
                time.sleep(self.delay_seconds)
                
        return stats


class SemanticScholarDownloader:
    """Downloader for Semantic Scholar papers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.settings = config.get('settings', {})
        self.topics = config.get('topics', [])
        self.batch_size = self.settings.get('batch_size', 20)
        self.delay_seconds = self.settings.get('delay_seconds', 5)
        self.date_filter_days = self.settings.get('date_filter_days', 730)
        self.data_dir = Path(self.settings.get('data_dir', 'data/pdf'))
        self.api_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        
    def search_topic(self, topic: Dict[str, str]) -> List[Dict[str, Any]]:
        """Search Semantic Scholar for a specific topic."""
        query = topic.get('query', '')
        author_filter = topic.get('author_filter')
        
        if not query:
            return []
            
        # Build parameters
        params = {
            'query': query,
            'limit': self.batch_size,
            'fields': 'title,authors,url,abstract,publicationDate,externalIds',
            'sort': 'publicationDate:desc'
        }
        
        # Add author filter if specified
        if author_filter:
            # Note: Semantic Scholar API doesn't directly support author filtering in search
            # We'll filter results manually
            pass
            
        try:
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = data.get('data', [])
            
            # Filter by date and authors
            filtered_results = []
            start_date = datetime.now() - timedelta(days=self.date_filter_days)
            
            for paper in results:
                pub_date_str = paper.get('publicationDate')
                if pub_date_str:
                    try:
                        pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                        if pub_date < start_date:
                            continue
                    except:
                        pass
                
                # Filter by author if specified
                if author_filter:
                    authors = paper.get('authors', [])
                    author_names = [a.get('name', '') for a in authors]
                    if not any(author in author_names for author in author_filter):
                        continue
                        
                filtered_results.append(paper)
                
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error searching Semantic Scholar for topic {topic.get('name')}: {e}")
            return []
    
    def download_paper(self, paper: Dict[str, Any]) -> Optional[str]:
        """Download a single paper from Semantic Scholar."""
        try:
            # Get PDF URL (if available)
            external_ids = paper.get('externalIds', {})
            doi = external_ids.get('DOI')
            
            if not doi:
                return None
                
            # Try to construct PDF URL (this is simplified - real implementation may vary)
            pdf_url = f"https://doi.org/{doi}"
            
            # Create filename
            title = paper.get('title', 'unknown')
            safe_title = "".join(c for c in title if c.isalnum() or c in ' -_')[:50]
            authors = paper.get('authors', [])
            first_author = authors[0].get('name', 'unknown').split()[-1] if authors else 'unknown'
            pub_date = paper.get('publicationDate', '')[:10].replace('-', '') if paper.get('publicationDate') else 'unknown'
            
            filename = f"{safe_title}_{first_author}_{pub_date}.pdf"
            filepath = self.data_dir / filename
            
            # Download PDF
            response = requests.get(pdf_url, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logger.info(f"Downloaded: {title[:50]}...")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error downloading paper from Semantic Scholar: {e}")
            return None
    
    def run(self) -> Dict[str, int]:
        """Run download for all topics."""
        stats = {'found': 0, 'downloaded': 0, 'skipped': 0, 'errors': 0}
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Get existing papers to avoid duplicates
        existing_titles = get_existing_papers()
        
        for topic in self.topics:
            topic_name = topic.get('name', 'unknown')
            logger.info(f"Searching Semantic Scholar for topic: {topic_name}")
            
            papers = self.search_topic(topic)
            stats['found'] += len(papers)
            
            for paper in papers:
                title = paper.get('title', '')
                
                # Check if already exists
                if title in existing_titles:
                    stats['skipped'] += 1
                    continue
                
                # Download
                filepath = self.download_paper(paper)
                if filepath:
                    # Add to database
                    try:
                        authors = [a.get('name', '') for a in paper.get('authors', [])]
                        add_paper_to_db(
                            title=title,
                            authors=authors,
                            filepath=filepath,
                            source='semantic_scholar',
                            url=paper.get('url', ''),
                            published_date=paper.get('publicationDate'),
                            abstract=paper.get('abstract', ''),
                            topics=[topic_name]
                        )
                        stats['downloaded'] += 1
                    except Exception as e:
                        logger.error(f"Error adding paper to DB: {e}")
                        stats['errors'] += 1
                else:
                    stats['errors'] += 1
                    
                # Delay to respect rate limits
                time.sleep(self.delay_seconds)
                
        return stats


def load_config() -> Dict[str, Any]:
    """Load configuration from topics.json."""
    config_path = Path(__file__).parent / 'topics.json'
    
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def download_all() -> Dict[str, Dict[str, int]]:
    """Run downloaders for all configured sources."""
    config = load_config()
    results = {}
    
    # Run arXiv downloader
    if 'arxiv' in config:
        logger.info("Starting arXiv download...")
        arxiv_downloader = ArxivDownloader(config['arxiv'])
        results['arxiv'] = arxiv_downloader.run()
        logger.info(f"arXiv complete: {results['arxiv']}")
    
    # Run Semantic Scholar downloader
    if 'semantic_scholar' in config:
        logger.info("Starting Semantic Scholar download...")
        ss_downloader = SemanticScholarDownloader(config['semantic_scholar'])
        results['semantic_scholar'] = ss_downloader.run()
        logger.info(f"Semantic Scholar complete: {results['semantic_scholar']}")
    
    return results


def main():
    """Main entry point for standalone execution."""
    logger.info("=" * 50)
    logger.info("Starting unified downloader")
    logger.info("=" * 50)
    
    try:
        results = download_all()
        
        # Print summary
        logger.info("=" * 50)
        logger.info("DOWNLOAD SUMMARY")
        logger.info("=" * 50)
        
        total_found = 0
        total_downloaded = 0
        total_skipped = 0
        total_errors = 0
        
        for source, stats in results.items():
            logger.info(f"\n{source.upper()}:")
            logger.info(f"  Found:       {stats['found']}")
            logger.info(f"  Downloaded:  {stats['downloaded']}")
            logger.info(f"  Skipped:     {stats['skipped']}")
            logger.info(f"  Errors:      {stats['errors']}")
            
            total_found += stats['found']
            total_downloaded += stats['downloaded']
            total_skipped += stats['skipped']
            total_errors += stats['errors']
        
        logger.info("\n" + "=" * 50)
        logger.info(f"TOTALS:")
        logger.info(f"  Found:       {total_found}")
        logger.info(f"  Downloaded:  {total_downloaded}")
        logger.info(f"  Skipped:     {total_skipped}")
        logger.info(f"  Errors:      {total_errors}")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Downloader failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
