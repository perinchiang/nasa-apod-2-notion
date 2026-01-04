import requests
import os
import json
from bs4 import BeautifulSoup
from datetime import datetime

# ================= 配置区 =================
# 不需要 NASA_API_KEY 了！只需要 Notion 的配置
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
# =========================================

def scrape_apod():
    """直接从 HTML 抓取数据，绕过 API Key"""
    url = "https://apod.nasa.gov/apod/astropix.html"
    try:
        # 伪装成浏览器 User-Agent，防止被反爬
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # 解析 HTML
        soup = BeautifulSoup(response.content, "html.parser")
        
        # 1. 抓取图片
        # NASA 官网结构很简单，通常图片在 <img src="...">
        img_tag = soup.find("img")
        if not img_tag:
            # 有时候是视频（iframe），这里做个简单的处理
            iframe = soup.find("iframe")
            if iframe:
                print("⚠️ 今天是视频，尝试抓取缩略图或跳过...")
                image_url = iframe["src"] # 视频链接
            else:
                print("❌ 未找到图片")
                return None
        else:
            image_url = "https://apod.nasa.gov/apod/" + img_tag["src"]
        
        # 2. 抓取标题 (通常在 <center> 里的 <b>)
        # 寻找包含年月日信息的上一级
        center_tags = soup.find_all("center")
        title = "NASA APOD"
        if len(center_tags) >= 2:
            # 通常标题在第二个 center 标签里的 b 标签
            title_tag = center_tags[1].find("b")
            if title_tag:
                title = title_tag.text.strip()
        
        # 3. 抓取解释 (Explanation)
        text_content = soup.get_text()
        explanation = "Check the image!"
        if "Explanation:" in text_content:
            # 截取 Explanation 之后的内容
            parts = text_content.split("Explanation:")
            if len(parts) > 1:
                # 再截取 "Tomorrow's picture" 之前的内容
                explanation = parts[1].split("Tomorrow's picture")[0].strip()
                explanation = explanation[:1500] # Notion 限制长度
            
        print(f"✅ 成功抓取官网: {title}")
        
        return {
            "title": title,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "url": image_url,
            "explanation": explanation,
            "copyright": "NASA APOD (Public Domain)"
        }
        
    except Exception as e:
        print(f"❌ 抓取网页失败: {e}")
        return None

def create_notion_page(data):
    """创建 Notion 页面"""
    if not NOTION_TOKEN or not DATABASE_ID:
        print("❌ 错误: 未找到 Notion Token 或 Database ID")
        return

    url = "https://api.notion.com/v1/pages"
    
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    payload = {
        "parent": {"database_id": DATABASE_ID},
        "cover": {
            "type": "external",
            "external": {"url": data["url"]}
        },
        "properties": {
            "Name": {
                "title": [{"text": {"content": data["title"]}}]
            },
            "Date": {
                "date": {"start": data["date"]}
            },
            "Explanation": {
                "rich_text": [{"text": {"content": data["explanation"]}}]
            },
            "Copyright": {
                "rich_text": [{"text": {"content": data["copyright"]}}]
            }
        }
    }
    
    # 如果是视频链接，Notion Cover 不支持，删掉 cover 字段
    if "youtube" in data["url"] or "vimeo" in data["url"]:
        del payload["cover"]

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        print(f"✅ 成功发布到 Notion: {data['title']}")
    else:
        print(f"❌ Notion API Error: {response.text}")

if __name__ == "__main__":
    print("🚀 开始运行 NASA APOD (免Key版)...")
    apod_data = scrape_apod()
    if apod_data:
        create_notion_page(apod_data)
