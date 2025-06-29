#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Единый AML пайплайн для Агентства финансового мониторинга РК
Объединяет все виды анализа в один оптимизированный процесс
"""

import os
import json
import time
import logging
import threading
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict

# Импорты существующих анализаторов
from transaction_profile_afm import TransactionProfile
from customer_profile_afm import CustomerProfile  
from network_profile_afm import NetworkProfile
from behavioral_profile_afm import BehavioralProfile
from geographic_profile_afm import GeographicProfile
from aml_database_setup import AMLDatabaseManager
from aml_json_loader import AMLJSONDataLoader

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ProcessingConfig:
    """Конфигурация обработки"""
    max_workers: int = cpu_count()
    batch_size: int = 1000
    chunk_size: int = 10000
    enable_caching: bool = True
    validation_level: str = "strict"  # strict, normal, minimal
    risk_threshold: float = 3.0
    
@dataclass 
class AnalysisResult:
    """Результат единого анализа"""
    client_id: str
    transaction_risk: float
    customer_risk: float  
    network_risk: float
    behavioral_risk: float
    geographic_risk: float
    overall_risk: float
    risk_category: str
    explanations: List[str]
    suspicious_flags: List[str]
    processing_time: float
    timestamp: datetime

class ExplanationEngine:
    """Движок объяснений для рисков"""
    
    def __init__(self):
        self.risk_thresholds = {
            'low': 2.0,
            'medium': 4.0, 
            'high': 6.0,
            'critical': 8.0
        }
        
    def explain_risk(self, result: AnalysisResult) -> Dict[str, Any]:
        """Генерирует детальное объяснение рисков"""
        explanations = {
            'overall_assessment': self._get_risk_category(result.overall_risk),
            'risk_breakdown': {
                'transaction': {
                    'score': result.transaction_risk,
                    'impact': 'Высокий' if result.transaction_risk > 5.0 else 'Средний',
                    'details': self._explain_transaction_risk(result.transaction_risk)
                },
                'customer': {
                    'score': result.customer_risk,
                    'impact': 'Высокий' if result.customer_risk > 5.0 else 'Средний', 
                    'details': self._explain_customer_risk(result.customer_risk)
                },
                'network': {
                    'score': result.network_risk,
                    'impact': 'Высокий' if result.network_risk > 5.0 else 'Средний',
                    'details': self._explain_network_risk(result.network_risk)
                },
                'behavioral': {
                    'score': result.behavioral_risk,
                    'impact': 'Высокий' if result.behavioral_risk > 5.0 else 'Средний',
                    'details': self._explain_behavioral_risk(result.behavioral_risk)
                },
                'geographic': {
                    'score': result.geographic_risk,
                    'impact': 'Высокий' if result.geographic_risk > 5.0 else 'Средний',
                    'details': self._explain_geographic_risk(result.geographic_risk)
                }
            },
            'suspicious_activities': result.suspicious_flags,
            'recommendations': self._get_recommendations(result),
            'next_actions': self._get_next_actions(result.overall_risk)
        }
        
        return explanations
    
    def _get_risk_category(self, risk_score: float) -> str:
        """Определяет категорию риска"""
        if risk_score >= self.risk_thresholds['critical']:
            return 'КРИТИЧЕСКИЙ'
        elif risk_score >= self.risk_thresholds['high']:
            return 'ВЫСОКИЙ'
        elif risk_score >= self.risk_thresholds['medium']:
            return 'СРЕДНИЙ'
        else:
            return 'НИЗКИЙ'
    
    def _explain_transaction_risk(self, score: float) -> List[str]:
        """Объясняет транзакционные риски"""
        explanations = []
        if score > 7.0:
            explanations.append("Обнаружены критические нарушения пороговых значений")
        if score > 5.0:
            explanations.append("Выявлены подозрительные паттерны операций")
        if score > 3.0:
            explanations.append("Операции требуют дополнительной проверки")
        return explanations
    
    def _explain_customer_risk(self, score: float) -> List[str]:
        """Объясняет клиентские риски"""
        explanations = []
        if score > 7.0:
            explanations.append("Клиент в санкционных списках или PEP")
        if score > 5.0:
            explanations.append("Высокорисковый профиль клиента")
        if score > 3.0:
            explanations.append("Требуется углубленная проверка клиента")
        return explanations
    
    def _explain_network_risk(self, score: float) -> List[str]:
        """Объясняет сетевые риски"""
        explanations = []
        if score > 7.0:
            explanations.append("Обнаружены схемы отмывания денег")
        if score > 5.0:
            explanations.append("Подозрительные сетевые связи")
        if score > 3.0:
            explanations.append("Нетипичные паттерны взаимодействий")
        return explanations
    
    def _explain_behavioral_risk(self, score: float) -> List[str]:
        """Объясняет поведенческие риски"""
        explanations = []
        if score > 7.0:
            explanations.append("Критические изменения в поведении")
        if score > 5.0:
            explanations.append("Аномальные паттерны активности")
        if score > 3.0:
            explanations.append("Отклонения от обычного поведения")
        return explanations
    
    def _explain_geographic_risk(self, score: float) -> List[str]:
        """Объясняет географические риски"""
        explanations = []
        if score > 7.0:
            explanations.append("Операции с высокорисковыми юрисдикциями")
        if score > 5.0:
            explanations.append("Подозрительные географические маршруты")
        if score > 3.0:
            explanations.append("Операции требуют географической проверки")
        return explanations
    
    def _get_recommendations(self, result: AnalysisResult) -> List[str]:
        """Генерирует рекомендации"""
        recommendations = []
        
        if result.overall_risk >= 8.0:
            recommendations.extend([
                "Немедленно заблокировать операции",
                "Подать СПО в АФМ РК",
                "Провести расследование"
            ])
        elif result.overall_risk >= 6.0:
            recommendations.extend([
                "Повышенный мониторинг",
                "Дополнительная проверка документов",
                "Анализ источников средств"
            ])
        elif result.overall_risk >= 4.0:
            recommendations.extend([
                "Регулярный мониторинг",
                "Проверка при следующих операциях"
            ])
        
        return recommendations
    
    def _get_next_actions(self, risk_score: float) -> List[str]:
        """Определяет следующие действия"""
        if risk_score >= 8.0:
            return ["БЛОКИРОВКА", "СПО", "РАССЛЕДОВАНИЕ"]
        elif risk_score >= 6.0:
            return ["МОНИТОРИНГ", "ПРОВЕРКА", "АНАЛИЗ"]
        elif risk_score >= 4.0:
            return ["НАБЛЮДЕНИЕ", "КОНТРОЛЬ"]
        else:
            return ["ОБЫЧНЫЙ_РЕЖИМ"]

class UnifiedRiskCalculator:
    """Единый калькулятор рисков"""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        # Веса для различных типов рисков (сумма = 1.0)
        self.risk_weights = {
            'transaction': 0.25,
            'customer': 0.20,
            'network': 0.20,
            'behavioral': 0.20,
            'geographic': 0.15
        }
        
    def calculate_overall_risk(self, risks: Dict[str, float]) -> Tuple[float, str]:
        """Рассчитывает общий риск"""
        overall_risk = sum(
            risks.get(risk_type, 0.0) * weight 
            for risk_type, weight in self.risk_weights.items()
        )
        
        # Применяем нелинейное усиление для высоких рисков
        if overall_risk > 7.0:
            overall_risk = min(10.0, overall_risk * 1.2)
        elif overall_risk > 5.0:
            overall_risk = min(10.0, overall_risk * 1.1)
            
        category = self._determine_category(overall_risk)
        return overall_risk, category
    
    def _determine_category(self, risk_score: float) -> str:
        """Определяет категорию риска"""
        if risk_score >= 8.0:
            return "КРИТИЧЕСКИЙ"
        elif risk_score >= 6.0:
            return "ВЫСОКИЙ"
        elif risk_score >= 4.0:
            return "СРЕДНИЙ"
        elif risk_score >= 2.0:
            return "НИЗКИЙ"
        else:
            return "МИНИМАЛЬНЫЙ"

class UnifiedAMLPipeline:
    """Единый пайплайн AML анализа"""
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        self.config = config or ProcessingConfig()
        self.db_manager = None
        self.json_loader = None  # Будет инициализирован в _initialize_database
        self.risk_calculator = UnifiedRiskCalculator(self.config)
        self.explanation_engine = ExplanationEngine()
        
        # Инициализируем анализаторы
        self.analyzers = {}
        self._initialize_analyzers()
        
        # Статистика
        self.stats = {
            'total_processed': 0,
            'suspicious_clients': 0,
            'processing_time': 0.0,
            'start_time': None,
            'errors': 0
        }
        
    def _initialize_analyzers(self):
        """Инициализирует все анализаторы"""
        try:
            self.analyzers = {
                'transaction': TransactionProfile(),
                'customer': CustomerProfile(),
                'network': NetworkProfile(), 
                'behavioral': BehavioralProfile(),
                'geographic': GeographicProfile()
            }
            logger.info("✅ Все анализаторы успешно инициализированы")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации анализаторов: {e}")
            raise
    
    def _initialize_database(self, db_path: str = "aml_system_unified.db"):
        """Инициализирует базу данных"""
        try:
            self.db_manager = AMLDatabaseManager(db_path=db_path)
            self.json_loader = AMLJSONDataLoader(self.db_manager)
            logger.info(f"✅ База данных инициализирована: {db_path}")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise
    
    def process_json_files(self, json_dir: str) -> Dict[str, Any]:
        """Основной метод обработки JSON файлов"""
        self.stats['start_time'] = time.time()
        
        try:
            # 1. Инициализация
            self._initialize_database()
            
            # 2. Поиск и валидация JSON файлов
            json_files = self._find_json_files(json_dir)
            logger.info(f"📁 Найдено JSON файлов: {len(json_files)}")
            
            # 3. Обработка каждого файла
            all_results = []
            for json_file in json_files:
                logger.info(f"📂 Обработка файла: {json_file}")
                file_results = self._process_single_file(json_file)
                all_results.extend(file_results)
            
            # 4. Сохранение результатов
            self._save_results(all_results)
            
            # 5. Генерация финального отчета
            final_report = self._generate_final_report(all_results)
            
            return final_report
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в пайплайне: {e}")
            self.stats['errors'] += 1
            raise
        finally:
            self.stats['processing_time'] = time.time() - self.stats['start_time']
    
    def _find_json_files(self, json_dir: str) -> List[str]:
        """Находит все JSON файлы в директории"""
        json_path = Path(json_dir)
        if not json_path.exists():
            raise FileNotFoundError(f"Директория не найдена: {json_dir}")
        
        json_files = list(json_path.glob("*.json"))
        if not json_files:
            raise ValueError(f"JSON файлы не найдены в: {json_dir}")
        
        return [str(f) for f in json_files]
    
    def _load_json_file(self, json_file: str) -> List[Dict]:
        """Загружает данные из JSON файла"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Извлекаем транзакции из структуры АФМ
            transactions = []
            for item in data:
                if isinstance(item, dict) and 'row_to_json' in item:
                    transactions.append(item['row_to_json'])
                elif isinstance(item, dict):
                    transactions.append(item)
            
            return transactions
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки JSON файла {json_file}: {e}")
            return []
    
    def _process_single_file(self, json_file: str) -> List[AnalysisResult]:
        """Обрабатывает один JSON файл"""
        start_time = time.time()
        
        # Загрузка данных
        transactions = self._load_json_file(json_file)
        logger.info(f"📊 Загружено транзакций: {len(transactions):,}")
        
        # Разбиение на батчи для мультипроцессинга
        batches = self._create_batches(transactions)
        results = []
        
        # Обработка батчами с мультипроцессингом
        with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
            future_to_batch = {
                executor.submit(self._process_batch, batch): i 
                for i, batch in enumerate(batches)
            }
            
            for future in as_completed(future_to_batch):
                try:
                    batch_results = future.result()
                    results.extend(batch_results)
                    
                    # Прогресс
                    processed = len(results)
                    total = len(transactions)
                    progress = (processed / total) * 100
                    logger.info(f"📈 Прогресс: {processed:,}/{total:,} ({progress:.1f}%)")
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка обработки батча: {e}")
                    self.stats['errors'] += 1
        
        processing_time = time.time() - start_time
        logger.info(f"⏱️ Файл обработан за {processing_time:.2f} сек")
        
        return results
    
    def _create_batches(self, transactions: List[Dict]) -> List[List[Dict]]:
        """Создает батчи для мультипроцессинга"""
        batches = []
        for i in range(0, len(transactions), self.config.batch_size):
            batch = transactions[i:i + self.config.batch_size]
            batches.append(batch)
        return batches
    
    def _process_batch(self, batch: List[Dict]) -> List[AnalysisResult]:
        """Обрабатывает один батч транзакций"""
        results = []
        
        for transaction in batch:
            try:
                result = self._analyze_single_transaction(transaction)
                results.append(result)
                
                if result.overall_risk >= self.config.risk_threshold:
                    self.stats['suspicious_clients'] += 1
                    
            except Exception as e:
                logger.error(f"❌ Ошибка анализа транзакции: {e}")
                self.stats['errors'] += 1
                continue
        
        self.stats['total_processed'] += len(results)
        return results
    
    def _analyze_single_transaction(self, transaction: Dict) -> AnalysisResult:
        """Выполняет полный анализ одной транзакции"""
        start_time = time.time()
        client_id = transaction.get('debtor_account', 'UNKNOWN')
        
        # Выполняем все виды анализа
        risks = {}
        explanations = []
        suspicious_flags = []
        
        # 1. Транзакционный анализ
        try:
            tx_risk = self.analyzers['transaction'].analyze_transaction(transaction)
            risks['transaction'] = tx_risk.get('risk_score', 0.0)
            if tx_risk.get('suspicious_flags'):
                suspicious_flags.extend(tx_risk['suspicious_flags'])
        except Exception as e:
            logger.warning(f"Ошибка транзакционного анализа: {e}")
            risks['transaction'] = 0.0
        
        # 2. Клиентский анализ  
        try:
            customer_risk = self.analyzers['customer'].analyze_customer(client_id)
            risks['customer'] = customer_risk.get('risk_score', 0.0)
            if customer_risk.get('risk_factors'):
                explanations.extend(customer_risk['risk_factors'])
        except Exception as e:
            logger.warning(f"Ошибка клиентского анализа: {e}")
            risks['customer'] = 0.0
        
        # 3. Сетевой анализ
        try:
            network_risk = self.analyzers['network'].analyze_network_patterns(transaction)
            risks['network'] = network_risk.get('risk_score', 0.0)
            if network_risk.get('network_flags'):
                suspicious_flags.extend(network_risk['network_flags'])
        except Exception as e:
            logger.warning(f"Ошибка сетевого анализа: {e}")
            risks['network'] = 0.0
        
        # 4. Поведенческий анализ
        try:
            behavioral_risk = self.analyzers['behavioral'].analyze_behavior(client_id, transaction)
            risks['behavioral'] = behavioral_risk.get('risk_score', 0.0)
            if behavioral_risk.get('anomalies'):
                explanations.extend(behavioral_risk['anomalies'])
        except Exception as e:
            logger.warning(f"Ошибка поведенческого анализа: {e}")
            risks['behavioral'] = 0.0
        
        # 5. Географический анализ
        try:
            geo_risk = self.analyzers['geographic'].analyze_geography(transaction)
            risks['geographic'] = geo_risk.get('risk_score', 0.0)
            if geo_risk.get('geo_flags'):
                suspicious_flags.extend(geo_risk['geo_flags'])
        except Exception as e:
            logger.warning(f"Ошибка географического анализа: {e}")
            risks['geographic'] = 0.0
        
        # 6. Расчет общего риска
        overall_risk, risk_category = self.risk_calculator.calculate_overall_risk(risks)
        
        # 7. Создание результата
        result = AnalysisResult(
            client_id=client_id,
            transaction_risk=risks.get('transaction', 0.0),
            customer_risk=risks.get('customer', 0.0),
            network_risk=risks.get('network', 0.0),
            behavioral_risk=risks.get('behavioral', 0.0),
            geographic_risk=risks.get('geographic', 0.0),
            overall_risk=overall_risk,
            risk_category=risk_category,
            explanations=explanations,
            suspicious_flags=suspicious_flags,
            processing_time=time.time() - start_time,
            timestamp=datetime.now()
        )
        
        return result
    
    def _save_results(self, results: List[AnalysisResult]):
        """Сохраняет результаты в базу данных"""
        if not self.db_manager:
            logger.warning("⚠️ БД не инициализирована, пропускаем сохранение")
            return
        
        try:
            for result in results:
                # Сохраняем в соответствующие таблицы
                self.db_manager.save_analysis_result(asdict(result))
            
            logger.info(f"✅ Сохранено результатов: {len(results):,}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения результатов: {e}")
    
    def _generate_final_report(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """Генерирует финальный отчет"""
        if not results:
            return {"error": "Нет результатов для отчета"}
        
        # Статистика по рискам
        risk_stats = {
            'total_analyzed': len(results),
            'suspicious_count': len([r for r in results if r.overall_risk >= self.config.risk_threshold]),
            'risk_distribution': {
                'КРИТИЧЕСКИЙ': len([r for r in results if r.overall_risk >= 8.0]),
                'ВЫСОКИЙ': len([r for r in results if 6.0 <= r.overall_risk < 8.0]),
                'СРЕДНИЙ': len([r for r in results if 4.0 <= r.overall_risk < 6.0]),
                'НИЗКИЙ': len([r for r in results if r.overall_risk < 4.0])
            },
            'avg_processing_time': np.mean([r.processing_time for r in results]),
            'avg_risk_scores': {
                'transaction': np.mean([r.transaction_risk for r in results]),
                'customer': np.mean([r.customer_risk for r in results]),
                'network': np.mean([r.network_risk for r in results]),
                'behavioral': np.mean([r.behavioral_risk for r in results]),
                'geographic': np.mean([r.geographic_risk for r in results]),
                'overall': np.mean([r.overall_risk for r in results])
            }
        }
        
        # Топ подозрительных клиентов
        top_suspicious = sorted(results, key=lambda x: x.overall_risk, reverse=True)[:20]
        
        # Детальные объяснения для критических случаев
        critical_cases = [r for r in results if r.overall_risk >= 8.0]
        detailed_explanations = []
        
        for case in critical_cases[:10]:  # Топ 10 критических
            explanation = self.explanation_engine.explain_risk(case)
            detailed_explanations.append({
                'client_id': case.client_id,
                'risk_score': case.overall_risk,
                'explanation': explanation
            })
        
        report = {
            'summary': risk_stats,
            'top_suspicious': [
                {
                    'client_id': r.client_id,
                    'risk_score': r.overall_risk,
                    'category': r.risk_category,
                    'flags': r.suspicious_flags[:5]  # Первые 5 флагов
                } for r in top_suspicious
            ],
            'detailed_explanations': detailed_explanations,
            'processing_stats': self.stats,
            'timestamp': datetime.now().isoformat(),
            'config': asdict(self.config)
        }
        
        # Сохраняем отчет в JSON
        report_file = f"unified_aml_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"📊 Финальный отчет сохранен: {report_file}")
        return report

def main():
    """Главная функция для запуска"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Единый AML пайплайн')
    parser.add_argument('--json-dir', required=True, help='Директория с JSON файлами')
    parser.add_argument('--workers', type=int, default=cpu_count(), help='Количество воркеров')
    parser.add_argument('--batch-size', type=int, default=1000, help='Размер батча')
    parser.add_argument('--risk-threshold', type=float, default=3.0, help='Порог риска')
    
    args = parser.parse_args()
    
    # Конфигурация
    config = ProcessingConfig(
        max_workers=args.workers,
        batch_size=args.batch_size,
        risk_threshold=args.risk_threshold
    )
    
    # Запуск пайплайна
    pipeline = UnifiedAMLPipeline(config)
    
    print("🚀 Запуск единого AML пайплайна")
    print("=" * 50)
    print(f"📁 Директория JSON: {args.json_dir}")
    print(f"👥 Воркеров: {config.max_workers}")
    print(f"📦 Размер батча: {config.batch_size}")
    print(f"⚠️ Порог риска: {config.risk_threshold}")
    print("=" * 50)
    
    try:
        report = pipeline.process_json_files(args.json_dir)
        
        print("\n🎉 Обработка завершена успешно!")
        print("=" * 50)
        print(f"📊 Обработано: {report['summary']['total_analyzed']:,}")
        print(f"⚠️ Подозрительных: {report['summary']['suspicious_count']:,}")
        print(f"⏱️ Время: {pipeline.stats['processing_time']:.2f} сек")
        print(f"🔥 Производительность: {report['summary']['total_analyzed']/pipeline.stats['processing_time']:.0f} тр/сек")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())