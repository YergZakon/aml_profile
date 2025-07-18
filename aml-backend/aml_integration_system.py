# Интеграционная система AML - объединение всех профилей
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json
import os
import threading
import traceback

# Импорт всех профилей (в реальной системе это будут отдельные модули)
from customer_profile_afm import CustomerProfile
from transaction_profile_afm import TransactionProfile
from network_profile_afm import NetworkProfile
from behavioral_profile_afm import BehavioralProfile
from geographic_profile_afm import GeographicProfile
from aml_database_setup import AMLDatabaseManager
from aml_json_loader import AMLJSONDataLoader

class AMLIntegrationSystem:
    """Главная система AML, интегрирующая все профили"""
    
    def __init__(self, db_manager: AMLDatabaseManager):
        self.system_id = "AML_SYSTEM_KZ"
        self.created_at = datetime.now()
        self.db_manager = db_manager
        
        # Инициализация всех профилей
        self.transaction_profile = TransactionProfile()
        self.customer_profile = CustomerProfile()
        self.network_profile = NetworkProfile(db_manager) 
        self.geographic_profile = GeographicProfile(db_manager)
        self.behavioral_profile = BehavioralProfile(customer_id="placeholder", lookback_days=90) # Добавлен lookback_days
        
        # Настройки системы
        self.config = {
            'min_risk_for_str': 7.0,
            'behavioral_lookback_days': 90,
        }
        
        # Статистика системы
        self.system_stats = {
            'total_transactions_processed': 0,
            'suspicious_transactions': 0,
        }
        
    def run_full_analysis(self):
        """Запускает полный цикл анализа для всех транзакций в базе данных."""
        print("Интеграционная система: Запуск полного анализа...")
        transactions = self.db_manager.get_all_transactions()
        total_transactions = len(transactions)
        print(f"Найдено {total_transactions} транзакций для анализа.")

        # Создаем индекс транзакций по sender_id для быстрого поиска истории
        transactions_by_sender = {}
        for tx in transactions:
            sender_id = tx.get('sender_id')
            if sender_id:
                if sender_id not in transactions_by_sender:
                    transactions_by_sender[sender_id] = []
                transactions_by_sender[sender_id].append(tx)

        results = []
        for i, transaction in enumerate(transactions):
            print(f"Анализ транзакции {i+1}/{total_transactions} (ID: {transaction.get('transaction_id')})")
            
            # Преобразуем строковую дату из БД в объект datetime
            if 'transaction_date' in transaction and isinstance(transaction['transaction_date'], str):
                try:
                    transaction['date'] = datetime.fromisoformat(transaction['transaction_date'])
                except (ValueError, TypeError):
                    transaction['date'] = datetime.now()
            else:
                 transaction['date'] = datetime.now()

            try:
                # Получаем историю транзакций для текущего отправителя
                sender_id = transaction.get('sender_id')
                transaction_history = transactions_by_sender.get(sender_id, []) if sender_id else []
                
                # 1. Транзакционный анализ с историей
                transactional_result = self.transaction_profile.analyze_transaction(
                    transaction, 
                    transaction_history=transaction_history
                )

                # 2. Клиентский анализ
                customer_result = self.customer_profile.analyze_customer_data(transaction)

                # 3. Сетевой анализ (передаем историю транзакций)
                network_result = self.network_profile.analyze_transaction_network(
                    transaction,
                    transaction_history=transaction_history
                )

                # 4. Поведенческий анализ
                # Получаем исторические транзакции для клиента
                customer_id = transaction.get('sender_name', 'UNKNOWN')
                cursor = self.db_manager.get_db_cursor()
                cursor.execute('''
                    SELECT transaction_date, amount, sender_country, beneficiary_country, sender_name, beneficiary_name
                    FROM transactions 
                    WHERE sender_name = ? OR beneficiary_name = ?
                    ORDER BY transaction_date DESC LIMIT 100
                ''', (customer_id, customer_id))
                
                historical_data = []
                for row in cursor.fetchall():
                    try:
                        # Конвертируем дату из строки в datetime
                        if isinstance(row[0], str):
                            tx_date = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                        else:
                            tx_date = row[0]
                            
                        historical_data.append({
                            'date': tx_date,
                            'amount': row[1],
                            'country': row[2] or 'KZ',
                            'counterparty': row[4] or row[5] or 'Unknown',
                            'channel': 'electronic'
                        })
                    except Exception:
                        continue
                
                # Создаем новый профиль для каждого клиента
                behavioral_profile = BehavioralProfile(customer_id, lookback_days=90)
                behavioral_result = behavioral_profile.analyze_transaction(transaction, historical_data)
                
                # 5. Географический анализ
                geographic_result = self.geographic_profile.analyze_transaction_geography(transaction)

                # Собираем все результаты
                analysis_summary = {
                    'transaction_id': transaction.get('transaction_id'),
                    'sender_id': transaction.get('sender_id'),
                    'beneficiary_id': transaction.get('beneficiary_id'),
                    'amount': transaction.get('amount') or transaction.get('amount_kzt'),
                    'date': transaction.get('transaction_date'),
                    'final_risk_score': self._calculate_final_risk_score(
                        transactional_result, network_result, customer_result, 
                        behavioral_result, geographic_result
                    ),
                    'is_suspicious': self._is_transaction_suspicious(
                        transactional_result, network_result, customer_result, 
                        behavioral_result, geographic_result
                    ),
                    'profiles': {
                        'transactional': transactional_result,
                        'customer': customer_result,
                        'network': network_result,
                        'behavioral': behavioral_result,
                        'geographic': geographic_result
                    },
                    'consolidated_reasons': self._consolidate_reasons(
                        transactional_result, customer_result, network_result, 
                        behavioral_result, geographic_result
                    )
                }
                
                # Обновляем статистику
                self.system_stats['total_transactions_processed'] += 1
                if analysis_summary['is_suspicious']:
                    self.system_stats['suspicious_transactions'] += 1
                
                results.append(analysis_summary)

                # Обновляем транзакцию в базе
                cursor = self.db_manager.get_db_cursor()
                final_risk_score = analysis_summary['final_risk_score']
                is_suspicious = analysis_summary['is_suspicious']
                risk_indicators = analysis_summary['profiles']['transactional'].get('risk_indicators', [])
                reasons = analysis_summary['consolidated_reasons']
                transaction_id = analysis_summary['transaction_id']
                cursor.execute('''
                UPDATE transactions 
                SET final_risk_score = ?,
                    is_suspicious = ?,
                    risk_indicators = ?,
                    rule_triggers = ?,
                    suspicious_reasons = ?
                WHERE transaction_id = ?
                ''', (
                    final_risk_score,
                    is_suspicious,
                    json.dumps(risk_indicators),
                    json.dumps(reasons),
                    json.dumps(reasons),  # Сохраняем reasons как suspicious_reasons
                    transaction_id
                ))
                self.db_manager.commit()

            except Exception as e:
                print(f"ОШИБКА при анализе транзакции {transaction.get('transaction_id')}: {str(e)}")
                traceback.print_exc()
                results.append({'transaction_id': transaction.get('transaction_id'), 'error': str(e)})

        print("Анализ всех транзакций завершен.")
        print(f"Обработано: {self.system_stats['total_transactions_processed']}")
        print(f"Подозрительных: {self.system_stats['suspicious_transactions']}")
        
        results_path = os.path.join(os.path.dirname(__file__), '..', 'aml-backend', 'results', 'analysis_results.json')
        os.makedirs(os.path.dirname(results_path), exist_ok=True)
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        
        print(f"Результаты анализа сохранены в: {os.path.basename(results_path)}")
        
    def _consolidate_reasons(self, *profile_results) -> List[str]:
        """Объединяет причины подозрительности из всех профилей"""
        all_reasons = []
        for result in profile_results:
            if isinstance(result, dict):
                # Ищем причины в разных полях
                reasons = result.get('reasons', [])
                suspicious_reasons = result.get('suspicious_reasons', [])
                
                if reasons:
                    all_reasons.extend(reasons)
                if suspicious_reasons:
                    all_reasons.extend(suspicious_reasons)
                    
                # Специальная обработка для сетевого анализа
                if 'schemes_found' in result and result['schemes_found']:
                    for scheme in result['schemes_found']:
                        all_reasons.append(f"[СЕТЬ] Обнаружена схема: {scheme}")
                        
            elif isinstance(result, list):
                # Обработка списков (например, поведенческий анализ)
                for item in result:
                    if isinstance(item, dict):
                        reasons = item.get('reasons', [])
                        suspicious_reasons = item.get('suspicious_reasons', [])
                        
                        if reasons:
                            all_reasons.extend(reasons)
                        if suspicious_reasons:
                            all_reasons.extend(suspicious_reasons)
                        
        return list(set(all_reasons))  # Убираем дубликаты

    def _calculate_final_risk_score(self, transactional_result, network_result, 
                                   customer_result, behavioral_result, geographic_result):
        """Рассчитывает итоговый риск-скор с учетом всех профилей"""
        scores = []
        
        # Транзакционный анализ (вес 40%)
        trans_score = transactional_result.get('risk_score', 0) * 0.4
        scores.append(trans_score)
        
        # Сетевой анализ (вес 30%)
        network_score = network_result.get('risk_score', 0) * 0.3
        scores.append(network_score)
        
        # Клиентский анализ (вес 15%)
        customer_score = customer_result.get('risk_score', 0) * 0.15
        scores.append(customer_score)
        
        # Поведенческий анализ (вес 10%)
        if isinstance(behavioral_result, list):
            # Если behavioral_result - это список, берем максимальный риск-скор
            behavioral_score = max([item.get('risk_score', 0) for item in behavioral_result] + [0]) * 0.1
        else:
            behavioral_score = behavioral_result.get('risk_score', 0) * 0.1
        scores.append(behavioral_score)
        
        # Географический анализ (вес 5%)
        geographic_score = geographic_result.get('risk_score', 0) * 0.05
        scores.append(geographic_score)
        
        # Итоговый скор
        final_score = sum(scores)
        
        # Бонус за множественные профили (если несколько профилей показывают риск)
        results_to_check = [transactional_result, network_result, customer_result, geographic_result]
        
        suspicious_count = sum(1 for result in results_to_check if result.get('is_suspicious', False))
        
        # Обработка behavioral_result отдельно
        if isinstance(behavioral_result, list):
            if any(item.get('is_suspicious', False) for item in behavioral_result):
                suspicious_count += 1
        else:
            if behavioral_result.get('is_suspicious', False):
                suspicious_count += 1
        
        if suspicious_count > 1:
            final_score += min(suspicious_count * 0.5, 2.0)  # Максимум +2 балла
        
        return min(final_score, 10.0)  # Ограничиваем максимумом 10

    def _is_transaction_suspicious(self, transactional_result, network_result, 
                                  customer_result, behavioral_result, geographic_result):
        """Определяет, является ли транзакция подозрительной"""
        # Если хотя бы один профиль считает транзакцию подозрительной
        results_to_check = [transactional_result, network_result, customer_result, geographic_result]
        
        # Обработка behavioral_result, который может быть списком
        if isinstance(behavioral_result, list):
            behavioral_suspicious = any(item.get('is_suspicious', False) for item in behavioral_result)
        else:
            behavioral_suspicious = behavioral_result.get('is_suspicious', False)
            
        if behavioral_suspicious or any(result.get('is_suspicious', False) for result in results_to_check):
            return True
        
        # Или если итоговый риск-скор высокий
        final_score = self._calculate_final_risk_score(
            transactional_result, network_result, customer_result, 
            behavioral_result, geographic_result
        )
        
        return final_score > 7.0

def run_full_analysis(json_filepath: str, db_filepath: str = "aml_system.db"):
    """
    Полный цикл анализа: загрузка данных, обработка и сохранение результатов.
    """
    print(f"Запуск полного анализа для файла: {json_filepath}")
    db_manager = AMLDatabaseManager(db_path=db_filepath)
    print("Менеджер БД инициализирован.")

    loader = AMLJSONDataLoader(db_manager)
    loader.load_and_process_json(json_filepath)
    print("Данные из JSON загружены в базу данных.")

    aml_system = AMLIntegrationSystem(db_manager)
    print("Интеграционная система инициализирована.")
    
    # Запускаем основной метод анализа внутри класса
    aml_system.run_full_analysis()
    
    # Возвращаем путь к отчету (для обратной совместимости с app.py)
    report_path = os.path.join(os.path.dirname(db_filepath), "analysis_results.json")
    return report_path

if __name__ == '__main__':
    if os.path.exists("aml_system_test.db"):
        os.remove("aml_system_test.db")
    run_full_analysis("../do_range.json", db_filepath="aml_system_test.db")
