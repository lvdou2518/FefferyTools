'''
Created on Fri Jul 19 14:59:05 2019

@author: feffery
Email:fefferypzy@gmail.com

这个脚本提供一些基本的工具，清单如下:
GetLatLng:单线程版的地址->经纬度(高德)工具
LngLatTransfer:实现百度、火星坐标系、WGS84、web墨卡托四种坐标之间互相转换
GetDistanceViaLngLat:根据经纬度计算两点之间的真实球面距离(单位：m)
MyThread:用键值对维系输入与输出的方式，将任意单线程函数改造成任意线程数的多线程版本以加速运算
Shp2JSON:将Shp格式文件转换为GeoJSON格式
JSON2Shp:将GeoJSON格式文件转换为Shp格式
'''

import requests
import math
import warnings
import threading
from tqdm import tqdm
import codecs
import shapefile
import os
import json
warnings.filterwarnings("ignore")


def GetLatLng(address):
    '''
    这个脚本利用高德的官网接口来获取文本地址对应解析出的经纬度
    :param address:文本地址，需要去除特殊符号和括号内容
    :return:经度纬度
    '''
    print(address)
    while True:
        try:
            html = requests.get(
                f'https://www.amap.com/service/poiTipslite?&city=500000&type=dir&words={address}')
            result = eval(html.text)
            lng, lat = float(result['data']['tip_list'][0]['tip']['x']),float(result['data']['tip_list'][0]['tip']['y'])
            break
        except Exception as e:
            print(f'重试！{address}')
            pass

    return lng,lat

class LngLatTransfer():

    def __init__(self):
        self.x_pi = 3.14159265358979324 * 3000.0 / 180.0
        self.pi = math.pi  # π
        self.a = 6378245.0  # 长半轴
        self.es = 0.00669342162296594323  # 偏心率平方
        pass

    def GCJ02_to_BD09(self, gcj_lng, gcj_lat):
        """
        实现GCJ02向BD09坐标系的转换
        :param lng: GCJ02坐标系下的经度
        :param lat: GCJ02坐标系下的纬度
        :return: 转换后的BD09下经纬度
        """
        z = math.sqrt(gcj_lng * gcj_lng + gcj_lat * gcj_lat) + 0.00002 * math.sin(gcj_lat * self.x_pi)
        theta = math.atan2(gcj_lat, gcj_lng) + 0.000003 * math.cos(gcj_lng * self.x_pi)
        bd_lng = z * math.cos(theta) + 0.0065
        bd_lat = z * math.sin(theta) + 0.006
        return bd_lng, bd_lat


    def BD09_to_GCJ02(self, bd_lng, bd_lat):
        '''
        实现BD09坐标系向GCJ02坐标系的转换
        :param bd_lng: BD09坐标系下的经度
        :param bd_lat: BD09坐标系下的纬度
        :return: 转换后的GCJ02下经纬度
        '''
        x = bd_lng - 0.0065
        y = bd_lat - 0.006
        z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * self.x_pi)
        theta = math.atan2(y, x) - 0.000003 * math.cos(x * self.x_pi)
        gcj_lng = z * math.cos(theta)
        gcj_lat = z * math.sin(theta)
        return gcj_lng, gcj_lat


    def WGS84_to_GCJ02(self, lng, lat):
        '''
        实现WGS84坐标系向GCJ02坐标系的转换
        :param lng: WGS84坐标系下的经度
        :param lat: WGS84坐标系下的纬度
        :return: 转换后的GCJ02下经纬度
        '''
        dlat = self._transformlat(lng - 105.0, lat - 35.0)
        dlng = self._transformlng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * self.pi
        magic = math.sin(radlat)
        magic = 1 - self.es * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((self.a * (1 - self.es)) / (magic * sqrtmagic) * self.pi)
        dlng = (dlng * 180.0) / (self.a / sqrtmagic * math.cos(radlat) * self.pi)
        gcj_lng = lat + dlat
        gcj_lat = lng + dlng
        return gcj_lng, gcj_lat


    def GCJ02_to_WGS84(self, gcj_lng, gcj_lat):
        '''
        实现GCJ02坐标系向WGS84坐标系的转换
        :param gcj_lng: GCJ02坐标系下的经度
        :param gcj_lat: GCJ02坐标系下的纬度
        :return: 转换后的WGS84下经纬度
        '''
        dlat = self._transformlat(gcj_lng - 105.0, gcj_lat - 35.0)
        dlng = self._transformlng(gcj_lng - 105.0, gcj_lat - 35.0)
        radlat = gcj_lat / 180.0 * self.pi
        magic = math.sin(radlat)
        magic = 1 - self.es * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((self.a * (1 - self.es)) / (magic * sqrtmagic) * self.pi)
        dlng = (dlng * 180.0) / (self.a / sqrtmagic * math.cos(radlat) * self.pi)
        mglat = gcj_lat + dlat
        mglng = gcj_lng + dlng
        lng = gcj_lng * 2 - mglng
        lat = gcj_lat * 2 - mglat
        return lng, lat


    def BD09_to_WGS84(self, bd_lng, bd_lat):
        '''
        实现BD09坐标系向WGS84坐标系的转换
        :param bd_lng: BD09坐标系下的经度
        :param bd_lat: BD09坐标系下的纬度
        :return: 转换后的WGS84下经纬度
        '''
        lng, lat = self.BD09_to_GCJ02(bd_lng, bd_lat)
        return self.GCJ02_to_WGS84(lng, lat)


    def WGS84_to_BD09(self, lng, lat):
        '''
        实现WGS84坐标系向BD09坐标系的转换
        :param lng: WGS84坐标系下的经度
        :param lat: WGS84坐标系下的纬度
        :return: 转换后的BD09下经纬度
        '''
        lng, lat = self.WGS84_to_GCJ02(lng, lat)
        return self.GCJ02_to_BD09(lng, lat)


    def _transformlat(self, lng, lat):
        ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
              0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
        ret += (20.0 * math.sin(6.0 * lng * self.pi) + 20.0 *
                math.sin(2.0 * lng * self.pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(lat * self.pi) + 40.0 *
                math.sin(lat / 3.0 * self.pi)) * 2.0 / 3.0
        ret += (160.0 * math.sin(lat / 12.0 * self.pi) + 320 *
                math.sin(lat * self.pi / 30.0)) * 2.0 / 3.0
        return ret


    def _transformlng(self, lng, lat):
        ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
              0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
        ret += (20.0 * math.sin(6.0 * lng * self.pi) + 20.0 *
                math.sin(2.0 * lng * self.pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(lng * self.pi) + 40.0 *
                math.sin(lng / 3.0 * self.pi)) * 2.0 / 3.0
        ret += (150.0 * math.sin(lng / 12.0 * self.pi) + 300.0 *
                math.sin(lng / 30.0 * self.pi)) * 2.0 / 3.0
        return ret

    def WGS84_to_WebMercator(self, lng, lat):
        '''
        实现WGS84向web墨卡托的转换
        :param lng: WGS84经度
        :param lat: WGS84纬度
        :return: 转换后的web墨卡托坐标
        '''
        x = lng * 20037508.342789 / 180
        y = math.log(math.tan((90 + lat) * self.pi / 360)) / (self.pi / 180)
        y = y * 20037508.34789 / 180
        return x, y

    def WebMercator_to_WGS84(self, x, y):
        '''
        实现web墨卡托向WGS84的转换
        :param x: web墨卡托x坐标
        :param y: web墨卡托y坐标
        :return: 转换后的WGS84经纬度
        '''
        lng = x / 20037508.34 * 180
        lat = y / 20037508.34 * 180
        lat = 180 / self.pi * (2 * math.atan(math.exp(lat * self.pi / 180)) - self.pi / 2)
        return lng, lat


def GetDistanceViaLngLat(lng1,lat1,lng2,lat2):
    '''
    这个函数用于根据传入的一对经纬度计算两个点之间的球面距离（单位：m）
    :param lng1:
    :param lat1:
    :param lng2:
    :param lat2:
    :return:
    '''
    rad1 = lat1 * math.pi / 180.0
    rad2 = lat2 * math.pi / 180.0
    a = rad1 - rad2
    b = lng1 * math.pi / 180.0 - lng2 * math.pi /180.0
    r = 6378137
    distance = r*2*math.asin(math.sqrt(math.sin(a/2)**2
                                       + math.cos(rad1)*math.cos(rad2)*math.sin(b/2)**2))

    return distance

class MyThread(threading.Thread):

    def __init__(self, threadID,key,func):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.key = key
        self.func = func


    def run(self):
        print('开始线程：' ,self.threadID)
        self.func(self.key)
        print('结束线程：' ,self.threadID)

def Shp2JSON(filename,shp_encoding='ANSI',json_encoding='utf-8'):
    '''
    这个函数用于将
    :param filename:
    :param shp_encoding:
    :param json_encoding:
    :return:
    '''

    '''创建shp IO连接'''
    reader = shapefile.Reader(filename,encoding=shp_encoding)

    '''提取所有field部分内容'''
    fields = reader.fields[1:]

    '''提取所有field的名称'''
    field_names = [field[0] for field in fields]

    '''初始化要素列表'''
    buffer = []

    for sr in tqdm(reader.shapeRecords()):
        '''提取每一个矢量对象对应的属性值'''
        record = sr.record

        '''属性转换为列表'''
        record = [r.decode('gb2312','ignore') if isinstance(r, bytes)
                  else r for r in record]

        '''对齐属性与对应数值的键值对'''
        atr = dict(zip(field_names, record))

        '''获取当前矢量对象的类型及矢量信息'''
        geom = sr.shape.__geo_interface__

        '''向要素列表追加新对象'''
        buffer.append(dict(type="Feature",
                           geometry=geom,
                           properties=atr))

    '''写出GeoJSON文件'''
    geojson = codecs.open(filename + "-geo.json","w", encoding=json_encoding)
    geojson.write(json.dumps({"type":"FeatureCollection",
                              "features":buffer}) + '\n')
    geojson.close()
    print('转换成功！')

def JSON2Shp(filename,json_encoding='utf-8',shp_encoding='utf-8'):
    '''
    这个函数用于将GeoJSON格式文件转换为Shp格式
    :param filename:
    :param json_encoding:
    :param shp_encoding:
    :return:
    '''
    with open(filename,encoding=json_encoding) as j:
        GeoJSON = json.load(j)

    fieldType_dict = {
        str:'C',
        int:'N',
        float:'F',
        bool:'L',
        list:'C'
    }

    writer = shapefile.Writer(filename.replace('.json',''),
                              autoBalance=1,
                              encoding=shp_encoding)
    field2type = {}
    for key,value in GeoJSON['features'][0]['properties'].items():
        field2type[key] = \
            fieldType_dict[
            type(value)
            ]
    for key,value in field2type.items():
        writer.field(key,value)
    for item in GeoJSON['features']:
        try:
            writer.poly(item['geometry']['coordinates'][0])
        except:
            writer.poly(item['geometry']['coordinates'])
        writer.record(**item['properties'])

    writer.close()
    print('转换成功！')


if __name__ == '__main__':

    pass

