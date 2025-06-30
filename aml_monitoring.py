#!/usr/bin/env python3
"""
📊 Система мониторинга и логирования AML
Версия: 3.0

Функции:
- Расширенное логирование всех компонентов
- Мониторинг производительности в реальном времени  
- Сбор метрик обработки транзакций
- Алерты и уведомления о критических событиях
- Dashboard метрик и статистики
"""

import os
import sys
import time
import json
import psutil
import logging
import threading
import smtplib
import requests
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
import sqlite3
from contextlib import contextmanager

# Импорт конфигурации
try:
    from aml_config import get_config
except ImportError:
    print("⚠️ Модуль aml_config не найден")
    get_config = lambda: None


@dataclass
class MetricPoint:
    """Точка метрики"""
    timestamp: datetime
    name: str
    value: Union[int, float]
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'name': self.name,
            'value': self.value,
            'tags': self.tags
        }


@dataclass
class Alert:
    """Алерт"""
    id: str
    level: str  # info, warning, error, critical
    message: str
    component: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'level': self.level,
            'message': self.message,
            'component': self.component,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved,
            'resolution_time': self.resolution_time.isoformat() if self.resolution_time else None
        }


class MetricsCollector:
    """Сборщик метрик"""
    
    def __init__(self, max_points: int = 10000):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()
    
    def record_metric(self, name: str, value: Union[int, float], tags: Dict[str, str] = None):
        """Запись метрики"""
        with self.lock:
            point = MetricPoint(
                timestamp=datetime.now(),
                name=name,
                value=value,
                tags=tags or {}
            )
            self.metrics[name].append(point)
    
    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Увеличение счетчика"""
        with self.lock:
            self.counters[name] += value
            self.record_metric(f"{name}_total", self.counters[name], tags)
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Установка значения gauge"""
        with self.lock:
            self.gauges[name] = value
            self.record_metric(name, value, tags)
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Запись в гистограмму"""
        with self.lock:
            self.histograms[name].append(value)
            # Ограничиваем размер гистограммы
            if len(self.histograms[name]) > 1000:
                self.histograms[name] = self.histograms[name][-1000:]
            
            # Записываем статистики
            values = self.histograms[name]
            self.record_metric(f"{name}_avg", sum(values) / len(values), tags)
            self.record_metric(f"{name}_min", min(values), tags)
            self.record_metric(f"{name}_max", max(values), tags)
    
    def get_metrics(self, name: str = None, since: datetime = None) -> Dict[str, List[MetricPoint]]:
        """Получение метрик"""
        with self.lock:
            if name:
                if name in self.metrics:
                    points = list(self.metrics[name])
                    if since:
                        points = [p for p in points if p.timestamp >= since]
                    return {name: points}
                return {}
            
            result = {}
            for metric_name, points in self.metrics.items():
                filtered_points = list(points)
                if since:
                    filtered_points = [p for p in filtered_points if p.timestamp >= since]
                result[metric_name] = filtered_points
            
            return result
    
    def get_latest_values(self) -> Dict[str, Any]:
        """Получение последних значений всех метрик"""
        with self.lock:
            result = {}
            
            # Последние значения метрик
            for name, points in self.metrics.items():
                if points:
                    result[name] = points[-1].value
            
            # Счетчики
            for name, value in self.counters.items():
                result[f"{name}_total"] = value
            
            # Gauges
            result.update(self.gauges)
            
            return result
    
    def clear_old_metrics(self, before: datetime):
        """Очистка старых метрик"""
        with self.lock:
            for name, points in self.metrics.items():
                while points and points[0].timestamp < before:
                    points.popleft()


class AlertManager:
    """Менеджер алертов"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_rules: List[Callable] = []
        self.notification_handlers: List[Callable] = []
        self.lock = threading.Lock()
        self.alert_counter = 0
    
    def add_alert_rule(self, rule: Callable):
        """Добавление правила алертов"""
        self.alert_rules.append(rule)
    
    def add_notification_handler(self, handler: Callable):
        """Добавление обработчика уведомлений"""
        self.notification_handlers.append(handler)
    
    def create_alert(self, level: str, message: str, component: str) -> Alert:
        """Создание алерта"""
        with self.lock:
            self.alert_counter += 1
            alert = Alert(
                id=f"alert_{self.alert_counter:06d}",
                level=level,
                message=message,
                component=component,
                timestamp=datetime.now()
            )
            
            self.alerts.append(alert)
            
            # Уведомления
            for handler in self.notification_handlers:
                try:
                    handler(alert)
                except Exception as e:
                    print(f"Ошибка в обработчике уведомлений: {e}")
            
            return alert
    
    def resolve_alert(self, alert_id: str):
        """Разрешение алерта"""
        with self.lock:
            for alert in self.alerts:
                if alert.id == alert_id:
                    alert.resolved = True
                    alert.resolution_time = datetime.now()
                    break
    
    def get_active_alerts(self) -> List[Alert]:
        """Получение активных алертов"""
        with self.lock:
            return [alert for alert in self.alerts if not alert.resolved]
    
    def get_all_alerts(self, since: datetime = None) -> List[Alert]:
        """Получение всех алертов"""
        with self.lock:
            alerts = list(self.alerts)
            if since:
                alerts = [alert for alert in alerts if alert.timestamp >= since]
            return alerts
    
    def check_rules(self, metrics: Dict[str, Any]):
        """Проверка правил алертов"""
        for rule in self.alert_rules:
            try:
                rule(metrics, self)
            except Exception as e:
                print(f"Ошибка в правиле алерта: {e}")


class LoggingManager:
    """Менеджер логирования"""
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.loggers: Dict[str, logging.Logger] = {}
        self.setup_logging()
    
    def setup_logging(self):
        """Настройка системы логирования"""
        # Создаем папку для логов
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Настройка форматирования
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Настройка обработчиков
        self.setup_main_logger(detailed_formatter)
        self.setup_component_loggers(detailed_formatter)
        self.setup_error_logger(detailed_formatter)
        self.setup_audit_logger(simple_formatter)
    
    def setup_main_logger(self, formatter):
        """Настройка основного логгера"""
        logger = logging.getLogger('AMLSystem')
        logger.setLevel(logging.INFO)
        
        # Консольный вывод
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Файловый вывод с ротацией
        file_handler = RotatingFileHandler(
            'logs/aml_system.log',
            maxBytes=50*1024*1024,  # 50MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        self.loggers['main'] = logger
    
    def setup_component_loggers(self, formatter):
        """Настройка логгеров компонентов"""
        components = [
            'backend', 'frontend', 'processor', 'analyzer', 
            'database', 'network', 'monitoring'
        ]
        
        for component in components:
            logger = logging.getLogger(f'AML.{component}')
            logger.setLevel(logging.DEBUG)
            
            # Отдельный файл для каждого компонента
            file_handler = TimedRotatingFileHandler(
                f'logs/{component}.log',
                when='midnight',
                interval=1,
                backupCount=7
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            self.loggers[component] = logger
    
    def setup_error_logger(self, formatter):
        """Настройка логгера ошибок"""
        logger = logging.getLogger('AML.errors')
        logger.setLevel(logging.ERROR)
        
        # Файл только для ошибок
        error_handler = RotatingFileHandler(
            'logs/errors.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
        
        self.loggers['errors'] = logger
    
    def setup_audit_logger(self, formatter):
        """Настройка аудит логгера"""
        logger = logging.getLogger('AML.audit')
        logger.setLevel(logging.INFO)
        logger.propagate = False  # Не передавать в родительские логгеры
        
        # Аудит лог - не ротируется, только добавляется
        audit_handler = logging.FileHandler('logs/audit.log')
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(formatter)
        logger.addHandler(audit_handler)
        
        self.loggers['audit'] = logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """Получение логгера"""
        if name in self.loggers:
            return self.loggers[name]
        return self.loggers.get('main', logging.getLogger(name))


class SystemMonitor:
    """Системный монитор"""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.alerts = AlertManager()
        self.logging_manager = LoggingManager()
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Настройка алертов
        self.setup_alert_rules()
        self.setup_notification_handlers()
        
        # Логгер
        self.logger = self.logging_manager.get_logger('monitoring')
    
    def setup_alert_rules(self):
        """Настройка правил алертов"""
        
        def cpu_rule(metrics: Dict[str, Any], alert_manager: AlertManager):
            cpu_usage = metrics.get('system.cpu_percent', 0)
            if cpu_usage > 90:
                alert_manager.create_alert(
                    'critical', f'Высокая загрузка CPU: {cpu_usage:.1f}%', 'system'
                )
            elif cpu_usage > 80:
                alert_manager.create_alert(
                    'warning', f'Повышенная загрузка CPU: {cpu_usage:.1f}%', 'system'
                )
        
        def memory_rule(metrics: Dict[str, Any], alert_manager: AlertManager):
            memory_usage = metrics.get('system.memory_percent', 0)
            if memory_usage > 85:
                alert_manager.create_alert(
                    'critical', f'Высокое использование памяти: {memory_usage:.1f}%', 'system'
                )
            elif memory_usage > 75:
                alert_manager.create_alert(
                    'warning', f'Повышенное использование памяти: {memory_usage:.1f}%', 'system'
                )
        
        def disk_rule(metrics: Dict[str, Any], alert_manager: AlertManager):
            disk_usage = metrics.get('system.disk_percent', 0)
            if disk_usage > 90:
                alert_manager.create_alert(
                    'critical', f'Мало места на диске: {disk_usage:.1f}%', 'system'
                )
            elif disk_usage > 80:
                alert_manager.create_alert(
                    'warning', f'Заканчивается место на диске: {disk_usage:.1f}%', 'system'
                )
        
        def processing_rule(metrics: Dict[str, Any], alert_manager: AlertManager):
            error_rate = metrics.get('processing.error_rate', 0)
            if error_rate > 10:
                alert_manager.create_alert(
                    'error', f'Высокий уровень ошибок обработки: {error_rate:.1f}%', 'processor'
                )
        
        self.alerts.add_alert_rule(cpu_rule)
        self.alerts.add_alert_rule(memory_rule)
        self.alerts.add_alert_rule(disk_rule)
        self.alerts.add_alert_rule(processing_rule)
    
    def setup_notification_handlers(self):
        """Настройка обработчиков уведомлений"""
        
        def console_notification(alert: Alert):
            level_icons = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '❌',
                'critical': '🚨'
            }
            icon = level_icons.get(alert.level, '📢')
            print(f"{icon} [{alert.level.upper()}] {alert.component}: {alert.message}")
        
        def log_notification(alert: Alert):
            logger = self.logging_manager.get_logger('alerts')
            if alert.level == 'critical':
                logger.critical(f"{alert.component}: {alert.message}")
            elif alert.level == 'error':
                logger.error(f"{alert.component}: {alert.message}")
            elif alert.level == 'warning':
                logger.warning(f"{alert.component}: {alert.message}")
            else:
                logger.info(f"{alert.component}: {alert.message}")
        
        self.alerts.add_notification_handler(console_notification)
        self.alerts.add_notification_handler(log_notification)
    
    def start_monitoring(self, interval: float = 5.0):
        """Запуск мониторинга"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info("Системный мониторинг запущен")
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        if not self.running:
            return
        
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        self.logger.info("Системный мониторинг остановлен")
    
    def _monitor_loop(self, interval: float):
        """Цикл мониторинга"""
        while self.running:
            try:
                self._collect_system_metrics()
                self._check_alerts()
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"Ошибка в цикле мониторинга: {e}")
    
    def _collect_system_metrics(self):
        """Сбор системных метрик"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics.set_gauge('system.cpu_percent', cpu_percent)
            
            # Память
            memory = psutil.virtual_memory()
            self.metrics.set_gauge('system.memory_percent', memory.percent)
            self.metrics.set_gauge('system.memory_available_gb', memory.available / (1024**3))
            
            # Диск
            disk = psutil.disk_usage('/')
            self.metrics.set_gauge('system.disk_percent', disk.percent)
            self.metrics.set_gauge('system.disk_free_gb', disk.free / (1024**3))
            
            # Сеть
            network = psutil.net_io_counters()
            self.metrics.set_gauge('system.network_bytes_sent', network.bytes_sent)
            self.metrics.set_gauge('system.network_bytes_recv', network.bytes_recv)
            
            # Процессы
            process_count = len(psutil.pids())
            self.metrics.set_gauge('system.process_count', process_count)
            
        except Exception as e:
            self.logger.error(f"Ошибка сбора системных метрик: {e}")
    
    def _check_alerts(self):
        """Проверка алертов"""
        try:
            latest_metrics = self.metrics.get_latest_values()
            self.alerts.check_rules(latest_metrics)
        except Exception as e:
            self.logger.error(f"Ошибка проверки алертов: {e}")
    
    def record_processing_metric(self, 
                                metric_name: str, 
                                value: Union[int, float], 
                                component: str = 'processor',
                                tags: Dict[str, str] = None):
        """Запись метрики обработки"""
        full_name = f"processing.{metric_name}"
        tags = tags or {}
        tags['component'] = component
        
        self.metrics.record_metric(full_name, value, tags)
        
        # Логирование важных метрик
        if metric_name in ['transactions_processed', 'errors_count', 'processing_time']:
            logger = self.logging_manager.get_logger('processor')
            logger.info(f"{metric_name}: {value} (component: {component})")
    
    def record_analysis_metric(self,
                              analysis_type: str,
                              transactions_count: int,
                              processing_time: float,
                              errors_count: int = 0):
        """Запись метрик анализа"""
        tags = {'analysis_type': analysis_type}
        
        self.metrics.record_metric('analysis.transactions_processed', transactions_count, tags)
        self.metrics.record_histogram('analysis.processing_time', processing_time, tags)
        self.metrics.increment_counter('analysis.total_processed', transactions_count, tags)
        
        if errors_count > 0:
            self.metrics.increment_counter('analysis.errors', errors_count, tags)
            error_rate = (errors_count / transactions_count) * 100
            self.metrics.set_gauge('analysis.error_rate', error_rate, tags)
        
        # Логирование
        logger = self.logging_manager.get_logger('analyzer')
        logger.info(f"Анализ {analysis_type}: {transactions_count} транзакций, "
                   f"{processing_time:.2f}с, ошибок: {errors_count}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Получение данных для dashboard"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        return {
            'timestamp': now.isoformat(),
            'system_metrics': {
                name: value for name, value in self.metrics.get_latest_values().items()
                if name.startswith('system.')
            },
            'processing_metrics': {
                name: value for name, value in self.metrics.get_latest_values().items()
                if name.startswith('processing.') or name.startswith('analysis.')
            },
            'active_alerts': [alert.to_dict() for alert in self.alerts.get_active_alerts()],
            'recent_alerts': [alert.to_dict() for alert in self.alerts.get_all_alerts(since=hour_ago)],
            'uptime': self._get_uptime(),
            'summary': self._get_summary_stats()
        }
    
    def _get_uptime(self) -> str:
        """Получение времени работы системы"""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{days}d {hours}h {minutes}m"
        except:
            return "Unknown"
    
    def _get_summary_stats(self) -> Dict[str, Any]:
        """Получение сводной статистики"""
        latest = self.metrics.get_latest_values()
        
        return {
            'total_transactions_processed': latest.get('analysis.total_processed_total', 0),
            'current_cpu_usage': latest.get('system.cpu_percent', 0),
            'current_memory_usage': latest.get('system.memory_percent', 0),
            'active_alerts_count': len(self.alerts.get_active_alerts()),
            'processing_error_rate': latest.get('processing.error_rate', 0)
        }
    
    def save_metrics_to_db(self, db_path: str = "aml_metrics.db"):
        """Сохранение метрик в БД"""
        try:
            # Создание таблиц если их нет
            with sqlite3.connect(db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        name TEXT NOT NULL,
                        value REAL NOT NULL,
                        tags TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id TEXT PRIMARY KEY,
                        level TEXT NOT NULL,
                        message TEXT NOT NULL,
                        component TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        resolved BOOLEAN DEFAULT FALSE,
                        resolution_time TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Сохранение последних метрик
                hour_ago = datetime.now() - timedelta(hours=1)
                metrics_data = self.metrics.get_metrics(since=hour_ago)
                
                for name, points in metrics_data.items():
                    for point in points[-100:]:  # Последние 100 точек
                        conn.execute(
                            'INSERT INTO metrics (timestamp, name, value, tags) VALUES (?, ?, ?, ?)',
                            (point.timestamp.isoformat(), point.name, point.value, json.dumps(point.tags))
                        )
                
                # Сохранение алертов
                for alert in self.alerts.get_all_alerts(since=hour_ago):
                    conn.execute('''
                        INSERT OR REPLACE INTO alerts 
                        (id, level, message, component, timestamp, resolved, resolution_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        alert.id, alert.level, alert.message, alert.component,
                        alert.timestamp.isoformat(), alert.resolved,
                        alert.resolution_time.isoformat() if alert.resolution_time else None
                    ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения метрик в БД: {e}")


# Глобальный экземпляр монитора
system_monitor = SystemMonitor()


def get_monitor() -> SystemMonitor:
    """Получение глобального экземпляра монитора"""
    return system_monitor


if __name__ == "__main__":
    # Тестирование системы мониторинга
    monitor = get_monitor()
    
    print("🚀 Запуск тестирования системы мониторинга...")
    monitor.start_monitoring(interval=2.0)
    
    try:
        # Имитация метрик
        for i in range(10):
            monitor.record_processing_metric('test_transactions', i * 10)
            monitor.record_analysis_metric('transaction', i * 5, 1.5 + i * 0.1)
            time.sleep(2)
            
            if i == 5:
                # Тест алерта
                monitor.alerts.create_alert('warning', 'Тестовый алерт', 'test')
        
        # Вывод dashboard
        dashboard = monitor.get_dashboard_data()
        print("\n📊 DASHBOARD DATA:")
        print(json.dumps(dashboard, indent=2, ensure_ascii=False))
        
        # Сохранение в БД
        monitor.save_metrics_to_db()
        print("\n💾 Метрики сохранены в БД")
        
    except KeyboardInterrupt:
        print("\n⚠️ Остановка тестирования...")
    finally:
        monitor.stop_monitoring()