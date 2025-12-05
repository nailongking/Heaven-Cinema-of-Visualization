#coding=utf-8
import re
import requests
import json
from lxml import etree
import time
import os
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_page(url):
    #定义请求头
    try:
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://movie.douban.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        }
        #发起请求
        print(f"正在请求URL: {url}")
        res = requests.get(url=url, headers=headers, verify=False, timeout=10)
        #判断请求是否成功
        if res.status_code == 200:
            print("请求成功！")
            response = res.content.decode("utf-8")
            return response
        else:
            print(f"请求失败，状态码: {res.status_code}")
            return None
    except Exception as e:
        print(f"请求异常: {e}")
        return None

def parse_data(html, page_num):
    #使用xpath进行数据解析
    try:
        html = etree.HTML(html)
        
        # 检查是否成功解析HTML
        if html is None:
            print("HTML解析失败")
            return [], [], []
        
        # 获取所有电影项目的根节点 - 使用更通用的选择器
        movie_items = html.xpath('//div[@class="item"]')
        print(f"找到 {len(movie_items)} 个电影项目")
        
        if not movie_items:
            print("没有找到电影项目，可能是页面结构变化")
            return [], [], []
        
        title_data = []
        estimate_score = []
        paming_data = []
        image_urls = []
        infor_data = []
        category_data = []  # 存储电影类别
        director_data = []  # 存储导演信息
        year_data = []      # 存储上映年份
        country_data = []   # 存储国家/地区
        
        for item in movie_items:
            # 从每个电影项目中提取数据
            # 电影标题 - 使用更精确的选择器
            title = item.xpath('.//span[@class="title"][1]/text()')
            if not title:
                title = item.xpath('.//a/span[@class="title"][1]/text()')
            title_data.append(title[0] if title else "未知")
            
            # 评分
            score = item.xpath('.//span[@class="rating_num"]/text()')
            estimate_score.append(score[0] if score else "0.0")
            
            # 排名
            rank = item.xpath('.//em/text()')
            paming_data.append(rank[0] if rank else "0")
            
            # 图片URL
            img = item.xpath('.//img/@src')
            image_urls.append(img[0] if img else "")
            
            # 简介/引语
            quote = item.xpath('.//span[@class="inq"]/text()')
            infor_data.append(quote[0] if quote else "")
            
            # 提取电影详细信息
            info_text = item.xpath('.//div[@class="bd"]/p[1]//text()')
            if info_text:
                # 清理文本
                cleaned_info = [text.strip() for text in info_text if text.strip()]
                
                # 导演信息通常在第一个非空文本节点
                if cleaned_info:
                    director_text = cleaned_info[0]
                    director_data.append(director_text)
                else:
                    director_data.append("未知")
                
                # 年份、国家和类别信息通常在最后一个非空文本节点
                if len(cleaned_info) > 1:
                    detail_text = cleaned_info[-1]
                    # 分割详细信息
                    parts = detail_text.split('/')
                    if len(parts) >= 3:
                        year = parts[0].strip() if parts[0].strip() else "未知"
                        country = parts[1].strip() if parts[1].strip() else "未知"
                        categories = parts[2].strip() if parts[2].strip() else "未知"
                    elif len(parts) == 2:
                        year = parts[0].strip() if parts[0].strip() else "未知"
                        country = "未知"
                        categories = parts[1].strip() if parts[1].strip() else "未知"
                    else:
                        year = "未知"
                        country = "未知"
                        categories = detail_text
                    
                    year_data.append(year)
                    country_data.append(country)
                    category_data.append(categories)
                else:
                    year_data.append("未知")
                    country_data.append("未知")
                    category_data.append("未知")
            else:
                director_data.append("未知")
                year_data.append("未知")
                country_data.append("未知")
                category_data.append("未知")
        
        print(f"解析结果 - 标题: {len(title_data)}, 评分: {len(estimate_score)}, 排名: {len(paming_data)}, 图片: {len(image_urls)}, 简介: {len(infor_data)}, 类别: {len(category_data)}")
        
        # 生成图片文件名列表
        image_filenames = []
        for i, (url, title, rank) in enumerate(zip(image_urls, title_data, paming_data)):
            if url:  # 确保URL不为空
                # 清理文件名中的非法字符
                clean_title = re.sub(r'[\\/*?:"<>|]', "", title)
                # 从URL中提取原始文件名
                original_filename = url.split("/")[-1]
                # 组合成新文件名：排名_电影名称_原始文件名
                filename = f"{rank}_{clean_title}_{original_filename}"
                image_filenames.append(filename)
            else:
                image_filenames.append("")
        
        # 组合所有数据
        datalist = list(zip(title_data, estimate_score, paming_data, image_filenames, infor_data, 
                           director_data, year_data, country_data, category_data, image_urls))
        
        datamore = [{
            "电影名称": i[0], 
            "评分": i[1], 
            "排名": i[2], 
            "电影海报文件名": i[3],
            "电影宣传语": i[4],
            "导演": i[5],
            "上映年份": i[6],
            "国家/地区": i[7],
            "电影类别": i[8],
            "原始海报URL": i[9]
        } for i in datalist]
        
        return datamore, image_urls, image_filenames
    except Exception as e:
        print(f"解析数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return [], [], []

def download_image(image_urls, image_filenames):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://movie.douban.com/'
    }
    
    try:
        # 过滤掉空URL
        valid_data = [(url, filename) for url, filename in zip(image_urls, image_filenames) if url]
        print(f"准备下载 {len(valid_data)} 张图片")
        
        success_count = 0
        for url, filename in valid_data:
            time.sleep(1.5)  # 避免大规模访问导致网站崩
            
            try:
                # 添加 verify=False 禁用SSL验证，增加timeout
                response = requests.get(url, headers=headers, verify=False, timeout=15)
                if response.status_code == 200:
                    dir_name = './haobao'
                    if not os.path.exists(dir_name):
                        os.makedirs(dir_name)  # 使用makedirs更安全
                    
                    file_path = os.path.join(dir_name, filename)
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    print(f"成功下载图片: {filename}")
                    success_count += 1
                else:
                    print(f"下载失败，状态码: {response.status_code}, URL: {url}")
            except Exception as e:
                print(f"下载图片失败: {url}, 错误: {e}")
                continue  # 跳过当前图片，继续下一个
        
        print(f"图片下载完成，成功下载 {success_count}/{len(valid_data)} 张图片")
    except Exception as e:
        print(f"下载图片时出错: {e}")
        import traceback
        traceback.print_exc()

def save_to_json(datamore, json_path):
    """将数据保存到JSON文件"""
    try:
        with open(json_path, 'a+', encoding='utf-8') as f:
            for a in datamore:
                print(f"写入数据: {a['电影名称']} - 评分: {a['评分']} - 类别: {a['电影类别']}")
                f.write(json.dumps(a, ensure_ascii=False))
                f.write("\n")
        print(f"成功写入 {len(datamore)} 条数据到 {json_path}")
        return True
    except Exception as e:
        print(f"写入文件失败: {e}")
        return False

def main(num, page_num, json_path):
    #定义url
    url = f'https://movie.douban.com/top250?start={num}'
    print(f"开始处理第{page_num}页: {url}")
    
    #调用请求函数
    html = get_page(url)
    if html:
        #调用解析函数，和下载函数
        datamore, image_urls, image_filenames = parse_data(html, page_num)
        if datamore:  # 只有解析到数据才下载图片和保存数据
            # 保存数据到JSON
            save_to_json(datamore, json_path)
            # 下载图片
            download_image(image_urls, image_filenames)
            return True
        else:
            print("没有解析到数据，跳过此页")
            return False
    else:
        print("获取页面失败，跳过此页")
        return False

if __name__ == "__main__":
    # 确保数据文件存在
    json_path = "./douban.json"
    if os.path.exists(json_path):
        # 清空现有文件内容
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write("")
        print(f"清空文件: {json_path}")
    else:
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write("")  # 创建空文件
        print(f"创建文件: {json_path}")
    
    # 检查文件权限
    try:
        with open(json_path, 'a', encoding='utf-8') as f:
            f.write("测试\n")  
        print("文件写入权限正常")
    except Exception as e:
        print(f"文件写入权限异常: {e}")
    
    print("开始爬取豆瓣Top250数据...")
    success_pages = 0
    for i in range(10): 
        print(f"\n正在爬取第{i+1}页数据")
        if main(i*25, i+1, json_path):
            success_pages += 1
        print(f"第{i+1}页数据处理完成，等待3秒...")
        time.sleep(3)  #
    print(f"\n数据爬取完成！成功处理 {success_pages}/10 页数据")
    
    
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines:
                print(f"JSON文件中有 {len(lines)} 条数据")
                print("\n前3条数据示例:")
                for i, line in enumerate(lines[:3]):
                    data = json.loads(line.strip())
                    print(f"{i+1}. {data['电影名称']}")
                    print(f"   评分: {data['评分']}")
                    print(f"   排名: {data['排名']}")
                    print(f"   导演: {data['导演']}")
                    print(f"   年份: {data['上映年份']}")
                    print(f"   国家: {data['国家/地区']}")
                    print(f"   类别: {data['电影类别']}")
                    print(f"   宣传语: {data['电影宣传语']}")
                    print(f"   图片: {data['电影海报文件名']}")
                    print()
            else:
                print("JSON文件为空")
    else:
        print("JSON文件不存在")
    
    
    image_dir = "./haobao"
    if os.path.exists(image_dir):
        image_files = os.listdir(image_dir)
        print(f"\n图片文件夹中有 {len(image_files)} 张图片")
        if image_files:
            print("前5张图片示例:")
            for i, filename in enumerate(image_files[:5]):
                print(f"{i+1}. {filename}")
    else:
        print("图片文件夹不存在")