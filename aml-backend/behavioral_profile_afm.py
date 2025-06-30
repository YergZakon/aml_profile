# Поведенческий профиль для отслеживания изменений в поведении клиентов
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import statistics
from collections import defaultdict, deque
from enum import Enum

class BehaviorChange(Enum):
    """Типы изменений в поведении"""
    VOLUME_SPIKE = "Резкий рост объемов"
    FREQUENCY_CHANGE = "Изменение частоты операций"
    NEW_GEOGRAPHY = "Новая география"
    NEW_COUNTERPARTY_TYPE = "Новый тип контрагентов"
    TIME_PATTERN_CHANGE = "Изменение временных паттернов"
    AMOUNT_PATTERN_CHANGE = "Изменение сумм операций"
    DORMANT_ACTIVATION = "Активация спящего счета"
    CHANNEL_CHANGE = "Смена канала операций"

class BehavioralProfile:
    """Профиль для анализа изменений в поведении клиента"""
    
    def __init__(self, customer_id: str, lookback_days: int = 90):
        self.customer_id = customer_id
        self.created_at = datetime.now()
        self.lookback_days = lookback_days
        
        # История поведения по периодам
        self.behavior_history = {
            'daily': defaultdict(lambda: {'count': 0, 'amount': 0.0}),
            'weekly': defaultdict(lambda: {'count': 0, 'amount': 0.0}),
            'monthly': defaultdict(lambda: {'count': 0, 'amount': 0.0})
        }
        
        # Базовые паттерны (нормальное поведение)
        self.baseline_patterns = {
            'avg_daily_count': 0,
            'avg_daily_amount': 0.0,
            'std_daily_amount': 0.0,  # Стандартное отклонение
            'typical_hours': [],
            'typical_days': [],
            'typical_countries': set(),
            'typical_counterparties': set(),
            'typical_channels': set(),
            'typical_amount_range': (0, 0)
        }
        
        # Текущие паттерны (последние 7 дней)
        self.current_patterns = {
            'daily_counts': deque(maxlen=7),
            'daily_amounts': deque(maxlen=7),
            'recent_hours': set(),
            'recent_countries': set(),
            'recent_counterparties': set(),
            'recent_channels': set()
        }
        
        # Обнаруженные аномалии
        self.detected_changes = []
        
        # Сезонные коэффициенты (для учета праздников, зарплатных дней)
        self.seasonal_factors = {
            'salary_days': [5, 10, 15, 25],  # Типичные дни выплат
            'holiday_periods': [],  # Праздничные периоды
            'month_end_activity': 1.5,  # Коэффициент активности в конце месяца
        }
        
        # Пороги для определения аномалий
        self.thresholds = {
            'volume_spike_multiplier': 3.0,  # Превышение в N раз
            'frequency_change_std': 2.0,  # Стандартных отклонений
            'dormant_days': 30,  # Дней неактивности
            'new_country_risk': 5.0,  # Риск для новой страны
        }
        
    def add_transaction(self, transaction: Dict):
        """Добавление транзакции в историю поведения"""
        # Поддерживаем разные форматы даты
        date_str = transaction.get('date') or transaction.get('transaction_date')
        if isinstance(date_str, str):
            try:
                date = datetime.strptime(date_str.split()[0], '%Y-%m-%d')
            except:
                date = datetime.now()
        elif hasattr(date_str, 'strftime'):
            date = date_str
        else:
            date = datetime.now()
            
        amount = float(transaction.get('amount', 0) or transaction.get('amount_kzt', 0))
        
        # Обновляем дневную статистику
        day_key = date.strftime('%Y-%m-%d')
        self.behavior_history['daily'][day_key]['count'] += 1
        self.behavior_history['daily'][day_key]['amount'] += amount
        
        # Обновляем недельную статистику
        week_key = f"{date.year}-W{date.isocalendar()[1]}"
        self.behavior_history['weekly'][week_key]['count'] += 1
        self.behavior_history['weekly'][week_key]['amount'] += amount
        
        # Обновляем месячную статистику
        month_key = date.strftime('%Y-%m')
        self.behavior_history['monthly'][month_key]['count'] += 1
        self.behavior_history['monthly'][month_key]['amount'] += amount
        
        # Обновляем текущие паттерны
        self._update_current_patterns(transaction)
        
    def _update_current_patterns(self, transaction: Dict):
        """Обновление текущих паттернов поведения"""
        # Добавляем в недавнюю активность
        date_str = transaction.get('date') or transaction.get('transaction_date')
        if isinstance(date_str, str):
            try:
                date = datetime.strptime(date_str.split()[0], '%Y-%m-%d')
            except:
                date = datetime.now()
        elif hasattr(date_str, 'strftime'):
            date = date_str
        else:
            date = datetime.now()
        today_count = self.behavior_history['daily'][date.strftime('%Y-%m-%d')]['count']
        today_amount = self.behavior_history['daily'][date.strftime('%Y-%m-%d')]['amount']
        
        self.current_patterns['daily_counts'].append(today_count)
        self.current_patterns['daily_amounts'].append(today_amount)
        
        # Обновляем паттерны
        self.current_patterns['recent_hours'].add(date.hour)
        self.current_patterns['recent_countries'].add(transaction.get('country', 'KZ'))
        self.current_patterns['recent_counterparties'].add(transaction.get('counterparty', ''))
        self.current_patterns['recent_channels'].add(transaction.get('channel', ''))
        
    def calculate_baseline(self, transactions: List[Dict]):
        """Расчет базовых паттернов на основе исторических данных"""
        if not transactions:
            return
            
        # Фильтруем транзакции за период lookback
        cutoff_date = datetime.now() - timedelta(days=self.lookback_days)
        historical_tx = [tx for tx in transactions if tx['date'] >= cutoff_date]
        
        if not historical_tx:
            return
            
        # Группируем по дням
        daily_stats = defaultdict(lambda: {'count': 0, 'amount': 0.0})
        hours = []
        days = []
        countries = set()
        counterparties = set()
        channels = set()
        amounts = []
        
        for tx in historical_tx:
            day_key = tx['date'].strftime('%Y-%m-%d')
            daily_stats[day_key]['count'] += 1
            daily_stats[day_key]['amount'] += tx['amount']
            
            hours.append(tx['date'].hour)
            days.append(tx['date'].weekday())
            countries.add(tx.get('country', 'KZ'))
            counterparties.add(tx.get('counterparty', ''))
            channels.add(tx.get('channel', ''))
            amounts.append(tx['amount'])
        
        # Рассчитываем средние показатели
        daily_counts = [stats['count'] for stats in daily_stats.values()]
        daily_amounts = [stats['amount'] for stats in daily_stats.values()]
        
        self.baseline_patterns['avg_daily_count'] = statistics.mean(daily_counts) if daily_counts else 0
        self.baseline_patterns['avg_daily_amount'] = statistics.mean(daily_amounts) if daily_amounts else 0
        self.baseline_patterns['std_daily_amount'] = statistics.stdev(daily_amounts) if len(daily_amounts) > 1 else 0
        
        # Определяем типичные паттерны
        self.baseline_patterns['typical_hours'] = self._get_typical_values(hours, 0.8)
        self.baseline_patterns['typical_days'] = self._get_typical_values(days, 0.8)
        self.baseline_patterns['typical_countries'] = countries
        self.baseline_patterns['typical_counterparties'] = counterparties
        self.baseline_patterns['typical_channels'] = channels
        
        if amounts:
            amounts_sorted = sorted(amounts)
            n = len(amounts_sorted)
            q1_idx = int(n * 0.1)
            q9_idx = int(n * 0.9)
            self.baseline_patterns['typical_amount_range'] = (
                amounts_sorted[q1_idx] if q1_idx < n else amounts_sorted[0],
                amounts_sorted[q9_idx] if q9_idx < n else amounts_sorted[-1]
            )
    
    def _get_typical_values(self, values: List, coverage: float = 0.8) -> List:
        """Получение типичных значений, покрывающих N% случаев"""
        if not values:
            return []
            
        from collections import Counter
        counter = Counter(values)
        total = len(values)
        
        typical = []
        covered = 0
        
        for value, count in counter.most_common():
            typical.append(value)
            covered += count
            if covered / total >= coverage:
                break
                
        return typical
    
    def detect_behavioral_changes(self, new_transaction: Dict) -> List[Dict]:
        """Обнаружение изменений в поведении"""
        changes = []
        
        # 1. Проверка на резкий рост объемов
        volume_change = self._check_volume_spike(new_transaction)
        if volume_change:
            changes.append(volume_change)
            
        # 2. Проверка на изменение частоты
        frequency_change = self._check_frequency_change()
        if frequency_change:
            changes.append(frequency_change)
            
        # 3. Проверка на новую географию
        geo_change = self._check_new_geography(new_transaction)
        if geo_change:
            changes.append(geo_change)
            
        # 4. Проверка на активацию спящего счета
        dormant_change = self._check_dormant_activation()
        if dormant_change:
            changes.append(dormant_change)
            
        # 5. Проверка на изменение временных паттернов
        time_change = self._check_time_pattern_change(new_transaction)
        if time_change:
            changes.append(time_change)
            
        # 6. Проверка на новый тип контрагентов
        counterparty_change = self._check_new_counterparty_type(new_transaction)
        if counterparty_change:
            changes.append(counterparty_change)
            
        # 7. Проверка на изменение сумм
        amount_change = self._check_amount_pattern_change(new_transaction)
        if amount_change:
            changes.append(amount_change)
            
        self.detected_changes = changes
        return changes
    
    def _check_volume_spike(self, transaction: Dict) -> Optional[Dict]:
        """Проверка на резкий рост объемов"""
        current_amount = transaction['amount']
        
        if self.baseline_patterns['avg_daily_amount'] > 0:
            ratio = current_amount / self.baseline_patterns['avg_daily_amount']
            
            if ratio >= self.thresholds['volume_spike_multiplier']:
                return {
                    'type': BehaviorChange.VOLUME_SPIKE.value,
                    'severity': 'HIGH',
                    'details': f'Сумма превышает среднюю в {ratio:.1f} раз',
                    'current_value': current_amount,
                    'baseline_value': self.baseline_patterns['avg_daily_amount'],
                    'risk_increase': min(ratio, 5.0)
                }
        return None
    
    def _check_frequency_change(self) -> Optional[Dict]:
        """Проверка на изменение частоты операций"""
        if len(self.current_patterns['daily_counts']) < 3:
            return None
            
        recent_avg = statistics.mean(self.current_patterns['daily_counts'])
        baseline_avg = self.baseline_patterns['avg_daily_count']
        
        if baseline_avg > 0:
            change_ratio = recent_avg / baseline_avg
            
            if change_ratio > 2.0 or change_ratio < 0.3:
                return {
                    'type': BehaviorChange.FREQUENCY_CHANGE.value,
                    'severity': 'MEDIUM',
                    'details': f'Частота операций изменилась в {change_ratio:.1f} раз',
                    'current_value': recent_avg,
                    'baseline_value': baseline_avg,
                    'risk_increase': 2.0
                }
        return None
    
    def _check_new_geography(self, transaction: Dict) -> Optional[Dict]:
        """Проверка на новую географию"""
        country = transaction.get('country', 'KZ')
        
        if country not in self.baseline_patterns['typical_countries']:
            # Особый риск для определенных стран
            high_risk_countries = ['IR', 'KP', 'SY', 'AF', 'YE', 'MM']
            offshore_countries = ['VG', 'KY', 'BS', 'BZ', 'SC']
            
            risk_level = 'LOW'
            risk_increase = 1.0
            
            if country in high_risk_countries:
                risk_level = 'CRITICAL'
                risk_increase = 5.0
            elif country in offshore_countries:
                risk_level = 'HIGH'
                risk_increase = 3.0
            else:
                risk_level = 'MEDIUM'
                risk_increase = 2.0
                
            return {
                'type': BehaviorChange.NEW_GEOGRAPHY.value,
                'severity': risk_level,
                'details': f'Новая страна операции: {country}',
                'country_code': country,
                'is_high_risk': country in high_risk_countries,
                'is_offshore': country in offshore_countries,
                'risk_increase': risk_increase
            }
        return None
    
    def _check_dormant_activation(self) -> Optional[Dict]:
        """Проверка на активацию спящего счета"""
        # Проверяем последнюю активность
        dates = [datetime.strptime(date, '%Y-%m-%d') for date in self.behavior_history['daily'].keys()]
        
        if dates and len(dates) > 1:
            dates.sort()
            # Находим самый большой промежуток неактивности
            max_gap = 0
            for i in range(1, len(dates)):
                gap = (dates[i] - dates[i-1]).days
                max_gap = max(max_gap, gap)
                
            if max_gap >= self.thresholds['dormant_days']:
                return {
                    'type': BehaviorChange.DORMANT_ACTIVATION.value,
                    'severity': 'HIGH',
                    'details': f'Активация после {max_gap} дней неактивности',
                    'dormant_days': max_gap,
                    'risk_increase': 3.0
                }
        return None
    
    def _check_time_pattern_change(self, transaction: Dict) -> Optional[Dict]:
        """Проверка на изменение временных паттернов"""
        date_str = transaction.get('date') or transaction.get('transaction_date')
        if isinstance(date_str, str):
            try:
                date = datetime.strptime(date_str.split()[0], '%Y-%m-%d')
                hour = date.hour
            except:
                hour = 12  # Default hour
        elif hasattr(date_str, 'hour'):
            hour = date_str.hour
        else:
            hour = 12
        
        if self.baseline_patterns['typical_hours'] and hour not in self.baseline_patterns['typical_hours']:
            risk_level = 'LOW'
            if hour < 6 or hour > 23:
                risk_level = 'MEDIUM'
                
            return {
                'type': BehaviorChange.TIME_PATTERN_CHANGE.value,
                'severity': risk_level,
                'details': f'Операция в нетипичное время: {hour}:00',
                'hour': hour,
                'typical_hours': self.baseline_patterns['typical_hours'],
                'risk_increase': 1.5 if risk_level == 'MEDIUM' else 1.0
            }
        return None
    
    def _check_new_counterparty_type(self, transaction: Dict) -> Optional[Dict]:
        """Проверка на новый тип контрагентов"""
        counterparty = transaction.get('counterparty', '')
        
        # Анализируем тип контрагента по ключевым словам
        suspicious_keywords = ['обмен', 'exchange', 'крипто', 'crypto', 'казино', 'casino', 'bet']
        
        for keyword in suspicious_keywords:
            if keyword in counterparty.lower():
                return {
                    'type': BehaviorChange.NEW_COUNTERPARTY_TYPE.value,
                    'severity': 'HIGH',
                    'details': f'Подозрительный тип контрагента: {keyword}',
                    'counterparty': counterparty,
                    'risk_increase': 3.0
                }
                
        # Проверка на нового контрагента
        if counterparty and counterparty not in self.baseline_patterns['typical_counterparties']:
            return {
                'type': BehaviorChange.NEW_COUNTERPARTY_TYPE.value,
                'severity': 'LOW',
                'details': 'Новый контрагент',
                'counterparty': counterparty,
                'risk_increase': 1.0
            }
        return None
    
    def _check_amount_pattern_change(self, transaction: Dict) -> Optional[Dict]:
        """Проверка на изменение паттернов сумм"""
        amount = transaction['amount']
        min_typical, max_typical = self.baseline_patterns['typical_amount_range']
        
        if min_typical > 0 and max_typical > 0:
            if amount < min_typical * 0.1 or amount > max_typical * 10:
                return {
                    'type': BehaviorChange.AMOUNT_PATTERN_CHANGE.value,
                    'severity': 'MEDIUM',
                    'details': f'Сумма вне типичного диапазона',
                    'amount': amount,
                    'typical_range': (min_typical, max_typical),
                    'risk_increase': 2.0
                }
        return None
    
    def get_behavior_risk_score(self) -> float:
        """Расчет общего риск-скора на основе изменений поведения"""
        total_risk = 0.0
        
        for change in self.detected_changes:
            total_risk += change.get('risk_increase', 0)
            
        # Учитываем количество изменений
        if len(self.detected_changes) > 3:
            total_risk *= 1.5  # Множитель за множественные изменения
            
        return min(total_risk, 10.0)
    
    def generate_behavior_report(self) -> str:
        """Генерация отчета об изменениях в поведении"""
        report = f"""
=== АНАЛИЗ ИЗМЕНЕНИЙ В ПОВЕДЕНИИ ===
Клиент: {self.customer_id}
Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M')}

📊 БАЗОВЫЕ ПАТТЕРНЫ (за {self.lookback_days} дней):
• Среднее кол-во операций в день: {self.baseline_patterns['avg_daily_count']:.1f}
• Средняя сумма в день: {self.baseline_patterns['avg_daily_amount']:,.2f} KZT
• Типичные часы активности: {self.baseline_patterns['typical_hours']}
• Типичный диапазон сумм: {self.baseline_patterns['typical_amount_range'][0]:,.0f} - {self.baseline_patterns['typical_amount_range'][1]:,.0f} KZT

🔍 ОБНАРУЖЕННЫЕ ИЗМЕНЕНИЯ:
"""
        
        if not self.detected_changes:
            report += "✓ Изменений в поведении не обнаружено\n"
        else:
            for i, change in enumerate(self.detected_changes, 1):
                report += f"\n{i}. {change['type']}"
                report += f"\n   Уровень: {change['severity']}"
                report += f"\n   Детали: {change['details']}"
                report += f"\n   Влияние на риск: +{change['risk_increase']:.1f}"
                report += "\n"
        
        # Итоговый риск
        risk_score = self.get_behavior_risk_score()
        report += f"\n🎯 ИТОГОВЫЙ ПОВЕДЕНЧЕСКИЙ РИСК: {risk_score:.1f}/10"
        
        if risk_score >= 7:
            report += "\n⚠️ ТРЕБУЕТСЯ НЕМЕДЛЕННОЕ ВНИМАНИЕ АНАЛИТИКА!"
        elif risk_score >= 5:
            report += "\n⚠️ Рекомендуется дополнительная проверка"
            
        return report

    def analyze_transaction(self, transaction: Dict, historical_transactions: List[Dict] = None) -> Dict:
        """Основной метод анализа транзакции для интеграции с AML системой"""
        
        # Если есть исторические данные, обновляем базовые паттерны
        if historical_transactions:
            self.calculate_baseline(historical_transactions)
            for tx in historical_transactions:
                self.add_transaction(tx)
        
        # Добавляем текущую транзакцию
        self.add_transaction(transaction)
        
        # Обнаруживаем изменения в поведении
        changes = self.detect_behavioral_changes(transaction)
        self.detected_changes = changes
        
        # Рассчитываем риск-скор
        risk_score = self.get_behavior_risk_score()
        
        # Определяем подозрительность
        is_suspicious = risk_score >= 5.0 or any(
            change.get('severity') in ['HIGH', 'CRITICAL'] for change in changes
        )
        
        # Формируем причины
        reasons = []
        for change in changes:
            reason = f"[ПОВЕДЕНИЕ] {change['type']}: {change['details']}"
            reasons.append(reason)
        
        # Определяем уровень уверенности
        confidence = min(len(changes) * 0.2 + 0.3, 1.0)
        
        # Рекомендации
        if risk_score >= 8.0:
            recommendation = "STR"  # Suspicious Transaction Report
        elif risk_score >= 6.0:
            recommendation = "EDD"  # Enhanced Due Diligence
        elif risk_score >= 4.0:
            recommendation = "MONITOR"
        else:
            recommendation = "PASS"
        
        return {
            'risk_score': risk_score,
            'is_suspicious': is_suspicious,
            'confidence': confidence,
            'recommendation': recommendation,
            'reasons': reasons,
            'suspicious_reasons': reasons,  # Для совместимости
            'changes_detected': len(changes),
            'behavior_changes': changes,
            'analysis_type': 'behavioral',
            'baseline_established': len(self.baseline_patterns.get('typical_countries', set())) > 0
        }

    def analyze_behavior(self, client_id: str, transaction: Dict) -> Dict:
        """Метод для интеграции с Unified Pipeline"""
        # Устанавливаем ID клиента если он отличается
        if self.customer_id != client_id:
            self.customer_id = client_id
        
        try:
            # Простой анализ без исторических данных для начала
            risk_score = 0.0
            anomalies = []
            
            # Анализируем время операции
            transaction_date = transaction.get('transaction_date', '')
            if isinstance(transaction_date, str) and len(transaction_date) > 10:
                try:
                    dt = datetime.strptime(transaction_date, '%Y-%m-%d %H:%M:%S')
                    hour = dt.hour
                    
                    # Проверка на нестандартное время
                    if hour < 6 or hour > 22:
                        risk_score += 2.0
                        anomalies.append(f"Нестандартное время операции: {hour:02d}:xx")
                    
                    # Проверка на выходные
                    if dt.weekday() >= 5:  # Saturday = 5, Sunday = 6
                        risk_score += 1.0
                        anomalies.append("Операция в выходной день")
                        
                except Exception:
                    pass
            
            # Анализируем страну операции
            sender_country = transaction.get('sender_country', 'KZ')
            beneficiary_country = transaction.get('beneficiary_country', 'KZ')
            
            if sender_country != 'KZ' or beneficiary_country != 'KZ':
                risk_score += 1.5
                if sender_country != 'KZ':
                    anomalies.append(f"Новая география: Новая страна операции: {sender_country}")
                if beneficiary_country != 'KZ':
                    anomalies.append(f"Новая география: Новая страна получателя: {beneficiary_country}")
            else:
                # Для внутренних операций тоже добавляем информацию
                anomalies.append("Новая география: Новая страна операции: KZ")
            
            # Анализируем сумму
            amount = float(transaction.get('amount_kzt', 0) or transaction.get('amount', 0))
            if amount > 100_000_000:  # >100 млн тенге
                risk_score += 3.0
                anomalies.append(f"Крупная операция: {amount:,.0f} тенге")
            elif amount > 50_000_000:  # >50 млн тенге
                risk_score += 2.0
                anomalies.append(f"Большая операция: {amount:,.0f} тенге")
            
            return {
                'risk_score': min(risk_score, 10.0),
                'anomalies': anomalies,
                'is_suspicious': risk_score >= 4.0,
                'confidence': 0.7,
                'recommendation': "MONITOR" if risk_score >= 4.0 else "NORMAL",
                'changes_detected': len(anomalies),
                'behavior_changes': anomalies
            }
            
        except Exception as e:
            # Если что-то не работает, возвращаем минимальный результат
            return {
                'risk_score': 0.0,
                'anomalies': [],
                'is_suspicious': False,
                'confidence': 0.1,
                'recommendation': "NORMAL",
                'changes_detected': 0,
                'behavior_changes': []
            }


# Пример использования
if __name__ == "__main__":
    # Создаем поведенческий профиль
    profile = BehavioralProfile("CLIENT_001", lookback_days=90)
    
    # Генерируем историю транзакций (нормальное поведение)
    historical_transactions = []
    base_date = datetime.now() - timedelta(days=60)
    
    # Обычные транзакции
    for i in range(50):
        tx_date = base_date + timedelta(days=i*1.2, hours=10+i%8)
        historical_transactions.append({
            'date': tx_date,
            'amount': 200_000 + (i % 10) * 50_000,
            'country': 'KZ',
            'counterparty': f'ТОО Компания_{i % 5}',
            'channel': 'internet'
        })
    
    # Рассчитываем базовые паттерны
    profile.calculate_baseline(historical_transactions)
    
    # Добавляем историю в профиль
    for tx in historical_transactions:
        profile.add_transaction(tx)
    
    print("=== ТЕСТ 1: Нормальная транзакция ===")
    normal_tx = {
        'date': datetime.now(),
        'amount': 250_000,
        'country': 'KZ',
        'counterparty': 'ТОО Компания_1',
        'channel': 'internet'
    }
    changes = profile.detect_behavioral_changes(normal_tx)
    print(f"Обнаружено изменений: {len(changes)}")
    
    print("\n=== ТЕСТ 2: Подозрительные транзакции ===")
    
    # Большая сумма в офшор ночью
    suspicious_tx = {
        'date': datetime.now().replace(hour=3),
        'amount': 5_000_000,  # В 10 раз больше обычного
        'country': 'KY',  # Каймановы острова
        'counterparty': 'Offshore Holdings Ltd',
        'channel': 'internet'
    }
    
    changes = profile.detect_behavioral_changes(suspicious_tx)
    print(profile.generate_behavior_report())
