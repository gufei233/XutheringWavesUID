from gsuid_core.logger import logger
from typing import Any, Dict, Tuple

def calc_phantom_entry(*args, **kwargs) -> Tuple[float, float]:
    from .waves_build.calculate import calc_phantom_entry as _func

    return _func(*args, **kwargs)


def calc_phantom_score(*args, **kwargs) -> Tuple[float, str]:
    from .waves_build.calculate import calc_phantom_score as _func

    return _func(*args, **kwargs)


def get_calc_map(*args, **kwargs) -> Dict:
    from .waves_build.calculate import get_calc_map as _func

    return _func(*args, **kwargs)


def get_max_score(*args, **kwargs) -> Tuple[float, Any]:
    from .waves_build.calculate import get_max_score as _func

    return _func(*args, **kwargs)


def get_total_score_bg(*args, **kwargs) -> str:
    from .waves_build.calculate import get_total_score_bg as _func

    return _func(*args, **kwargs)


def get_valid_color(*args, **kwargs) -> Tuple[str, str]:
    from .waves_build.calculate import get_valid_color as _func

    return _func(*args, **kwargs)

# try:
#     from .waves_build.calculate import *
# except ImportError:
#     logger.warning("无法导入 calculate，将尝试下载")

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
