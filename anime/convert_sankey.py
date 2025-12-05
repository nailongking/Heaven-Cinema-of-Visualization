import pandas as pd
import json
import re
import math


print("正在读取 Excel...")
try:
    df = pd.read_excel('douban_movies_unified_china_final.xlsx')
except:
    print("找不到文件，请确认路径。")
    exit()

df = df.dropna(subset=['电影类别', '导演', '评分'])
anime_df = df[df['电影类别'].str.contains('动画', na=False)].copy()
print(f"筛选出 {len(anime_df)} 部动漫电影")


def clean_director_name(val):
    s = str(val).strip().replace("['", "").replace("']", "").replace("'", "").replace('"', "")
    s = re.sub(r'^导演[:：]?\s*', '', s)
    first_person = s.split('/')[0].strip()
    cn_match = re.search(r'[\u4e00-\u9fa5·]+', first_person)
    return cn_match.group(0) if cn_match else first_person.split(' ')[0]

anime_df['clean_director'] = anime_df['导演'].apply(clean_director_name)


nodes = []
node_map = {} 

def get_node_index(name):
    if name not in node_map:
        node_map[name] = len(nodes)
        nodes.append({"name": name})
    return node_map[name]

links = []

for _, row in anime_df.iterrows():
    region = str(row['国家/地区']).split(' ')[0].split('/')[0].strip()
    movie_name = row['电影名称']
    director = row['clean_director']
    rating = float(row['评分'])


    weight = math.pow(rating - 8.0, 4.5) + 0.1

 
    links.append({
        "source": get_node_index(region), 
        "target": get_node_index(movie_name), 
        "value": weight,
        "rating": rating
    })


    links.append({
        "source": get_node_index(movie_name), 
        "target": get_node_index(director), 
        "value": weight,
        "rating": rating
    })


output_data = {"nodes": nodes, "links": links}
with open('sankey_vivid_data.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print("生成完毕！差异极大的数据已保存为 sankey_vivid_data.json")