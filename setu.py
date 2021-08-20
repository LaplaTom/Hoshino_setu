import os
import random
import re
#import requests
import time
import aiohttp

from nonebot.exceptions import CQHttpError

from hoshino import R, Service, priv
from hoshino.util import FreqLimiter, DailyNumberLimiter
from hoshino.typing import CQEvent, MessageSegment

_max = 5
EXCEED_NOTICE = f'您今天已经冲过{_max}次了，请明早5点后再来！'
_nlmt = DailyNumberLimiter(_max)
_flmt = FreqLimiter(5)

sv = Service('setu', manage_priv=priv.SUPERUSER, enable_on_default=True, visible=False)
setu_folder = R.img('setu/').path

def setu_gener():
    while True:
        filelist = os.listdir(setu_folder)
        random.shuffle(filelist)
        for filename in filelist:
            if os.path.isfile(os.path.join(setu_folder, filename)):
                yield R.img('setu/', filename)

setu_gener = setu_gener()

def get_setu():
    return setu_gener.__next__()

async def download(url, path):
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            content = await resp.read()
            with open(path, 'wb') as f:
                f.write(content)

@sv.on_fullmatch(('来份涩图', '来份色图', '来点色图', '来点涩图', '色图', '涩图'))
async def setu(bot, ev):
    """随机叫一份涩图，对每个用户有冷却时间"""
    uid = ev['user_id']
    if not _nlmt.check(uid):
        await bot.send(ev, EXCEED_NOTICE, at_sender=True)
        return
    if not _flmt.check(uid):
        await bot.send(ev, '您冲得太快了，请稍候再冲', at_sender=True)
        return
    _flmt.start_cd(uid)
    _nlmt.increase(uid)

    # conditions all ok, send a setu.
    pic = get_setu()
    try:
        await bot.send(ev, os.path.split(str(pic.path))[1]+pic.cqcode)
    except CQHttpError:
        sv.logger.error(f"发送图片{pic.path}失败")
        try:
            await bot.send(ev, '涩图太涩，发不出去勒...')
        except:
            pass

@sv.on_prefix(('我要看色图','我要看涩图'))
async def choose_setu(bot, ev):
    uid = ev['user_id']
    if not _nlmt.check(uid):
        await bot.send(ev, EXCEED_NOTICE, at_sender=True)
        return
    if not _flmt.check(uid):
        await bot.send(ev, '您冲得太快了，请稍候再冲', at_sender=True)
        return
    _flmt.start_cd(uid)
    _nlmt.increase(uid)
    text = str(ev.message).strip()
    if not text or text=="":
        await bot.send(ev, '请在后面加上要专门看的涩图名字~')
        return
    # conditions all ok, send a setu.
    try:
        text=text+".jpg"
        text=text.replace(".jpg.jpg",".jpg")
        text=text.replace(".png.jpg",".png")
        setuname=os.path.join(setu_folder,text)
        await bot.send(ev, str(MessageSegment.image(f'file:///{os.path.abspath(setuname)}')) + '\n客官，这是您点的涩图~')
    except CQHttpError:
        sv.logger.error(f"发送图片{setuname}失败")
        try:
            await bot.send(ev, 'T T涩图不知道为什么发不出去勒...')
        except:
            pass


@sv.on_prefix('请笑纳')
async def give_setu(bot, ev:CQEvent):
    #text = str(ev.message).strip()
    try:
       # ticks = int(time.time())
        ticks=time.strftime("%Y%m%d%H%M%S", time.localtime())
        setuname=str(ev['user_id'])+"_"+str(ticks)+"_setu"
        
        if not str(ev.message).strip() or str(ev.message).strip()=="":
            await bot.send(ev, '发涩图发涩图~')
            return
        for i,seg in enumerate(ev.message):
         #   print("??????????????",seg)
            if seg.type == 'image':
                img_url = seg.data['url']
              #  with open(os.path.join(setu_folder,setuname+str(i)+".jpg"), 'wb') as fp:
             #       fp.write(requests.get(img_url).content)
                await download(img_url, os.path.join(setu_folder,setuname+str(i)+".jpg"))
        await bot.send(ev, f'涩图{setuname}批次收到了~')
    except Exception as e:
        print("yichang",e)
        await bot.send(ev, 'wuwuwu~涩图不知道在哪~')

@sv.on_prefix(('删除涩图', '删除色图'))
async def del_setu(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '抱歉，您非管理员，无此指令使用权限')
    text = str(ev.message).strip()
    if not text or text=="":
        await bot.send(ev, '请在后面加上要删除的涩图名字~')
        return
    try:
        text=text+".jpg"
        text=text.replace(".jpg.jpg",".jpg")
        text=text.replace(".png.jpg",".png")
        os.remove(os.path.join(setu_folder, text))
        await bot.send(ev, 'OvO~涩图删掉了~')
    except:
        await bot.send(ev, 'QAQ~删涩图的时候出现了问题，但一定不是我的问题~')



