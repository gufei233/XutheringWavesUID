import asyncio
import time
from pathlib import Path
from typing import List, Optional, Union

from PIL import Image, ImageDraw
from pydantic import BaseModel

from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.image.image_tools import crop_center_img

from ..utils.api.model import RoleDetailData
from ..utils.cache import TimedCache
from ..utils.calc import WuWaCalc
from ..utils.calculate import (
    calc_phantom_score,
    get_calc_map,
)
from ..utils.char_info_utils import get_all_role_detail_info_list
from ..utils.database.models import WavesBind
from ..utils.fonts.waves_fonts import (
    waves_font_12,
    waves_font_16,
    waves_font_18,
    waves_font_20,
    waves_font_28,
    waves_font_30,
    waves_font_34,
    waves_font_58,
)
from ..utils.image import (
    AMBER,
    GREY,
    RED,
    SPECIAL_GOLD,
    WAVES_FREEZING,
    WAVES_LINGERING,
    WAVES_MOLTEN,
    WAVES_MOONLIT,
    WAVES_SIERRA,
    WAVES_VOID,
    add_footer,
    get_ICON,
    get_qq_avatar,
    get_square_avatar,
    get_waves_bg,
)
from ..wutheringwaves_config import PREFIX
from .slash_rank import get_avatar

TEXT_PATH = Path(__file__).parent / "texture2d"
avatar_mask = Image.open(TEXT_PATH / "avatar_mask.png")
char_mask = Image.open(TEXT_PATH / "char_mask.png")
pic_cache = TimedCache(600, 200)


BOT_COLOR = [
    WAVES_MOLTEN,
    AMBER,
    WAVES_VOID,
    WAVES_SIERRA,
    WAVES_FREEZING,
    WAVES_LINGERING,
    WAVES_MOONLIT,
]


class PracticeRankInfo(BaseModel):
    qid: str  # qq id
    uid: str  # uid
    kuro_name: str  # 玩家名字
    total_score: float  # 总声骸分数
    role_details: List[RoleDetailData]  # 角色详情列表


async def get_all_practice_rank_info(
    users: List[WavesBind],
    threshold: int = 175,
) -> List[PracticeRankInfo]:
    """获取所有用户的练度排行信息（基于声骸分数）

    Args:
        users: 用户列表
        threshold: 计入排行的角色声骸分数阈值 (150-195)
    """
    rankInfoList = []

    for user in users:
        if not user.uid:
            continue

        # 获取该用户的所有角色信息
        role_details_list = await get_all_role_detail_info_list(user.uid)
        if role_details_list is None:
            continue

        role_details = list(role_details_list)
        if not role_details:
            continue

        # 计算总声骸分数
        total_score = 0.0
        valid_role_details = []

        for role_detail in role_details:
            # 检查是否有声骸装备
            if not role_detail.phantomData or not role_detail.phantomData.equipPhantomList:
                continue

            # 计算该角色的声骸总分
            calc: WuWaCalc = WuWaCalc(role_detail)
            calc.phantom_pre = calc.prepare_phantom()
            calc.phantom_card = calc.enhance_summation_phantom_value(calc.phantom_pre)
            calc.calc_temp = get_calc_map(
                calc.phantom_card,
                role_detail.role.roleName,
                role_detail.role.roleId,
            )

            phantom_score = 0.0
            for _phantom in role_detail.phantomData.equipPhantomList:
                if _phantom and _phantom.phantomProp:
                    props = _phantom.get_props()
                    _score, _bg = calc_phantom_score(
                        role_detail.role.roleId, props, _phantom.cost, calc.calc_temp
                    )
                    phantom_score += _score

            # 只计算分数>=阈值的角色
            if phantom_score >= threshold:
                total_score += phantom_score
                valid_role_details.append(role_detail)

        if total_score == 0:
            continue

        total_score = round(total_score, 2)
        rankInfo = PracticeRankInfo(
            qid=user.user_id,
            uid=user.uid,
            kuro_name=user.uid,  # 使用uid作为名字，因为本地数据没有玩家昵称
            total_score=total_score,
            role_details=valid_role_details,
        )
        rankInfoList.append(rankInfo)

    return rankInfoList


async def draw_rank_list(bot: Bot, ev: Event, pages: int = 1, threshold: int = 175) -> Union[str, bytes]:
    start_time = time.time()
    logger.info(f"[draw_practice_rank_list] start: {start_time}")

    # 解析参数以获取阈值
    text = ev.text.strip() if ev.text else ""
    if text:
        # 支持 s/a/ss 或数字形式
        if text.lower() == "ss":
            threshold = 195
        elif text.lower() == "a":
            threshold = 150
        elif text.lower() == "s":
            threshold = 175

    # 获取群里的所有用户
    users = await WavesBind.get_group_all_uid(ev.group_id)
    if not users:
        msg = []
        msg.append(f"[鸣潮] 群【{ev.group_id}】暂无练度排行数据")
        msg.append(f"请使用【{PREFIX}刷新面板】后再使用此功能！")
        msg.append("")
        return "\n".join(msg)

    rankInfoList = await get_all_practice_rank_info(list(users), threshold)
    if len(rankInfoList) == 0:
        msg = []
        msg.append(f"[鸣潮] 群【{ev.group_id}】暂无练度排行数据")
        msg.append(f"请使用【{PREFIX}刷新面板】后再使用此功能！")
        msg.append("")
        return "\n".join(msg)

    # 按总声骸分数排序
    rankInfoList.sort(key=lambda i: i.total_score, reverse=True)

    # 获取自己的排名
    self_uid = None
    rankId = None
    rankInfo = None
    try:
        self_uid = await WavesBind.get_uid_by_game(ev.user_id, ev.bot_id)
        if self_uid:
            rankId, rankInfo = next(
                (
                    (rankId, rankInfo)
                    for rankId, rankInfo in enumerate(rankInfoList, start=1)
                    if rankInfo.uid == self_uid and ev.user_id == rankInfo.qid
                ),
                (None, None),
            )
    except Exception as _:
        pass

    rank_length = 20  # 显示前20条
    rankInfoList_display = rankInfoList[:rank_length]
    if rankId and rankInfo and rankId > rank_length:
        rankInfoList_display.append(rankInfo)

    # 获取等级标签 (S/A/SS)
    threshold_label = "S"  # 默认值
    if threshold == 195:
        threshold_label = "SS"
    elif threshold == 150:
        threshold_label = "A"
    elif threshold == 175:
        threshold_label = "S"

    # 设置图像尺寸 - 变窄
    width = 1000
    text_bar_height = 140
    item_spacing = 120
    header_height = 510
    footer_height = 50
    char_list_len = len(rankInfoList_display)

    # 计算所需的总高度
    total_height = (
        header_height + text_bar_height + item_spacing * char_list_len + footer_height
    )

    # 创建带背景的画布
    card_img = get_waves_bg(width, total_height, "bg9")

    text_bar_img = Image.new("RGBA", (width, 140), color=(0, 0, 0, 0))
    text_bar_draw = ImageDraw.Draw(text_bar_img)
    # 绘制深灰色背景
    bar_bg_color = (36, 36, 41, 230)
    text_bar_draw.rounded_rectangle(
        [20, 20, width - 40, 120], radius=8, fill=bar_bg_color
    )

    # 绘制顶部的金色高亮线
    accent_color = (203, 161, 95)
    text_bar_draw.rectangle([20, 20, width - 40, 26], fill=accent_color)

    # 左侧标题
    text_bar_draw.text((40, 60), "排行说明", GREY, waves_font_28, "lm")
    text_bar_draw.text(
        (185, 50),
        "1. 综合所有角色的声骸分数。具备声骸套装的角色，全量刷新面板后生效。",
        SPECIAL_GOLD,
        waves_font_20,
        "lm",
    )
    text_bar_draw.text(
        (185, 85), "2. 显示声骸分数最高的前5个角色", SPECIAL_GOLD, waves_font_20, "lm"
    )

    # 备注 - 排行标准，根据阈值动态生成文案
    temp_notes = f"排行标准：以所有角色声骸分数总和（角色分数>={threshold}（{threshold_label}级））为排序的综合排名"
    text_bar_draw.text((width - 40, 110), temp_notes, SPECIAL_GOLD, waves_font_16, "rm")

    card_img.alpha_composite(text_bar_img, (0, header_height))

    # 导入必要的图片资源
    bar = Image.open(TEXT_PATH / "bar2.png")

    # 获取头像
    tasks = [get_avatar(rank.qid) for rank in rankInfoList_display]
    results = await asyncio.gather(*tasks)

    # 绘制排行条目
    for rank_temp_index, temp in enumerate(zip(rankInfoList_display, results)):
        rankInfo = temp[0]
        role_avatar = temp[1]
        y_pos = header_height + 130 + rank_temp_index * item_spacing

        # 创建条目背景
        bar_bg = bar.copy()
        bar_bg.paste(role_avatar, (100, 0), role_avatar)
        bar_draw = ImageDraw.Draw(bar_bg)

        # 绘制排名
        rank_id = rank_temp_index + 1
        rank_color = (54, 54, 54)
        if rank_id == 1:
            rank_color = (255, 0, 0)
        elif rank_id == 2:
            rank_color = (255, 180, 0)
        elif rank_id == 3:
            rank_color = (185, 106, 217)

        # 排名背景
        info_rank = Image.new("RGBA", (50, 50), color=(255, 255, 255, 0))
        rank_draw = ImageDraw.Draw(info_rank)
        rank_draw.rounded_rectangle(
            [0, 0, 50, 50], radius=8, fill=rank_color + (int(0.9 * 255),)
        )
        rank_draw.text((25, 25), f"{rank_id}", "white", waves_font_34, "mm")
        bar_bg.alpha_composite(info_rank, (40, 35))

        # 绘制UID（无标签）
        uid_color = "white"
        if rankInfo.uid == self_uid:
            uid_color = RED
        bar_draw.text(
            (210, 40), f"{rankInfo.uid}", uid_color, waves_font_20, "lm"
        )

        # 绘制角色数量（根据等级显示）
        char_count = len(rankInfo.role_details)
        bar_draw.text((210, 75), f"{threshold_label}级: {char_count}", "white", waves_font_18, "lm")

        # 绘制角色信息
        if rankInfo.role_details:
            # 按声骸分数排序，取前5名
            role_scores = []
            for role in rankInfo.role_details:
                if not role.phantomData or not role.phantomData.equipPhantomList:
                    continue
                calc: WuWaCalc = WuWaCalc(role)
                calc.phantom_pre = calc.prepare_phantom()
                calc.phantom_card = calc.enhance_summation_phantom_value(calc.phantom_pre)
                calc.calc_temp = get_calc_map(
                    calc.phantom_card,
                    role.role.roleName,
                    role.role.roleId,
                )
                phantom_score = 0.0
                for _phantom in role.phantomData.equipPhantomList:
                    if _phantom and _phantom.phantomProp:
                        props = _phantom.get_props()
                        _score, _ = calc_phantom_score(
                            role.role.roleId, props, _phantom.cost, calc.calc_temp
                        )
                        phantom_score += _score
                role_scores.append((role, phantom_score))

            sorted_roles = sorted(
                role_scores, key=lambda x: x[1], reverse=True
            )[:8]

            # 在条目底部绘制前5名角色的头像（放在UID右边）
            char_size = 40
            char_spacing = 45
            char_start_x = 350
            char_start_y = 35

            for i, (role, score) in enumerate(sorted_roles):
                char_x = char_start_x + i * char_spacing

                # 获取角色头像
                char_avatar = await get_square_avatar(role.role.roleId)
                char_avatar = char_avatar.resize((char_size, char_size))

                # 应用圆形遮罩
                char_mask_img = Image.open(TEXT_PATH / "char_mask.png")
                char_mask_resized = char_mask_img.resize((char_size, char_size))
                char_avatar_masked = Image.new("RGBA", (char_size, char_size))
                char_avatar_masked.paste(char_avatar, (0, 0), char_mask_resized)

                # 粘贴头像
                bar_bg.paste(
                    char_avatar_masked, (char_x, char_start_y), char_avatar_masked
                )

                # 绘制分数
                score_text = f"{int(score)}"
                bar_draw.text(
                    (char_x + char_size // 2, char_start_y + char_size + 2),
                    score_text,
                    SPECIAL_GOLD,
                    waves_font_12,
                    "mm",
                )

            # 显示最高声骸分数（第五个角色头像右边）
            if sorted_roles:
                best_score = f"{int(sorted_roles[0][1])}"
                bar_draw.text((770, 45), best_score, "lightgreen", waves_font_30, "mm")
                bar_draw.text((770, 75), "最高分", "white", waves_font_16, "mm")

        # 总分（放在最右边）
        bar_draw.text(
            (880, 45),
            f"{rankInfo.total_score}",
            (255, 255, 255),
            waves_font_34,
            "mm",
        )
        bar_draw.text((880, 75), "总分", "white", waves_font_16, "mm")

        # 贴到背景
        card_img.paste(bar_bg, (0, y_pos), bar_bg)

    # title
    title_bg = Image.open(TEXT_PATH / "totalrank.jpg")
    title_bg = title_bg.crop((0, 0, width, 475))

    # icon
    icon = get_ICON()
    icon = icon.resize((128, 128))
    title_bg.paste(icon, (60, 240), icon)

    # title
    title_text = "#练度群排行"
    title_bg_draw = ImageDraw.Draw(title_bg)
    title_bg_draw.text((220, 290), title_text, "white", waves_font_58, "lm")

    # 遮罩
    char_mask_img = Image.open(TEXT_PATH / "char_mask.png").convert("RGBA")
    # 根据width扩图
    char_mask_img = char_mask_img.resize((width, char_mask_img.height * width // char_mask_img.width))
    char_mask_img = char_mask_img.crop((0, char_mask_img.height - 475, width, char_mask_img.height))
    char_mask_temp = Image.new("RGBA", char_mask_img.size, (0, 0, 0, 0))
    char_mask_temp.paste(title_bg, (0, 0), char_mask_img)

    card_img.paste(char_mask_temp, (0, 0), char_mask_temp)

    card_img = add_footer(card_img)
    card_img = await convert_img(card_img)

    return card_img