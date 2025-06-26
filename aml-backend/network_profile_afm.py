# Сетевой профиль для выявления схем отмывания денег
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, deque
import json
import networkx as nx
import numpy as np
from itertools import combinations

class NetworkProfile:
    """Сетевой профиль для анализа связей между участниками транзакций"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.network_id = "placeholder"
        self.created_at = datetime.now()
        
        # NetworkX граф для расширенного анализа
        self.graph = nx.DiGraph()
        
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
            'clustering_coefficient': 0.0,
            'density': 0.0,
            'avg_degree': 0.0
        }
        
        # Параметры для казахстанского контекста
        self.kz_thresholds = {
            'large_amount': 5_000_000,  # 5 млн тенге - крупная сумма
            'reporting_threshold': 2_000_000,  # Порог обязательного контроля
            'min_smurfing_count': 3,  # Минимум транзакций для дробления
            'rapid_time_minutes': 30,  # Быстрые транзакции (30 минут)
            'min_cycle_length': 3,  # Минимальная длина цикла
            'max_cycle_length': 7   # Максимальная длина цикла для поиска
        }
        
    def add_transaction(self, sender: str, beneficiary: str, 
                       amount: float, date: datetime, transaction_id: str,
                       sender_type: str = 'unknown', beneficiary_type: str = 'unknown'):
        """Добавление транзакции в сеть"""
        # Добавляем связь в обычный граф
        self.connections[sender].append(beneficiary)
        
        # Добавляем узлы в NetworkX граф с атрибутами
        self.graph.add_node(sender, 
                           node_type=sender_type,
                           first_seen=date,
                           total_sent=0.0,
                           total_received=0.0)
        
        self.graph.add_node(beneficiary,
                           node_type=beneficiary_type,
                           first_seen=date,
                           total_sent=0.0,
                           total_received=0.0)
        
        # Добавляем или обновляем ребро
        if self.graph.has_edge(sender, beneficiary):
            # Обновляем существующее ребро
            edge_data = self.graph[sender][beneficiary]
            edge_data['weight'] += amount
            edge_data['count'] += 1
            edge_data['transactions'].append(transaction_id)
            edge_data['last_date'] = max(edge_data['last_date'], date)
        else:
            # Создаем новое ребро
            self.graph.add_edge(sender, beneficiary,
                               weight=amount,
                               count=1,
                               first_date=date,
                               last_date=date,
                               transactions=[transaction_id])
        
        # Обновляем суммы в узлах
        self.graph.nodes[sender]['total_sent'] += amount
        self.graph.nodes[beneficiary]['total_received'] += amount
        
        # Сохраняем детали транзакции
        transaction = {
            'id': transaction_id,
            'sender': sender,
            'beneficiary': beneficiary,
            'amount': amount,
            'date': date,
            'sender_type': sender_type,
            'beneficiary_type': beneficiary_type
        }
        
        # Ключ для пары участников
        pair_key = f"{sender}->{beneficiary}"
        self.transaction_details[pair_key].append(transaction)
        
        # Обновляем статистику
        self._update_stats()
        
    def detect_money_laundering_schemes(self) -> List[Dict]:
        """Обнаружение типовых схем отмывания денег"""
        schemes = []
        
        # Проверяем, что есть данные для анализа
        if not self.graph.nodes():
            return schemes
        
        # 1. Поиск круговых схем (циклов)
        cycles = self._find_cycles()
        for cycle_info in cycles:
            schemes.append({
                'type': 'CIRCULAR_SCHEME',
                'participants': cycle_info['participants'],
                'risk_score': cycle_info['risk_score'],
                'description': f'Круговое движение средств через {cycle_info["length"]} участников',
                'details': {
                    'total_amount': cycle_info['total_amount'],
                    'loss_percentage': cycle_info['loss_percentage'],
                    'transactions': cycle_info['transactions']
                }
            })
        
        # 2. Поиск звездообразных схем (один центр, много связей)
        stars = self._find_star_patterns()
        for star in stars:
            schemes.append({
                'type': 'STAR_SCHEME',
                'center': star['center'],
                'satellites': star['satellites'],
                'risk_score': star.get('risk_score', 8.0),
                'description': f'Концентрация операций через центр: {star["incoming_count"]} входящих, {star["outgoing_count"]} исходящих',
                'details': star
            })
        
        # 3. Поиск цепочек транзита
        chains = self._find_transit_chains()
        for chain_info in chains:
            schemes.append({
                'type': 'TRANSIT_CHAIN',
                'participants': chain_info['participants'],
                'risk_score': chain_info.get('risk_score', 7.5),
                'description': f'Последовательный транзит через {len(chain_info["participants"])} участников',
                'details': chain_info
            })
        
        # 4. Поиск схем дробления (смурфинг)
        smurfing = self._find_smurfing_patterns()
        for pattern in smurfing:
            schemes.append({
                'type': 'SMURFING',
                'source': pattern['source'],
                'destinations': pattern['destinations'],
                'risk_score': pattern.get('risk_score', 8.5),
                'description': f'Дробление {pattern["total_amount"]:,.0f} KZT на {pattern["transaction_count"]} транзакций',
                'details': pattern
            })
            
        # 5. Поиск временных аномалий
        temporal = self._find_temporal_anomalies()
        for anomaly in temporal:
            schemes.append({
                'type': 'TEMPORAL_ANOMALY',
                'participants': anomaly['participants'],
                'risk_score': anomaly.get('risk_score', 7.0),
                'description': anomaly['description'],
                'details': anomaly
            })
        
        # 6. Анализ сетевых метрик для выявления аномалий
        network_anomalies = self._analyze_network_metrics()
        schemes.extend(network_anomalies)
        
        self.detected_schemes = schemes
        return schemes
    
    def _find_cycles(self, max_length: int = None) -> List[Dict]:
        """Поиск циклических схем используя NetworkX"""
        if max_length is None:
            max_length = self.kz_thresholds['max_cycle_length']
            
        min_length = self.kz_thresholds['min_cycle_length']
        
        cycles_info = []
        
        try:
            # Используем алгоритм NetworkX для поиска всех простых циклов
            all_cycles = list(nx.simple_cycles(self.graph))
            
            for cycle in all_cycles:
                cycle_length = len(cycle)
                
                # Фильтруем по длине
                if cycle_length < min_length or cycle_length > max_length:
                    continue
                
                # Вычисляем общую сумму в цикле
                total_amount = 0
                min_amount = float('inf')
                max_amount = 0
                transactions_in_cycle = []
                
                for i in range(len(cycle)):
                    sender = cycle[i]
                    beneficiary = cycle[(i + 1) % len(cycle)]
                    
                    if self.graph.has_edge(sender, beneficiary):
                        edge_data = self.graph[sender][beneficiary]
                        amount = edge_data['weight']
                        total_amount += amount
                        min_amount = min(min_amount, amount)
                        max_amount = max(max_amount, amount)
                        transactions_in_cycle.extend(edge_data['transactions'])
                
                # Анализ потерь в цикле (комиссии)
                loss_percentage = 0
                if max_amount > 0:
                    loss_percentage = ((max_amount - min_amount) / max_amount) * 100
                
                # Определяем риск на основе характеристик
                risk_score = self._calculate_cycle_risk(
                    cycle_length=cycle_length,
                    total_amount=total_amount,
                    loss_percentage=loss_percentage
                )
                
                cycles_info.append({
                    'participants': cycle,
                    'length': cycle_length,
                    'total_amount': total_amount,
                    'min_amount': min_amount,
                    'max_amount': max_amount,
                    'loss_percentage': loss_percentage,
                    'risk_score': risk_score,
                    'transactions': transactions_in_cycle
                })
                
        except Exception as e:
            # Фолбек на простой DFS если NetworkX не работает
            print(f"NetworkX cycle detection failed: {e}")
            return self._find_cycles_fallback(max_length)
            
        # Сортируем по риску
        cycles_info.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return cycles_info
    
    def _calculate_cycle_risk(self, cycle_length: int, total_amount: float, 
                             loss_percentage: float) -> float:
        """Расчет риска для циклической схемы"""
        risk = 5.0  # Базовый риск для любого цикла
        
        # Короткие циклы более подозрительны
        if cycle_length == 3:
            risk += 2.0
        elif cycle_length == 4:
            risk += 1.5
        
        # Крупные суммы
        if total_amount > self.kz_thresholds['large_amount']:
            risk += 1.5
        
        # Минимальные потери (типично для отмывания)
        if loss_percentage < 5:
            risk += 1.0
        
        return min(risk, 10.0)
    
    def _find_cycles_fallback(self, max_length: int) -> List[Dict]:
        """Fallback метод для поиска циклов без NetworkX"""
        cycles_info = []
        
        # Простой DFS для поиска циклов
        for start_node in self.connections:
            visited = set()
            path = []
            
            def dfs(node: str, target: str, depth: int):
                if depth > max_length:
                    return
                    
                if node == target and depth >= self.kz_thresholds['min_cycle_length']:
                    # Нашли цикл, вычисляем его характеристики
                    cycle_participants = path.copy()
                    total_amount = 0
                    
                    for i in range(len(cycle_participants)):
                        sender = cycle_participants[i]
                        beneficiary = cycle_participants[(i + 1) % len(cycle_participants)]
                        pair_key = f"{sender}->{beneficiary}"
                        
                        if pair_key in self.transaction_details:
                            for tx in self.transaction_details[pair_key]:
                                total_amount += tx['amount']
                    
                    cycles_info.append({
                        'participants': cycle_participants,
                        'length': len(cycle_participants),
                        'total_amount': total_amount,
                        'risk_score': 7.0,  # Базовый риск для fallback
                        'transactions': []
                    })
                    return
                    
                if node in visited and node != target:
                    return
                    
                visited.add(node)
                path.append(node)
                
                for neighbor in self.connections.get(node, []):
                    dfs(neighbor, target, depth + 1)
                    
                path.pop()
                if node in visited:
                    visited.remove(node)
            
            dfs(start_node, start_node, 0)
        
        return cycles_info
    
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
    
    def _find_transit_chains(self, min_length: int = 3) -> List[Dict]:
        """Поиск цепочек транзита (A->B->C->D)"""
        chains_info = []
        
        # Используем NetworkX для поиска путей
        if self.graph.number_of_nodes() == 0:
            return chains_info
            
        # Находим узлы без исходящих связей (потенциальные концы цепочек)
        end_nodes = [n for n in self.graph.nodes() if self.graph.out_degree(n) == 0]
        
        # Находим узлы без входящих связей (потенциальные начала цепочек)
        start_nodes = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
        
        # Ищем все простые пути между началами и концами
        for start in start_nodes:
            for end in end_nodes:
                if start != end:
                    try:
                        # Находим все простые пути
                        paths = list(nx.all_simple_paths(self.graph, start, end, cutoff=min_length+2))
                        
                        for path in paths:
                            if len(path) >= min_length:
                                # Проверяем, что это действительно линейная цепочка
                                is_linear = True
                                for i in range(1, len(path) - 1):
                                    node = path[i]
                                    if self.graph.in_degree(node) > 1 or self.graph.out_degree(node) > 1:
                                        is_linear = False
                                        break
                                
                                if is_linear:
                                    # Вычисляем характеристики цепочки
                                    total_amount = 0
                                    transactions = []
                                    
                                    for i in range(len(path) - 1):
                                        if self.graph.has_edge(path[i], path[i+1]):
                                            edge_data = self.graph[path[i]][path[i+1]]
                                            total_amount += edge_data['weight']
                                            transactions.extend(edge_data['transactions'])
                                    
                                    # Расчет риска для цепочки
                                    risk_score = 6.0  # Базовый риск
                                    if len(path) > 5:
                                        risk_score += 1.0  # Длинные цепочки подозрительнее
                                    if total_amount > self.kz_thresholds['large_amount']:
                                        risk_score += 1.0
                                    
                                    chains_info.append({
                                        'participants': path,
                                        'length': len(path),
                                        'total_amount': total_amount,
                                        'risk_score': min(risk_score, 10.0),
                                        'transactions': transactions
                                    })
                    except:
                        # Нет пути между узлами
                        pass
        
        # Удаляем дубликаты
        unique_chains = []
        seen = set()
        for chain in chains_info:
            chain_tuple = tuple(chain['participants'])
            if chain_tuple not in seen:
                seen.add(chain_tuple)
                unique_chains.append(chain)
        
        return unique_chains
    
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
        """Обновление статистики сети с использованием NetworkX"""
        if not self.graph.nodes():
            return
            
        # Базовые метрики
        self.network_stats['total_participants'] = self.graph.number_of_nodes()
        self.network_stats['total_connections'] = self.graph.number_of_edges()
        
        # Подсчет общей суммы
        total_amount = sum(data['weight'] for _, _, data in self.graph.edges(data=True))
        transaction_count = sum(data['count'] for _, _, data in self.graph.edges(data=True))
        
        self.network_stats['total_amount'] = total_amount
        self.network_stats['avg_transaction'] = total_amount / transaction_count if transaction_count > 0 else 0
        
        # Расширенные метрики NetworkX
        try:
            # Плотность сети (0 = разреженная, 1 = полная)
            self.network_stats['density'] = nx.density(self.graph)
            
            # Средняя степень узлов
            degrees = [d for n, d in self.graph.degree()]
            self.network_stats['avg_degree'] = sum(degrees) / len(degrees) if degrees else 0
            
            # Коэффициент кластеризации (насколько узлы склонны формировать группы)
            self.network_stats['clustering_coefficient'] = nx.average_clustering(self.graph.to_undirected())
            
            # Глубина сети (самый длинный кратчайший путь)
            if nx.is_weakly_connected(self.graph):
                self.network_stats['network_depth'] = nx.diameter(self.graph.to_undirected())
            else:
                # Для несвязного графа берем максимальный диаметр компонент
                components = list(nx.weakly_connected_components(self.graph))
                max_diameter = 0
                for comp in components:
                    if len(comp) > 1:
                        subgraph = self.graph.subgraph(comp)
                        try:
                            diameter = nx.diameter(subgraph.to_undirected())
                            max_diameter = max(max_diameter, diameter)
                        except:
                            pass
                self.network_stats['network_depth'] = max_diameter
                
        except Exception as e:
            print(f"Error calculating network metrics: {e}")
    
    def _analyze_network_metrics(self) -> List[Dict]:
        """Анализ сетевых метрик для выявления аномалий"""
        anomalies = []
        
        if not self.graph.nodes():
            return anomalies
            
        # 1. Поиск узлов с аномально высокой центральностью
        try:
            # Betweenness centrality - узлы, через которые проходит много путей
            betweenness = nx.betweenness_centrality(self.graph)
            
            # Находим аномально высокие значения
            if betweenness:
                mean_betweenness = np.mean(list(betweenness.values()))
                std_betweenness = np.std(list(betweenness.values()))
                threshold = mean_betweenness + 2 * std_betweenness
                
                for node, centrality in betweenness.items():
                    if centrality > threshold and centrality > 0.1:
                        anomalies.append({
                            'type': 'HIGH_CENTRALITY',
                            'participants': [node],
                            'risk_score': min(7.0 + centrality * 3, 10.0),
                            'description': f'Узел {node} является критической точкой в сети (centrality: {centrality:.2f})',
                            'metric_value': centrality
                        })
                        
        except Exception as e:
            print(f"Error in centrality analysis: {e}")
            
        # 2. Поиск изолированных подграфов
        try:
            components = list(nx.weakly_connected_components(self.graph))
            
            for comp in components:
                if 3 <= len(comp) <= 10:  # Подозрительные малые группы
                    subgraph = self.graph.subgraph(comp)
                    
                    # Проверяем, является ли подграф плотным
                    density = nx.density(subgraph)
                    if density > 0.5:  # Плотная группа
                        anomalies.append({
                            'type': 'ISOLATED_DENSE_GROUP',
                            'participants': list(comp),
                            'risk_score': 7.5,
                            'description': f'Изолированная плотная группа из {len(comp)} участников',
                            'density': density
                        })
                        
        except Exception as e:
            print(f"Error in component analysis: {e}")
            
        return anomalies
    
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

    def analyze_transaction_network(self, transaction: Dict, 
                                   transaction_history: List[Dict] = None) -> Dict:
        """
        Главный метод для анализа сетевых связей транзакции.
        Загружает историю транзакций для участников и строит граф связей.
        """
        self.network_id = transaction.get('transaction_id', 'N/A')
        sender = transaction.get('sender_id') or transaction.get('sender_name')
        beneficiary = transaction.get('beneficiary_id') or transaction.get('beneficiary_name')
        
        if not sender or not beneficiary:
            return {
                'is_suspicious': False,
                'risk_score': 0,
                'schemes_found': [],
                'suspicious_reasons': [],
                'reason': 'Отсутствуют участники для анализа сети'
            }
        
        # Добавляем текущую транзакцию
        self.add_transaction(
            sender=sender,
            beneficiary=beneficiary,
            amount=transaction.get('amount_kzt', transaction.get('amount', 0)),
            date=transaction.get('transaction_date', transaction.get('date', datetime.now())),
            transaction_id=self.network_id,
            sender_type='individual' if self._is_individual(sender) else 'company',
            beneficiary_type='individual' if self._is_individual(beneficiary) else 'company'
        )
        
        # Загружаем историю транзакций для построения полной сети
        if transaction_history:
            for hist_tx in transaction_history:
                hist_sender = hist_tx.get('sender_id') or hist_tx.get('sender_name')
                hist_beneficiary = hist_tx.get('beneficiary_id') or hist_tx.get('beneficiary_name')
                
                if hist_sender and hist_beneficiary:
                    # Добавляем только транзакции, связанные с участниками текущей транзакции
                    if hist_sender in [sender, beneficiary] or hist_beneficiary in [sender, beneficiary]:
                        self.add_transaction(
                            sender=hist_sender,
                            beneficiary=hist_beneficiary,
                            amount=hist_tx.get('amount_kzt', hist_tx.get('amount', 0)),
                            date=hist_tx.get('transaction_date', hist_tx.get('date', datetime.now())),
                            transaction_id=hist_tx.get('transaction_id', f'HIST_{len(self.transaction_details)}'),
                            sender_type='individual' if self._is_individual(hist_sender) else 'company',
                            beneficiary_type='individual' if self._is_individual(hist_beneficiary) else 'company'
                        )
        
        # Запускаем обнаружение схем
        schemes = self.detect_money_laundering_schemes()
        
        # Собираем причины подозрительности
        suspicious_reasons = []
        scheme_types = []
        
        # Расчет риска
        risk_score = 0.0
        if schemes:
            # Берем максимальный риск из всех обнаруженных схем
            risk_score = max(s.get('risk_score', 0.0) for s in schemes)
            
            # Добавляем причины
            for scheme in schemes:
                scheme_types.append(scheme['type'])
                suspicious_reasons.append(f"[СЕТЬ] {scheme['description']}")
        
        # Анализ конкретных участников
        sender_risk = self.get_participant_risk_score(sender)
        beneficiary_risk = self.get_participant_risk_score(beneficiary)
        
        # Проверяем количество связей участников
        sender_connections = len(self.graph.edges(sender)) if sender in self.graph else 0
        beneficiary_connections = len(self.graph.edges(beneficiary)) if beneficiary in self.graph else 0
        
        if sender_connections > 10:
            suspicious_reasons.append(f"[СЕТЬ] Отправитель имеет {sender_connections} связей")
            risk_score += 1.0
            
        if beneficiary_connections > 10:
            suspicious_reasons.append(f"[СЕТЬ] Получатель имеет {beneficiary_connections} связей")
            risk_score += 1.0
        
        # Финальный риск-скор
        total_risk = min(10.0, risk_score)
        
        return {
            'is_suspicious': total_risk > 6.0 or len(schemes) > 0,
            'risk_score': total_risk,
            'schemes_found': scheme_types,
            'suspicious_reasons': suspicious_reasons,
            'network_stats': self.network_stats,
            'participants_risk': {
                'sender': sender_risk,
                'beneficiary': beneficiary_risk
            },
            'detected_schemes': schemes,  # Полная информация о схемах
            'reason': suspicious_reasons[0] if suspicious_reasons else "Подозрительных сетевых схем не обнаружено"
        }
    
    def _is_individual(self, participant_id: str) -> bool:
        """Определяет, является ли участник физическим лицом по ID"""
        # Простая эвристика: если ID содержит только цифры и длина 12 - это ИИН физлица
        return participant_id.isdigit() and len(participant_id) == 12


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
