from gsuid_core.utils.download_resource.download_core import download_all_file
from gsuid_core.logger import logger

from .RESOURCE_PATH import (
    AVATAR_PATH,
    JIEXING_GUIDE_PATH,
    JINLINGZI_GUIDE_PATH,
    MATERIAL_PATH,
    MOEALKYNE_GUIDE_PATH,
    PHANTOM_PATH,
    ROLE_DETAIL_CHAINS_PATH,
    ROLE_DETAIL_SKILL_PATH,
    ROLE_PILE_PATH,
    ROLE_BG_PATH,
    SHARE_BG_PATH,
    WEAPON_PATH,
    WUHEN_GUIDE_PATH,
    XIAOYANG_GUIDE_PATH,
    XMU_GUIDE_PATH,
    XFM_GUIDE_PATH,
    BUILD_PATH,
    MAP_BUILD_PATH,
)

from ..map.damage.register import reload_all_register

import sys
import platform
import os

def get_target_package():
    system = sys.platform
    machine = platform.machine().lower()
    
    py_ver = f"py{sys.version_info.major}.{sys.version_info.minor}"
    
    if py_ver not in ['py3.10', 'py3.11', 'py3.12', 'py3.13']:
        logger.error(f"不支持的Python版本: {py_ver}")
        return ""
    
    if system == 'win32':
        if '64' in machine: 
            return f"win-x86_64-{py_ver}"
        else:
            logger.error("暂不支持32位Windows")    
            return  ""

    elif system == 'linux':
        if 'x86_64' in machine:
            return f"linux-x86_64-{py_ver}"
        elif 'aarch64' in machine:
            return f"linux-aarch64-{py_ver}"
        else:
            logger.error("暂不支持非x86_64架构的Linux")
            
    is_android = 'ANDROID_ROOT' in os.environ or 'ANDROID_DATA' in os.environ
    if is_android:
        if py_ver == 'py3.12':
            return "android-aarch64-ndk"
        else:
            logger.error("安卓环境仅支持Python 3.12")
            return  f"linux-x86_64-{py_ver}"

    elif system == 'darwin':
        if 'arm64' in machine:
            return f"macos-arm64-{py_ver}"
        elif 'x86_64' in machine:
            logger.error("暂不支持Intel架构的Mac")
            return  ""

    logger.error(f"不支持的操作系统: {system} {machine}")
    return  f"linux-x86_64-{py_ver}"

PLATFORM = get_target_package()

async def download_all_resource():
    await download_all_file(
        "XutheringWavesUID",
        {
            "resource/avatar": AVATAR_PATH,
            "resource/weapon": WEAPON_PATH,
            "resource/role_pile": ROLE_PILE_PATH,
            "resource/role_bg": ROLE_BG_PATH,
            "resource/role_detail/skill": ROLE_DETAIL_SKILL_PATH,
            "resource/role_detail/chains": ROLE_DETAIL_CHAINS_PATH,
            "resource/share": SHARE_BG_PATH,
            "resource/phantom": PHANTOM_PATH,
            "resource/material": MATERIAL_PATH,
            "resource/guide/XMu": XMU_GUIDE_PATH,
            "resource/guide/Moealkyne": MOEALKYNE_GUIDE_PATH,
            "resource/guide/JinLingZi": JINLINGZI_GUIDE_PATH,
            "resource/guide/JieXing": JIEXING_GUIDE_PATH,
            "resource/guide/XiaoYang": XIAOYANG_GUIDE_PATH,
            "resource/guide/WuHen": WUHEN_GUIDE_PATH,
            "resource/guide/XFM": XFM_GUIDE_PATH,
            f"resource/build/{PLATFORM}/waves_build": BUILD_PATH,
            f"resource/build/{PLATFORM}/map/waves_build": MAP_BUILD_PATH,
        },
        "https://ww.loping151.top", 
        "小维US"
    )
    reload_all_register()
    
    
