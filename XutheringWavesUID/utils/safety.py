from gsuid_core.logger import logger

try:
    from .waves_build.safety import *
except ImportError:
    logger.warning("无法导入 safety，将尝试下载")

import importlib

def reload_safety_module():
    try:
        module = importlib.import_module('.waves_build.safety', package=__package__)
        importlib.reload(module) 
        
    except ImportError as e:
        logger.warning(f"无法导入 safety 模块: {e}")
        return

    current_globals = globals()

    if hasattr(module, '__all__'):
        attributes = module.__all__
    else:
        attributes = [name for name in dir(module) if not name.startswith('_')]

    for attr in attributes:
        val = getattr(module, attr)
        current_globals[attr] = val
        
    logger.info("safety 模块已重新加载")    