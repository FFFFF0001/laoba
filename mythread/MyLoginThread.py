# #coding:utf-8
import ctypes
import logging

import requests
from PyQt4 import QtCore
from PyQt4.QtCore import *

from common.common import req_session
from myutil.MyTool import getCurrentTimestamp


class MyLoginThread(QtCore.QThread):
    def __init__(self, overlay, console):
        QtCore.QThread.__init__(self)
        self.overlay = overlay
        self.console = console
        lines = str(self.console.linesEntry.toPlainText())
        lines = lines.split('\n')

        self.loginUrl = str(lines[0])
        self.host = self.loginUrl.replace("http://", "").split('/')[0]
        self.rootUrl = "http://" + self.host
        self.path = self.host + ''
        self.origin_url = ""
        self.headers = {}

        logging.info(u"【登录线程】: lineText=%s" % lines)
        logging.info(u"【登录线程】: loginUrl=%s" % self.loginUrl)
        logging.info(u"【登录线程】: host=%s" % self.host)
        logging.info(u"【登录线程】: rootUrl=%s" % self.rootUrl)
        logging.info(u"【登录线程】: path=%s" % self.path)

    # 从antivc获取验证码错误返回error
    def getCheckcode(self):
        dll = ctypes.windll.LoadLibrary('./config/AntiVC.dll')
        a = dll.LoadCdsFromFile('./config/laobapro.cds', '123qwe')
        yzm = '99999'
        file = './config/checkcode.png'
        if a != -1:
            ttt = dll.GetVcodeFromFile(a, file, yzm)
            return yzm
        else:
            return 'error'

    def login(self):
        get_code_url1 = self.rootUrl + "/getCodeInfo/.auth?u=0.7473080656164435&systemversion=4_6&.auth"

        r1 = requests.Request('GET', get_code_url1)
        prep1 = req_session.prepare_request(r1)
        rr1 = req_session.send(prep1, stream=False, timeout=10)

        # r = requests.get(get_code_url1, timeout=10)
        a = rr1.content
        b = a.split('_')[0]
        __VerifyValue = a.split('_')[1]
        get_code_url2 = self.rootUrl + "/getVcode/.auth?t=%s&systemversion=4_6&.auth" % b

        r2 = requests.Request('GET', get_code_url2)
        prep2 = req_session.prepare_request(r2)
        rr2 = req_session.send(prep2, stream=False, timeout=10)

        # r = requests.get(get_code_url2, timeout=10)
        with open('./config/checkcode.png', 'wb') as f:
            f.write(rr2.content)

        code = self.getCheckcode()
        logging.info(u"【登录】验证码=%s" % code)
        headers = {
            'Host': self.host,
            'Proxy-Connection': 'keep-alive',
            'Accept': '*/*',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36',
            'ajax': 'true',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Origin': 'http://' + self.host,
            'Referer': self.loginUrl,
        }

        payload = {
            'VerifyCode': code,
            '__VerifyValue': __VerifyValue,
            '__name': str(self.console.userEntry.text()),
            'password': str(self.console.passEntry.text()),
            'isSec': 0,
            'cid': 1229,
            'cname': '星际',
            'systemversion': '4_6'
        }

        r3 = requests.Request('POST', self.rootUrl + "/loginVerify/.auth", data=payload, headers=headers)
        prep3 = req_session.prepare_request(r3)
        rr3 = req_session.send(prep3, stream=False, timeout=5)

        # r = requests.post(self.rootUrl + "/loginVerify/.auth", data=payload, headers=headers, timeout=5)
        real_content = rr3.content.split('êêê')[0]
        real_content = real_content.replace('\xef\xbb\xbf', '')  # 去掉BOM开头的\xef\xbb\xbf
        a = real_content.split('\n')
        logging.info(u"【登录线程】登录body=%s" % a)
        logging.info(u"【登录线程】登录header=%s" % r3.headers)

        recheck_url = a[1].replace('host', self.host)
        cookies_jar = requests.cookies.RequestsCookieJar()
        a = rr3.headers['Set-Cookie']
        b = a.split('/,')
        ddd = "mobiLogin=0; sysinfo=ssc%7C1%7Cb%7Cuc%7Cbeishu100; navNum=0; "
        for i in b:
            if i[-6:] != 'path=/':
                i = i + '/'
            i = i[1:]
            if 'sys' in i:
                continue

            c = i.split(';')
            d = c[0].split('=')
            e = c[1].split('=')
            if '_' in e[1]:
                self.origin_url = "http://" + self.host + e[1]
            cookies_jar.set(d[0], d[1], path=e[1])
            if d[0] in ['PHPSESSID', 'AC']:
                d[1] = d[1].replace(' ', '')
                ddd += "%s=%s;" % (d[0], d[1])

        logging.info(u"【登录】cookies_jar=%s" % cookies_jar)

        headers2 = {
            'Host': 'pc10.sss66.us',
            'Proxy-Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://pc10.sss66.us/scowa1414556f/.auth',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        self.headers = headers2
        logging.info(u"【登录线程】再次校验URL=%s" % recheck_url)

        r4 = requests.Request('GET', recheck_url, cookies=cookies_jar, headers=headers2)
        prep4 = req_session.prepare_request(r4)
        req_session.send(prep4, stream=False, timeout=10)

        # r = requests.get(recheck_url, cookies=cookies_jar, headers=headers2, timeout=10)
        # r.close()
        return cookies_jar

    def run(self):
        try:
            if False:
                # if self.console.fake_mode:
                cookies_jar = {'AC': 1}
            else:
                cookies_jar = self.login()

            if 'AC' in cookies_jar:
                name = self.console.nameEntry.text()
                name += u"【已登录】"
                QMetaObject.invokeMethod(self.console.parent, "mySetWindowTitle", Qt.QueuedConnection, Q_ARG(str, name))

                now = getCurrentTimestamp()
                self.pk_pre_bet_get_data_url = self.origin_url.split("index.htm")[
                                                   0] + 'pk/order/list?&_=%s__autorefresh' % now
                self.pk_post_bet_url = self.origin_url.split("index.htm")[
                                           0] + 'pk/order/leftInfo/?post_submit&&_=%s__ajax' % now
                logging.info(">>>origin_url=%s" % self.origin_url)
                logging.info(">>>pk_pre_bet_get_data_url=%s" % self.pk_pre_bet_get_data_url)
                logging.info(">>>pk_post_bet_url=%s" % self.pk_post_bet_url)

                # 把牛逼的参数传回去
                data_dic = {
                    "cookies_jar": cookies_jar,
                    "origin_url": self.origin_url,
                    "pk_pre_bet_get_data_url": self.pk_pre_bet_get_data_url,
                    "pk_post_bet_url": self.pk_post_bet_url,
                    "headers": self.headers
                }

                # 一旦登录成功，这开始获取两个数据：预下注数据 + 历史数据
                QMetaObject.invokeMethod(self.console, "onGetPreBetDataHideBtn", Qt.QueuedConnection,
                                         Q_ARG(dict, data_dic))
                QMetaObject.invokeMethod(self.console, "onGetHistoryResultDataHideBtn", Qt.QueuedConnection,
                                         Q_ARG(dict, data_dic))
                QMetaObject.invokeMethod(self.console, "onLoginSuccess", Qt.QueuedConnection)

            else:
                msg = u"获取数据异常..."
                QMetaObject.invokeMethod(self.console, "onLoginFailed", Qt.QueuedConnection, Q_ARG(str, msg))
                name = self.console.nameEntry.text()
                QMetaObject.invokeMethod(self.console.parent, "mySetWindowTitle", Qt.QueuedConnection, Q_ARG(str, name))
        except Exception, ex:
            logging.error(ex, exc_info=1)
            msg = u"登录失败，可能是动态获取验证码出问题，请重试！"
            QMetaObject.invokeMethod(self.console, "onLoginFailed", Qt.QueuedConnection, Q_ARG(str, msg))
            name = self.console.nameEntry.text()
            QMetaObject.invokeMethod(self.console.parent, "mySetWindowTitle", Qt.QueuedConnection, Q_ARG(str, name))
        finally:
            QMetaObject.invokeMethod(self.overlay, "myclose", Qt.QueuedConnection)
