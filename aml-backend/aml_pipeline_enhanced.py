#!/usr/bin/env python3
"""
Расширенный AML пайплайн с поддержкой параллельной обработки JSON файлов АФМ РК
Версия: 2.0
"""

import os
import sys
import json
import time
import psutil
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Optional, Tuple

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from aml_database_setup import AMLDatabaseManager
    from customer_profile_afm import CustomerProfile
    from transaction_profile_afm import TransactionProfile
    from behavioral_profile_afm import BehavioralProfile
    from geographic_profile_afm import GeographicProfile
    from network_profile_afm import NetworkProfile
except ImportError as e:
    print(f"❌ Ошибка импорта модулей: {e}")
    sys.exit(1)

class AMLPipelineEnhanced:
    """Расширенный AML пайплайн с поддержкой JSON файлов и параллельной обработки"""
    
    def __init__(self, db_path: str = None):
        """Инициализация пайплайна"""
        self.db_path = db_path or "aml_system.db"
        self.db_manager = AMLDatabaseManager(self.db_path)
        self.stats = {
            'start_time': time.time(),
            'json_files_processed': 0,
            'transactions_loaded': 0,
            'transactions_analyzed': 0,
            'customers_created': 0,
            'suspicious_found': 0,
            'high_risk_found': 0,
            'errors': 0
        }
        
        # Системная информация
        self.cpu_count = psutil.cpu_count()
        self.memory_gb = round(psutil.virtual_memory().total / (1024**3), 1)
        
    def load_json_file(self, json_file_path: str) -> List[Dict]:
        """Загрузка данных из JSON файла АФМ"""
        print(f"📂 Загрузка JSON файла: {json_file_path}")
        
        if not os.path.exists(json_file_path):
            print(f"❌ Файл не найден: {json_file_path}")
            return []
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"📊 Загружено записей: {len(data):,}")
            self.stats['json_files_processed'] += 1
            
            # Преобразуем в формат транзакций
            transactions = []
            for record in data:
                tx_data = record.get('row_to_json')
                if tx_data:
                    transaction = self._convert_afm_to_transaction(tx_data)
                    if transaction:
                        transactions.append(transaction)
            
            print(f"✅ Преобразовано транзакций: {len(transactions):,}")
            self.stats['transactions_loaded'] += len(transactions)
            
            return transactions
            
        except Exception as e:
            print(f"❌ Ошибка загрузки JSON: {e}")
            self.stats['errors'] += 1
            return []
    
    def _convert_afm_to_transaction(self, tx_data: Dict) -> Optional[Dict]:
        """Преобразование данных АФМ в формат транзакции"""
        try:
            # Проверяем обязательные поля
            if not tx_data.get('gmess_id'):
                return None
            
            # Извлекаем участников
            participants = self._extract_participants(tx_data)
            
            # Сохраняем клиентов в БД
            for participant in participants:
                self._save_customer_if_not_exists(participant)
            
            # Формируем транзакцию
            sender = participants[0] if participants else {}
            beneficiary = participants[1] if len(participants) > 1 else {}
            
            # Определяем подозрительность
            is_suspicious = bool(tx_data.get('goper_susp_first') or 
                               tx_data.get('goper_susp_second') or 
                               tx_data.get('goper_susp_third'))
            
            # Безопасное извлечение суммы
            amount_raw = tx_data.get('goper_tenge_amount')
            if amount_raw is None or amount_raw == '':
                amount = 0.0
            else:
                try:
                    amount = float(amount_raw)
                except (ValueError, TypeError):
                    amount = 0.0
            
            transaction = {
                'transaction_id': f"AFM_{tx_data.get('gmess_id')}",
                'amount': amount,
                'currency': 'KZT',
                'amount_kzt': amount,
                'transaction_date': self._parse_afm_date(tx_data.get('goper_trans_date')),
                'sender_id': sender.get('customer_id'),
                'sender_name': sender.get('full_name'),
                'beneficiary_id': beneficiary.get('customer_id'),
                'beneficiary_name': beneficiary.get('full_name'),
                'purpose_text': tx_data.get('goper_dopinfo', ''),
                'is_suspicious': is_suspicious,
                'final_risk_score': 8.0 if is_suspicious else 2.0,
                'risk_indicators': json.dumps({
                    'susp_first': tx_data.get('goper_susp_first'),
                    'susp_second': tx_data.get('goper_susp_second'),
                    'susp_third': tx_data.get('goper_susp_third'),
                    'status': tx_data.get('gmess_oper_status'),
                    'reason_code': tx_data.get('gmess_reason_code')
                }),
                'source_data': json.dumps(tx_data)  # Сохраняем исходные данные
            }
            
            return transaction
            
        except Exception as e:
            print(f"⚠️ Ошибка конвертации транзакции: {e}")
            self.stats['errors'] += 1
            return None
    
    def _extract_participants(self, tx_data: Dict) -> List[Dict]:
        """Извлечение участников из данных АФМ"""
        participants = []
        
        # Участник 1 (gmember1)
        if tx_data.get('gmember1_maincode'):
            if tx_data.get('gmember1_ur_name'):
                # Юридическое лицо
                full_name = tx_data['gmember1_ur_name'].strip()
                member_type = 1
            else:
                # Физическое лицо
                parts = []
                if tx_data.get('gmember1_ac_secondname'):
                    parts.append(tx_data['gmember1_ac_secondname'])
                if tx_data.get('gmember1_ac_firstname'):
                    parts.append(tx_data['gmember1_ac_firstname'])
                if tx_data.get('gmember1_ac_middlename'):
                    parts.append(tx_data['gmember1_ac_middlename'])
                full_name = ' '.join(parts).strip()
                member_type = 2
            
            participants.append({
                'customer_id': tx_data['gmember1_maincode'],
                'full_name': full_name,
                'member_type': member_type,
                'bank_address': tx_data.get('gmember1_bank_address'),
                'residence': tx_data.get('gmember_residence_pol1')
            })
        
        # Участник 2 (gmember2)
        if tx_data.get('gmember2_maincode'):
            if tx_data.get('gmember2_ur_name'):
                # Юридическое лицо
                full_name = tx_data['gmember2_ur_name'].strip()
                member_type = 1
            else:
                # Физическое лицо
                parts = []
                if tx_data.get('gmember2_ac_secondname'):
                    parts.append(tx_data['gmember2_ac_secondname'])
                if tx_data.get('gmember2_ac_firstname'):
                    parts.append(tx_data['gmember2_ac_firstname'])
                if tx_data.get('gmember2_ac_middlename'):
                    parts.append(tx_data['gmember2_ac_middlename'])
                full_name = ' '.join(parts).strip()
                member_type = 2
            
            participants.append({
                'customer_id': tx_data['gmember2_maincode'],
                'full_name': full_name,
                'member_type': member_type,
                'bank_address': tx_data.get('gmember2_bank_address'),
                'residence': tx_data.get('gmember_residence_pl2')
            })
        
        return participants
    
    def _save_customer_if_not_exists(self, customer_data: Dict):
        """Сохранение клиента в БД если его еще нет"""
        try:
            customer_id = customer_data['customer_id']
            
            # Проверяем, есть ли уже такой клиент
            cursor = self.db_manager.connection.cursor()
            cursor.execute("SELECT customer_id FROM customer_profiles WHERE customer_id = ?", (customer_id,))
            
            if not cursor.fetchone():
                # Создаем профиль клиента
                profile_data = {
                    'customer_id': customer_id,
                    'full_name': customer_data.get('full_name', ''),
                    'entity_type': 'individual' if customer_data.get('member_type') == 2 else 'legal',
                    'registration_date': datetime.now().strftime('%Y-%m-%d'),
                    'country_code': 'KZ',
                    'risk_level': 'medium',
                    'total_transactions': 0,
                    'total_amount': 0.0,
                    'suspicious_transactions': 0,
                    'last_transaction_date': None,
                    'kyc_status': 'pending',
                    'source_of_funds': 'unknown',
                    'occupation': 'unknown',
                    'bank_address': customer_data.get('bank_address'),
                    'residence_code': customer_data.get('residence')
                }
                
                self.db_manager.save_customer_profile(profile_data)
                self.stats['customers_created'] += 1
                
        except Exception as e:
            print(f"⚠️ Ошибка сохранения клиента {customer_data.get('customer_id')}: {e}")
            self.stats['errors'] += 1
    
    def _parse_afm_date(self, date_str: Optional[str]) -> Optional[str]:
        """Парсинг даты из формата АФМ"""
        if not date_str:
            return None
        try:
            # Формат: 2025-04-21T21:00:00
            return datetime.fromisoformat(date_str.split('.')[0]).strftime('%Y-%m-%d %H:%M:%S')
        except:
            return None
    
    def analyze_transactions_parallel(self, transactions: List[Dict], 
                                    num_workers: int = None, 
                                    batch_size: int = 100) -> Dict:
        """Параллельный анализ транзакций"""
        if not transactions:
            print("❌ Нет транзакций для анализа")
            return {}
        
        num_workers = num_workers or min(20, max(1, self.cpu_count - 2))
        total_transactions = len(transactions)
        
        print(f"\n🔍 ПАРАЛЛЕЛЬНЫЙ АНАЛИЗ ТРАНЗАКЦИЙ")
        print(f"{'='*50}")
        print(f"💻 Система:")
        print(f"   CPU: {self.cpu_count} ядер")
        print(f"   RAM: {self.memory_gb} GB")
        print(f"   Транзакций: {total_transactions:,}")
        print(f"   Рабочих процессов: {num_workers}")
        print(f"   Размер батча: {batch_size}")
        
        # Разбиваем на батчи
        batches = [transactions[i:i + batch_size] 
                  for i in range(0, total_transactions, batch_size)]
        
        print(f"   Батчей для обработки: {len(batches)}")
        
        start_time = time.time()
        all_results = []
        
        try:
            with ProcessPoolExecutor(max_workers=num_workers) as executor:
                # Запускаем параллельную обработку
                futures = [executor.submit(analyze_batch_worker, batch, self.db_path) 
                          for batch in batches]
                
                # Собираем результаты
                for i, future in enumerate(futures):
                    try:
                        batch_results = future.result(timeout=300)  # 5 минут на батч
                        all_results.extend(batch_results)
                        print(f"  ✅ Батч {i+1}/{len(batches)} завершен ({len(batch_results)} транзакций)")
                    except Exception as e:
                        print(f"  ❌ Ошибка в батче {i+1}: {e}")
                        self.stats['errors'] += 1
        
        except Exception as e:
            print(f"❌ Критическая ошибка параллельной обработки: {e}")
            return {}
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Анализ результатов
        suspicious_transactions = [tx for tx in all_results if tx.get('final_risk_score', 0) > 10]
        high_risk_transactions = [tx for tx in all_results if tx.get('final_risk_score', 0) > 15]
        
        self.stats['transactions_analyzed'] = len(all_results)
        self.stats['suspicious_found'] = len(suspicious_transactions)
        self.stats['high_risk_found'] = len(high_risk_transactions)
        
        # Вывод результатов
        print(f"\n📈 РЕЗУЛЬТАТЫ АНАЛИЗА:")
        print(f"{'='*40}")
        print(f"⏱️  Время обработки: {processing_time:.2f} секунд")
        print(f"⚡ Скорость: {len(all_results)/processing_time:.1f} транзакций/сек")
        print(f"✅ Обработано: {len(all_results):,}/{total_transactions:,} ({len(all_results)/total_transactions*100:.1f}%)")
        print(f"🔴 Подозрительных: {len(suspicious_transactions):,} ({len(suspicious_transactions)/len(all_results)*100:.1f}%)")
        print(f"🟠 Высокого риска: {len(high_risk_transactions):,}")
        
        return {
            'total_processed': len(all_results),
            'suspicious_count': len(suspicious_transactions),
            'high_risk_count': len(high_risk_transactions),
            'processing_time': processing_time,
            'transactions_per_second': len(all_results)/processing_time if processing_time > 0 else 0,
            'all_results': all_results,
            'suspicious_transactions': suspicious_transactions,
            'high_risk_transactions': high_risk_transactions
        }
    
    def process_json_files(self, json_files: List[str], 
                          parallel_analysis: bool = True,
                          save_to_db: bool = True) -> Dict:
        """Обработка нескольких JSON файлов"""
        print(f"\n🚀 ОБРАБОТКА JSON ФАЙЛОВ АФМ")
        print(f"{'='*50}")
        print(f"📁 Файлов для обработки: {len(json_files)}")
        
        all_transactions = []
        
        # Загружаем все файлы
        for json_file in json_files:
            transactions = self.load_json_file(json_file)
            all_transactions.extend(transactions)
            
            # Сохраняем в БД если нужно
            if save_to_db:
                for tx in transactions:
                    try:
                        self.db_manager.save_transaction(tx)
                    except Exception as e:
                        print(f"⚠️ Ошибка сохранения транзакции: {e}")
                        self.stats['errors'] += 1
        
        print(f"📊 Всего загружено транзакций: {len(all_transactions):,}")
        
        # Анализируем
        if parallel_analysis and len(all_transactions) > 100:
            results = self.analyze_transactions_parallel(all_transactions)
        else:
            print("🔄 Используется последовательная обработка")
            results = self._analyze_transactions_sequential(all_transactions)
        
        return results
    
    def _analyze_transactions_sequential(self, transactions: List[Dict]) -> Dict:
        """Последовательный анализ транзакций"""
        print(f"🔄 Последовательный анализ {len(transactions):,} транзакций...")
        
        start_time = time.time()
        analyzed_transactions = []
        
        for i, tx in enumerate(transactions):
            try:
                analyzed_tx = self._analyze_single_transaction(tx)
                analyzed_transactions.append(analyzed_tx)
                
                if (i + 1) % 100 == 0:
                    print(f"  Обработано: {i + 1:,}/{len(transactions):,}")
                    
            except Exception as e:
                print(f"⚠️ Ошибка анализа транзакции {tx.get('transaction_id')}: {e}")
                self.stats['errors'] += 1
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        suspicious_transactions = [tx for tx in analyzed_transactions if tx.get('final_risk_score', 0) > 10]
        high_risk_transactions = [tx for tx in analyzed_transactions if tx.get('final_risk_score', 0) > 15]
        
        print(f"✅ Последовательный анализ завершен за {processing_time:.2f} сек")
        print(f"⚡ Скорость: {len(analyzed_transactions)/processing_time:.1f} транзакций/сек")
        
        return {
            'total_processed': len(analyzed_transactions),
            'suspicious_count': len(suspicious_transactions),
            'high_risk_count': len(high_risk_transactions),
            'processing_time': processing_time,
            'transactions_per_second': len(analyzed_transactions)/processing_time,
            'all_results': analyzed_transactions,
            'suspicious_transactions': suspicious_transactions,
            'high_risk_transactions': high_risk_transactions
        }
    
    def _analyze_single_transaction(self, transaction: Dict) -> Dict:
        """Анализ одной транзакции"""
        try:
            # Создаем профили для анализа
            customer_profile = CustomerProfile(
                customer_id=transaction.get('sender_id'),
                db_manager=self.db_manager
            )
            
            transaction_profile = TransactionProfile(
                transaction_data=transaction,
                db_manager=self.db_manager
            )
            
            # Анализ рисков
            customer_risk = customer_profile.calculate_risk_score()
            transaction_risk = transaction_profile.calculate_risk_score()
            
            # Итоговый риск-скор
            final_risk_score = (customer_risk + transaction_risk) / 2
            
            # Обновляем транзакцию
            transaction['final_risk_score'] = final_risk_score
            transaction['customer_risk_score'] = customer_risk
            transaction['transaction_risk_score'] = transaction_risk
            transaction['analysis_timestamp'] = datetime.now().isoformat()
            
            return transaction
            
        except Exception as e:
            print(f"❌ Ошибка анализа транзакции: {e}")
            transaction['final_risk_score'] = 5.0  # Средний риск при ошибке
            return transaction
    
    def generate_report(self, results: Dict, output_file: str = None) -> str:
        """Генерация отчета по результатам"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"aml_pipeline_enhanced_results_{timestamp}.json"
        
        report_data = {
            'pipeline_info': {
                'version': '2.0',
                'timestamp': datetime.now().isoformat(),
                'database': self.db_path,
                'system_info': {
                    'cpu_cores': self.cpu_count,
                    'memory_gb': self.memory_gb
                }
            },
            'statistics': self.stats,
            'analysis_results': results,
            'performance_metrics': {
                'total_time': time.time() - self.stats['start_time'],
                'transactions_per_second': results.get('transactions_per_second', 0),
                'efficiency_score': self._calculate_efficiency_score(results)
            }
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n💾 Отчет сохранен: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Ошибка сохранения отчета: {e}")
            return ""
    
    def _calculate_efficiency_score(self, results: Dict) -> float:
        """Расчет показателя эффективности"""
        try:
            processed = results.get('total_processed', 0)
            speed = results.get('transactions_per_second', 0)
            accuracy = 1.0 - (self.stats['errors'] / max(1, processed))
            
            # Нормализованный показатель эффективности
            efficiency = (speed / 1000) * accuracy * 100
            return min(100.0, max(0.0, efficiency))
            
        except:
            return 0.0
    
    def print_final_summary(self):
        """Вывод итогового резюме"""
        total_time = time.time() - self.stats['start_time']
        
        print(f"\n🎉 ИТОГОВОЕ РЕЗЮМЕ ПАЙПЛАЙНА")
        print(f"{'='*50}")
        print(f"📁 JSON файлов обработано: {self.stats['json_files_processed']}")
        print(f"📦 Транзакций загружено: {self.stats['transactions_loaded']:,}")
        print(f"🔍 Транзакций проанализировано: {self.stats['transactions_analyzed']:,}")
        print(f"👥 Клиентов создано: {self.stats['customers_created']:,}")
        print(f"🚨 Подозрительных операций: {self.stats['suspicious_found']:,}")
        print(f"🔴 Высокого риска: {self.stats['high_risk_found']:,}")
        print(f"❌ Ошибок: {self.stats['errors']}")
        print(f"⏱️  Общее время: {total_time:.2f} секунд")
        
        if self.stats['transactions_analyzed'] > 0:
            avg_speed = self.stats['transactions_analyzed'] / total_time
            print(f"⚡ Средняя скорость: {avg_speed:.1f} транзакций/сек")


def analyze_batch_worker(batch: List[Dict], db_path: str) -> List[Dict]:
    """Воркер для параллельной обработки батча транзакций"""
    try:
        # Создаем локальные экземпляры для каждого процесса
        db_manager = AMLDatabaseManager(db_path)
        analyzed_transactions = []
        
        for transaction in batch:
            try:
                # Простой анализ без создания сложных профилей
                risk_score = calculate_simple_risk_score(transaction)
                
                transaction['final_risk_score'] = risk_score
                transaction['analysis_timestamp'] = datetime.now().isoformat()
                analyzed_transactions.append(transaction)
                
            except Exception as e:
                # В случае ошибки присваиваем средний риск
                transaction['final_risk_score'] = 5.0
                transaction['error'] = str(e)
                analyzed_transactions.append(transaction)
        
        return analyzed_transactions
        
    except Exception as e:
        print(f"❌ Критическая ошибка в воркере: {e}")
        return []


def calculate_simple_risk_score(transaction: Dict) -> float:
    """Упрощенный расчет риск-скора для параллельной обработки"""
    risk_score = 3.0  # Базовый риск
    
    try:
        amount_raw = transaction.get('amount', 0)
        if amount_raw is None:
            amount = 0.0
        else:
            try:
                amount = float(amount_raw)
            except (ValueError, TypeError):
                amount = 0.0
        
        is_suspicious = transaction.get('is_suspicious', False)
        
        # Анализ суммы
        if amount > 50_000_000:  # > 50 млн тенге
            risk_score += 8.0
        elif amount > 10_000_000:  # > 10 млн тенге
            risk_score += 5.0
        elif amount > 1_000_000:  # > 1 млн тенге
            risk_score += 2.0
        
        # Если уже помечена как подозрительная
        if is_suspicious:
            risk_score += 10.0
        
        # Анализ целевого назначения
        purpose = transaction.get('purpose_text', '').lower()
        suspicious_keywords = ['наркотик', 'криптовалют', 'обнал', 'дроппер', 'мошенничеств']
        for keyword in suspicious_keywords:
            if keyword in purpose:
                risk_score += 5.0
                break
        
        # Анализ индикаторов риска
        risk_indicators_str = transaction.get('risk_indicators', '{}')
        try:
            risk_indicators = json.loads(risk_indicators_str)
            if any(risk_indicators.values()):
                risk_score += 3.0
        except:
            pass
        
        return min(25.0, max(1.0, risk_score))
        
    except Exception:
        return 5.0  # Средний риск при ошибке


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Расширенный AML пайплайн с поддержкой JSON файлов АФМ')
    parser.add_argument('--json-files', nargs='+', help='JSON файлы для обработки')
    parser.add_argument('--json-dir', default='uploads', help='Папка с JSON файлами')
    parser.add_argument('--db-path', default='aml_system.db', help='Путь к базе данных')
    parser.add_argument('--workers', type=int, help='Количество рабочих процессов')
    parser.add_argument('--batch-size', type=int, default=100, help='Размер батча')
    parser.add_argument('--no-parallel', action='store_true', help='Отключить параллельную обработку')
    parser.add_argument('--no-save-db', action='store_true', help='Не сохранять в БД')
    parser.add_argument('--output', help='Файл для сохранения результатов')
    
    args = parser.parse_args()
    
    # Определяем файлы для обработки
    json_files = []
    
    if args.json_files:
        json_files = args.json_files
    else:
        # Ищем в указанной папке
        json_dir = Path(args.json_dir)
        if json_dir.exists():
            json_files = [str(f) for f in json_dir.glob('*.json')]
        
        if not json_files:
            print(f"❌ JSON файлы не найдены в папке: {args.json_dir}")
            print("💡 Укажите файлы через --json-files или проверьте папку --json-dir")
            return
    
    print(f"🚀 Запуск расширенного AML пайплайна")
    print(f"📁 Найдено JSON файлов: {len(json_files)}")
    for f in json_files:
        print(f"   • {f}")
    
    # Создаем пайплайн
    pipeline = AMLPipelineEnhanced(args.db_path)
    
    try:
        # Обрабатываем файлы
        results = pipeline.process_json_files(
            json_files=json_files,
            parallel_analysis=not args.no_parallel,
            save_to_db=not args.no_save_db
        )
        
        # Генерируем отчет
        if results:
            pipeline.generate_report(results, args.output)
        
        # Выводим итоги
        pipeline.print_final_summary()
        
    except KeyboardInterrupt:
        print("\n⚠️ Обработка прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
    finally:
        print("\n🎉 Пайплайн завершен!")


if __name__ == "__main__":
    main() 