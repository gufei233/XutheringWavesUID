from gsuid_core.logger import logger

try:
    from .waves_build.calculate import *
except ImportError:
    logger.warning("无法导入 calculate，将尝试下载")

import importlib        
        
def reload_calculate_module():
    try:
        module = importlib.import_module('.waves_build.calculate', package=__package__)
        importlib.reload(module) 
        
    except ImportError as e:
        logger.warning(f"无法导入 calculate 模块: {e}")
        return

    current_globals = globals()

    if hasattr(module, '__all__'):
        attributes = module.__all__
    else:
        attributes = [name for name in dir(module) if not name.startswith('_')]

    for attr in attributes:
        val = getattr(module, attr)
        current_globals[attr] = val
        
    logger.info("calculate 模块已重新加载")