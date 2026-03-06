import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional


class Logger:
    """
    日志记录器
    """
    
    def __init__(self, name: str, log_file: Optional[str] = None, level: str = 'INFO'):
        """
        初始化日志记录器
        
        Args:
            name: 日志记录器名称
            log_file: 日志文件路径，如果为 None 则不输出到文件
            level: 日志级别（DEBUG、INFO、WARNING、ERROR）
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        if not self.logger.handlers:
            formatter = logging.Formatter(
                '%(asctime)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            if log_file:
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=10*1024*1024,
                    backupCount=5,
                    encoding='utf-8'
                )
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
    
    def debug(self, message: str):
        """
        记录 DEBUG 级别日志
        
        Args:
            message: 日志消息
        """
        self.logger.debug(message)
    
    def info(self, message: str):
        """
        记录 INFO 级别日志
        
        Args:
            message: 日志消息
        """
        self.logger.info(message)
    
    def warning(self, message: str):
        """
        记录 WARNING 级别日志
        
        Args:
            message: 日志消息
        """
        self.logger.warning(message)
    
    def error(self, message: str):
        """
        记录 ERROR 级别日志
        
        Args:
            message: 日志消息
        """
        self.logger.error(message)
    
    def critical(self, message: str):
        """
        记录 CRITICAL 级别日志
        
        Args:
            message: 日志消息
        """
        self.logger.critical(message)
    
    def exception(self, message: str, exc_info=True):
        """
        记录异常信息
        
        Args:
            message: 日志消息
            exc_info: 是否包含异常信息
        """
        self.logger.exception(message, exc_info=exc_info)