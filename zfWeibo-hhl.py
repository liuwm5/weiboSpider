import requests
from requests.adapters import HTTPAdapter
import re
from lxml import etree
from lxml import html as htm
import pandas as pd
import json
import numpy as np
import time
import random
import datetime
import os
import xlrd
import xlwt
import excelSave as save
import urllib.parse

headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36'}
# headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:79.0) Gecko/20100101 Firefox/79.0'}
requests.packages.urllib3.disable_warnings()
session = requests.Session()
# 爬虫运行过程中可能出现网页请求错误，设置尝试3次
session.mount('http://', HTTPAdapter(max_retries=3))

# 爬一段时间要手动更换一次，因为登录的时候绕不过验证码，我只能手动更新，即微博登录-手动扒cookie，填到这里
cookies = {
    'cookie': ''}


# 创建文件，用这个包如果数据重复的话提示数据重复，不会写入
def web_crawler(book_name_xls, sheet_name_xls):
    if os.path.exists(book_name_xls):
        print("文件已存在")
    else:
        print("文件不存在，重新创建")
        # 表头
        value_title = [["用户名称", "微博等级", "发送时间", "@对象", "是否原博", "博文内容", "原博内容", "点赞数", "转发数", "评论数"], ]
        save.write_excel_xls(book_name_xls, sheet_name_xls, value_title)


# url构造-时间，因为微博最多返回100页数据，所以时间间隔要尽量缩短才能获得更多数据，start 和 end首尾斜街且数量对应
def get_time(start, end, space):  # 传入形式为字符串，如'20190601','20200721','1D'
    time_range = pd.date_range(start, end, freq=space)
    starttime = [i.strftime('%Y%m%d') for i in time_range[0:-1]]
    endtime = [i.strftime('%Y%m%d') for i in time_range[1::]]
    return starttime, endtime


start, end = get_time('20200501', '20200731', '1D')
# start,end

for k in range(len(start)):
    starttime = start[k]
    endtime = end[k]


# print(starttime,endtime)


# 获取页面内容
def get_page_contents(data, path):
    html = etree.HTML(data.text.encode('utf-8'))
    #     judge = re.compile(u'[\u4e00-\u9fa5]')
    #     if not judge.findall(data.text):
    #         html = etree.HTML(data.content)
    counts = html.xpath('count(//div/@id)') - 1
    for i in range(int(counts)):
        #         可能存在有些博文没有内容只有图片，所以每次写入之后要初始化，防止串行
        at = ''
        like = ''
        repost = ''
        img = ''
        original_contents = ''
        contents = ''
        try:
            lst_id = html.xpath('//div[@class="pm"]//form/@action')[0][-6::]  # 获取检索页面id
            user_id = html.xpath('//div/@id')[i]  # 用户id
            user_name = html.xpath('//a[@class="nk"]/text()')[i]  # 用户名称
            #     微博等级
            try:  # 如果报错则为普通
                user_class = html.xpath('//div[@id="%s"]//div[1]/img/@alt' % user_id)[0]
            except:
                user_class = '普通用户'
            send_time = html.xpath('//div[@id="%s"]//span[@class="ct"]/text()' % user_id)[0][0:12]  # 发布时间
            if '2019' in send_time:
                send_time = html.xpath('//div[@id="%s"]//span[@class="ct"]/text()' % user_id)[0][0:19]
            comment = html.xpath('//div[@id="%s"]//div//a[@class="cc"]/text()' % user_id)[-1]  # 评论数量

            # 判断是否为原博，是否有图片，获取博文内容、原博内容、点赞数和转发数。
            # 在是否转发、有图没图的情况下数据存放位置也是不一样的，要多看多测试html
            try:
                img = html.xpath('//div[@id="%s"]//div[2]//img/@alt' % user_id)[0]  # 如果原博无图则找不到img
            except:
                pass
            whether = html.xpath('//div[@id="%s"]//div//span[@class="cmt"]/text()' % user_id)
            if whether:
                original = 'False'
                original_content = html.xpath('//div[@id="%s"]//div/span[@class="ctt"]/text()' % user_id)
                for m in original_content:
                    original_contents += ''.join(m.replace(' ', '').replace('\xa0', ''))
                if img == '图片':
                    all_ = html.xpath('//div[@id="%s"]//div[3]//a/text()' % user_id)
                    content = html.xpath('//div[@id="%s"]//div[3]/text()' % user_id)
                    for n in content:
                        contents += ''.join(n.replace(' ', '').replace('\xa0', ''))
                else:
                    all_ = html.xpath('//div[@id="%s"]//div[2]//a/text()' % user_id)
                    content = html.xpath('//div[@id="%s"]//div[2]/text()' % user_id)
                    for n in content:
                        contents += ''.join(n.replace(' ', '').replace('\xa0', ''))
                for item in all_:
                    item.replace('http://', '')
                    if '@' in item:
                        at += item
                    if '赞' in item:
                        like += item
                    if '转发' in item:
                        repost += item
            else:
                original = 'True'
                content = html.xpath('//div[@id="%s"]//div/span[@class="ctt"]/text()' % user_id)
                for n in content:
                    contents += ''.join(n.replace(' ', '').replace('\xa0', ''))
                for att in html.xpath('//div[@id="%s"]//div//span[@class="ctt"]/a/text()' % user_id):
                    att.replace('http://', '')
                    at += att
                if img == '图片':
                    all_ = html.xpath('//div[@id="%s"]//div[2]//a/text()' % user_id)
                else:
                    all_ = html.xpath('//div[@id="%s"]//div[1]//a/text()' % user_id)
                for item in all_:
                    if '赞' in item:
                        like += item
                    if '转发' in item:
                        repost += item

            #     数据保存
            value1 = [
                [user_name, user_class, send_time, at, original, contents, original_contents, like, repost, comment], ]
            save.write_excel_xls_append_norepeat(path, value1)
        except BaseException as be:
            print(be)
            print(i)


# 网页获取
def get_page(keyword, start, end, space, path):
    starttime, endtime = get_time(start, end, space)  # 最后运行的时候要输入的字段包括三个时间一个Keyword以及文件存放的path
    for k in range(len(starttime)):
        try:
            start = starttime[k]
            end = endtime[k]
            url = r'https://weibo.cn/search/mblog?hideSearchFrame=&keyword={}&advancedfilter=1&starttime={}&endtime={}&sort=time&page=1'.format(
                keyword, start, end)
            data = session.get(url, headers=headers, cookies=cookies, timeout=20, verify=False)  # 因为只有先爬下第一页才知道总页数是多少，后面要循环几次
            time.sleep(random.randint(1, 3))
            # 获取总页数
            try:
                page_pattern = 'value="跳页" />&nbsp;1/(.*?)页</div>'
                page_re = re.compile(page_pattern)
                page = page_re.findall(data.text)[0]
                print('开始爬取！共{}页'.format(page))
                get_page_contents(data, path)

                for num in range(2, int(page)):
                    page_url = r'https://weibo.cn/search/mblog?hideSearchFrame=&keyword={}&advancedfilter=1&starttime={}&endtime={}&sort=time&page={}'.format(
                        keyword, start, end, num)
                    page_data = session.get(page_url, headers=headers, cookies=cookies, timeout=20, verify=False)
                    time.sleep(0.5)
                    get_page_contents(page_data, path)
            except:
                get_page_contents(data, path)
        except BaseException as be:
            print(be)
            print(start, end)
            time.sleep(100)


def covert_label_urlencode(str):
    '''
    返回## 的urlencode
    :param str:
    :return:
    '''
    # return urllib.parse.quote(str)
    return urllib.parse.quote("#" + str + "#")


start = '20200401'
end = '20201109'
# scenics = {'东方明珠', '外滩', '上海迪士尼', '上海城隍庙', '田子坊', '豫园'}
scenics = {'黄鹤楼'}
for scenic in scenics:
    path = r"E:\IPython\爬虫\\" + scenic + "[" + start + "-" + end + "].xls";
    web_crawler(path, '微博数据')
    url = r'https://weibo.cn/search/mblog?hideSearchFrame=&keyword={}&advancedfilter=1&starttime={}&endtime={}&sort=time&page=1'.format(
        covert_label_urlencode(scenic), start, end)
    print(url)
    # keyword编码要在开发者工具里找
    get_page(covert_label_urlencode(scenic), start, end, '10D', path)
