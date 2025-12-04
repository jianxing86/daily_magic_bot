"""
科学新闻获取模块
支持多个新闻源：Nature, Science, ScienceDaily
"""
import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict
from datetime import datetime, timedelta
import time
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiSourceNewsFetcher:
    """多源科学新闻获取器"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.sources = {
            'nature_news': 'https://www.nature.com/latest-news',
            'nature_research': 'https://www.nature.com/nature/research-articles',
            'sciencedaily': 'https://www.sciencedaily.com/',
            'sciencedaily_top': 'https://www.sciencedaily.com/news/top/science/',
            'sciencedaily_brain': 'https://www.sciencedaily.com/news/mind_brain/'
        }
    
    def fetch_all_news_titles(self) -> List[Dict]:
        """
        获取所有新闻源的标题列表
        
        Returns:
            新闻列表，每条包含 title, url, source, date
        """
        all_news = []
        
        logger.info("开始从多个新闻源获取标题...")
        
        # 1. Nature 最新新闻
        all_news.extend(self._fetch_nature_news())
        
        # 2. Nature 研究文章
        all_news.extend(self._fetch_nature_research())
        
        # 3. ScienceDaily 主页
        all_news.extend(self._fetch_sciencedaily())
        
        # 4. ScienceDaily 科学板块
        all_news.extend(self._fetch_sciencedaily_top())
        
        # 5. ScienceDaily 大脑认知
        all_news.extend(self._fetch_sciencedaily_brain())
        
        logger.info(f"总共获取 {len(all_news)} 条新闻标题")
        
        # 过滤最近1-2天的新闻
        recent_news = self._filter_recent_news(all_news, days=2)
        logger.info(f"过滤后保留最近2天的新闻: {len(recent_news)} 条")
        
        return recent_news
    
    def _fetch_nature_news(self) -> List[Dict]:
        """获取 Nature 最新新闻"""
        try:
            logger.info("正在获取 Nature 最新新闻...")
            response = requests.get(self.sources['nature_news'], headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_list = []
            # Nature 使用 c-article-item 结构
            articles = soup.select('div.c-article-item__content')
            
            for article in articles[:30]:  # 限制每个源的数量
                title_elem = article.select_one('h3.c-article-item__title')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                
                # 获取链接
                link_elem = article.select_one('a')
                url = link_elem.get('href', '') if link_elem else ''
                if url and not url.startswith('http'):
                    url = 'https://www.nature.com' + url
                
                # 提取日期 (格式: 03 DEC 2025)
                date_elem = article.select_one('span.c-article-item__date')
                date_str = date_elem.get_text(strip=True) if date_elem else ''
                
                news_list.append({
                    'title': title,
                    'url': url,
                    'source': 'Nature News',
                    'date': self._parse_date(date_str)
                })
            
            logger.info(f"  - Nature News: {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"获取 Nature 新闻失败: {e}")
            return []
    
    def _fetch_nature_research(self) -> List[Dict]:
        """获取 Nature 研究文章"""
        try:
            logger.info("正在获取 Nature 研究文章...")
            response = requests.get(self.sources['nature_research'], headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_list = []
            articles = soup.select('article')
            
            for article in articles[:30]:
                title_elem = article.select_one('h3 a, h2 a')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                url = title_elem.get('href', '')
                if url.startswith('/'):
                    url = 'https://www.nature.com' + url
                
                date_elem = article.select_one('time')
                date_str = date_elem.get('datetime', '') if date_elem else ''
                
                news_list.append({
                    'title': title,
                    'url': url,
                    'source': 'Nature Research',
                    'date': self._parse_date(date_str)
                })
            
            logger.info(f"  - Nature Research: {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"获取 Nature 研究文章失败: {e}")
            return []
    
    def _fetch_sciencedaily(self) -> List[Dict]:
        """获取 ScienceDaily 主页新闻"""
        try:
            logger.info("正在获取 ScienceDaily 主页...")
            response = requests.get(self.sources['sciencedaily'], headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_list = []
            links = soup.select('a[href*="/releases/"]')
            
            seen_urls = set()
            for link in links:
                url = link.get('href', '')
                if not url or url in seen_urls:
                    continue
                    
                if url.startswith('/'):
                    url = 'https://www.sciencedaily.com' + url
                    
                title = link.get_text(strip=True)
                if len(title) < 10:
                    continue
                
                # 从 URL 中提取日期 (格式: /releases/YYYY/MM/YYMMDDHHMMSS.htm)
                date_match = re.search(r'/releases/(\d{4})/(\d{2})/(\d{2})(\d{2})(\d{2})(\d{2})\.htm', url)
                if date_match:
                    year, month, day = date_match.group(1), date_match.group(2), date_match.group(3)
                    date_str = f"{year}-{month}-{day}"
                else:
                    date_str = ''
                
                seen_urls.add(url)
                news_list.append({
                    'title': title,
                    'url': url,
                    'source': 'ScienceDaily',
                    'date': self._parse_date(date_str)
                })
                
                if len(news_list) >= 50:
                    break
            
            logger.info(f"  - ScienceDaily: {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"获取 ScienceDaily 失败: {e}")
            return []
    
    def _fetch_sciencedaily_top(self) -> List[Dict]:
        """获取 ScienceDaily 科学板块"""
        try:
            logger.info("正在获取 ScienceDaily 科学板块...")
            response = requests.get(self.sources['sciencedaily_top'], headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_list = []
            links = soup.select('a[href*="/releases/"]')
            
            seen_urls = set()
            for link in links:
                url = link.get('href', '')
                if not url or url in seen_urls:
                    continue
                    
                if url.startswith('/'):
                    url = 'https://www.sciencedaily.com' + url
                    
                title = link.get_text(strip=True)
                if len(title) < 10:
                    continue
                
                date_match = re.search(r'/releases/(\d{4})/(\d{2})/(\d{2})(\d{2})(\d{2})(\d{2})\.htm', url)
                if date_match:
                    year, month, day = date_match.group(1), date_match.group(2), date_match.group(3)
                    date_str = f"{year}-{month}-{day}"
                else:
                    date_str = ''
                
                seen_urls.add(url)
                news_list.append({
                    'title': title,
                    'url': url,
                    'source': 'ScienceDaily Top',
                    'date': self._parse_date(date_str)
                })
                
                if len(news_list) >= 30:
                    break
            
            logger.info(f"  - ScienceDaily Top: {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"获取 ScienceDaily Top 失败: {e}")
            return []
    
    def _fetch_sciencedaily_brain(self) -> List[Dict]:
        """获取 ScienceDaily 大脑认知板块"""
        try:
            logger.info("正在获取 ScienceDaily 大脑认知板块...")
            response = requests.get(self.sources['sciencedaily_brain'], headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_list = []
            links = soup.select('a[href*="/releases/"]')
            
            seen_urls = set()
            for link in links:
                url = link.get('href', '')
                if not url or url in seen_urls:
                    continue
                    
                if url.startswith('/'):
                    url = 'https://www.sciencedaily.com' + url
                    
                title = link.get_text(strip=True)
                if len(title) < 10:
                    continue
                
                date_match = re.search(r'/releases/(\d{4})/(\d{2})/(\d{2})(\d{2})(\d{2})(\d{2})\.htm', url)
                if date_match:
                    year, month, day = date_match.group(1), date_match.group(2), date_match.group(3)
                    date_str = f"{year}-{month}-{day}"
                else:
                    date_str = ''
                
                seen_urls.add(url)
                news_list.append({
                    'title': title,
                    'url': url,
                    'source': 'ScienceDaily Brain',
                    'date': self._parse_date(date_str)
                })
                
                if len(news_list) >= 30:
                    break
            
            logger.info(f"  - ScienceDaily Brain: {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"获取 ScienceDaily Brain 失败: {e}")
            return []
    
    def _parse_date(self, date_str: str) -> str:
        """解析并标准化日期格式为 YYYY-MM-DD"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        try:
            # 尝试多种日期格式
            formats = [
                '%Y-%m-%d',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%d %b %Y',
                '%B %d, %Y'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str[:19] if 'T' in date_str else date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except:
                    continue
            
            # 如果所有格式都失败，返回今天的日期
            return datetime.now().strftime('%Y-%m-%d')
            
        except Exception as e:
            logger.warning(f"日期解析失败 '{date_str}': {e}")
            return datetime.now().strftime('%Y-%m-%d')
    
    def _filter_recent_news(self, news_list: List[Dict], days: int = 2) -> List[Dict]:
        """过滤最近几天的新闻"""
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        filtered = []
        for news in news_list:
            if news['date'] >= cutoff_str:
                filtered.append(news)
        
        return filtered
    
    def fetch_article_content(self, url: str) -> Dict:
        """
        获取文章详细内容
        
        Args:
            url: 文章URL
            
        Returns:
            包含 title, abstract, full_text 的字典
        """
        try:
            logger.info(f"正在获取文章详情: {url}")
            response = requests.get(url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 根据不同网站使用不同的解析策略
            if 'nature.com' in url:
                return self._parse_nature_article(soup, url)
            elif 'sciencedaily.com' in url:
                return self._parse_sciencedaily_article(soup, url)
            elif 'science.org' in url:
                return self._parse_science_article(soup, url)
            else:
                return {'title': '未知', 'abstract': '', 'full_text': '', 'url': url}
                
        except Exception as e:
            logger.error(f"获取文章详情失败 {url}: {e}")
            return {'title': '未知', 'abstract': '', 'full_text': '', 'url': url}
    
    def _parse_nature_article(self, soup: BeautifulSoup, url: str) -> Dict:
        """解析 Nature 文章"""
        title_elem = soup.select_one('h1.c-article-title, h1')
        title = title_elem.get_text(strip=True) if title_elem else '未知'
        
        abstract_elem = soup.select_one('div#Abs1-content, div.c-article-section__content')
        abstract = abstract_elem.get_text(strip=True) if abstract_elem else ''
        
        # 获取文章主体
        body_elem = soup.select_one('div.c-article-body, article')
        if body_elem:
            for script in body_elem(['script', 'style']):
                script.decompose()
            full_text = body_elem.get_text(separator='\n', strip=True)
        else:
            full_text = abstract
        
        return {
            'title': title,
            'abstract': abstract,
            'full_text': full_text[:3000],  # 限制长度
            'url': url
        }
    
    def _parse_sciencedaily_article(self, soup: BeautifulSoup, url: str) -> Dict:
        """解析 ScienceDaily 文章"""
        title_elem = soup.select_one('#headline')
        title = title_elem.get_text(strip=True) if title_elem else '未知'
        
        intro_elem = soup.select_one('#abstract')
        abstract = intro_elem.get_text(strip=True) if intro_elem else ''
        
        story_elem = soup.select_one('#story_text')
        if story_elem:
            for script in story_elem(['script', 'style']):
                script.decompose()
            full_text = story_elem.get_text(separator='\n', strip=True)
        else:
            full_text = abstract
        
        return {
            'title': title,
            'abstract': abstract,
            'full_text': full_text[:3000],
            'url': url
        }
    
    def _parse_science_article(self, soup: BeautifulSoup, url: str) -> Dict:
        """解析 Science 文章"""
        title_elem = soup.select_one('h1.article__headline, h1')
        title = title_elem.get_text(strip=True) if title_elem else '未知'
        
        abstract_elem = soup.select_one('div.article__summary, p.article__teaser')
        abstract = abstract_elem.get_text(strip=True) if abstract_elem else ''
        
        body_elem = soup.select_one('div.article__body, article')
        if body_elem:
            for script in body_elem(['script', 'style']):
                script.decompose()
            full_text = body_elem.get_text(separator='\n', strip=True)
        else:
            full_text = abstract
        
        return {
            'title': title,
            'abstract': abstract,
            'full_text': full_text[:3000],
            'url': url
        }


def fetch_all_news() -> List[Dict]:
    """
    获取所有新闻源的标题
    
    Returns:
        新闻列表，包含基本信息
    """
    fetcher = MultiSourceNewsFetcher()
    news_list = fetcher.fetch_all_news_titles()
    return news_list


if __name__ == '__main__':
    # 测试
    news = fetch_all_news()
    print(f"\n总共获取 {len(news)} 条新闻")
    for i, item in enumerate(news[:10], 1):
        print(f"\n{i}. [{item['source']}] {item['title']}")
        print(f"   日期: {item['date']}")
        print(f"   URL: {item['url']}")
