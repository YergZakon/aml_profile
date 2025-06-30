#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Движок анализа рисков АФМ РК
Реализует логику ранжирования согласно действующей системе АФМ
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class RiskCategory(Enum):
    """Категории риска АФМ"""
    OD = "OD"  # Отмывание денег
    FT = "FT"  # Финансирование терроризма  
    ABR = "ABR"  # Переводы за рубеж
    PYRAMID = "PYRAMID"  # Финансовые пирамиды
    DMFT = "DMFT"  # Списки ДМФТ

@dataclass
class AFMRiskResult:
    """Результат анализа рисков АФМ"""
    rank: int  # 1-11
    category: RiskCategory
    criteria: str
    reasons: List[str]
    is_high_risk: bool
    requires_simbase: bool

class AFMRiskEngine:
    """Движок анализа рисков по стандартам АФМ РК"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        # Суммовые пороги АФМ (в тенге)
        self.amount_thresholds = {
            'od_high': 300_000_000,      # 300 млн - высокий риск ОД
            'od_medium': 212_200_000,    # 212.2 млн - средний риск ОД
            'od_low': 169_700_000,       # 169.7 млн - низкий риск ОД
            'abr_high': 200_000_000,     # 200 млн - высокий риск ABR
            'abr_medium': 100_000_000,   # 100 млн - средний риск ABR
            'abr_low': 50_000_000        # 50 млн - низкий риск ABR
        }
        
        # Ключевые слова для разных категорий
        self.keywords = {
            'ft1': ['террор', 'нко', 'экстреми', 'оружи', 'благотворительн', 'религиозн', 'митинг'],
            'ft2': ['нарко'],
            'pyramid': ['пирамид', 'инвест', 'доход', 'прибыль', 'процент'],
            'loan': ['займ', 'кредит', 'беспроцентн'],
            'advance': ['аванс', 'предоплат']
        }
        
        # Высокорисковые юрисдикции (20 стран)
        self.high_risk_countries = [
            'AF', 'KP', 'IR', 'IQ', 'LY', 'ML', 'SO', 'SS', 'SY', 'YE',
            'MM', 'KH', 'LA', 'PK', 'BD', 'VE', 'CU', 'BI', 'ZW', 'HT'
        ]
        
        # КППО для разных категорий
        self.kppo_codes = {
            'pyramid': [1056, 1062],
            'ft': [1001, 1002, 1003, 1004, 1005],
            'od': [2001, 2002, 2003, 2004, 2005]
        }
    
    def analyze_transaction(self, transaction: Dict) -> AFMRiskResult:
        """Основной метод анализа транзакции по правилам АФМ"""
        
        # Получаем данные транзакции
        amount = float(transaction.get('amount', 0))
        amount_kzt = float(transaction.get('amount_kzt', amount))
        sender_country = transaction.get('sender_country', 'KZ') or 'KZ'
        beneficiary_country = transaction.get('beneficiary_country', 'KZ') or 'KZ'
        purpose_text = str(transaction.get('purpose_text') or '').lower()
        transaction_id = str(transaction.get('transaction_id', ''))
        sender_id = str(transaction.get('sender_id', ''))
        beneficiary_id = str(transaction.get('beneficiary_id', ''))
        
        # Проверяем каждую категорию
        results = []
        
        # 1. Отмывание денег (ОД)
        od_result = self._check_money_laundering(amount_kzt, sender_id, beneficiary_id, purpose_text)
        if od_result:
            results.append(od_result)
        
        # 2. Финансирование терроризма (ФТ)
        ft_result = self._check_terrorism_financing(amount_kzt, sender_country, beneficiary_country, purpose_text, sender_id, beneficiary_id)
        if ft_result:
            results.append(ft_result)
        
        # 3. Переводы за рубеж (ABR)
        abr_result = self._check_abroad_transfers(amount_kzt, sender_country, beneficiary_country, purpose_text)
        if abr_result:
            results.append(abr_result)
        
        # 4. Финансовые пирамиды
        pyramid_result = self._check_financial_pyramids(purpose_text)
        if pyramid_result:
            results.append(pyramid_result)
        
        # 5. Списки ДМФТ
        dmft_result = self._check_dmft_lists(sender_id, beneficiary_id, purpose_text)
        if dmft_result:
            results.append(dmft_result)
        
        # Возвращаем результат с максимальным рангом
        if results:
            return max(results, key=lambda x: x.rank)
        else:
            # Базовый анализ - если нет специальных правил
            return self._basic_risk_assessment(amount_kzt)
    
    def _check_money_laundering(self, amount_kzt: float, sender_id: str, beneficiary_id: str, purpose_text: str) -> Optional[AFMRiskResult]:
        """Проверка на отмывание денег (ОД)"""
        reasons = []
        rank = 0
        
        # Проверка сумм
        if amount_kzt >= self.amount_thresholds['od_high']:
            rank = 8
            reasons.append(f"Крупная операция: {amount_kzt:,.0f} тенге (>300 млн)")
        elif amount_kzt >= self.amount_thresholds['od_medium']:
            rank = 4  
            reasons.append(f"Средняя операция: {amount_kzt:,.0f} тенге (212.2-300 млн)")
        elif amount_kzt >= self.amount_thresholds['od_low']:
            rank = 1
            reasons.append(f"Операция под контролем: {amount_kzt:,.0f} тенге (169.7-212.2 млн)")
        
        if rank > 0:
            # Дополнительные проверки списков (упрощенно)
            if self._check_suspicious_lists(sender_id, beneficiary_id, 'od'):
                rank += 1
                reasons.append("Участник в списке подозрительных (ОД)")
            
            return AFMRiskResult(
                rank=rank,
                category=RiskCategory.OD,
                criteria=f"OD_RANK_{rank}",
                reasons=reasons,
                is_high_risk=rank >= 6,
                requires_simbase=rank >= 8
            )
        
        return None
    
    def _check_terrorism_financing(self, amount_kzt: float, sender_country: str, beneficiary_country: str, purpose_text: str, sender_id: str, beneficiary_id: str) -> Optional[AFMRiskResult]:
        """Проверка на финансирование терроризма (ФТ)"""
        reasons = []
        rank = 0
        
        # Проверка международных переводов
        is_international = sender_country != 'KZ' or beneficiary_country != 'KZ'
        
        # Проверка высокорисковых стран
        high_risk_country = (sender_country in self.high_risk_countries or 
                           beneficiary_country in self.high_risk_countries)
        
        # Проверка ключевых слов FT1
        has_ft1_keywords = any(keyword in purpose_text for keyword in self.keywords['ft1'])
        
        # Проверка ключевых слов FT2 (наркотики)
        has_ft2_keywords = any(keyword in purpose_text for keyword in self.keywords['ft2'])
        
        # Определение ранга
        if is_international and high_risk_country and has_ft1_keywords:
            rank = 10
            reasons.append("Международный перевод в высокорисковую страну с признаками ФТ")
        elif is_international and (high_risk_country or has_ft1_keywords):
            rank = 6
            reasons.append("Международный перевод с признаками ФТ")
        elif has_ft2_keywords:
            rank = 6
            reasons.append("Признаки связи с наркотиками")
        elif is_international and amount_kzt >= 10_000_000:  # 10 млн тенге
            rank = 3
            reasons.append("Крупный международный перевод")
        
        if rank > 0:
            # Дополнительные проверки списков ФТ
            if self._check_suspicious_lists(sender_id, beneficiary_id, 'ft'):
                rank += 2
                reasons.append("Участник в списке ФТ")
            
            return AFMRiskResult(
                rank=min(rank, 11),  # Максимум 11
                category=RiskCategory.FT,
                criteria=f"FT_RANK_{rank}",
                reasons=reasons,
                is_high_risk=rank >= 6,
                requires_simbase=rank >= 8
            )
        
        return None
    
    def _check_abroad_transfers(self, amount_kzt: float, sender_country: str, beneficiary_country: str, purpose_text: str) -> Optional[AFMRiskResult]:
        """Проверка переводов за рубеж (ABR)"""
        # Только для международных операций
        if sender_country == 'KZ' and beneficiary_country == 'KZ':
            return None
        
        reasons = []
        rank = 0
        
        # Проверка сумм
        if amount_kzt >= self.amount_thresholds['abr_high']:
            rank = 9
            reasons.append(f"Крупный международный перевод: {amount_kzt:,.0f} тенге (>200 млн)")
        elif amount_kzt >= self.amount_thresholds['abr_medium']:
            rank = 5
            reasons.append(f"Средний международный перевод: {amount_kzt:,.0f} тенге (100-200 млн)")
        elif amount_kzt >= self.amount_thresholds['abr_low']:
            rank = 2
            reasons.append(f"Международный перевод: {amount_kzt:,.0f} тенге (50-100 млн)")
        
        # Дополнительные факторы риска
        if any(keyword in purpose_text for keyword in self.keywords['loan']):
            rank += 1
            reasons.append("Займы/кредиты")
        
        if any(keyword in purpose_text for keyword in self.keywords['advance']):
            rank += 1
            reasons.append("Авансовые платежи")
        
        if rank > 0:
            return AFMRiskResult(
                rank=min(rank, 11),
                category=RiskCategory.ABR,
                criteria=f"ABR_RANK_{rank}",
                reasons=reasons,
                is_high_risk=rank >= 6,
                requires_simbase=rank >= 8
            )
        
        return None
    
    def _check_financial_pyramids(self, purpose_text: str) -> Optional[AFMRiskResult]:
        """Проверка на финансовые пирамиды"""
        has_pyramid_keywords = any(keyword in purpose_text for keyword in self.keywords['pyramid'])
        
        if has_pyramid_keywords:
            if 'пирамид' in purpose_text:
                rank = 11
                reasons = ["Прямое упоминание пирамиды в назначении платежа"]
            else:
                rank = 7
                reasons = ["Признаки финансовой пирамиды"]
            
            return AFMRiskResult(
                rank=rank,
                category=RiskCategory.PYRAMID,
                criteria=f"PYRAMID_RANK_{rank}",
                reasons=reasons,
                is_high_risk=True,
                requires_simbase=True
            )
        
        return None
    
    def _check_dmft_lists(self, sender_id: str, beneficiary_id: str, purpose_text: str) -> Optional[AFMRiskResult]:
        """Проверка списков ДМФТ (упрощенная версия)"""
        # Здесь можно реализовать проверку по реальным спискам из БД
        # Пока делаем упрощенную проверку
        
        # Проверка на PDL (публично-должностные лица)
        if 'депутат' in purpose_text or 'министр' in purpose_text or 'акимат' in purpose_text:
            return AFMRiskResult(
                rank=5,
                category=RiskCategory.DMFT,
                criteria="DMFT_PDL",
                reasons=["Возможная связь с публично-должностными лицами"],
                is_high_risk=False,
                requires_simbase=False
            )
        
        return None
    
    def _check_suspicious_lists(self, sender_id: str, beneficiary_id: str, category: str) -> bool:
        """Проверка участников в подозрительных списках (упрощенная)"""
        # Здесь должна быть реальная проверка по БД
        # Пока возвращаем False для упрощения
        return False
    
    def _basic_risk_assessment(self, amount_kzt: float) -> AFMRiskResult:
        """Базовая оценка риска для операций, не попадающих под специальные правила"""
        if amount_kzt >= 50_000_000:  # 50 млн тенге
            rank = 2
            reasons = ["Крупная операция требует внимания"]
        elif amount_kzt >= 10_000_000:  # 10 млн тенге
            rank = 1
            reasons = ["Операция средней величины"]
        else:
            rank = 1
            reasons = ["Обычная операция"]
        
        return AFMRiskResult(
            rank=rank,
            category=RiskCategory.OD,  # По умолчанию ОД
            criteria=f"BASIC_RANK_{rank}",
            reasons=reasons,
            is_high_risk=False,
            requires_simbase=False
        )
    
    def get_risk_statistics(self) -> Dict:
        """Получение статистики по рискам из БД"""
        try:
            with self.db_manager as db:
                cursor = db.connection.cursor()
                
                # Статистика по существующим данным
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN final_risk_score >= 6.0 THEN 1 ELSE 0 END) as high_risk,
                        SUM(CASE WHEN final_risk_score >= 3.0 AND final_risk_score < 6.0 THEN 1 ELSE 0 END) as medium_risk,
                        SUM(CASE WHEN final_risk_score < 3.0 THEN 1 ELSE 0 END) as low_risk,
                        SUM(CASE WHEN is_suspicious = 1 THEN 1 ELSE 0 END) as suspicious
                    FROM transactions
                """)
                
                stats = cursor.fetchone()
                return {
                    'total_transactions': stats[0],
                    'high_risk_count': stats[1], 
                    'medium_risk_count': stats[2],
                    'low_risk_count': stats[3],
                    'suspicious_count': stats[4]
                }
        except Exception as e:
            print(f"Ошибка получения статистики: {e}")
            return {
                'total_transactions': 0,
                'high_risk_count': 0,
                'medium_risk_count': 0, 
                'low_risk_count': 0,
                'suspicious_count': 0
            }