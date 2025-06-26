# Сетевой профиль для выявления схем отмывания денег
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque
import json

class NetworkProfile:
    """Сетевой профиль для анализа связей между участниками транзакций"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.network_id = "placeholder"
        self.created_at = datetime.now()
        
        # Граф связей (участник -> список связанных участников)
        self.connections = defaultdict(list)
        
        # Детали транзакций между участниками
        self.transaction_details = defaultdict(list)
        
        # Участники сети
        self.participants = {
            'individuals': {},  # Физлица
            'companies': {},    # Юрлица
            'suspicious': set() # Подозрительные участники
        }
        
        # Обнаруженные схемы
        self.detected_schemes = []
        
        # Статистика сети
        self.network_stats = {
            'total_participants': 0,
            'total_connections': 0,
            'total_amount': 0.0,
            'avg_transaction': 0.0,
            'network_depth': 0,
            'clustering_coefficient': 0.0
        }
        
    def add_transaction(self, sender: str, beneficiary: str, 
                       amount: float, date: datetime, transaction_id: str):
        """Добавление транзакции в сеть"""
        # Добавляем связь
        self.connections[sender].append(beneficiary)
        
        # Сохраняем детали транзакции
        transaction = {
            'id': transaction_id,
            'sender': sender,
            'beneficiary': beneficiary,
            'amount': amount,
            'date': date
        }
        
        # Ключ для пары участников
        pair_key = f"{sender}->{beneficiary}"
        self.transaction_details[pair_key].append(transaction)
        
        # Обновляем статистику
        self._update_stats()
        
    def detect_money_laundering_schemes(self) -> List[Dict]:
        """Обнаружение типовых схем отмывания денег"""
        schemes = []
        
        # 1. Поиск круговых схем (циклов)
        cycles = self._find_cycles()
        for cycle in cycles:
            schemes.append({
                'type': 'CIRCULAR_SCHEME',
                'participants': cycle,
                'risk_score': 9.0,
                'description': 'Круговое движение средств'
            })
        
        # 2. Поиск звездообразных схем (один центр, много связей)
        stars = self._find_star_patterns()
        for star in stars:
            schemes.append({
                'type': 'STAR_SCHEME',
                'center': star['center'],
                'satellites': star['satellites'],
                'risk_score': 8.0,
                'description': 'Концентрация операций через один центр'
            })
        
        # 3. Поиск цепочек транзита
        chains = self._find_transit_chains()
        for chain in chains:
            schemes.append({
                'type': 'TRANSIT_CHAIN',
                'participants': chain,
                'risk_score': 7.5,
                'description': 'Последовательный транзит средств'
            })
        
        # 4. Поиск схем дробления (смурфинг)
        smurfing = self._find_smurfing_patterns()
        for pattern in smurfing:
            schemes.append({
                'type': 'SMURFING',
                'source': pattern['source'],
                'destinations': pattern['destinations'],
                'risk_score': 8.5,
                'description': 'Дробление крупной суммы на мелкие'
            })
            
        # 5. Поиск временных аномалий
        temporal = self._find_temporal_anomalies()
        for anomaly in temporal:
            schemes.append({
                'type': 'TEMPORAL_ANOMALY',
                'participants': anomaly['participants'],
                'risk_score': 7.0,
                'description': anomaly['description']
            })
        
        self.detected_schemes = schemes
        return schemes
    
    def _find_cycles(self, max_length: int = 6) -> List[List[str]]:
        """Поиск циклических схем (деньги возвращаются к источнику)"""
        cycles = []
        
        for start_node in self.connections:
            visited = set()
            path = []
            
            def dfs(node: str, target: str, depth: int):
                if depth > max_length:
                    return False
                    
                if node == target and depth > 2:
                    cycles.append(path.copy())
                    return True
                    
                if node in visited and node != target:
                    return False
                    
                visited.add(node)
                path.append(node)
                
                found = False
                for neighbor in self.connections.get(node, []):
                    if dfs(neighbor, target, depth + 1):
                        found = True
                        
                path.pop()
                visited.remove(node)
                return found
            
            dfs(start_node, start_node, 0)
        
        # Удаляем дубликаты
        unique_cycles = []
        for cycle in cycles:
            if not any(set(cycle) == set(existing) for existing in unique_cycles):
                unique_cycles.append(cycle)
                
        return unique_cycles
    
    def _find_star_patterns(self, min_connections: int = 5) -> List[Dict]:
        """Поиск звездообразных схем (много входящих/исходящих от одного узла)"""
        stars = []
        
        # Подсчет входящих соединений
        incoming_count = defaultdict(int)
        for sender, recipients in self.connections.items():
            for recipient in recipients:
                incoming_count[recipient] += 1
        
        # Поиск узлов с большим количеством связей
        for node in self.connections:
            outgoing = len(set(self.connections[node]))
            incoming = incoming_count[node]
            
            if outgoing >= min_connections or incoming >= min_connections:
                # Собираем всех связанных участников
                satellites = set(self.connections[node])
                
                # Добавляем тех, кто отправлял этому узлу
                for sender, recipients in self.connections.items():
                    if node in recipients:
                        satellites.add(sender)
                
                satellites.discard(node)  # Убираем сам центр
                
                if len(satellites) >= min_connections:
                    stars.append({
                        'center': node,
                        'satellites': list(satellites),
                        'incoming_count': incoming,
                        'outgoing_count': outgoing
                    })
        
        return stars
    
    def _find_transit_chains(self, min_length: int = 3) -> List[List[str]]:
        """Поиск цепочек транзита (A->B->C->D)"""
        chains = []
        
        # Находим узлы, которые только принимают (потенциальные концы цепочек)
        end_nodes = set()
        for node in self.connections:
            if not self.connections[node]:  # Нет исходящих
                end_nodes.add(node)
        
        # Для каждого потенциального начала ищем пути
        for start in self.connections:
            visited = set()
            current_path = [start]
            
            def find_paths(node: str, path: List[str]):
                if len(path) >= min_length and (node in end_nodes or not self.connections[node]):
                    chains.append(path.copy())
                    return
                
                for next_node in self.connections.get(node, []):
                    if next_node not in visited:
                        visited.add(next_node)
                        path.append(next_node)
                        find_paths(next_node, path)
                        path.pop()
                        visited.remove(next_node)
            
            visited.add(start)
            find_paths(start, current_path)
        
        # Фильтруем цепочки, оставляя только линейные (без разветвлений)
        linear_chains = []
        for chain in chains:
            is_linear = True
            for i in range(1, len(chain) - 1):
                node = chain[i]
                # Проверяем, что у промежуточных узлов только один вход и один выход
                incoming = sum(1 for s in self.connections if node in self.connections[s])
                outgoing = len(set(self.connections.get(node, [])))
                if incoming > 1 or outgoing > 1:
                    is_linear = False
                    break
            
            if is_linear:
                linear_chains.append(chain)
        
        return linear_chains
    
    def _find_smurfing_patterns(self, threshold_ratio: float = 0.3) -> List[Dict]:
        """Поиск схем дробления (одна крупная сумма разбивается на мелкие)"""
        patterns = []
        
        for sender in self.connections:
            recipients = self.connections[sender]
            if len(recipients) < 3:  # Минимум 3 получателя для дробления
                continue
            
            # Анализируем суммы
            transactions_by_recipient = defaultdict(list)
            total_sent = 0.0
            
            for recipient in recipients:
                pair_key = f"{sender}->{recipient}"
                transactions = self.transaction_details.get(pair_key, [])
                for tx in transactions:
                    transactions_by_recipient[recipient].append(tx['amount'])
                    total_sent += tx['amount']
            
            # Проверяем паттерн дробления
            if total_sent > 0:
                amounts = []
                for recipient, tx_amounts in transactions_by_recipient.items():
                    amounts.extend(tx_amounts)
                
                if amounts:
                    avg_amount = sum(amounts) / len(amounts)
                    max_amount = max(amounts)
                    
                    # Если все суммы примерно одинаковые и их много
                    if (avg_amount / max_amount > 0.8 and 
                        len(amounts) >= 5 and
                        avg_amount < total_sent * threshold_ratio):
                        
                        patterns.append({
                            'source': sender,
                            'destinations': list(transactions_by_recipient.keys()),
                            'total_amount': total_sent,
                            'avg_transaction': avg_amount,
                            'transaction_count': len(amounts)
                        })
        
        return patterns
    
    def _find_temporal_anomalies(self) -> List[Dict]:
        """Поиск временных аномалий (подозрительная частота операций)"""
        anomalies = []
        
        # Анализ частоты транзакций между парами
        for pair_key, transactions in self.transaction_details.items():
            if len(transactions) < 3:
                continue
            
            # Сортируем по времени
            sorted_tx = sorted(transactions, key=lambda x: x['date'])
            
            # Вычисляем интервалы между транзакциями
            intervals = []
            for i in range(1, len(sorted_tx)):
                interval = (sorted_tx[i]['date'] - sorted_tx[i-1]['date']).total_seconds() / 60  # в минутах
                intervals.append(interval)
            
            avg_interval = sum(intervals) / len(intervals) if intervals else 0
            
            # Проверяем аномалии
            if avg_interval < 5:  # Средний интервал менее 5 минут
                sender, beneficiary = pair_key.split('->')
                anomalies.append({
                    'participants': [sender, beneficiary],
                    'transaction_count': len(transactions),
                    'avg_interval_minutes': avg_interval,
                    'description': 'Слишком частые транзакции (возможен автоматический перевод)'
                })
            
            # Проверка на транзакции в нерабочее время
            night_transactions = sum(1 for tx in transactions if tx['date'].hour < 6 or tx['date'].hour > 23)
            if night_transactions > len(transactions) * 0.5:
                sender, beneficiary = pair_key.split('->')
                anomalies.append({
                    'participants': [sender, beneficiary],
                    'night_percentage': night_transactions / len(transactions) * 100,
                    'description': 'Большинство транзакций в ночное время'
                })
        
        return anomalies
    
    def _update_stats(self):
        """Обновление статистики сети"""
        # Подсчет уникальных участников
        all_participants = set()
        for sender, recipients in self.connections.items():
            all_participants.add(sender)
            all_participants.update(recipients)
        
        self.network_stats['total_participants'] = len(all_participants)
        self.network_stats['total_connections'] = sum(len(v) for v in self.connections.values())
        
        # Подсчет общей суммы
        total_amount = 0
        transaction_count = 0
        for transactions in self.transaction_details.values():
            for tx in transactions:
                total_amount += tx['amount']
                transaction_count += 1
        
        self.network_stats['total_amount'] = total_amount
        self.network_stats['avg_transaction'] = total_amount / transaction_count if transaction_count > 0 else 0
    
    def get_participant_risk_score(self, participant: str) -> float:
        """Расчет риск-скора участника на основе его роли в сети"""
        score = 0.0
        
        # Проверка участия в схемах
        for scheme in self.detected_schemes:
            if scheme['type'] == 'CIRCULAR_SCHEME' and participant in scheme['participants']:
                score += 3.0
            elif scheme['type'] == 'STAR_SCHEME' and participant == scheme['center']:
                score += 4.0
            elif scheme['type'] == 'STAR_SCHEME' and participant in scheme['satellites']:
                score += 2.0
            elif scheme['type'] == 'TRANSIT_CHAIN' and participant in scheme['participants']:
                position = scheme['participants'].index(participant)
                if position == 0 or position == len(scheme['participants']) - 1:
                    score += 2.0  # Начало или конец цепочки
                else:
                    score += 3.0  # Промежуточное звено
            elif scheme['type'] == 'SMURFING' and participant == scheme['source']:
                score += 3.5
        
        # Количество связей
        outgoing = len(set(self.connections.get(participant, [])))
        incoming = sum(1 for s in self.connections if participant in self.connections[s])
        
        if outgoing > 10 or incoming > 10:
            score += 1.5
        
        return min(score, 10.0)
    
    def visualize_network_text(self) -> str:
        """Текстовая визуализация сети для отчета"""
        output = f"""
=== СЕТЕВОЙ АНАЛИЗ ===
ID сети: {self.network_id}
Дата анализа: {self.created_at.strftime('%Y-%m-%d %H:%M')}

📊 СТАТИСТИКА СЕТИ:
• Участников: {self.network_stats['total_participants']}
• Связей: {self.network_stats['total_connections']}
• Общая сумма: {self.network_stats['total_amount']:,.2f} KZT
• Средняя транзакция: {self.network_stats['avg_transaction']:,.2f} KZT

🔍 ОБНАРУЖЕННЫЕ СХЕМЫ:
"""
        
        for i, scheme in enumerate(self.detected_schemes, 1):
            output += f"\n{i}. {scheme['type']}"
            output += f"\n   Риск: {scheme['risk_score']}/10"
            output += f"\n   Описание: {scheme['description']}"
            
            if scheme['type'] == 'CIRCULAR_SCHEME':
                output += f"\n   Участники: {' → '.join(scheme['participants'])} → {scheme['participants'][0]}"
            elif scheme['type'] == 'STAR_SCHEME':
                output += f"\n   Центр: {scheme['center']}"
                output += f"\n   Связанные: {len(scheme['satellites'])} участников"
            elif scheme['type'] == 'TRANSIT_CHAIN':
                output += f"\n   Цепочка: {' → '.join(scheme['participants'])}"
            elif scheme['type'] == 'SMURFING':
                output += f"\n   Источник: {scheme['source']}"
                output += f"\n   Получателей: {len(scheme['destinations'])}"
                output += f"\n   Общая сумма: {scheme['total_amount']:,.2f} KZT"
            
            output += "\n"
        
        return output

    def analyze_transaction_network(self, transaction: Dict) -> Dict:
        """
        Главный метод для анализа сетевых связей транзакции.
        """
        self.network_id = transaction.get('transaction_id', 'N/A')
        sender = transaction.get('sender_id')
        beneficiary = transaction.get('beneficiary_id')
        
        if not sender or not beneficiary:
            return {
                'is_suspicious': False,
                'risk_score': 0,
                'schemes_found': [],
                'reason': 'Отсутствуют участники для анализа сети'
            }
            
        # Добавляем транзакцию в граф. 
        # В реальной системе мы бы подгружали историю для этих участников.
        self.add_transaction(
            sender=sender,
            beneficiary=beneficiary,
            amount=transaction.get('amount', 0),
            date=transaction.get('date', datetime.now()),
            transaction_id=self.network_id
        )
        
        # Запускаем обнаружение схем (упрощенно, на основе одной транзакции)
        schemes = self.detect_money_laundering_schemes()
        
        # Расчет риска
        risk_score = 0.0
        if schemes:
            risk_score = max(s.get('risk_score', 0.0) for s in schemes)
        
        # Дополнительный риск, если участники уже были замечены в подозрительных операциях
        sender_risk = self.get_participant_risk_score(sender)
        beneficiary_risk = self.get_participant_risk_score(beneficiary)
        
        total_risk = min(10.0, risk_score + sender_risk + beneficiary_risk)
        
        return {
            'is_suspicious': total_risk > 7.0,
            'risk_score': total_risk,
            'schemes_found': [s['type'] for s in schemes],
            'participants_risk': {
                'sender': sender_risk,
                'beneficiary': beneficiary_risk
            },
            'reason': f"Обнаружены схемы: {[s['type'] for s in schemes]}" if schemes else "Подозрительных схем не обнаружено"
        }


# Пример использования
if __name__ == "__main__":
    # Создаем сетевой профиль
    network = NetworkProfile()
    
    # Добавляем транзакции для примера круговой схемы
    network.add_transaction("Company_A", "Company_B", 5_000_000, datetime.now(), "TX001")
    network.add_transaction("Company_B", "Company_C", 4_800_000, datetime.now() + timedelta(hours=2), "TX002")
    network.add_transaction("Company_C", "Company_D", 4_600_000, datetime.now() + timedelta(hours=4), "TX003")
    network.add_transaction("Company_D", "Company_A", 4_400_000, datetime.now() + timedelta(hours=6), "TX004")
    
    # Добавляем транзакции для звездообразной схемы
    hub = "Transit_Company"
    for i in range(7):
        network.add_transaction(f"Sender_{i}", hub, 1_000_000 + i*100_000, datetime.now(), f"TX10{i}")
        network.add_transaction(hub, f"Recipient_{i}", 900_000 + i*100_000, datetime.now() + timedelta(hours=1), f"TX20{i}")
    
    # Добавляем схему дробления
    network.add_transaction("Big_Sender", "Small_1", 500_000, datetime.now(), "TX301")
    network.add_transaction("Big_Sender", "Small_2", 500_000, datetime.now(), "TX302")
    network.add_transaction("Big_Sender", "Small_3", 500_000, datetime.now(), "TX303")
    network.add_transaction("Big_Sender", "Small_4", 500_000, datetime.now(), "TX304")
    network.add_transaction("Big_Sender", "Small_5", 500_000, datetime.now(), "TX305")
    
    # Обнаруживаем схемы
    schemes = network.detect_money_laundering_schemes()
    
    # Выводим результаты
    print(network.visualize_network_text())
    
    # Проверяем риск-скор конкретного участника
    print("\n🎯 РИСК-СКОРЫ КЛЮЧЕВЫХ УЧАСТНИКОВ:")
    key_participants = ["Company_A", "Transit_Company", "Big_Sender"]
    for participant in key_participants:
        risk = network.get_participant_risk_score(participant)
        print(f"• {participant}: {risk:.1f}/10")
