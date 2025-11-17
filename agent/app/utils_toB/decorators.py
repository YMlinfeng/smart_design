# ==================== 装饰器模块 ====================
"""
装饰器模块

提供各种装饰器功能，包括：
- 时间记录装饰器
- 日志记录装饰器
- 性能监控装饰器
"""

import time
import logging
import functools
from typing import Callable, Any, Optional
# 导入asyncio用于检查协程函数
import asyncio


# ==================== 时间记录装饰器 ====================
def log_execution_time(
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
    include_args: bool = False,
    include_result: bool = False
):
    """
    记录函数执行时间的装饰器
    
    Args:
        logger: 日志记录器，如果为None则使用默认logger
        level: 日志级别，默认为INFO
        include_args: 是否在日志中包含函数参数
        include_result: 是否在日志中包含函数返回值
    
    Usage:
        @log_execution_time()
        async def my_function():
            pass
            
        @log_execution_time(logger=my_logger, include_args=True)
        def my_function_with_args(arg1, arg2):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # 获取日志记录器
            if logger is None:
                func_logger = logging.getLogger(func.__module__)
            else:
                func_logger = logger
            
            # 记录开始时间
            start_time = time.perf_counter()
            
            # 构建日志消息
            func_name = func.__name__
            class_name = ""
            if args and hasattr(args[0], '__class__'):
                class_name = f"{args[0].__class__.__name__}."
            
            start_msg = f"开始: {class_name}{func_name}"
            if include_args and (args or kwargs):
                args_str = ", ".join([str(arg) for arg in args[1:]])  # 跳过self参数
                kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
                all_args = ", ".join(filter(None, [args_str, kwargs_str]))
                if all_args:
                    start_msg += f" (参数: {all_args})"
            
            func_logger.log(level, start_msg)
            
            try:
                # 执行函数
                result = await func(*args, **kwargs)
                
                # 计算执行时间
                execution_time = (time.perf_counter() - start_time) * 1000
                
                # 构建结束日志消息
                end_msg = f"结束: {class_name}{func_name}, 用时 {int(execution_time)} ms"
                if include_result and result is not None:
                    result_str = str(result)[:100]  # 限制结果长度
                    if len(str(result)) > 100:
                        result_str += "..."
                    end_msg += f" (结果: {result_str})"
                
                func_logger.log(level, end_msg)
                
                return result
                
            except Exception as e:
                # 计算执行时间（即使出错）
                execution_time = (time.perf_counter() - start_time) * 1000
                
                # 记录错误日志
                error_msg = f"错误: {class_name}{func_name}, 用时 {int(execution_time)} ms, 错误: {str(e)}"
                func_logger.error(error_msg)
                
                # 重新抛出异常
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # 获取日志记录器
            if logger is None:
                func_logger = logging.getLogger(func.__module__)
            else:
                func_logger = logger
            
            # 记录开始时间
            start_time = time.perf_counter()
            
            # 构建日志消息
            func_name = func.__name__
            class_name = ""
            if args and hasattr(args[0], '__class__'):
                class_name = f"{args[0].__class__.__name__}."
            
            start_msg = f"开始: {class_name}{func_name}"
            if include_args and (args or kwargs):
                args_str = ", ".join([str(arg) for arg in args[1:]])  # 跳过self参数
                kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
                all_args = ", ".join(filter(None, [args_str, kwargs_str]))
                if all_args:
                    start_msg += f" (参数: {all_args})"
            
            func_logger.log(level, start_msg)
            
            try:
                # 执行函数
                result = func(*args, **kwargs)
                
                # 计算执行时间
                execution_time = (time.perf_counter() - start_time) * 1000
                
                # 构建结束日志消息
                end_msg = f"结束: {class_name}{func_name}, 用时 {int(execution_time)} ms"
                if include_result and result is not None:
                    result_str = str(result)[:100]  # 限制结果长度
                    if len(str(result)) > 100:
                        result_str += "..."
                    end_msg += f" (结果: {result_str})"
                
                func_logger.log(level, end_msg)
                
                return result
                
            except Exception as e:
                # 计算执行时间（即使出错）
                execution_time = (time.perf_counter() - start_time) * 1000
                
                # 记录错误日志
                error_msg = f"错误: {class_name}{func_name}, 用时 {int(execution_time)} ms, 错误: {str(e)}"
                func_logger.error(error_msg)
                
                # 重新抛出异常
                raise
        
        # 根据函数是否为协程函数返回相应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# ==================== 简化版时间记录装饰器 ====================
def timing(func: Callable) -> Callable:
    """
    简化的时间记录装饰器，使用默认配置
    
    Usage:
        @timing
        async def my_function():
            pass
    """
    return log_execution_time()(func)


# ==================== 带自定义消息的时间记录装饰器 ====================
def log_timing_with_message(message_prefix: str = ""):
    """
    带自定义消息前缀的时间记录装饰器
    
    Args:
        message_prefix: 日志消息前缀
    
    Usage:
        @log_timing_with_message("处理用户请求")
        async def process_request():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger(func.__module__)
            start_time = time.perf_counter()
            
            func_name = func.__name__
            class_name = ""
            if args and hasattr(args[0], '__class__'):
                class_name = f"{args[0].__class__.__name__}."
            
            start_msg = f"开始: {message_prefix}{class_name}{func_name}" if message_prefix else f"开始: {class_name}{func_name}"
            logger.info(start_msg)
            
            try:
                result = await func(*args, **kwargs)
                execution_time = (time.perf_counter() - start_time) * 1000
                end_msg = f"结束: {message_prefix}{class_name}{func_name}, 用时 {int(execution_time)} ms" if message_prefix else f"结束: {class_name}{func_name}, 用时 {int(execution_time)} ms"
                logger.info(end_msg)
                return result
            except Exception as e:
                execution_time = (time.perf_counter() - start_time) * 1000
                error_msg = f"错误: {message_prefix}{class_name}{func_name}, 用时 {int(execution_time)} ms, 错误: {str(e)}" if message_prefix else f"错误: {class_name}{func_name}, 用时 {int(execution_time)} ms, 错误: {str(e)}"
                logger.error(error_msg)
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger(func.__module__)
            start_time = time.perf_counter()
            
            func_name = func.__name__
            class_name = ""
            if args and hasattr(args[0], '__class__'):
                class_name = f"{args[0].__class__.__name__}."
            
            start_msg = f"开始: {message_prefix}{class_name}{func_name}" if message_prefix else f"开始: {class_name}{func_name}"
            logger.info(start_msg)
            
            try:
                result = func(*args, **kwargs)
                execution_time = (time.perf_counter() - start_time) * 1000
                end_msg = f"结束: {message_prefix}{class_name}{func_name}, 用时 {int(execution_time)} ms" if message_prefix else f"结束: {class_name}{func_name}, 用时 {int(execution_time)} ms"
                logger.info(end_msg)
                return result
            except Exception as e:
                execution_time = (time.perf_counter() - start_time) * 1000
                error_msg = f"错误: {message_prefix}{class_name}{func_name}, 用时 {int(execution_time)} ms, 错误: {str(e)}" if message_prefix else f"错误: {class_name}{func_name}, 用时 {int(execution_time)} ms, 错误: {str(e)}"
                logger.error(error_msg)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# ==================== 性能监控装饰器 ====================
def performance_monitor(
    threshold_ms: float = 1000.0,
    logger: Optional[logging.Logger] = None,
    level: int = logging.WARNING
):
    """
    性能监控装饰器，当函数执行时间超过阈值时记录警告
    
    Args:
        threshold_ms: 时间阈值（毫秒）
        logger: 日志记录器
        level: 警告日志级别
    
    Usage:
        @performance_monitor(threshold_ms=500)
        async def slow_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            if logger is None:
                func_logger = logging.getLogger(func.__module__)
            else:
                func_logger = logger
            
            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            execution_time = (time.perf_counter() - start_time) * 1000
            
            if execution_time > threshold_ms:
                func_logger.log(level, f"性能警告: {func.__name__} 执行时间 {int(execution_time)} ms 超过阈值 {threshold_ms} ms")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            if logger is None:
                func_logger = logging.getLogger(func.__module__)
            else:
                func_logger = logger
            
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            execution_time = (time.perf_counter() - start_time) * 1000
            
            if execution_time > threshold_ms:
                func_logger.log(level, f"性能警告: {func.__name__} 执行时间 {int(execution_time)} ms 超过阈值 {threshold_ms} ms")
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


