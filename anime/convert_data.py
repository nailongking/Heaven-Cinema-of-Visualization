import pandas as pd
import json
import re

# 读取 Excel 文件
df = pd.read_excel('douban_movies_unified_china_final.xlsx')

# 定义一个清洗年份的函数（提取前4位数字）
def clean_year(val):
    match = re.search(r'\d{4}', str(val))
    return int(match.group()) if match else 0

# 准备存放 JSON 的列表
json_data = []

for index, row in df.iterrows():
    # 构建每一条电影的数据字典
    item = {
        "title": row['电影名称'],
        "rating": float(row['评分']),
        "rank": int(row['排名']),
        # 拼接本地路径：文件夹名 + 文件名
        "poster": f"haobao/{row['电影海报文件名']}", 
        "quote": str(row['电影宣传语']) if pd.notna(row['电影宣传语']) else "",
        "director": str(row['导演']),
        "year": clean_year(row['上映年份']),
        "region": str(row['国家/地区']),
        "genre": str(row['电影类别'])
    }
    json_data.append(item)

# 保存为 data.json，确保中文不乱码
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(json_data, f, ensure_ascii=False, indent=2)

print(f"成功转换 {len(json_data)} 条数据到 data.json！")