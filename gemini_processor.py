"""
Gemini AI处理模块
使用Gemini API进行内容处理和生成
"""
from google import genai
from typing import List, Dict
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiProcessor:
    """Gemini AI处理器"""
    
    def __init__(self, api_key: str):
        """
        初始化Gemini处理器
        
        Args:
            api_key: Gemini API密钥
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-2.5-flash'
        logger.info("Gemini处理器初始化成功")
    
    def generate_weather_content(self, character_name: str, weather_info: Dict) -> Dict[str, str]:
        """
        一次性生成哈利波特问候和天气建议
        
        Args:
            character_name: 角色名称
            weather_info: 天气信息
            
        Returns:
            包含 greeting, advice_beijing, advice_jinan 的字典
        """
        try:
            beijing = weather_info.get('beijing', {})
            jinan = weather_info.get('jinan', {})
            
            prompt = f"""你是哈利波特世界中的{character_name}。请根据以下天气信息，一次性生成问候语和穿衣建议。

天气数据：
- 北京：{beijing.get('weather', '未知')}，{beijing.get('temperature', '未知')}，{beijing.get('wind', '未知')}
- 济南：{jinan.get('weather', '未知')}，{jinan.get('temperature', '未知')}，{jinan.get('wind', '未知')}

请严格按照以下 JSON 格式返回（不要包含 Markdown 代码块标记）：
{{
    "greeting": "以{character_name}的第一人称口吻写的开场白（50-100字）。总结天气，语气符合角色性格，清新自然。",
    "advice_beijing": "北京的穿衣建议和注意事项（2-3行）。实用具体，包含穿衣和带伞/保暖提醒。",
    "advice_jinan": "济南的穿衣建议和注意事项（2-3行）。实用具体，包含穿衣和带伞/保暖提醒。"
}}
"""
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            
            import json
            return json.loads(response.text)
            
        except Exception as e:
            logger.error(f"生成天气内容失败: {e}")
            return {
                "greeting": f"{character_name}祝您早安！新的一天开始了！",
                "advice_beijing": "请根据天气情况适当增减衣物。",
                "advice_jinan": "请根据天气情况适当增减衣物。"
            }
    
    def summarize_news_article(self, article_content: str, title: str) -> str:
        """
        总结新闻文章
        
        Args:
            article_content: 文章全文
            title: 文章标题
            
        Returns:
            中文总结(3-5行)
        """
        try:
            prompt = f"""请阅读以下科学新闻并用中文总结（3-5行）：

标题：{title}

正文：
{article_content[:2000]}  # 限制长度避免token超限

要求：
1. 用中文总结
2. 3-5行，简洁清晰
3. 突出研究发现的关键点
4. 不要添加标题或序号
5. 直接返回总结内容
"""
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"总结文章失败: {e}")
            return "暂无总结"
    
    def translate_news_title(self, english_title: str) -> str:
        """
        将英文新闻标题翻译成中文
        
        Args:
            english_title: 英文标题
            
        Returns:
            中文标题
        """
        try:
            prompt = f"""请将以下英文新闻标题翻译成中文：

"{english_title}"

要求：
1. 翻译准确、专业
2. 保持科学术语的准确性
3. 只返回中文标题，不要其他内容
"""
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"翻译标题失败: {e}")
            return english_title  # 失败时返回原标题


    def generate_master_content(self, character_name: str, weather_info: Dict, news_list: List[Dict]) -> Dict:
        """
        一次性生成所有AI内容：问候（含新闻综述）、天气建议、新闻筛选
        
        Args:
            character_name: 角色名称
            weather_info: 天气数据
            news_list: 原始新闻列表（包含 title, url, source, date）
            
        Returns:
            JSON字典包含 greeting, advice_beijing, advice_jinan, selected_news_indices
        """
        try:
            beijing = weather_info.get('beijing', {})
            jinan = weather_info.get('jinan', {})
            
            # 构建新闻列表文本（包含来源和日期）
            news_text = ""
            for i, news in enumerate(news_list, 1):
                news_text += f"{i}. [{news.get('source', 'Unknown')}] {news['title']} ({news.get('date', '')})\n"
            
            prompt = f"""你是哈利波特世界中的{character_name}。请完成以下任务（**请全程使用中文回答**）：

1. **角色问候**：以{character_name}的第一人称口吻用中文写一段开场白（100-150字）。
   - 总结今日天气（北京和济南）。
   - **简要提及今日科学界发生的有趣事情**（根据新闻列表）。
   - 语气符合角色性格，清新自然。

2. **天气建议**：分别为北京和济南给出穿衣建议。

3. **新闻筛选**：从列表中选出 10-25 条最重要的科学新闻。
   **优先领域A - 天体物理学**（以下关键词平权）：
   - 球状星团(globular cluster)、白矮星(white dwarf)、毫秒脉冲星(millisecond pulsar)
   - 观测天体物理学(observational astrophysics)、恒星演化(stellar evolution)
   - 望远镜(telescope)、星震学(asteroseismology)
   - 中子星(neutron star)、X射线天文学(X-ray astronomy)、引力波(gravitational wave)
   - 变星(variable star)、恒星物理(stellar physics)、脉冲星(pulsar)
   
   **优先领域B - 心理学与神经科学**（以下关键词平权）：
   - 元认知(metacognition)、fMRI、脑成像(brain imaging)
   - 认知神经科学(cognitive neuroscience)、工作记忆(working memory)
   - 注意力(attention)、决策(decision making)、意识(consciousness)
   - 成瘾(addiction)、奖赏系统(reward system)、多巴胺(dopamine)
   - 心理学(psychology)、神经科学(neuroscience)
   
   **筛选原则**：
   - 如果其他领域有重大科学发现，也应包含
   - **日期优先**：同等重要性下，优先选择日期更近的新闻（今天 > 昨天）
   - 数量建议 10-25 条，如果重要新闻较多可扩展到 30 条
输入数据：
【天气】
- 北京：{beijing.get('weather', '未知')}，{beijing.get('temperature', '未知')}，{beijing.get('wind', '未知')}
- 济南：{jinan.get('weather', '未知')}，{jinan.get('temperature', '未知')}，{jinan.get('wind', '未知')}

【新闻列表】
{news_text}

请严格按照以下 JSON 格式返回（不要包含 Markdown 代码块标记）：
{{
    "greeting": "角色开场白内容...",
    "advice_beijing": "北京穿衣建议...",
    "advice_jinan": "济南穿衣建议...",
    "selected_news_indices": [1, 3, 5, ...] // 选中的新闻编号列表（数字，10-25条）
}}
"""
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            
            import json
            return json.loads(response.text)
            
        except Exception as e:
            logger.error(f"生成主要内容失败: {e}")
            return {
                "greeting": f"{character_name}祝您早安！今天的天气真不错！",
                "advice_beijing": "请注意天气变化。",
                "advice_jinan": "请注意天气变化。",
                "selected_news_indices": list(range(1, min(16, len(news_list) + 1)))
            }



    def process_news_batch(self, articles: List[Dict]) -> List[Dict]:
        """
        批量处理新闻：一次性完成标题翻译和内容总结
        
        Args:
            articles: 文章列表 [{'title': '...', 'content': '...', 'url': '...'}]
            
        Returns:
            处理后的列表 [{'title_en': '...', 'title_cn': '...', 'summary': '...', 'url': '...'}]
        """
        try:
            # 构建Prompt
            articles_text = ""
            for i, art in enumerate(articles, 1):
                # 限制每篇文章长度，避免token过多
                content_preview = art['content'][:5000]
                articles_text += f"""
文章 {i}:
标题: {art['title']}
内容: {content_preview}
---
"""
            
            prompt = f"""请批量处理以下 {len(articles)} 篇科学新闻/论文。

对于每一篇文章，请完成：
1. 将标题翻译成中文（准确、专业，保持学术风格）
2. 用中文总结文章核心内容，采用**倒金字塔结构**（先写最重要的发现/结论，再补充关键细节和背景）。总结为一个完整的小段落，可以稍长，但须精炼专业。

输入文章列表：
{articles_text}

请严格按照以下 JSON 格式返回列表（不要包含 Markdown 代码块标记）：
[
    {{
        "original_title": "原英文标题",
        "title_cn": "中文翻译标题",
        "summary": "中文总结内容（倒金字塔结构，一个小段落）"
    }},
    ...
]
"""
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            
            import json
            results = json.loads(response.text)
            
            # 合并结果
            processed_news = []
            for i, res in enumerate(results):
                if i < len(articles):
                    processed_news.append({
                        'title_en': articles[i]['title'],
                        'title_cn': res.get('title_cn', articles[i]['title']),
                        'summary': res.get('summary', '暂无总结'),
                        'url': articles[i]['url']
                    })
            
            return processed_news
            
        except Exception as e:
            logger.error(f"批量处理新闻失败: {e}")
            # 降级处理：返回原始数据
            return [{
                'title_en': art['title'],
                'title_cn': art['title'],  # 无法翻译
                'summary': 'AI处理失败，请查看原文',
                'url': art['url']
            } for art in articles]


def process_daily_report(weather_data: Dict, news_list: List[Dict]) -> Dict:
    """
    统一处理每日报告的所有AI内容
    
    Args:
        weather_data: 天气数据
        news_list: 原始新闻列表（包含 title, url, source, date）
        
    Returns:
        包含所有生成内容的字典
    """
    from config import config
    from news_fetcher import MultiSourceNewsFetcher
    
    processor = GeminiProcessor(config.GEMINI_API_KEY)
    fetcher = MultiSourceNewsFetcher()
    
    result = {
        'greeting': '',
        'weather_advice': {},
        'processed_news': [],
        'character': ''
    }
    
    try:
        # 1. 选择角色
        character = random.choice(config.HARRY_POTTER_CHARACTERS)
        result['character'] = character
        logger.info(f"选择角色: {character}")
        
        # 2. 生成主要内容（问候、建议、筛选）
        logger.info("正在生成主要内容（问候+建议+筛选）...")
        master_content = processor.generate_master_content(character, weather_data, news_list)
        
        result['greeting'] = master_content.get('greeting', '')
        result['weather_advice'] = {
            'beijing': master_content.get('advice_beijing', ''),
            'jinan': master_content.get('advice_jinan', '')
        }
        
        # 3. 处理选中的新闻
        selected_indices = master_content.get('selected_news_indices', [])
        logger.info(f"AI选中了 {len(selected_indices)} 条新闻")
        
        articles_to_process = []
        for idx in selected_indices:
            if isinstance(idx, int) and 0 <= idx - 1 < len(news_list):
                news = news_list[idx - 1]
                try:
                    # 获取文章详情
                    article = fetcher.fetch_article_content(news['url'])
                    content = article['full_text'] or article['abstract'] or "无内容"
                    
                    articles_to_process.append({
                        'title': news['title'],
                        'url': news['url'],
                        'content': content,
                        'date': news.get('date', ''),  # 保留日期
                        'source': news.get('source', '')  # 保留来源
                    })
                    
                    # 避免爬虫请求过快
                    import time
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"获取文章内容失败 {news['title']}: {e}")
                    continue
        
        # 4. 批量处理新闻内容
        if articles_to_process:
            logger.info("正在批量处理新闻内容...")
            processed = processor.process_news_batch(articles_to_process)
            
            # 添加日期和来源信息到结果中
            for i, item in enumerate(processed):
                if i < len(articles_to_process):
                    item['date'] = articles_to_process[i].get('date', '')
                    item['source'] = articles_to_process[i].get('source', '')
            
            result['processed_news'] = processed
            
        logger.info("所有AI处理完成")
        
    except Exception as e:
        logger.error(f"处理每日报告失败: {e}")
    
    return result


if __name__ == '__main__':
    # 测试代码
    from config import config
    from weather_parser import parse_weather_files
    
    # 模拟数据
    weather_data = {
        'beijing': {'weather': '晴', 'temperature': '5~15℃', 'wind': '北风3级'},
        'jinan': {'weather': '多云', 'temperature': '8~18℃', 'wind': '南风2级'}
    }
    
    news_list = [
        {'title': 'Scientists discover new planet', 'url': 'http://example.com/1'},
        {'title': 'New study on sleep patterns', 'url': 'http://example.com/2'},
        {'title': 'Breakthrough in quantum computing', 'url': 'http://example.com/3'}
    ]
    
    # AI处理
    processed_data = process_daily_report(weather_data, news_list)
    
    print(f"\n角色: {processed_data['character']}")
    print(f"问候: {processed_data['greeting']}")
    print(f"\n北京建议: {processed_data['weather_advice']['beijing']}")
    print(f"新闻数量: {len(processed_data['processed_news'])}")
