from gsuid_core.logger import logger

def check_if_ph_3(**kwargs) -> bool:
    from ..waves_build.damage import check_if_ph_3 as _func

    return _func(**kwargs)


def check_if_ph_5(**kwargs) -> bool:
    from ..waves_build.damage import check_if_ph_5 as _func

    return _func(**kwargs)

# try:
#     from ..waves_build.damage import *
# except ImportError:
#     logger.warning("无法导入 damage，将尝试下载")    

import importlib

def reload_damage_module():
    try:
        module = importlib.import_module('..waves_build.damage', package=__package__)
        importlib.reload(module) 
        
    except ImportError as e:
        logger.warning(f"无法导入 damage 模块: {e}")
        return

    current_globals = globals()

    if hasattr(module, '__all__'):
        attributes = module.__all__
    else:
        attributes = [name for name in dir(module) if not name.startswith('_')]

    for attr in attributes:
        val = getattr(module, attr)
        current_globals[attr] = val
        
    logger.info("damage 模块已重新加载")
