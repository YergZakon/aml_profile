# Географический профиль для оценки рисков по странам и регионам
from datetime import datetime
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict
from enum import Enum

class RiskLevel(Enum):
    """Уровни географического риска"""
    LOW = 1
    MEDIUM = 3
    HIGH = 5
    CRITICAL = 8
    PROHIBITED = 10

class GeographicProfile:
    """Профиль для анализа географических рисков в транзакциях"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        
        # Классификация стран по рискам
        self.country_classifications = {
            # Черный список FATF (высокий риск)
            'fatf_blacklist': {
                'IR': 'Иран',
                'KP': 'Северная Корея'
            },
            
            # Серый список FATF (повышенный мониторинг)
            'fatf_greylist': {
                'AF': 'Афганистан',
                'AL': 'Албания',
                'BB': 'Барбадос',
                'BF': 'Буркина-Фасо',
                'KH': 'Камбоджа',
                'KY': 'Каймановы острова',
                'CD': 'ДР Конго',
                'GI': 'Гибралтар',
                'HT': 'Гаити',
                'JM': 'Ямайка',
                'JO': 'Иордания',
                'ML': 'Мали',
                'MZ': 'Мозамбик',
                'MM': 'Мьянма',
                'NI': 'Никарагуа',
                'PK': 'Пакистан',
                'PA': 'Панама',
                'PH': 'Филиппины',
                'SN': 'Сенегал',
                'SS': 'Южный Судан',
                'SY': 'Сирия',
                'TZ': 'Танзания',
                'TR': 'Турция',
                'UG': 'Уганда',
                'AE': 'ОАЭ',
                'YE': 'Йемен',
                'ZW': 'Зимбабве'
            },
            
            # Офшорные юрисдикции
            'offshore_zones': {
                'AD': 'Андорра',
                'AG': 'Антигуа и Барбуда',
                'BS': 'Багамы',
                'BH': 'Бахрейн',
                'BB': 'Барбадос',
                'BZ': 'Белиз',
                'BM': 'Бермуды',
                'VG': 'Британские Виргинские острова',
                'BN': 'Бруней',
                'CK': 'Острова Кука',
                'CW': 'Кюрасао',
                'DM': 'Доминика',
                'GI': 'Гибралтар',
                'GG': 'Гернси',
                'IM': 'Остров Мэн',
                'JE': 'Джерси',
                'LR': 'Либерия',
                'LI': 'Лихтенштейн',
                'MO': 'Макао',
                'MV': 'Мальдивы',
                'MH': 'Маршалловы острова',
                'MU': 'Маврикий',
                'MC': 'Монако',
                'MS': 'Монтсеррат',
                'NR': 'Науру',
                'AN': 'Нидерландские Антилы',
                'NU': 'Ниуэ',
                'PA': 'Панама',
                'KN': 'Сент-Китс и Невис',
                'LC': 'Сент-Люсия',
                'VC': 'Сент-Винсент и Гренадины',
                'WS': 'Самоа',
                'SC': 'Сейшелы',
                'TC': 'Теркс и Кайкос',
                'VU': 'Вануату'
            },
            
            # Санкционные юрисдикции (для Казахстана)
            'sanctioned': {
                'RU': 'Россия (частичные санкции)',
                'BY': 'Беларусь (частичные санкции)',
                'IR': 'Иран',
                'KP': 'Северная Корея',
                'SY': 'Сирия',
                'CU': 'Куба',
                'VE': 'Венесуэла'
            },
            
            # Соседние страны (низкий риск для КЗ)
            'neighboring': {
                'RU': 'Россия',
                'CN': 'Китай',
                'KG': 'Кыргызстан',
                'UZ': 'Узбекистан',
                'TM': 'Туркменистан'
            },
            
            # Страны ЕАЭС (таможенный союз)
            'eaeu': {
                'RU': 'Россия',
                'BY': 'Беларусь',
                'KG': 'Кыргызстан',
                'AM': 'Армения',
                'KZ': 'Казахстан'
            }
        }
        
        # Уровни риска по категориям
        self.category_risk_levels = {
            'fatf_blacklist': RiskLevel.PROHIBITED,
            'fatf_greylist': RiskLevel.HIGH,
            'offshore_zones': RiskLevel.HIGH,
            'sanctioned': RiskLevel.CRITICAL,
            'neighboring': RiskLevel.LOW,
            'eaeu': RiskLevel.LOW,
            'other': RiskLevel.MEDIUM
        }
        
        # Статистика по коридорам
        self.corridor_stats = defaultdict(lambda: {
            'transaction_count': 0,
            'total_amount': 0.0,
            'suspicious_count': 0,
            'last_transaction': None
        })
        
        # Паттерны подозрительных маршрутов
        self.suspicious_routes = [
            # Классический транзит через офшоры
            ['KZ', 'offshore', 'KZ'],
            # Транзит через высокорисковые страны
            ['KZ', 'high_risk', 'low_risk'],
            # Сложные маршруты
            ['KZ', 'EU', 'offshore', 'KZ'],
            # Обход санкций
            ['sanctioned', 'neighboring', 'KZ']
        ]
        
    def get_country_risk(self, country_code: str) -> Tuple[Dict, List[str]]:
        """Получение уровня риска страны и причин"""
        risks = []
        risk_level = RiskLevel.MEDIUM  # По умолчанию
        
        # Проверяем все категории
        for category, countries in self.country_classifications.items():
            if country_code in countries:
                risks.append(f"{category}: {countries[country_code]}")
                # Берем максимальный риск
                category_risk = self.category_risk_levels[category]
                if category_risk.value > risk_level.value:
                    risk_level = category_risk
                    
        # Особые случаи
        if country_code == 'KZ':
            risk_level = RiskLevel.LOW
            risks = ['Домашняя юрисдикция']
        
        return {'level': risk_level.name, 'value': risk_level.value}, risks
    
    def analyze_transaction_geography(self, transaction: Dict) -> Dict:
        """Анализ географических рисков транзакции"""
        sender_country = transaction.get('sender_country', 'KZ')
        beneficiary_country = transaction.get('beneficiary_country', 'KZ')
        
        sender_risk, sender_reasons = self.get_country_risk(sender_country)
        beneficiary_risk, beneficiary_reasons = self.get_country_risk(beneficiary_country)

        analysis = {
            'sender_risk': sender_risk,
            'sender_reasons': sender_reasons,
            'beneficiary_risk': beneficiary_risk,
            'beneficiary_reasons': beneficiary_reasons,
            'total_risk_score': 0.0,
            'transit_risks': [],
            'red_flags': [],
            'route_pattern': None
        }
        
        # Анализ транзитных стран
        transit_countries = transaction.get('transit_countries', [])
        for country in transit_countries:
            risk, reasons = self.get_country_risk(country)
            analysis['transit_risks'].append({
                'country': country,
                'risk_level': risk['level'],
                'risk_value': risk['value'],
                'reasons': reasons
            })
        
        # Проверка на подозрительные маршруты
        route = [sender_country] + transit_countries + [beneficiary_country]
        route_pattern = self._check_route_pattern(route)
        if route_pattern:
            analysis['route_pattern'] = route_pattern
            analysis['red_flags'].append(f'Подозрительный маршрут: {route_pattern}')
        
        # Расчет общего риска
        analysis['total_risk_score'] = self._calculate_geographic_risk_score(analysis)
        
        # Дополнительные проверки
        self._check_additional_red_flags(analysis, transaction)
        
        return analysis
    
    def _check_route_pattern(self, route: List[str]) -> Optional[str]:
        """Проверка маршрута на подозрительные паттерны"""
        # Упрощаем маршрут до категорий
        simplified_route = []
        for country in route:
            if country in self.country_classifications['offshore_zones']:
                simplified_route.append('offshore')
            elif country in self.country_classifications['fatf_blacklist']:
                simplified_route.append('blacklist')
            elif country in self.country_classifications['fatf_greylist']:
                simplified_route.append('high_risk')
            elif country in self.country_classifications['sanctioned']:
                simplified_route.append('sanctioned')
            elif country in self.country_classifications['eaeu']:
                simplified_route.append('eaeu')
            else:
                simplified_route.append('other')
        
        # Проверяем паттерны
        if 'offshore' in simplified_route:
            if simplified_route[0] == simplified_route[-1]:
                return 'Круговой маршрут через офшор'
            else:
                return 'Транзит через офшор'
                
        if 'blacklist' in simplified_route:
            return 'Маршрут через страну черного списка FATF'
            
        if len(set(simplified_route)) > 3:
            return 'Сложный многоступенчатый маршрут'
            
        return None
    
    def _calculate_geographic_risk_score(self, analysis: Dict) -> float:
        """Расчет общего географического риска"""
        score = 0.0
        
        # Риск отправителя
        sender_risk_value = analysis['sender_risk']['value']
        score += sender_risk_value * 0.3
        
        # Риск получателя (больший вес)
        beneficiary_risk_value = analysis['beneficiary_risk']['value']
        score += beneficiary_risk_value * 0.4
        
        # Риски транзита
        if analysis['transit_risks']:
            max_transit_risk = max(tr['risk_value'] for tr in analysis['transit_risks'])
            score += max_transit_risk * 0.3
        
        # Дополнительные баллы за паттерны
        if analysis['route_pattern']:
            score += 2.0
            
        # Нормализация (максимум 10)
        return min(score, 10.0)
    
    def _check_additional_red_flags(self, analysis: Dict, transaction: Dict):
        """Дополнительные проверки на красные флаги"""
        sender_country = transaction.get('sender_country', 'KZ')
        beneficiary_country = transaction.get('beneficiary_country', 'KZ')
        amount = transaction.get('amount', 0)
        
        # Проверка на несоответствие экономического смысла
        if sender_country == 'KZ' and beneficiary_country in self.country_classifications['offshore_zones']:
            if amount > 10_000_000:  # 10 млн тенге
                analysis['red_flags'].append('Крупный перевод в офшор')
                
        # Проверка на обход санкций
        if beneficiary_country in self.country_classifications['sanctioned']:
            if transaction.get('transit_countries'):
                analysis['red_flags'].append('Возможный обход санкций через транзит')
                
        # Проверка на типичность маршрута
        corridor_key = f"{sender_country}->{beneficiary_country}"
        corridor_data = self.corridor_stats[corridor_key]
        
        if corridor_data['transaction_count'] > 0:
            suspicion_rate = corridor_data['suspicious_count'] / corridor_data['transaction_count']
            if suspicion_rate > 0.3:
                analysis['red_flags'].append(f'Высокий уровень подозрительности коридора ({suspicion_rate:.1%})')
    
    def update_corridor_statistics(self, transaction: Dict, is_suspicious: bool = False):
        """Обновление статистики по коридорам"""
        sender_country = transaction.get('sender_country', 'KZ')
        beneficiary_country = transaction.get('beneficiary_country', 'KZ')
        amount = transaction.get('amount', 0)
        
        corridor_key = f"{sender_country}->{beneficiary_country}"
        
        self.corridor_stats[corridor_key]['transaction_count'] += 1
        self.corridor_stats[corridor_key]['total_amount'] += amount
        if is_suspicious:
            self.corridor_stats[corridor_key]['suspicious_count'] += 1
        self.corridor_stats[corridor_key]['last_transaction'] = datetime.now()
    
    def get_country_profile(self, country_code: str) -> Dict:
        """Получение полного профиля страны"""
        risk_level, risk_reasons = self.get_country_risk(country_code)
        
        profile = {
            'country_code': country_code,
            'risk_level': risk_level['level'],
            'risk_score': risk_level['value'],
            'risk_reasons': risk_reasons,
            'categories': []
        }
        
        # Определяем все категории страны
        for category, countries in self.country_classifications.items():
            if country_code in countries:
                profile['categories'].append({
                    'category': category,
                    'name': countries[country_code]
                })
        
        # Статистика по коридорам с этой страной
        related_corridors = []
        for corridor, stats in self.corridor_stats.items():
            if country_code in corridor:
                related_corridors.append({
                    'corridor': corridor,
                    'stats': stats
                })
        
        profile['related_corridors'] = related_corridors
        
        return profile
    
    def generate_geographic_alert(self, analysis: Dict, transaction: Dict) -> str:
        """Генерация алерта по географическим рискам"""
        if analysis['total_risk_score'] < 5.0:
            return ""
            
        alert = f"""
🌍 ГЕОГРАФИЧЕСКИЙ РИСК-АЛЕРТ
Транзакция: {transaction.get('id', 'N/A')}
Сумма: {transaction.get('amount', 0):,.2f} {transaction.get('currency', 'KZT')}

📍 МАРШРУТ:
• Отправитель: {transaction.get('sender_country')} - Риск: {analysis['sender_risk']['level']}
• Получатель: {transaction.get('beneficiary_country')} - Риск: {analysis['beneficiary_risk']['level']}
"""
        
        if analysis['transit_risks']:
            alert += "\n📍 ТРАНЗИТ ЧЕРЕЗ:"
            for transit in analysis['transit_risks']:
                alert += f"\n• {transit['country']} - Риск: {transit['risk_level']}"
                
        if analysis['route_pattern']:
            alert += f"\n\n⚠️ ПАТТЕРН: {analysis['route_pattern']}"
            
        if analysis['red_flags']:
            alert += "\n\n🚩 КРАСНЫЕ ФЛАГИ:"
            for flag in analysis['red_flags']:
                alert += f"\n• {flag}"
                
        alert += f"\n\n📊 ОБЩИЙ ГЕОГРАФИЧЕСКИЙ РИСК: {analysis['total_risk_score']:.1f}/10"
        
        if analysis['total_risk_score'] >= 8:
            alert += "\n\n⛔ КРИТИЧЕСКИЙ УРОВЕНЬ РИСКА!"
        elif analysis['total_risk_score'] >= 6:
            alert += "\n\n⚠️ Требуется усиленная проверка"
            
        return alert
    
    def get_high_risk_countries_summary(self) -> Dict:
        """Сводка по высокорисковым странам"""
        summary = {
            'fatf_blacklist': list(self.country_classifications['fatf_blacklist'].items()),
            'fatf_greylist_count': len(self.country_classifications['fatf_greylist']),
            'offshore_count': len(self.country_classifications['offshore_zones']),
            'sanctioned_count': len(self.country_classifications['sanctioned']),
            'total_high_risk': 0
        }
        
        # Подсчет общего количества высокорисковых
        high_risk_countries = set()
        high_risk_countries.update(self.country_classifications['fatf_blacklist'].keys())
        high_risk_countries.update(self.country_classifications['fatf_greylist'].keys())
        high_risk_countries.update(self.country_classifications['sanctioned'].keys())
        
        summary['total_high_risk'] = len(high_risk_countries)
        
        return summary


# Пример использования
if __name__ == "__main__":
    # Создаем географический профиль
    geo_profile = GeographicProfile()
    
    print("=== ТЕСТ 1: Прямой перевод в офшор ===")
    transaction1 = {
        'id': 'TX001',
        'amount': 15_000_000,
        'currency': 'KZT',
        'sender_country': 'KZ',
        'beneficiary_country': 'KY',  # Каймановы острова
        'transit_countries': []
    }
    
    analysis1 = geo_profile.analyze_transaction_geography(transaction1)
    alert1 = geo_profile.generate_geographic_alert(analysis1, transaction1)
    print(alert1)
    
    print("\n=== ТЕСТ 2: Транзит через несколько стран ===")
    transaction2 = {
        'id': 'TX002',
        'amount': 5_000_000,
        'currency': 'KZT',
        'sender_country': 'KZ',
        'beneficiary_country': 'KZ',
        'transit_countries': ['AE', 'KY', 'CH']  # ОАЭ -> Каймановы -> Швейцария
    }
    
    analysis2 = geo_profile.analyze_transaction_geography(transaction2)
    alert2 = geo_profile.generate_geographic_alert(analysis2, transaction2)
    print(alert2)
    
    print("\n=== ТЕСТ 3: Профиль страны ===")
    iran_profile = geo_profile.get_country_profile('IR')
    print(f"\nПрофиль Ирана:")
    print(f"Уровень риска: {iran_profile['risk_level']} ({iran_profile['risk_score']})")
    print(f"Причины: {', '.join(iran_profile['risk_reasons'])}")
    
    print("\n=== СВОДКА ПО ВЫСОКОРИСКОВЫМ СТРАНАМ ===")
    summary = geo_profile.get_high_risk_countries_summary()
    print(f"Черный список FATF: {summary['fatf_blacklist']}")
    print(f"Серый список FATF: {summary['fatf_greylist_count']} стран")
    print(f"Офшорные зоны: {summary['offshore_count']} юрисдикций")
    print(f"Под санкциями: {summary['sanctioned_count']} стран")
    print(f"Всего высокорисковых: {summary['total_high_risk']} стран")
