import pandas as pd
import json
import re

# 1. 读取 Excel
print("正在读取 Excel...")
try:
    df = pd.read_excel('douban_movies_unified_china_final.xlsx')
    print("Excel 读取成功。")
except Exception as e:
    print(f"读取失败: {e}")
    exit()

# 2. 筛选动漫电影

df = df.dropna(subset=['电影类别', '导演'])

anime_df = df[df['电影类别'].str.contains('动画', na=False)].copy()
print(f"筛选出 {len(anime_df)} 部动画电影。")


def clean_director_name(val):

    s = str(val).strip()
    

    s = re.sub(r'^导演[:：]?\s*', '', s)

    s = s.replace("['", "").replace("']", "").replace("'", "").replace('"', "")
    
  
    first_person = s.split('/')[0].strip()
    

    chinese_match = re.search(r'[\u4e00-\u9fa5·]+', first_person)
    
    if chinese_match:
   
        return chinese_match.group(0)
    else:
  
        return first_person.split(' ')[0]

# 3. 开始分组
director_groups = {}
debug_names = []

for index, row in anime_df.iterrows():
    raw_dir = row['导演']
    clean_dir = clean_director_name(raw_dir)
    
    # 记录日志
    debug_names.append(f"原始: {str(raw_dir)[:15]}... -> 清洗后: {clean_dir}")
    
    if clean_dir not in director_groups:
        director_groups[clean_dir] = []
        
    item = {
        "name": row['电影名称'],
        "rating": float(row['评分']),
        "rank": int(row['排名']),
        # 确保路径拼接正确
        "poster": f"haobao/{row['电影海报文件名']}",
        "quote": str(row['电影宣传语']) if pd.notna(row['电影宣传语']) else "",
        "year": row['上映年份'],
        "value": 1 
    }
    director_groups[clean_dir].append(item)

# 4. 打印调试信息
print("\n--- 导演名字清洗抽样检查 (修复版) ---")
for log in debug_names[:5]:
    print(log)

print(f"\n--- 分组统计 ---")
print(f"共归类为 {len(director_groups)} 个导演组。")

if len(director_groups) <= 1:
    print("警告：依然只分了一个组，请检查正则表达式！")
else:
    # 按作品数量排序
    sorted_directors = sorted(director_groups.items(), key=lambda x: len(x[1]), reverse=True)
    print("Top 5 导演及其作品数:")
    for d, movies in sorted_directors[:5]:
        print(f"  [{d}]: {len(movies)} 部")

# 5. 构建 JSON
tree_data = {
    "name": "Anime Universe",
    "children": []
}

for director, movies in director_groups.items():
    if director and director != "None":
        tree_data["children"].append({
            "name": director,
            "children": movies
        })

# 6. 保存
with open('anime_data.json', 'w', encoding='utf-8') as f:
    json.dump(tree_data, f, ensure_ascii=False, indent=2)

print(f"\nJSON 生成成功！")