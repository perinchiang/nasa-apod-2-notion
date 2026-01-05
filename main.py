import requests
import json
import os
from datetime import datetime

# ================= 配置区 (改为读取环境变量) =================
# 这里的名字必须和 GitHub Secrets 里的名字一一对应
NASA_API_KEY = os.environ.get("NASA_API_KEY")
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
# =========================================================

def get_apod():
    """获取 NASA 每日天文图"""
    if not NASA_API_KEY:
        print("❌ 错误: 未找到 NASA_API_KEY")
        return None
        
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ NASA API Error: {response.text}")
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

    # 提取数据
    title = data.get("title", "No Title")
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    explanation = data.get("explanation", "")[:2000] # 截断防止超长
    image_url = data.get("hdurl", data.get("url")) 
    copyright_text = data.get("copyright", "Public Domain")

    # 构建 Payload
    payload = {
        "parent": {"database_id": DATABASE_ID},
        "cover": {
            "type": "external",
            "external": {"url": image_url}
        },
        "properties": {
            "Name": {
                "title": [{"text": {"content": title}}]
            },
            "Date": {
                "date": {"start": date}
            },
            "Explanation": {
                "rich_text": [{"text": {"content": explanation}}]
            },
            "Copyright": {
                "rich_text": [{"text": {"content": copyright_text}}]
            }
        }
    }
    
    # 视频容错处理
    if "youtube" in image_url or "vimeo" in image_url:
        if "cover" in payload:
            del payload["cover"]

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        print(f"✅ 成功发布到 Notion: {title}")
    else:
        print(f"❌ Notion API Error: {response.text}")

if __name__ == "__main__":
    print("🚀 开始运行 NASA APOD 同步任务...")
    apod_data = get_apod()
    if apod_data:
        create_notion_page(apod_data)
