import asyncio
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

from PIL import Image, ImageDraw

from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.image.image_tools import crop_center_img

from ..utils.api.model import AccountBaseInfo, DailyData
from ..utils.api.request_util import KuroApiResp
from ..utils.database.models import WavesBind, WavesUser
from ..utils.error_reply import ERROR_CODE, WAVES_CODE_102, WAVES_CODE_103

# [修改点1] 导入字体生成器，而不是具体的字体变量
from ..utils.fonts.waves_fonts import waves_font_origin

from ..utils.image import (
    GOLD,
    GREEN,
    GREY,
    RED,
    YELLOW,
    add_footer,
    get_event_avatar,
    get_random_waves_role_pile,
    get_random_waves_bg
)
from ..utils.name_convert import char_name_to_char_id
from ..utils.resource.constant import SPECIAL_CHAR
from ..utils.waves_api import waves_api
from ..wutheringwaves_config.wutheringwaves_config import ShowConfig

TEXT_PATH = Path(__file__).parent / "texture2d"

# [修改点2] 在本地定义放大3倍后的字体对象
# 原 size * 3
waves_font_72 = waves_font_origin(72)   # 对应原 waves_font_24
waves_font_75 = waves_font_origin(75)   # 对应原 waves_font_25
waves_font_78 = waves_font_origin(78)   # 对应原 waves_font_26
waves_font_90 = waves_font_origin(90)   # 对应原 waves_font_30
waves_font_96 = waves_font_origin(96)   # 对应原 waves_font_32
waves_font_126 = waves_font_origin(126) # 对应原 waves_font_42

# 图标尺寸放大 3 倍 (40 -> 120)
YES = Image.open(TEXT_PATH / "yes.png")
YES = YES.resize((120, 120))
NO = Image.open(TEXT_PATH / "no.png")
NO = NO.resize((120, 120))
bar_down = Image.open(TEXT_PATH / "bar_down.png")

# 基础分辨率放大 3 倍 (1150x850 -> 3450x2550)
based_w = 3450
based_h = 2550


async def seconds2hours(seconds: int) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return "%02d小时%02d分" % (h, m)


async def process_uid(uid, ev):
    ck = await waves_api.get_self_waves_ck(uid, ev.user_id, ev.bot_id)
    if not ck:
        return None

    # 并行请求所有相关 API
    results = await asyncio.gather(
        waves_api.get_daily_info(uid, ck),
        waves_api.get_base_info(uid, ck),
        return_exceptions=True,
    )

    (daily_info_res, account_info_res) = results
    if not isinstance(daily_info_res, KuroApiResp) or not daily_info_res.success:
        return None

    if not isinstance(account_info_res, KuroApiResp) or not account_info_res.success:
        return None

    daily_info = DailyData.model_validate(daily_info_res.data)
    account_info = AccountBaseInfo.model_validate(account_info_res.data)

    return {
        "daily_info": daily_info,
        "account_info": account_info,
    }


async def draw_stamina_img(bot: Bot, ev: Event):
    try:
        uid_list = await WavesBind.get_uid_list_by_game(ev.user_id, ev.bot_id)
        logger.info(f"[鸣潮][每日信息]UID: {uid_list}")
        if uid_list is None:
            return ERROR_CODE[WAVES_CODE_103]
        # 进行校验UID是否绑定CK
        tasks = [process_uid(uid, ev) for uid in uid_list]
        results = await asyncio.gather(*tasks)

        # 过滤掉 None 值
        valid_daily_list = [res for res in results if res is not None]

        if len(valid_daily_list) == 0:
            return ERROR_CODE[WAVES_CODE_102]

        # 开始绘图任务
        task = []
        img = Image.new(
            "RGBA", (based_w, based_h * len(valid_daily_list)), (0, 0, 0, 0)
        )
        for uid_index, valid in enumerate(valid_daily_list):
            task.append(_draw_all_stamina_img(ev, img, valid, uid_index))
        await asyncio.gather(*task)
        res = await convert_img(img)
        logger.info("[鸣潮][每日信息]绘图已完成,等待发送!")
    except TypeError:
        logger.exception("[鸣潮][每日信息]绘图失败!")
        res = "你绑定过的UID中可能存在过期CK~请重新绑定一下噢~"

    return res


async def _draw_all_stamina_img(ev: Event, img: Image.Image, valid: Dict, index: int):
    stamina_img = await _draw_stamina_img(ev, valid)
    stamina_img = stamina_img.convert("RGBA")
    img.paste(stamina_img, (0, based_h * index), stamina_img)


async def _draw_stamina_img(ev: Event, valid: Dict) -> Image.Image:
    daily_info: DailyData = valid["daily_info"]
    account_info: AccountBaseInfo = valid["account_info"]
    if daily_info.hasSignIn:
        sign_in_icon = YES
        sing_in_text = "签到已完成！"
    else:
        sign_in_icon = NO
        sing_in_text = "今日未签到！"

    if (
        daily_info.livenessData.total != 0
        and daily_info.livenessData.cur == daily_info.livenessData.total
    ):
        active_icon = YES
        active_text = "活跃度已满！"
    else:
        active_icon = NO
        active_text = "活跃度未满！"

    # ================= 资源加载与 Resize (x3) =================
    img = Image.open(TEXT_PATH / "bg.jpg").convert("RGBA")
    img = img.resize((based_w, based_h))

    info = Image.open(TEXT_PATH / "main_bar.png").convert("RGBA")
    # 原图不知道尺寸，保险起见按原逻辑放大或者直接指定宽度
    # 这里假设原图也是适配原 1150 宽度的，直接 x3
    info = info.resize((info.width * 3, info.height * 3))

    base_info_bg = Image.open(TEXT_PATH / "base_info_bg.png")
    base_info_bg = base_info_bg.resize((base_info_bg.width * 3, base_info_bg.height * 3))

    avatar_ring = Image.open(TEXT_PATH / "avatar_ring.png")
    avatar_ring = avatar_ring.resize((avatar_ring.width * 3, avatar_ring.height * 3))
    
    # 标题栏
    title_bar = Image.open(TEXT_PATH / "title_bar.png")
    title_bar = title_bar.resize((title_bar.width * 3, title_bar.height * 3))

    # 头像 (函数内已修复并适配x3)
    avatar = await draw_pic_with_ring(ev)

    # ================= Pile 处理 =================
    user = await WavesUser.get_user_by_attr(
        ev.user_id, ev.bot_id, "uid", daily_info.roleId
    )
    pile_id = None
    force_use_bg = False
    force_not_use_bg = False
    force_not_use_custom = False
    
    if user and user.stamina_bg_value:
        logger.info(f"[鸣潮][每日信息]用户自定义体力背景: {user.stamina_bg_value}")
        force_use_bg = "背景" in user.stamina_bg_value
        force_not_use_bg = "立绘" in user.stamina_bg_value
        force_not_use_custom = "官方" in user.stamina_bg_value
        stamina_bg_value = user.stamina_bg_value.replace("背景", "").replace("立绘", "").replace("官方", "").strip()
        char_id = char_name_to_char_id(stamina_bg_value)
        if char_id in SPECIAL_CHAR:
            ck = await waves_api.get_self_waves_ck(
                daily_info.roleId, ev.user_id, ev.bot_id
            )
            if ck:
                for char_id in SPECIAL_CHAR[char_id]:
                    role_detail_info = await waves_api.get_role_detail_info(
                        char_id, daily_info.roleId, ck
                    )
                    if not role_detail_info.success:
                        continue
                    role_detail_info = role_detail_info.data
                    if (
                        not isinstance(role_detail_info, Dict)
                        or "role" not in role_detail_info
                        or role_detail_info["role"] is None
                        or "level" not in role_detail_info
                        or role_detail_info["level"] is None
                    ):
                        continue
                    pile_id = char_id
                    break
        else:
            pile_id = char_id
    
    if force_use_bg:
        pile, has_bg = await get_random_waves_bg(pile_id, force_not_use_custom=force_not_use_custom)
    elif force_not_use_bg:
        pile = await get_random_waves_role_pile(pile_id, force_not_use_custom=force_not_use_custom)
        has_bg = False
    elif ShowConfig.get_config("MrUseBG"):
        pile, has_bg = await get_random_waves_bg(pile_id, force_not_use_custom=force_not_use_custom)
    else:
        pile = await get_random_waves_role_pile(pile_id, force_not_use_custom=force_not_use_custom)
        has_bg = False

    if ShowConfig.get_config("MrUseBG") and has_bg:
        bg_w, bg_h = pile.size
        target_w, target_h = based_w, based_h
        ratio = max(target_w / bg_w, target_h / bg_h)
        new_size = (int(bg_w * ratio), int(bg_h * ratio))
        pile = pile.resize(new_size, Image.LANCZOS)
        
        left = (pile.width - target_w) // 2
        top = (pile.height - target_h) // 2
        pile = pile.crop((left, top, left + target_w, top + target_h))
        
        img.paste(pile, (0, 0))
        
        info = Image.open(TEXT_PATH / "main_bar_bg.png").convert("RGBA")
        info = info.resize((info.width * 3, info.height * 3))

    # ================= 文字绘制 (坐标 x3, 字体替换) =================
    base_info_draw = ImageDraw.Draw(base_info_bg)
    
    # 名字: 原 waves_font_30 -> waves_font_90
    base_info_draw.text(
        (825, 360), f"{daily_info.roleName[:7]}", GREY, waves_font_90, "lm", stroke_width=2, stroke_fill="black"
    )
    # 特征码: 原 waves_font_25 -> waves_font_75
    base_info_draw.text(
        (678, 519), f"特征码:  {daily_info.roleId}", GOLD, waves_font_75, "lm", stroke_width=1, stroke_fill="black"
    )

    title_bar_draw = ImageDraw.Draw(title_bar)
    # 标题: 原 waves_font_26 -> waves_font_78
    title_bar_draw.text((1440, 375), "战歌重奏", GREY, waves_font_78, "mm", stroke_width=3, stroke_fill="black")
    
    color = RED if account_info.weeklyInstCount != 0 else GREEN
    if (
        account_info.weeklyInstCountLimit is not None
        and account_info.weeklyInstCount is not None
    ):
        # 战歌数值: 原 waves_font_42 -> waves_font_126
        title_bar_draw.text(
            (1440, 234),
            f"{account_info.weeklyInstCountLimit - account_info.weeklyInstCount} / {account_info.weeklyInstCountLimit}",
            color,
            waves_font_126,
            "mm",
            stroke_width=3, stroke_fill="black"
        )

    title_bar_draw.text((1890, 375), "先约电台", GREY, waves_font_78, "mm", stroke_width=3, stroke_fill="black")
    # 电台数值: 原 waves_font_42 -> waves_font_126
    title_bar_draw.text(
        (1890, 234),
        f"Lv.{daily_info.battlePassData[0].cur}",
        "white",
        waves_font_126,
        "mm",
        stroke_width=3, stroke_fill="black"
    )

    color = RED if account_info.rougeScore != account_info.rougeScoreLimit else GREEN
    # 异想: 原 waves_font_26 -> waves_font_78
    title_bar_draw.text((2430, 375), "千道门扉的异想", GREY, waves_font_78, "mm", stroke_width=3, stroke_fill="black")
    # 异想数值: 原 waves_font_32 -> waves_font_96
    title_bar_draw.text(
        (2430, 234),
        f"{account_info.rougeScore}/{account_info.rougeScoreLimit}",
        color,
        waves_font_96,
        "mm",
        stroke_width=3, stroke_fill="black"
    )

    # ================= 进度条与数值 (坐标 x3) =================
    active_draw = ImageDraw.Draw(info)
    curr_time = int(time.time())
    refreshTimeStamp = (
        daily_info.energyData.refreshTimeStamp
        if daily_info.energyData.refreshTimeStamp
        else curr_time
    )

    # 时间胶囊尺寸 x3 (180, 33) -> (540, 99)
    time_img = Image.new("RGBA", (540, 99), (255, 255, 255, 0))
    time_img_draw = ImageDraw.Draw(time_img)
    # 半径 15 -> 45
    time_img_draw.rounded_rectangle(
        [15, 0, 540, 99], radius=45, fill=(186, 55, 42, int(0.7 * 255))
    )

    if refreshTimeStamp != curr_time:
        date_from_timestamp = datetime.fromtimestamp(refreshTimeStamp)
        now = datetime.now()
        today = now.date()
        tomorrow = today + timedelta(days=1)

        remain_time = datetime.fromtimestamp(refreshTimeStamp).strftime(
            "%m.%d %H:%M:%S"
        )
        if date_from_timestamp.date() == today:
            remain_time = "今天 " + datetime.fromtimestamp(refreshTimeStamp).strftime(
                "%H:%M:%S"
            )
        elif date_from_timestamp.date() == tomorrow:
            remain_time = "明天 " + datetime.fromtimestamp(refreshTimeStamp).strftime(
                "%H:%M:%S"
            )
        # 时间文字: 原 waves_font_24 -> waves_font_72
        time_img_draw.text((30, 45), f"{remain_time}", "white", waves_font_72, "lm", stroke_width=1, stroke_fill="black")
    else:
        time_img_draw.text((30, 45), "漂泊者该上潮了", "white", waves_font_72, "lm", stroke_width=1, stroke_fill="black")

    # 贴时间胶囊 (280, 50) -> (840, 150)
    info.alpha_composite(time_img, (840, 150))

    # 进度条长度 345 -> 1035
    max_len = 1035
    
    # 体力条背景
    stamina_len = len(str(daily_info.energyData.cur))
    '''if stamina_len == 1:
        active_draw.rounded_rectangle([927, 303, 1305, 402], radius=45, fill=(0, 0, 0, int(0.3 * 255)))
    elif stamina_len == 2:
        active_draw.rounded_rectangle([876, 303, 1305, 402], radius=45, fill=(0, 0, 0, int(0.3 * 255)))
    else:
        active_draw.rounded_rectangle([825, 303, 1305, 402], radius=45, fill=(0, 0, 0, int(0.3 * 255)))'''
    
    # 体力数值: 原 waves_font_30 -> waves_font_90
    active_draw.text(
        (1050, 345), f"/{daily_info.energyData.total}", "white", waves_font_90, "lm", stroke_width=4, stroke_fill="black"
    )
    active_draw.text(
        (1044, 345), f"{daily_info.energyData.cur}", "white", waves_font_90, "rm", stroke_width=4, stroke_fill="black"
    )
    radio = daily_info.energyData.cur / daily_info.energyData.total
    color = RED if radio > 0.8 else YELLOW
    # 体力进度条 (173, 142) -> (519, 426)
    active_draw.rectangle((519, 426, int(519 + radio * max_len), 450), color)

    # 结晶背景
    store_len = len(str(account_info.storeEnergy))
    '''if store_len == 1:
        active_draw.rounded_rectangle([927, 648, 1305, 747], radius=45, fill=(0, 0, 0, int(0.3 * 255)))
    elif store_len == 2:
        active_draw.rounded_rectangle([876, 648, 1305, 747], radius=45, fill=(0, 0, 0, int(0.3 * 255)))
    else:
        active_draw.rounded_rectangle([825, 648, 1305, 747], radius=45, fill=(0, 0, 0, int(0.3 * 255)))'''
    
    # 结晶数值
    active_draw.text(
        (1050, 690), f"/{account_info.storeEnergyLimit}", "white", waves_font_90, "lm", stroke_width=4, stroke_fill="black"
    )
    active_draw.text(
        (1044, 690), f"{account_info.storeEnergy}", "white", waves_font_90, "rm", stroke_width=4, stroke_fill="black"
    )
    radio = (
        account_info.storeEnergy / account_info.storeEnergyLimit
        if account_info.storeEnergyLimit is not None
        and account_info.storeEnergy is not None
        and account_info.storeEnergyLimit != 0
        else 0
    )
    color = RED if radio > 0.8 else YELLOW
    # 结晶进度条 (173, 254) -> (519, 762)
    active_draw.rectangle((519, 762, int(519 + radio * max_len), 786), color)

    # 活跃度背景
    liveness_len = len(str(daily_info.livenessData.cur))
    '''if liveness_len == 1:
        active_draw.rounded_rectangle([927, 1008, 1305, 1107], radius=45, fill=(0, 0, 0, int(0.3 * 255)))
    elif liveness_len == 2:
        active_draw.rounded_rectangle([876, 1008, 1305, 1107], radius=45, fill=(0, 0, 0, int(0.3 * 255)))
    else:
        active_draw.rounded_rectangle([825, 1008, 1305, 1107], radius=45, fill=(0, 0, 0, int(0.3 * 255)))'''
    
    # 活跃度数值
    active_draw.text(
        (1050, 1050), f"/{daily_info.livenessData.total}", "white", waves_font_90, "lm", stroke_width=4, stroke_fill="black"
    )
    active_draw.text(
        (1044, 1050), f"{daily_info.livenessData.cur}", "white", waves_font_90, "rm", stroke_width=4, stroke_fill="black"
    )
    radio = (
        daily_info.livenessData.cur / daily_info.livenessData.total
        if daily_info.livenessData.total != 0
        else 0
    )
    # 活跃度进度条 (173, 374) -> (519, 1122)
    active_draw.rectangle((519, 1122, int(519 + radio * max_len), 1146), YELLOW)

    # 签到状态标签尺寸 x3
    status_img = Image.new("RGBA", (690, 120), (255, 255, 255, 0))
    status_img_draw = ImageDraw.Draw(status_img)
    #status_img_draw.rounded_rectangle([0, 0, 690, 120], radius=45, fill=(0, 0, 0, int(0.3 * 255)))
    status_img.alpha_composite(sign_in_icon, (0, 0))
    # 状态文字: 原 waves_font_30 -> waves_font_90
    status_img_draw.text((150, 60), f"{sing_in_text}", "white", waves_font_90, "lm", stroke_width=3, stroke_fill="black")
    # 粘贴位置 (70, 80) -> (210, 240)
    img.alpha_composite(status_img, (210, 240))
    if ShowConfig.get_config("MrUseBG") and has_bg:
        img.alpha_composite(status_img, (210, 240))

    # 活跃状态标签尺寸 x3
    status_img2 = Image.new("RGBA", (690, 120), (255, 255, 255, 0))
    status_img2_draw = ImageDraw.Draw(status_img2)
    #status_img2_draw.rounded_rectangle([0, 0, 690, 120], radius=45, fill=(0, 0, 0, int(0.3 * 255)))
    status_img2.alpha_composite(active_icon, (0, 0))
    status_img2_draw.text((150, 60), f"{active_text}", "white", waves_font_90, "lm", stroke_width=3, stroke_fill="black")
    # 粘贴位置 (70, 140) -> (210, 420)
    img.alpha_composite(status_img2, (210, 420))
    if ShowConfig.get_config("MrUseBG") and has_bg:
        img.alpha_composite(status_img2, (210, 420))

    # pile 放在背景上
    # 如果不是自定义背景，则按原样贴立绘
    if not (ShowConfig.get_config("MrUseBG") and has_bg):
        # 放大立绘
        if pile:
            p_w, p_h = pile.size
            pile = pile.resize((int(p_w * 3), int(p_h * 3)))
            # (550, -150) -> (1650, -450)
            img.paste(pile, (1650, -450), pile)

    # 贴个bar_down (如果需要)
    # img.alpha_composite(bar_down, (0, 0))

    # info (Main Bar) 粘贴位置 (0, 190) -> (0, 570)
    # 如果你想模仿 Upstream 的透明度逻辑，可以在这里修改。目前保持不透明
    if ShowConfig.get_config("MrUseBG") and has_bg:
         # 移植 Upstream 的透明度逻辑到你的 3x 代码
        img.paste(info, (0, 570), info.split()[-1].point(lambda x: x * 0.75))
    else:
        img.paste(info, (0, 570), info)
    
    # base_info 粘贴位置 (40, 570) -> (120, 1710)
    img.paste(base_info_bg, (120, 1710), base_info_bg)
    
    # avatar_ring 粘贴位置 (40, 620) -> (120, 1860)
    img.paste(avatar_ring, (120, 1860), avatar_ring)
    img.paste(avatar, (120, 1860), avatar)
    
    # account_info (Title Bar) 粘贴位置 (190, 620) -> (570, 1860)
    img.paste(title_bar, (570, 1860), title_bar)
    
    # Footer 尺寸调整 (600 -> 1800, 25 -> 75)
    #img = add_footer(img, 1800, 75)

    # 1. 准备画笔和字体
    footer_draw = ImageDraw.Draw(img)
    font = waves_font_72  # 使用之前定义的 3倍大小 字体

    # 2. 定义分段文字内容和颜色
    text_parts = [
        {"text": "Powered by ", "color": GREY},
        {"text": "GSCore", "color": "white"},
        {"text": " & Created by ", "color": GREY},
        {"text": "WutheringWavesUID", "color": "white"}, #我劝你老实
    ]

    # 3. 计算整段文字的总宽度（用于居中）
    total_width = sum(footer_draw.textlength(part["text"], font=font) for part in text_parts)

    # 4. 计算起始坐标
    # X轴：(总宽 - 文字宽) / 2 = 居中起始点
    current_x = (based_w - total_width) / 2
    
    # Y轴：总高 - 150 (数字越大，文字越往上移；数字越小，越贴近底部)
    current_y = based_h - 100

    # 5. 循环分段绘制
    for part in text_parts:
        # 绘制当前片段
        footer_draw.text(
            (current_x, current_y), 
            part["text"], 
            fill=part["color"], 
            font=font,
            stroke_width=2,      # 【关键修改】描边宽度，建议 3-5 px
            stroke_fill="black"  # 【关键修改】描边颜色
        )
        # 将 X 坐标向右移动
        current_x += footer_draw.textlength(part["text"], font=font)

    return img

async def draw_pic_with_ring(ev: Event):
    # 1. 获取头像
    pic = await get_event_avatar(ev, is_valid_at_param=False)
    
    # [修复点3] 确保定义 mask_pic
    mask_pic = Image.open(TEXT_PATH / "avatar_mask.png")

    # 2. 画布 (200, 200) -> (600, 600)
    img = Image.new("RGBA", (600, 600))
    
    # 3. 遮罩 resize (160, 160) -> (480, 480)
    mask = mask_pic.resize((480, 480))
    
    # 4. [修复点4] 容错逻辑：防止原头像过小
    if pic.width < 480 or pic.height < 480:
        pic = pic.resize((max(480, pic.width), max(480, pic.height)))

    # 5. 图片 crop (160, 160) -> (480, 480)
    resize_pic = crop_center_img(pic, 480, 480)
    
    # 6. 粘贴 (20, 20) -> (60, 60)
    img.paste(resize_pic, (60, 60), mask)

    return img