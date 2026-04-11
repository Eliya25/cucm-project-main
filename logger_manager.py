"""
מערכת הלוגים המרכזית של הפרויקט.

LoggerManager יוצר logger יחיד לכל האפליקציה, וכותב לוגים לקבצים
לפי תיקייה יומית תחת logs/DD-MM-YYYY. הכתיבה עצמה מתבצעת דרך queue
כדי לא לחסום בקשות HTTP בזמן כתיבה לדיסק.
"""

import atexit
import logging
import logging.handlers
import os
import queue
import shutil
import threading
from datetime import date, datetime, timedelta

from app.schemas import user

class LoggerManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        raise TypeError("Use LoggerManager.initialize(...) instead of constructor")

    @classmethod
    def initialize(
        cls, path_prefix="logs", size_mb=10, backup_count=30, retention_days=30
    ):
        # Initializes the singleton logger once and registers clean shutdown.

        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = object.__new__(cls)
                    instance.logger, instance.listener = instance._create_logger(
                        path_prefix=path_prefix,
                        size_mb=size_mb,
                        backup_count=backup_count,
                        retention_days=retention_days,
                    )
                    cls._instance = instance
                    atexit.register(cls.stop)
        return cls._instance

    @classmethod
    def get_logger(cls):
        # Returns the shared logger after initialize() has run.
        if cls._instance is None:
            raise RuntimeError("LoggerManager has not been initialized")

        return cls._instance.logger
    
    @classmethod
    def log_audit(cls, user: str, action: str, target: str, details: str = ""):
        logger = cls.get_logger()
        logger.info(f"AUDIT | User: {user} | Action: {action} | Target: {target} | Details: {details}")

    @classmethod
    def stop(cls):
        # Stops the queue listener so buffered logs are flushed on exit.
        if cls._instance is None:
            raise RuntimeError("LoggerManager has not been initialized")

        cls._instance.listener.stop()

    def _create_logger(
        self, path_prefix="logs", size_mb=10, backup_count=30, retention_days=30
    ):
        # Creates the root logger, queue handler, and size/day rotating file handler.
        log_queue = queue.Queue()
        logger = logging.getLogger()

        logger.setLevel(logging.DEBUG)

        queue_handler = logging.handlers.QueueHandler(log_queue)
        logger.addHandler(queue_handler)
        folder_name = date.today().strftime("%d-%m-%Y")
        log_dir = os.path.join(path_prefix, folder_name)

        os.makedirs(log_dir, exist_ok=True)

        file_handler = self.DailyFolderRotatingHandler(
            path_prefix=path_prefix,
            maxBytes=size_mb * 1024 * 1024,
            backupCount=backup_count,
            retention_days=retention_days,
        )

        formatter = logging.Formatter(
            "[%(levelname)s]-%(asctime)s %(message)s", datefmt="%H:%M:%S"
        )

        file_handler.setFormatter(formatter)
        listener = logging.handlers.QueueListener(log_queue, file_handler)
        listener.start()

        return logger, listener

    class DailyFolderRotatingHandler(logging.handlers.RotatingFileHandler):

        def __init__(self, path_prefix, maxBytes, backupCount, retention_days):
            self.path_prefix = path_prefix
            self.current_date = date.today().strftime("%d-%m-%Y")
            self.retention_days = retention_days
            self.log_dir = self._get_log_dir()
            os.makedirs(self.log_dir, exist_ok=True)
            filename = os.path.join(self.log_dir, "log.txt")
            super().__init__(filename, maxBytes=maxBytes, backupCount=backupCount)
            self._cleanup_old_logs()
            self._trigger_cleanup_thread()

        def _trigger_cleanup_thread(self):
            cleanup_thread = threading.Thread(target=self._cleanup_old_logs, daemon=True)
            cleanup_thread.start()
            
        def _cleanup_old_logs(self):
            # Deletes dated log folders older than the configured retention window.
            base_dir = self.path_prefix

            if not os.path.exists(base_dir):
                return

            cutoff = datetime.now() - timedelta(days=self.retention_days)

            for folder in os.listdir(base_dir):
                folder_path = os.path.join(base_dir, folder)
                if not os.path.isdir(folder_path):
                    continue

                try:
                    folder_date = datetime.strptime(folder, "%d-%m-%Y")

                except ValueError:
                    continue

                if folder_date < cutoff:
                    shutil.rmtree(folder_path)

        def _get_log_dir(self):
            return os.path.join(self.path_prefix, self.current_date)

        def _update_date_if_needed(self):
            # Switches the output file when the calendar day changes.
            new_date = date.today().strftime('%d-%m-%Y')
            if new_date != self.current_date:
                self.current_date = new_date
                self.log_dir = self._get_log_dir()
                os.makedirs(self.log_dir, exist_ok=True)

                if self.stream:
                    self.stream.close()
                    
                self.baseFilename = os.path.join(self.log_dir, 'log.txt')
                self.stream = self._open()

                self._trigger_cleanup_thread()
        
        def emit(self, record: logging.LogRecord):
            self._update_date_if_needed()
            super().emit(record)