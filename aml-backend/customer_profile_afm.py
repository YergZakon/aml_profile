# Клиентский профиль для системы мониторинга транзакций АФМ РК
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

class CustomerProfile:
    """Профиль клиента для анализа рисков ПОД/ФТ"""
    
    def __init__(self):
        # Основная информация
        self.created_at = datetime.now()
        
        # Личные данные
        self.personal_info = {
            'full_name': '',
            'iin': '',  # ИИН для физлиц
            'bin': '',  # БИН для юрлиц
            'birth_date': None,
            'citizenship': 'KZ',
            'residence_country': 'KZ'
        }
        
        # Тип клиента
        self.customer_type = {
            'is_individual': True,  # Физлицо/Юрлицо
            'is_pep': False,  # Публично значимое лицо
            'is_foreign': False,  # Иностранный клиент
            'business_type': None  # Для юрлиц: тип бизнеса
        }
        
        # Риск-факторы
        self.risk_factors = {
            'base_risk_level': 'LOW',  # LOW, MEDIUM, HIGH
            'country_risk': 1,  # 1-10
            'product_risk': 1,  # 1-10
            'behavior_risk': 1,  # 1-10
            'overall_risk_score': 1.0  # Общий риск-скор
        }
        
        # История транзакций (статистика)
        self.transaction_stats = {
            'total_count': 0,
            'total_amount': 0.0,
            'avg_transaction': 0.0,
            'max_transaction': 0.0,
            'monthly_avg': 0.0,
            'typical_counterparties': [],  # Частые контрагенты
            'typical_purposes': []  # Частые назначения платежей
        }
        
        # Поведенческие паттерны
        self.behavior_patterns = {
            'usual_transaction_range': (0, 0),  # Мин-макс обычной суммы
            'usual_frequency': 0,  # Транзакций в месяц
            'preferred_channels': [],  # Каналы: банк, мобайл, интернет
            'active_hours': [],  # Часы активности
            'active_days': []  # Дни недели активности
        }
        
        # Подозрительная активность
        self.suspicious_history = {
            'str_count': 0,  # Количество СПО (сообщений о подозрительных операциях)
            'last_str_date': None,
            'false_positive_count': 0,
            'confirmed_suspicious': 0
        }
        
    def update_personal_info(self, **kwargs):
        """Обновление личных данных"""
        for key, value in kwargs.items():
            if key in self.personal_info:
                self.personal_info[key] = value
                
    def calculate_risk_score(self):
        """Расчет общего риск-скора клиента"""
        # Базовые веса для разных факторов
        weights = {
            'country': 0.25,
            'product': 0.25,
            'behavior': 0.30,
            'history': 0.20
        }
        
        # Расчет исторического риска
        history_risk = min(self.suspicious_history['str_count'], 10)
        
        # Взвешенный расчет
        self.risk_factors['overall_risk_score'] = (
            self.risk_factors['country_risk'] * weights['country'] +
            self.risk_factors['product_risk'] * weights['product'] +
            self.risk_factors['behavior_risk'] * weights['behavior'] +
            history_risk * weights['history']
        )
        
        # Определение уровня риска
        if self.risk_factors['overall_risk_score'] <= 3:
            self.risk_factors['base_risk_level'] = 'LOW'
        elif self.risk_factors['overall_risk_score'] <= 7:
            self.risk_factors['base_risk_level'] = 'MEDIUM'
        else:
            self.risk_factors['base_risk_level'] = 'HIGH'
            
        return self.risk_factors['overall_risk_score']
    
    def update_transaction_stats(self, transactions: List[Dict]):
        """Обновление статистики транзакций"""
        if not transactions:
            return
            
        amounts = [t['amount'] for t in transactions]
        self.transaction_stats['total_count'] = len(transactions)
        self.transaction_stats['total_amount'] = sum(amounts)
        self.transaction_stats['avg_transaction'] = sum(amounts) / len(amounts)
        self.transaction_stats['max_transaction'] = max(amounts)
        
        # Анализ контрагентов
        counterparties = {}
        for t in transactions:
            cp = t.get('counterparty', 'Unknown')
            counterparties[cp] = counterparties.get(cp, 0) + 1
            
        # Топ-5 частых контрагентов
        self.transaction_stats['typical_counterparties'] = sorted(
            counterparties.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
    def detect_anomalies(self, new_transaction: Dict) -> Dict:
        """Проверка новой транзакции на аномалии"""
        anomalies = {
            'is_anomaly': False,
            'reasons': [],
            'risk_increase': 0
        }
        
        amount = new_transaction['amount']
        
        # Проверка 1: Превышение обычной суммы
        if self.behavior_patterns['usual_transaction_range'][1] > 0:
            if amount > self.behavior_patterns['usual_transaction_range'][1] * 3:
                anomalies['is_anomaly'] = True
                anomalies['reasons'].append('Сумма превышает обычную в 3+ раза')
                anomalies['risk_increase'] += 2
                
        # Проверка 2: Новый контрагент
        typical_cps = [cp[0] for cp in self.transaction_stats['typical_counterparties']]
        counterparty = new_transaction.get('counterparty') or new_transaction.get('beneficiary_id', 'Unknown')
        if counterparty not in typical_cps:
            if amount > self.transaction_stats['avg_transaction'] * 5:
                anomalies['is_anomaly'] = True
                anomalies['reasons'].append('Крупная сумма новому контрагенту')
                anomalies['risk_increase'] += 1
                
        # Проверка 3: Необычное время
        transaction_time = new_transaction.get('datetime') or new_transaction.get('date')
        if transaction_time:
            hour = transaction_time.hour
            if self.behavior_patterns['active_hours']:
                if hour not in self.behavior_patterns['active_hours']:
                    anomalies['reasons'].append('Операция в необычное время')
                    anomalies['risk_increase'] += 0.5
                
        return anomalies
    
    def to_json(self) -> str:
        """Экспорт профиля в JSON"""
        profile_data = {
            'created_at': self.created_at.isoformat(),
            'personal_info': self.personal_info,
            'customer_type': self.customer_type,
            'risk_factors': self.risk_factors,
            'transaction_stats': self.transaction_stats,
            'behavior_patterns': self.behavior_patterns,
            'suspicious_history': self.suspicious_history
        }
        return json.dumps(profile_data, ensure_ascii=False, indent=2)

    def analyze_customer_data(self, transaction: Dict) -> Dict:
        """
        Анализирует данные клиента на основе транзакции.
        В реальной системе здесь была бы загрузка профиля из БД.
        """
        self.__init__() # Сброс состояния
        customer_id = transaction.get('sender_id') or transaction.get('beneficiary_id')
        
        if not customer_id:
            return {
                'customer_id': 'N/A',
                'risk_level': 'UNKNOWN',
                'risk_score': 0,
                'is_suspicious': False,
                'reasons': ['Отсутствует ID клиента']
            }
            
        self.customer_id = customer_id
        
        # Симуляция загрузки данных клиента из БД
        # В реальной системе здесь будет: self.load_from_db(customer_id)
        self.risk_factors['country_risk'] = 2 # Предполагаем, что это резидент
        self.personal_info['iin'] = customer_id
        self.customer_type['is_pep'] = 'pep' in customer_id.lower() # Простая проверка на ПДЛ
        
        # Проверка на аномалии в транзакции
        anomalies = self.detect_anomalies(transaction)
        
        # Расчет риска
        if anomalies['is_anomaly']:
            self.risk_factors['behavior_risk'] = 5 + anomalies['risk_increase']
        
        if self.customer_type['is_pep']:
            self.risk_factors['base_risk_level'] = 'HIGH'
            self.risk_factors['overall_risk_score'] = 8.0 # Высокий базовый риск для ПДЛ
            
        final_score = self.calculate_risk_score()
        
        reasons = anomalies['reasons']
        if self.customer_type['is_pep']:
            reasons.append("Клиент является Публично-должностным лицом (ПДЛ)")

        return {
            'customer_id': self.customer_id,
            'risk_level': self.risk_factors['base_risk_level'],
            'risk_score': final_score,
            'is_suspicious': final_score > 6.0,
            'reasons': reasons
        }

    def analyze_customer(self, customer_id: str) -> Dict:
        """Метод для интеграции с Unified Pipeline"""
        # Симуляция анализа клиента (в реальной системе загружались бы данные из БД)
        self.customer_id = customer_id
        
        # Базовые риск-факторы для клиента
        self.risk_factors['country_risk'] = 2  # Низкий риск для резидента КЗ
        self.risk_factors['product_risk'] = 3  # Средний риск продукта
        self.risk_factors['behavior_risk'] = 2  # Низкий поведенческий риск
        
        # Проверяем, является ли клиент ПДЛ (простая эвристика)
        if 'pep' in customer_id.lower() or 'pdl' in customer_id.lower():
            self.customer_type['is_pep'] = True
            self.risk_factors['base_risk_level'] = 'HIGH'
            self.risk_factors['overall_risk_score'] = 8.0
        
        # Рассчитываем итоговый риск-скор
        final_score = self.calculate_risk_score()
        
        # Формируем риск-факторы для объяснения
        risk_factors = []
        if self.customer_type['is_pep']:
            risk_factors.append("Клиент является Публично-должностным лицом (ПДЛ)")
        if self.risk_factors['country_risk'] > 5:
            risk_factors.append("Высокий риск юрисдикции")
        if self.risk_factors['behavior_risk'] > 5:
            risk_factors.append("Подозрительные поведенческие паттерны")
        
        return {
            'risk_score': final_score,
            'risk_level': self.risk_factors['base_risk_level'],
            'risk_factors': risk_factors,
            'is_suspicious': final_score > 6.0,
            'is_pep': self.customer_type['is_pep'],
            'customer_id': customer_id
        }


# Пример использования
if __name__ == "__main__":
    # Создаем профиль клиента
    profile = CustomerProfile()
    
    # Заполняем личные данные
    profile.update_personal_info(
        full_name="Иванов Иван Иванович",
        iin="901231300123",
        birth_date=datetime(1990, 12, 31)
    )
    
    # Устанавливаем риск-факторы
    profile.risk_factors['country_risk'] = 2  # Низкий риск для резидента КЗ
    profile.risk_factors['product_risk'] = 3  # Средний риск продукта
    profile.risk_factors['behavior_risk'] = 2  # Низкий поведенческий риск
    
    # Рассчитываем общий риск
    risk_score = profile.calculate_risk_score()
    print(f"Риск-скор клиента: {risk_score:.2f}")
    print(f"Уровень риска: {profile.risk_factors['base_risk_level']}")
    
    # Пример транзакций для анализа
    sample_transactions = [
        {'amount': 150000, 'counterparty': 'ТОО Альфа', 'datetime': datetime.now()},
        {'amount': 200000, 'counterparty': 'ТОО Альфа', 'datetime': datetime.now()},
        {'amount': 75000, 'counterparty': 'ИП Бета', 'datetime': datetime.now()},
    ]
    
    # Обновляем статистику
    profile.update_transaction_stats(sample_transactions)
    
    # Устанавливаем обычные паттерны
    profile.behavior_patterns['usual_transaction_range'] = (50000, 250000)
    profile.behavior_patterns['usual_frequency'] = 10
    profile.behavior_patterns['active_hours'] = [9, 10, 11, 14, 15, 16, 17]
    
    # Проверяем новую транзакцию
    new_transaction = {
        'amount': 1000000,  # Подозрительно большая сумма
        'counterparty': 'ТОО Гамма',  # Новый контрагент
        'datetime': datetime.now()
    }
    
    anomalies = profile.detect_anomalies(new_transaction)
    if anomalies['is_anomaly']:
        print("\n⚠️ Обнаружены аномалии:")
        for reason in anomalies['reasons']:
            print(f"  - {reason}")
        print(f"  Увеличение риска: +{anomalies['risk_increase']}")
