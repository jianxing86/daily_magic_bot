"""
每日报告机器人主程序
整合所有模块，生成并发送每日报告
"""
import argparse
import logging
from datetime import datetime
from config import config
from weather_parser import parse_weather_files
from gemini_processor import process_daily_report
from email_sender import EmailSender


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_config():
    """验证配置"""
    errors = config.validate()
    if errors:
        logger.error("配置验证失败:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    return True


def generate_daily_report():
    """生成每日报告"""
    try:
        logger.info("=" * 60)
        logger.info("开始生成每日报告")
        logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        # 1. 解析天气数据
        logger.info("\n[1/3] 获取并解析天气数据...")
        weather_data = parse_weather_files(
            config.BEIJING_WEATHER_URL,
            config.JINAN_WEATHER_URL
        )
        logger.info(f"  - 北京天气: {weather_data['beijing'].get('weather', '未知')}")
        logger.info(f"  - 济南天气: {weather_data['jinan'].get('weather', '未知')}")
        
        # 2. 获取科学新闻（多源）
        logger.info("\n[2/4] 获取科学新闻...")
        from news_fetcher import fetch_all_news
        news_list = fetch_all_news()
        logger.info(f"  - 获取到 {len(news_list)} 条新闻")
        
        # 3. AI处理（统一流程）
        logger.info("\n[3/4] AI处理数据（统一请求）...")
        ai_result = process_daily_report(weather_data, news_list)
        
        logger.info(f"  - 角色: {ai_result['character']}")
        logger.info(f"  - 筛选出 {len(ai_result['processed_news'])} 条重点新闻")
        
        # 4. 生成邮件
        logger.info("\n[4/4] 生成邮件...")
        sender = EmailSender(
            config.SMTP_SERVER,
            config.SMTP_PORT,
            config.SENDER_EMAIL,
            config.SENDER_PASSWORD
        )
        
        # 准备邮件数据
        processed_data = {
            'greeting': ai_result['greeting'],
            'character': ai_result['character'],
            'weather_advice': ai_result['weather_advice']
        }
        processed_news = ai_result['processed_news']
        
        html_content = sender.create_html_email(weather_data, processed_data, processed_news)
        logger.info("  - 邮件HTML已生成")
        
        return html_content, sender
        
    except Exception as e:
        logger.error(f"生成报告失败: {e}", exc_info=True)
        raise


def create_test_email() -> str:
    """创建简单的测试邮件（不消耗API token）"""
    from datetime import datetime
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{{{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 40px 20px;
            background-color: #f9f9f9;
        }}}}
        .container {{{{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            text-align: center;
        }}}}
        h1 {{{{
            color: #2c3e50;
            font-size: 24px;
            margin-bottom: 20px;
        }}}}
        p {{{{
            color: #555;
            line-height: 1.6;
            margin: 10px 0;
        }}}}
        .success {{{{
            color: #27ae60;
            font-weight: bold;
            font-size: 18px;
        }}}}
    </style>
</head>
<body>
    <div class="container">
        <h1>📧 邮件测试</h1>
        <p class="success">✓ 邮件配置正常</p>
        <p>如果您收到这封邮件，说明SMTP配置正确。</p>
        <p>时间: {current_time}</p>
    </div>
</body>
</html>
    """
    
    return html


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='每日报告机器人')
    parser.add_argument('--test', action='store_true', help='测试模式（保存HTML到文件）')
    parser.add_argument('--no-send', action='store_true', help='不发送邮件（与--test配合使用）')
    parser.add_argument('--email-test', action='store_true', help='发送测试邮件（不消耗API token）')
    args = parser.parse_args()
    
    try:
        # 验证配置
        if not validate_config():
            logger.error("配置验证失败，程序退出")
            return 1
        
        # 邮件测试模式：发送简单测试邮件
        if args.email_test:
            logger.info("=" * 60)
            logger.info("邮件测试模式")
            logger.info("=" * 60)
            
            html_content = create_test_email()
            sender = EmailSender(
                config.SMTP_SERVER,
                config.SMTP_PORT,
                config.SENDER_EMAIL,
                config.SENDER_PASSWORD
            )
            
            subject = f"邮件测试 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            logger.info(f"\n正在发送测试邮件到: {', '.join(config.RECEIVER_EMAILS)}")
            success = sender.send_email(config.RECEIVER_EMAILS, subject, html_content)
            
            if success:
                logger.info("\n" + "=" * 60)
                logger.info("✓ 测试邮件发送成功！")
                logger.info("=" * 60)
                return 0
            else:
                logger.error("\n" + "=" * 60)
                logger.error("✗ 测试邮件发送失败")
                logger.error("=" * 60)
                return 1
        
        # 正常模式：生成完整报告
        html_content, sender = generate_daily_report()
        
        # 测试模式：保存HTML到文件
        if args.test:
            output_file = f"/tmp/daily_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"\n✓ 测试模式：邮件HTML已保存到 {output_file}")
        
        # 发送邮件
        if not args.no_send:
            today = datetime.now().strftime('%Y-%m-%d')
            subject = f"每日魔法报告-{today}"
            
            logger.info(f"\n正在发送邮件到: {', '.join(config.RECEIVER_EMAILS)}")
            success = sender.send_email(config.RECEIVER_EMAILS, subject, html_content)
            
            if success:
                logger.info("\n" + "=" * 60)
                logger.info("✓ 每日报告发送成功！")
                logger.info("=" * 60)
                return 0
            else:
                logger.error("\n" + "=" * 60)
                logger.error("✗ 邮件发送失败")
                logger.error("=" * 60)
                return 1
        else:
            logger.info("\n✓ 跳过邮件发送（--no-send 参数）")
            return 0
        
    except Exception as e:
        logger.error(f"\n程序执行失败: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())
