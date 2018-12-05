# -*- coding:utf-8 -*-

import urllib2
import cookielib
import urllib
import re
import zlib
from lxml import etree
from lxml.html import tostring,fromstring
import sys
import json
import time
reload(sys)
sys.setdefaultencoding('utf-8')

def dump(res):
    print res.getcode()
    print res.geturl()
    print res.info()

def unzip_content(res):
    html_content = res.read()
    ziped = res.info().getheader('Content-Encoding')
    if ziped:
        html_content = zlib.decompress(html_content,16+zlib.MAX_WBITS)
    return html_content

def build_postdata_lianjia(html_content):
    lt = re.compile(r'name="lt" value="([^\"]*)"').findall(html_content)[0]
    execution = re.compile(r'name="execution" value="([^\"]*)"').findall(html_content)[0]
    eventid = re.compile(r'name="_eventId" value="([^\"]*)"').findall(html_content)[0]
    userinfo = {
        'username':'',
        'password':'',
        'lt':lt,
        'execution':execution,
        '_eventId':eventid,
        'redirect':'http://sz.lianjia.com/',
        'verifyCode':'',
        'code':''
    }
    postdata = urllib.urlencode(userinfo)
    return postdata

# direct
res = urllib2.urlopen('http://sz.lianjia.com')
dump(res)

# with cookie
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Pragma': 'no-cache',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36',
}

cookie = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
urllib2.install_opener(opener)
req = urllib2.Request('http://sz.lianjia.com',headers=headers)
res = opener.open(req)
dump(res)

# login lianjia
res = urllib2.urlopen('https://passport.lianjia.com/cas/login?service=http%3A%2F%2Fsz.lianjia.com%2F')
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://passport.lianjia.com',
    'Pragma': 'no-cache',
    'Referer': 'https://passport.lianjia.com/cas/login?service=http%3A%2F%2Fsz.lianjia.com%2F',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36',
}
postdata = build_postdata_lianjia(unzip_content(res))
req = urllib2.Request('https://passport.lianjia.com/cas/login?service=http%3A%2F%2Fsz.lianjia.com%2F', data=postdata, headers=headers)
res = opener.open(req)
dump(res)

# get xiaoqu info
req = urllib2.Request('https://sz.lianjia.com/xiaoqu/')
res = opener.open(req)
dump(res)
html = unzip_content(res)
selector = etree.HTML(html)
xiaoqus = selector.xpath('/html/body/div[3]/div[1]/dl[2]/dd/div/div/a/@href')
for i in xiaoqus:
    print i
xiaoqu_urls = ['https://sz.lianjia.com'+i for i in xiaoqus]

def chengjiao_spider(xiaoqu_id,pg2=1,recur2=True):
    time.sleep(1)
    chengjiao_url = 'https://sz.lianjia.com/chengjiao/pg{0}c{1}'.format(pg2,xiaoqu_id)
    print chengjiao_url
    req2 = urllib2.Request(chengjiao_url)
    res2 = urllib2.urlopen(req2,timeout=5)
    html2 = unzip_content(res2)
    selector2 = etree.HTML(html2)
    chengjiao_list = selector2.xpath('//html/body/div[5]/div[1]/ul/li')
    for chengjiao_info in chengjiao_list:
        chengjiao_name = fromstring(tostring(chengjiao_info)).xpath('//li/div/div[1]/a/text()')[0]
        chengjiao_price = fromstring(tostring(chengjiao_info)).xpath('//li/div/div[2]/div[3]/span/text()')[0]
        chengjiao_floor = fromstring(tostring(chengjiao_info)).xpath('//li/div/div[3]/div[3]/span/text()')[0]
        chengjiao_date = fromstring(tostring(chengjiao_info)).xpath('//li/div/div[2]/div[2]/text()')[0]
        save_chengjiao(chengjiao_name,chengjiao_price,chengjiao_floor,chengjiao_date)
    if recur2:
        next_page2 = selector2.xpath('/html/body/div[5]/div[1]/div[5]/div[2]/div/@page-data')
        total_page2 = int(json.loads(next_page2[0])['totalPage']) if next_page2 else 0
        for i in range(2,total_page2+1):
            chengjiao_spider(xiaoqu_id,pg2=i,recur2=False)

def save_chengjiao(chengjiao_name,chengjiao_price,chengjiao_floor,chengjiao_date):
    with open('chengjiao_data','a') as f2:
        f2.write(';'.join([chengjiao_name,chengjiao_price,chengjiao_floor,chengjiao_date]))
        f2.write('\n')
    print chengjiao_name,chengjiao_price,chengjiao_floor,chengjiao_date

def save_xiaoqu(xiaoqu_name,xiaoqu_link,xiaoqu_price):
    with open('lianjia_data','a') as f:
        f.write(','.join([xiaoqu_name,xiaoqu_link,xiaoqu_price]))
        f.write('\n')
    print xiaoqu_name,xiaoqu_link,xiaoqu_price

def xiaoqu_spider(xiaoqu_url,recur=True):
    time.sleep(1)
    req = urllib2.Request(xiaoqu_url)
    res = urllib2.urlopen(req,timeout=5)
    html = unzip_content(res)
    selector = etree.HTML(html)
    xiaoqu_list = selector.xpath('//html/body/div[4]/div[1]/ul/li')
    for xiaoqu_info in xiaoqu_list:
        #print fromstring(tostring(xiaoqu_info)).xpath('//li/div[1]/div[1]/a/text()')[0]
        xiaoqu_name = fromstring(tostring(xiaoqu_info)).xpath('//li/div[1]/div[1]/a/text()')[0]
        xiaoqu_link = fromstring(tostring(xiaoqu_info)).xpath('//li/div[1]/div[1]/a/@href')[0]
        xiaoqu_price = fromstring(tostring(xiaoqu_info)).xpath('//li/div[2]/div[1]/div[1]/span/text()')[0]
        save_xiaoqu(xiaoqu_name,xiaoqu_link,xiaoqu_price)
        chengjiao_spider(xiaoqu_link.rstrip('/').split('/')[-1])

    if recur:
        next_page = selector.xpath('/html/body/div[4]/div[1]/div[3]/div[2]/div/@page-data')
        total_page = int(json.loads(next_page[0])['totalPage']) if next_page else 0
        for i in range(2,total_page+1):
            xiaoqu_spider(xiaoqu_url + '/pg{0}'.format(i),recur=False)

for xiaoqu_url in xiaoqu_urls:
    xiaoqu_spider(xiaoqu_url)
