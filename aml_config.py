#!/usr/bin/env python3
"""
🔧 Конфигурация AML системы для мультипроцессорной обработки
Версия: 3.0

Централизованная конфигурация для:
- Параметров параллельной обработки
- Настроек профилей анализа
- Пороговых значений и правил
- Производительности и мониторинга
"""

import os
import json
import psutil
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ProcessingConfig:
    """Конфигурация обработки данных"""
    # Параллельная обработка
    max_workers: int = field(default_factory=lambda: min(20, max(1, psutil.cpu_count() - 2)))
    batch_size: int = 100
    chunk_size: int = 1000
    
    # Лимиты ресурсов
    max_memory_gb: float = 4.0
    max_cpu_percent: float = 80.0
    timeout_seconds: int = 300
    
    # Стратегии обработки
    use_parallel_json_loading: bool = True
    use_parallel_analysis: bool = True
    auto_optimize_workers: bool = True
    
    # Кэширование
    enable_result_cache: bool = True
    cache_ttl_minutes: int = 60
    
    def optimize_for_system(self):
        """Автоматическая оптимизация под систему"""
        # Анализ системных ресурсов
        memory_gb = psutil.virtual_memory().total / (1024**3)
        cpu_count = psutil.cpu_count()
        
        # Адаптивная настройка
        if memory_gb < 4:
            self.batch_size = 50
            self.max_workers = min(4, cpu_count)
            self.max_memory_gb = memory_gb * 0.7
        elif memory_gb < 8:
            self.batch_size = 100
            self.max_workers = min(8, cpu_count - 1)
            self.max_memory_gb = memory_gb * 0.8
        else:
            self.batch_size = 200
            self.max_workers = min(20, cpu_count - 2)
            self.max_memory_gb = memory_gb * 0.8
        
        print(f"🔧 Автооптимизация: {self.max_workers} воркеров, батч {self.batch_size}")


@dataclass
class AnalysisConfig:
    """Конфигурация анализа рисков"""
    # Веса профилей (должны суммироваться до 1.0)
    profile_weights: Dict[str, float] = field(default_factory=lambda: {
        'transaction': 0.40,
        'network': 0.30,
        'customer': 0.15,
        'behavioral': 0.10,
        'geographic': 0.05
    })
    
    # Пороговые значения АФМ РК (в тенге)
    thresholds: Dict[str, float] = field(default_factory=lambda: {
        'cash_operations': 2_000_000,      # 2 млн тенге
        'international_transfers': 1_000_000,  # 1 млн тенге
        'domestic_transfers': 7_000_000,   # 7 млн тенге
        'suspicious_amount': 10_000_000,   # 10 млн тенге
        'high_risk_amount': 50_000_000     # 50 млн тенге
    })
    
    # Оценки риска
    risk_scores: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        'transaction': {
            'threshold_exceeded': 3.0,
            'round_amount': 2.0,
            'unusual_time': 1.5,
            'suspicious_purpose': 3.0,
            'multiple_patterns': 2.0
        },
        'network': {
            'circular_scheme': 8.0,
            'star_pattern': 6.0,
            'smurfing': 7.0,
            'transit_chain': 5.0,
            'high_centrality': 4.0
        },
        'geographic': {
            'offshore_zone': 5.0,
            'sanctioned_country': 8.0,
            'fatf_blacklist': 10.0,
            'fatf_greylist': 5.0,
            'high_risk_corridor': 3.0
        },
        'behavioral': {
            'volume_spike': 4.0,
            'frequency_change': 3.0,
            'new_geography': 2.0,
            'dormant_activation': 5.0,
            'pattern_deviation': 3.0
        },
        'customer': {
            'pep_status': 6.0,
            'high_risk_business': 4.0,
            'sanctions_match': 10.0,
            'adverse_media': 3.0,
            'kyc_incomplete': 2.0
        }
    })
    
    # Классификация рисков
    risk_categories: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        'thresholds': {
            'low': 3.0,
            'medium': 5.0,
            'high': 7.0,
            'critical': 9.0
        },
        'actions': {
            'pass': 3.0,
            'monitor': 5.0,
            'edd': 7.0,    # Enhanced Due Diligence
            'str': 7.0     # Suspicious Transaction Report
        }
    })
    
    # Бонусы за множественные индикаторы
    multi_indicator_bonus: float = 0.5
    max_bonus_points: float = 2.0
    
    def validate_weights(self) -> bool:
        """Проверка корректности весов профилей"""
        total_weight = sum(self.profile_weights.values())
        if abs(total_weight - 1.0) > 0.001:
            print(f"⚠️ Сумма весов профилей: {total_weight:.3f} (должна быть 1.0)")
            return False
        return True


@dataclass
class CountryRiskConfig:
    """Конфигурация страновых рисков"""
    # FATF списки (обновляется регулярно)
    fatf_blacklist: List[str] = field(default_factory=lambda: [
        'IR',  # Иран
        'KP'   # Северная Корея
    ])
    
    fatf_greylist: List[str] = field(default_factory=lambda: [
        'AF', 'AL', 'BB', 'BF', 'KH', 'CM', 'HR', 'GH', 'GI', 'JM', 
        'JO', 'ML', 'MZ', 'MM', 'NI', 'PK', 'PA', 'PH', 'SN', 'SO', 
        'SS', 'SY', 'TR', 'UG', 'AE', 'VU', 'YE'
    ])
    
    # Офшорные зоны
    offshore_zones: List[str] = field(default_factory=lambda: [
        'AD', 'AG', 'BS', 'BH', 'BB', 'BZ', 'BM', 'VG', 'KY', 'CK',
        'CW', 'CY', 'DM', 'GI', 'GG', 'GD', 'HK', 'IM', 'JE', 'KN',
        'LB', 'LR', 'LI', 'LU', 'MO', 'MT', 'MH', 'MU', 'MC', 'NR',
        'AN', 'NU', 'PA', 'WS', 'SM', 'SC', 'SG', 'LC', 'VC', 'CH',
        'TO', 'TC', 'VU', 'VE'
    ])
    
    # Санкционные страны
    sanctioned_countries: List[str] = field(default_factory=lambda: [
        'RU', 'BY', 'IR', 'KP', 'AF', 'MM', 'SY'
    ])
    
    # Страны ЕАЭС (низкий риск)
    eaeu_countries: List[str] = field(default_factory=lambda: [
        'KZ', 'RU', 'BY', 'AM', 'KG'
    ])
    
    def get_country_risk(self, country_code: str) -> float:
        """Получение риска страны"""
        if not country_code:
            return 5.0
        
        country_code = country_code.upper()
        
        if country_code in self.fatf_blacklist:
            return 10.0
        elif country_code in self.sanctioned_countries:
            return 8.0
        elif country_code in self.fatf_greylist or country_code in self.offshore_zones:
            return 5.0
        elif country_code in self.eaeu_countries:
            return 1.0
        else:
            return 3.0  # Нейтральный риск


@dataclass
class DatabaseConfig:
    """Конфигурация базы данных"""
    # Основные параметры
    database_path: str = "aml_system.db"
    connection_pool_size: int = 10
    query_timeout: int = 30
    
    # Оптимизация
    enable_wal_mode: bool = True
    enable_foreign_keys: bool = True
    cache_size_mb: int = 64
    temp_store_memory: bool = True
    
    # Индексы для быстрого поиска
    indexes: Dict[str, List[str]] = field(default_factory=lambda: {
        'transactions': [
            'idx_tx_date', 'idx_tx_amount', 'idx_tx_sender', 'idx_tx_beneficiary',
            'idx_tx_risk_score', 'idx_tx_suspicious'
        ],
        'customer_profiles': [
            'idx_customer_id', 'idx_customer_risk', 'idx_customer_country'
        ],
        'network_connections': [
            'idx_network_source', 'idx_network_target', 'idx_network_amount'
        ],
        'behavioral_history': [
            'idx_behavior_customer', 'idx_behavior_date'
        ]
    })
    
    # Настройки архивирования
    archive_after_days: int = 365
    cleanup_temp_tables: bool = True


@dataclass
class MonitoringConfig:
    """Конфигурация мониторинга и логирования"""
    # Логирование
    log_level: str = "INFO"
    log_file_path: str = "logs/aml_system.log"
    max_log_size_mb: int = 100
    backup_count: int = 5
    
    # Мониторинг производительности
    enable_performance_monitoring: bool = True
    monitoring_interval_seconds: int = 5
    alert_cpu_threshold: float = 90.0
    alert_memory_threshold: float = 85.0
    alert_disk_threshold: float = 90.0
    
    # Метрики
    collect_processing_metrics: bool = True
    metrics_retention_days: int = 30
    
    # Уведомления
    enable_alerts: bool = True
    alert_email: Optional[str] = None
    webhook_url: Optional[str] = None


class AMLConfigManager:
    """Менеджер конфигурации AML системы"""
    
    def __init__(self, config_file: str = "aml_config.json"):
        self.config_file = config_file
        self.processing = ProcessingConfig()
        self.analysis = AnalysisConfig()
        self.country_risk = CountryRiskConfig()
        self.database = DatabaseConfig()
        self.monitoring = MonitoringConfig()
        
        # Загружаем конфигурацию из файла
        self.load_from_file()
        
        # Автооптимизация
        if self.processing.auto_optimize_workers:
            self.processing.optimize_for_system()
    
    def load_from_file(self):
        """Загрузка конфигурации из JSON файла"""
        if not os.path.exists(self.config_file):
            print(f"📄 Файл конфигурации не найден, создаю {self.config_file}")
            self.save_to_file()
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Обновляем конфигурацию
            if 'processing' in config_data:
                self._update_dataclass(self.processing, config_data['processing'])
            
            if 'analysis' in config_data:
                self._update_dataclass(self.analysis, config_data['analysis'])
            
            if 'country_risk' in config_data:
                self._update_dataclass(self.country_risk, config_data['country_risk'])
            
            if 'database' in config_data:
                self._update_dataclass(self.database, config_data['database'])
            
            if 'monitoring' in config_data:
                self._update_dataclass(self.monitoring, config_data['monitoring'])
            
            print(f"✅ Конфигурация загружена из {self.config_file}")
            
        except Exception as e:
            print(f"⚠️ Ошибка загрузки конфигурации: {e}")
    
    def save_to_file(self):
        """Сохранение конфигурации в JSON файл"""
        try:
            config_data = {
                'processing': self._dataclass_to_dict(self.processing),
                'analysis': self._dataclass_to_dict(self.analysis),
                'country_risk': self._dataclass_to_dict(self.country_risk),
                'database': self._dataclass_to_dict(self.database),
                'monitoring': self._dataclass_to_dict(self.monitoring),
                'metadata': {
                    'version': '3.0',
                    'last_updated': str(pd.Timestamp.now()),
                    'description': 'AML система - конфигурация мультипроцессорной обработки'
                }
            }
            
            os.makedirs(os.path.dirname(self.config_file) if os.path.dirname(self.config_file) else '.', exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Конфигурация сохранена в {self.config_file}")
            
        except Exception as e:
            print(f"❌ Ошибка сохранения конфигурации: {e}")
    
    def _dataclass_to_dict(self, obj) -> Dict[str, Any]:
        """Преобразование dataclass в словарь"""
        result = {}
        for field_name, field_value in obj.__dict__.items():
            if isinstance(field_value, (str, int, float, bool, list, dict)):
                result[field_name] = field_value
            else:
                result[field_name] = str(field_value)
        return result
    
    def _update_dataclass(self, obj, data: Dict[str, Any]):
        """Обновление dataclass из словаря"""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
    
    def validate_configuration(self) -> bool:
        """Валидация всей конфигурации"""
        errors = []
        
        # Проверка весов профилей
        if not self.analysis.validate_weights():
            errors.append("Некорректные веса профилей анализа")
        
        # Проверка лимитов ресурсов
        if self.processing.max_workers <= 0:
            errors.append("Количество воркеров должно быть больше 0")
        
        if self.processing.batch_size <= 0:
            errors.append("Размер батча должен быть больше 0")
        
        # Проверка пороговых значений
        if self.analysis.thresholds['cash_operations'] <= 0:
            errors.append("Пороговое значение для наличных операций должно быть больше 0")
        
        # Проверка страновых списков
        if not self.country_risk.fatf_blacklist:
            errors.append("FATF blacklist не может быть пустым")
        
        if errors:
            print("❌ Найдены ошибки конфигурации:")
            for error in errors:
                print(f"  • {error}")
            return False
        
        print("✅ Конфигурация валидна")
        return True
    
    def get_optimal_settings(self, data_size: int) -> Dict[str, Any]:
        """Получение оптимальных настроек для размера данных"""
        if data_size < 1000:
            return {
                'use_parallel': False,
                'workers': 1,
                'batch_size': data_size
            }
        elif data_size < 10000:
            return {
                'use_parallel': True,
                'workers': min(4, self.processing.max_workers),
                'batch_size': 100
            }
        else:
            return {
                'use_parallel': True,
                'workers': self.processing.max_workers,
                'batch_size': self.processing.batch_size
            }
    
    def print_summary(self):
        """Вывод сводки конфигурации"""
        print(f"\n📋 КОНФИГУРАЦИЯ AML СИСТЕМЫ")
        print(f"{'='*60}")
        print(f"🔧 Обработка:")
        print(f"   Макс. воркеров: {self.processing.max_workers}")
        print(f"   Размер батча: {self.processing.batch_size}")
        print(f"   Лимит памяти: {self.processing.max_memory_gb:.1f} GB")
        print(f"   Таймаут: {self.processing.timeout_seconds} сек")
        
        print(f"\n⚖️ Анализ:")
        print(f"   Веса профилей: {self.analysis.profile_weights}")
        print(f"   Пороги (млн тенге): {{{k}: {v/1_000_000:.1f} for k, v in self.analysis.thresholds.items()}}")
        
        print(f"\n🌍 Страновые риски:")
        print(f"   FATF blacklist: {len(self.country_risk.fatf_blacklist)} стран")
        print(f"   FATF greylist: {len(self.country_risk.fatf_greylist)} стран")
        print(f"   Офшорные зоны: {len(self.country_risk.offshore_zones)} зон")
        
        print(f"\n💾 База данных:")
        print(f"   Путь: {self.database.database_path}")
        print(f"   Пул соединений: {self.database.connection_pool_size}")
        print(f"   WAL режим: {self.database.enable_wal_mode}")
        
        print(f"\n📊 Мониторинг:")
        print(f"   Уровень логов: {self.monitoring.log_level}")
        print(f"   Интервал: {self.monitoring.monitoring_interval_seconds} сек")
        print(f"   Алерты включены: {self.monitoring.enable_alerts}")


# Глобальный экземпляр конфигурации
config_manager = AMLConfigManager()


def get_config() -> AMLConfigManager:
    """Получение глобального экземпляра конфигурации"""
    return config_manager


if __name__ == "__main__":
    # Тестирование конфигурации
    import pandas as pd
    
    config = get_config()
    config.validate_configuration()
    config.print_summary()
    
    # Пример получения оптимальных настроек
    print(f"\n💡 Рекомендации для разных объемов данных:")
    for size in [500, 5000, 50000]:
        settings = config.get_optimal_settings(size)
        print(f"   {size:,} записей: {settings}")