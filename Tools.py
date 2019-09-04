'''
Created on Fri Jul 19 14:59:05 2019

@author: feffery
Email:fefferypzy@gmail.com

����ű��ṩһЩ�����Ĺ��ߣ��嵥����:
GetLatLng:���̰߳�ĵ�ַ->��γ��(�ߵ�)����
LngLatTransfer:ʵ�ְٶȡ���������ϵ��WGS84��webī������������֮�以��ת��
GetDistanceViaLngLat:���ݾ�γ�ȼ�������֮�����ʵ�������(��λ��m)
MyThread:�ü�ֵ��άϵ����������ķ�ʽ�������ⵥ�̺߳�������������߳����Ķ��̰߳汾�Լ�������
Shp2JSON:��Shp��ʽ�ļ�ת��ΪGeoJSON��ʽ
JSON2Shp:��GeoJSON��ʽ�ļ�ת��ΪShp��ʽ
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
    ����ű����øߵµĹ����ӿ�����ȡ�ı���ַ��Ӧ�������ľ�γ��
    :param address:�ı���ַ����Ҫȥ��������ź���������
    :return:����γ��
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
            print(f'���ԣ�{address}')
            pass

    return lng,lat

class LngLatTransfer():

    def __init__(self):
        self.x_pi = 3.14159265358979324 * 3000.0 / 180.0
        self.pi = math.pi  # ��
        self.a = 6378245.0  # ������
        self.es = 0.00669342162296594323  # ƫ����ƽ��
        pass

    def GCJ02_to_BD09(self, gcj_lng, gcj_lat):
        """
        ʵ��GCJ02��BD09����ϵ��ת��
        :param lng: GCJ02����ϵ�µľ���
        :param lat: GCJ02����ϵ�µ�γ��
        :return: ת�����BD09�¾�γ��
        """
        z = math.sqrt(gcj_lng * gcj_lng + gcj_lat * gcj_lat) + 0.00002 * math.sin(gcj_lat * self.x_pi)
        theta = math.atan2(gcj_lat, gcj_lng) + 0.000003 * math.cos(gcj_lng * self.x_pi)
        bd_lng = z * math.cos(theta) + 0.0065
        bd_lat = z * math.sin(theta) + 0.006
        return bd_lng, bd_lat


    def BD09_to_GCJ02(self, bd_lng, bd_lat):
        '''
        ʵ��BD09����ϵ��GCJ02����ϵ��ת��
        :param bd_lng: BD09����ϵ�µľ���
        :param bd_lat: BD09����ϵ�µ�γ��
        :return: ת�����GCJ02�¾�γ��
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
        ʵ��WGS84����ϵ��GCJ02����ϵ��ת��
        :param lng: WGS84����ϵ�µľ���
        :param lat: WGS84����ϵ�µ�γ��
        :return: ת�����GCJ02�¾�γ��
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
        ʵ��GCJ02����ϵ��WGS84����ϵ��ת��
        :param gcj_lng: GCJ02����ϵ�µľ���
        :param gcj_lat: GCJ02����ϵ�µ�γ��
        :return: ת�����WGS84�¾�γ��
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
        ʵ��BD09����ϵ��WGS84����ϵ��ת��
        :param bd_lng: BD09����ϵ�µľ���
        :param bd_lat: BD09����ϵ�µ�γ��
        :return: ת�����WGS84�¾�γ��
        '''
        lng, lat = self.BD09_to_GCJ02(bd_lng, bd_lat)
        return self.GCJ02_to_WGS84(lng, lat)


    def WGS84_to_BD09(self, lng, lat):
        '''
        ʵ��WGS84����ϵ��BD09����ϵ��ת��
        :param lng: WGS84����ϵ�µľ���
        :param lat: WGS84����ϵ�µ�γ��
        :return: ת�����BD09�¾�γ��
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
        ʵ��WGS84��webī���е�ת��
        :param lng: WGS84����
        :param lat: WGS84γ��
        :return: ת�����webī��������
        '''
        x = lng * 20037508.342789 / 180
        y = math.log(math.tan((90 + lat) * self.pi / 360)) / (self.pi / 180)
        y = y * 20037508.34789 / 180
        return x, y

    def WebMercator_to_WGS84(self, x, y):
        '''
        ʵ��webī������WGS84��ת��
        :param x: webī����x����
        :param y: webī����y����
        :return: ת�����WGS84��γ��
        '''
        lng = x / 20037508.34 * 180
        lat = y / 20037508.34 * 180
        lat = 180 / self.pi * (2 * math.atan(math.exp(lat * self.pi / 180)) - self.pi / 2)
        return lng, lat


def GetDistanceViaLngLat(lng1,lat1,lng2,lat2):
    '''
    ����������ڸ��ݴ����һ�Ծ�γ�ȼ���������֮���������루��λ��m��
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
        print('��ʼ�̣߳�' ,self.threadID)
        self.func(self.key)
        print('�����̣߳�' ,self.threadID)

def Shp2JSON(filename,shp_encoding='ANSI',json_encoding='utf-8'):
    '''
    ����������ڽ�
    :param filename:
    :param shp_encoding:
    :param json_encoding:
    :return:
    '''

    '''����shp IO����'''
    reader = shapefile.Reader(filename,encoding=shp_encoding)

    '''��ȡ����field��������'''
    fields = reader.fields[1:]

    '''��ȡ����field������'''
    field_names = [field[0] for field in fields]

    '''��ʼ��Ҫ���б�'''
    buffer = []

    for sr in tqdm(reader.shapeRecords()):
        '''��ȡÿһ��ʸ�������Ӧ������ֵ'''
        record = sr.record

        '''����ת��Ϊ�б�'''
        record = [r.decode('gb2312','ignore') if isinstance(r, bytes)
                  else r for r in record]

        '''�����������Ӧ��ֵ�ļ�ֵ��'''
        atr = dict(zip(field_names, record))

        '''��ȡ��ǰʸ����������ͼ�ʸ����Ϣ'''
        geom = sr.shape.__geo_interface__

        '''��Ҫ���б�׷���¶���'''
        buffer.append(dict(type="Feature",
                           geometry=geom,
                           properties=atr))

    '''д��GeoJSON�ļ�'''
    geojson = codecs.open(filename + "-geo.json","w", encoding=json_encoding)
    geojson.write(json.dumps({"type":"FeatureCollection",
                              "features":buffer}) + '\n')
    geojson.close()
    print('ת���ɹ���')

def JSON2Shp(filename,json_encoding='utf-8',shp_encoding='utf-8'):
    '''
    ����������ڽ�GeoJSON��ʽ�ļ�ת��ΪShp��ʽ
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
    print('ת���ɹ���')


if __name__ == '__main__':

    pass

