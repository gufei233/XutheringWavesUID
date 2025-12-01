"""init"""

from gsuid_core.sv import Plugins
from pathlib import Path
from gsuid_core.logger import logger
import shutil

Plugins(name="XutheringWavesUID", force_prefix=["ww"], allow_empty_prefix=False)

if "WutheringWavesUID" in str(Path(__file__)):
    logger.error("请修改插件文件夹名称为 XutheringWavesUID 以支持后续指令更新")

from gsuid_core.data_store import get_res_path
MAIN_PATH = get_res_path()
if not Path(MAIN_PATH / 'XutheringWavesUID').exists() and Path(MAIN_PATH / 'WutheringWavesUID').exists():
    logger.info("存在旧版插件资源，正在进行重命名...")
    shutil.copytree(MAIN_PATH / 'WutheringWavesUID', MAIN_PATH / 'XutheringWavesUID')

if Path(MAIN_PATH / 'WutheringWavesUID').exists():
    logger.warning("检测到旧版资源 WutheringWavesUID，建议删除以节省空间")

cfg_path = MAIN_PATH / 'config.json'
with open(cfg_path, 'r', encoding='utf-8') as f:
    cfg_text = f.read()
if 'WutheringWavesUID' in cfg_text and not 'XutheringWavesUID' in cfg_text:
    logger.info("正在更新配置文件中的插件名称...")
    shutil.copyfile(cfg_path, MAIN_PATH / 'config_backup.json')
    cfg_text = cfg_text.replace('WutheringWavesUID', 'XutheringWavesUID')
    with open(cfg_path, 'w', encoding='utf-8') as f:
        f.write(cfg_text)
    Path(MAIN_PATH / 'config_backup.json').unlink()
elif 'WutheringWavesUID' in cfg_text and 'XutheringWavesUID' in cfg_text:
    logger.warning("同时存在 WutheringWavesUID 和 XutheringWavesUID 配置，可保留老的配置文件后重启，请自己编辑 gsuid_core/data/config.json 删除冗余配置")
    
show_cfg_path = MAIN_PATH / 'XutheringWavesUID' / 'show_config.json'
if Path(show_cfg_path).exists():
    with open(show_cfg_path, 'r', encoding='utf-8') as f:
        show_cfg_text = f.read()
    if 'WutheringWavesUID' in show_cfg_text:
        logger.info("正在更新显示配置文件中的插件名称...")
        shutil.copyfile(show_cfg_path, MAIN_PATH / 'show_config_back.json')
        show_cfg_text = show_cfg_text.replace('WutheringWavesUID', 'XutheringWavesUID')
        with open(show_cfg_path, 'w', encoding='utf-8') as f:
            f.write(show_cfg_text)
        Path(MAIN_PATH / 'show_config_back.json').unlink()