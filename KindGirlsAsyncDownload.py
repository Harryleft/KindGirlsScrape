import hashlib
import logging
import time
import aiofiles
from retrying import retry
from pyquery import PyQuery as pq
import re
from os.path import exists
from os import makedirs
from datetime import datetime
import aiohttp
import asyncio

# 起始ID
START_ID = 10701
# 结束
END_ID = 10800
# 并发控制
CONCURRENCY = 50
semaphore = asyncio.Semaphore (CONCURRENCY)

# 格式化时间
dt = datetime.now ()
download_time = dt.strftime ('%Y-%m-%d')

# 设置logging
logging.basicConfig (level=logging.INFO,
                     format='%(asctime)s - %(levelname)s : %(message)s')
# 首页地址
MAIN_URL = 'https://www.kindgirls.com/gallery.php?id={model_id}'

# HEADER
HEADER = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
}

async def parse_page(model_url):
    """
    :param model_url:model UrL地址
    :return:返回model基本信息
    """
    logging.info('Scraping url : %s ', model_url)

    # 获取详情页的HTML
    async with semaphore:

        model_html = pq(model_url)
        # 获取model姓名
        model_name = model_html.find ('#up_izq h3').text ()

        # 获取model界面id
        pattern = re.compile (r'id=(\d+)')
        model_id = re.search (pattern, model_url)

        # 存储图片URL
        model_photo_urls = []

        # 迭代获取url
        for item in model_html ('.gal_list a').items ():
            # 使用正则表达式获取URL
            urls = re.findall ("""<a[^>]+href=["']([^'"<>]+)["'][^<>]+/?>""", str (item))
            for url in urls:
                 model_photo_urls.append (url)

        # 使用字典存储
        model_photos = {
                    'model_id': model_id.group (1),
                    'model_name': model_name,
                    'model_urls': model_photo_urls
        }

        return model_photos


async def save_data(model_data):
    """
    将图片保存至本地路径
    :param model_data:包含'model_name','model_id','model_urls'
    :return:
    """
    async with semaphore:
        start_time = time.time()
        # 获取id和name
        model_id = model_data.get('model_id')
        model_name = model_data.get('model_name')
        for model_url in model_data.get('model_urls'):
            # 设置路径
            MODEL_DATA_PATH = f'KindGirls/KindGirls_{download_time}/{model_name}/{model_name}_{model_id}'
            exists (MODEL_DATA_PATH) or makedirs (MODEL_DATA_PATH)

            # 异步下载到本地
            async with aiohttp.ClientSession(headers=HEADER) as session:
                async with session.get (model_url) as response:
                    fileName = hashlib.sha256(model_url.encode('utf-8')).hexdigest ()
                    async with aiofiles.open(f'{MODEL_DATA_PATH}/{fileName}.jpg', 'wb') as afp:
                        logging.info ('Now Saving model name is %s, model id is : %s , FileName : %s',
                                      model_name,
                                      model_id, fileName)
                        await afp.write(await response.content.read())
                        end_time = time.time ()
                        print('Time :', end_time - start_time)
                        await afp.close()





# 装饰器retry
@retry(stop_max_attempt_number=10, retry_on_result= lambda x: x is False)
async def main():
    """
    主程序
    :return:
    """
    async with aiohttp.ClientSession(headers=HEADER, timeout=600) as session:
        # 设置tasks
        tasks = [asyncio.ensure_future(save_data(await parse_page(MAIN_URL.format(model_id=model_id))))
                 for model_id in range(START_ID, END_ID + 1) ]
        await asyncio.wait(tasks)
        # 关闭会话
        await session.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop ()
    loop.run_until_complete((main ()))
