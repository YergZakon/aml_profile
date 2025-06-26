# Настройка локальной базы данных для системы AML АФМ РК
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

class AMLDatabaseManager:
    """Менеджер базы данных для системы AML"""
    
    def __init__(self, db_path: str = "aml_system.db"):
        self.db_path = db_path
        self.connection = None
        
        # Создаем базу данных и таблицы при первом запуске
        self._initialize_database()
        
    def _initialize_database(self):
        """Инициализация базы данных и создание всех таблиц"""
        print(f"🗄️ Инициализация базы данных: {self.db_path}")
        
        # Создаем соединение
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # Для удобной работы с результатами
        
        # Включаем поддержку внешних ключей
        self.connection.execute("PRAGMA foreign_keys = ON")
        
        # Создаем все таблицы
        self._create_tables()
        
        print("✅ База данных успешно инициализирована")
        
    def _create_tables(self):
        """Создание всех таблиц для профилей"""
        cursor = self.connection.cursor()
        
        # =====================================================
        # 1. ТАБЛИЦА КЛИЕНТСКИХ ПРОФИЛЕЙ
        # =====================================================
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer_profiles (
            customer_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Личные данные
            full_name TEXT,
            iin TEXT,  -- ИИН для физлиц
            bin TEXT,  -- БИН для юрлиц
            birth_date DATE,
            citizenship TEXT DEFAULT 'KZ',
            residence_country TEXT DEFAULT 'KZ',
            
            -- Тип клиента
            is_individual BOOLEAN DEFAULT 1,
            is_pep BOOLEAN DEFAULT 0,
            is_foreign BOOLEAN DEFAULT 0,
            business_type TEXT,
            
            -- Риск-факторы
            base_risk_level TEXT DEFAULT 'LOW',
            country_risk INTEGER DEFAULT 1,
            product_risk INTEGER DEFAULT 1,
            behavior_risk INTEGER DEFAULT 1,
            overall_risk_score REAL DEFAULT 1.0,
            
            -- Статистика транзакций
            total_transaction_count INTEGER DEFAULT 0,
            total_amount REAL DEFAULT 0.0,
            avg_transaction REAL DEFAULT 0.0,
            max_transaction REAL DEFAULT 0.0,
            monthly_avg REAL DEFAULT 0.0,
            
            -- Поведенческие паттерны (JSON)
            behavior_patterns TEXT,  -- JSON с паттернами
            typical_counterparties TEXT,  -- JSON массив
            typical_purposes TEXT,  -- JSON массив
            
            -- История подозрительности
            str_count INTEGER DEFAULT 0,
            last_str_date TIMESTAMP,
            false_positive_count INTEGER DEFAULT 0,
            confirmed_suspicious INTEGER DEFAULT 0
        )
        ''')
        
        # =====================================================
        # 2. ТАБЛИЦА ТРАНЗАКЦИЙ
        # =====================================================
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Основная информация
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'KZT',
            amount_kzt REAL NOT NULL,
            transaction_date TIMESTAMP,
            value_date TIMESTAMP,
            channel TEXT,  -- branch, atm, mobile, internet
            
            -- Участники
            sender_id TEXT,
            sender_name TEXT,
            sender_account TEXT,
            sender_bank_bic TEXT,
            sender_country TEXT DEFAULT 'KZ',
            
            beneficiary_id TEXT,
            beneficiary_name TEXT,
            beneficiary_account TEXT,
            beneficiary_bank_bic TEXT,
            beneficiary_country TEXT DEFAULT 'KZ',
            
            -- Детали операции
            operation_code TEXT,
            operation_type TEXT,
            purpose_code TEXT,
            purpose_text TEXT,
            is_cash BOOLEAN DEFAULT 0,
            is_international BOOLEAN DEFAULT 0,
            
            -- Результаты анализа
            final_risk_score REAL DEFAULT 0.0,
            is_suspicious BOOLEAN DEFAULT 0,
            str_generated BOOLEAN DEFAULT 0,
            str_id TEXT,
            
            -- Риск-индикаторы (JSON)
            risk_indicators TEXT,  -- JSON с флагами
            rule_triggers TEXT,  -- JSON массив сработавших правил
            
            FOREIGN KEY (sender_id) REFERENCES customer_profiles(customer_id),
            FOREIGN KEY (beneficiary_id) REFERENCES customer_profiles(customer_id)
        )
        ''')
        
        # =====================================================
        # 3. ТАБЛИЦА СЕТЕВЫХ СВЯЗЕЙ
        # =====================================================
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS network_connections (
            connection_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            sender_id TEXT NOT NULL,
            beneficiary_id TEXT NOT NULL,
            
            -- Статистика связи
            transaction_count INTEGER DEFAULT 1,
            total_amount REAL DEFAULT 0.0,
            avg_amount REAL DEFAULT 0.0,
            first_transaction_date TIMESTAMP,
            last_transaction_date TIMESTAMP,
            avg_interval_days REAL,
            
            -- Риск связи
            connection_risk_score REAL DEFAULT 0.0,
            is_suspicious_route BOOLEAN DEFAULT 0,
            
            UNIQUE(sender_id, beneficiary_id),
            FOREIGN KEY (sender_id) REFERENCES customer_profiles(customer_id),
            FOREIGN KEY (beneficiary_id) REFERENCES customer_profiles(customer_id)
        )
        ''')
        
        # =====================================================
        # 4. ТАБЛИЦА ОБНАРУЖЕННЫХ СХЕМ
        # =====================================================
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS detected_schemes (
            scheme_id INTEGER PRIMARY KEY AUTOINCREMENT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            scheme_type TEXT NOT NULL,  -- CIRCULAR, STAR, TRANSIT, SMURFING
            participants TEXT NOT NULL,  -- JSON массив участников
            transactions TEXT NOT NULL,  -- JSON массив транзакций
            
            total_amount REAL,
            scheme_start_date TIMESTAMP,
            scheme_end_date TIMESTAMP,
            
            risk_score REAL DEFAULT 0.0,
            confidence REAL DEFAULT 0.0,
            
            is_confirmed BOOLEAN DEFAULT 0,
            analyst_notes TEXT,
            
            -- Статус
            status TEXT DEFAULT 'DETECTED',  -- DETECTED, INVESTIGATING, CONFIRMED, FALSE_POSITIVE
            resolution_date TIMESTAMP,
            resolution_notes TEXT
        )
        ''')
        
        # =====================================================
        # 5. ТАБЛИЦА ПОВЕДЕНЧЕСКОЙ ИСТОРИИ
        # =====================================================
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS behavioral_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            date DATE NOT NULL,
            
            -- Дневная статистика
            transaction_count INTEGER DEFAULT 0,
            total_amount REAL DEFAULT 0.0,
            
            -- Аномалии
            has_anomaly BOOLEAN DEFAULT 0,
            anomaly_types TEXT,  -- JSON массив типов аномалий
            anomaly_score REAL DEFAULT 0.0,
            
            UNIQUE(customer_id, date),
            FOREIGN KEY (customer_id) REFERENCES customer_profiles(customer_id)
        )
        ''')
        
        # =====================================================
        # 6. ТАБЛИЦА ГЕОГРАФИЧЕСКИХ КОРИДОРОВ
        # =====================================================
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS geographic_corridors (
            corridor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            sender_country TEXT NOT NULL,
            beneficiary_country TEXT NOT NULL,
            transit_countries TEXT,  -- JSON массив
            
            -- Статистика
            transaction_count INTEGER DEFAULT 0,
            total_amount REAL DEFAULT 0.0,
            suspicious_count INTEGER DEFAULT 0,
            suspicion_rate REAL DEFAULT 0.0,
            
            last_transaction_date TIMESTAMP,
            
            -- Риск коридора
            corridor_risk_score REAL DEFAULT 0.0,
            is_high_risk BOOLEAN DEFAULT 0,
            
            UNIQUE(sender_country, beneficiary_country, transit_countries)
        )
        ''')
        
        # =====================================================
        # 7. ТАБЛИЦА АЛЕРТОВ И СПО
        # =====================================================
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            transaction_id TEXT,
            customer_id TEXT,
            scheme_id INTEGER,
            
            alert_type TEXT NOT NULL,  -- TRANSACTION, BEHAVIOR, NETWORK, GEOGRAPHIC
            severity TEXT NOT NULL,  -- LOW, MEDIUM, HIGH, CRITICAL
            
            title TEXT NOT NULL,
            description TEXT,
            evidence TEXT,  -- JSON с доказательствами
            
            risk_score REAL,
            
            -- Статус обработки
            status TEXT DEFAULT 'NEW',  -- NEW, REVIEWING, ESCALATED, CLOSED
            assigned_to TEXT,
            reviewed_at TIMESTAMP,
            resolution TEXT,
            
            -- СПО
            str_required BOOLEAN DEFAULT 0,
            str_id TEXT,
            str_codes TEXT,  -- JSON массив кодов АФМ
            
            FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
            FOREIGN KEY (customer_id) REFERENCES customer_profiles(customer_id),
            FOREIGN KEY (scheme_id) REFERENCES detected_schemes(scheme_id)
        )
        ''')
        
        # =====================================================
        # 8. ТАБЛИЦА НАСТРОЕК И МЕТАДАННЫХ
        # =====================================================
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT,
            setting_type TEXT,  -- STRING, NUMBER, JSON, BOOLEAN
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # =====================================================
        # СОЗДАНИЕ ИНДЕКСОВ ДЛЯ ОПТИМИЗАЦИИ
        # =====================================================
        
        # Индексы для customer_profiles
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_customer_risk 
        ON customer_profiles(overall_risk_score DESC)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_customer_suspicious 
        ON customer_profiles(str_count DESC)
        ''')
        
        # Индексы для transactions
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_transaction_date 
        ON transactions(transaction_date DESC)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_transaction_risk 
        ON transactions(final_risk_score DESC)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_transaction_suspicious 
        ON transactions(is_suspicious)
        ''')
        
        # Индексы для network_connections
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_network_participants 
        ON network_connections(sender_id, beneficiary_id)
        ''')
        
        # Индексы для alerts
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_alert_status 
        ON alerts(status, created_at DESC)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_alert_severity 
        ON alerts(severity, created_at DESC)
        ''')
        
        # Сохраняем изменения
        self.connection.commit()
        
        # Добавляем начальные настройки
        self._initialize_settings()
        
    def _initialize_settings(self):
        """Инициализация системных настроек"""
        settings = [
            ('threshold_cash', '2000000', 'NUMBER', 'Порог для наличных операций'),
            ('threshold_transfer', '7000000', 'NUMBER', 'Порог для переводов'),
            ('threshold_international', '1000000', 'NUMBER', 'Порог для международных операций'),
            ('min_risk_for_str', '7.0', 'NUMBER', 'Минимальный риск для СПО'),
            ('min_risk_for_edd', '5.0', 'NUMBER', 'Минимальный риск для усиленной проверки'),
            ('behavioral_lookback_days', '90', 'NUMBER', 'Дней для анализа поведения'),
            ('network_min_connections', '5', 'NUMBER', 'Минимум связей для анализа схем'),
            ('high_risk_countries', '["IR", "KP", "SY", "AF", "YE", "MM"]', 'JSON', 'Список высокорисковых стран'),
            ('offshore_countries', '["KY", "VG", "BS", "BZ", "SC", "VU"]', 'JSON', 'Список офшорных зон'),
        ]
        
        cursor = self.connection.cursor()
        for key, value, type_, desc in settings:
            cursor.execute('''
            INSERT OR IGNORE INTO system_settings (setting_key, setting_value, setting_type, description)
            VALUES (?, ?, ?, ?)
            ''', (key, value, type_, desc))
        
        self.connection.commit()
    
    # =====================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С КЛИЕНТСКИМИ ПРОФИЛЯМИ
    # =====================================================
    
    def save_customer_profile(self, profile_data: Dict) -> bool:
        """Сохранение или обновление клиентского профиля"""
        cursor = self.connection.cursor()
        
        try:
            # Конвертируем сложные объекты в JSON
            behavior_patterns = json.dumps(profile_data.get('behavior_patterns', {}))
            typical_counterparties = json.dumps(profile_data.get('typical_counterparties', []))
            typical_purposes = json.dumps(profile_data.get('typical_purposes', []))
            
            cursor.execute('''
            INSERT OR REPLACE INTO customer_profiles (
                customer_id, full_name, iin, bin, birth_date, citizenship, residence_country,
                is_individual, is_pep, is_foreign, business_type,
                base_risk_level, country_risk, product_risk, behavior_risk, overall_risk_score,
                total_transaction_count, total_amount, avg_transaction, max_transaction, monthly_avg,
                behavior_patterns, typical_counterparties, typical_purposes,
                str_count, last_str_date, false_positive_count, confirmed_suspicious,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                profile_data['customer_id'],
                profile_data.get('full_name'),
                profile_data.get('iin'),
                profile_data.get('bin'),
                profile_data.get('birth_date'),
                profile_data.get('citizenship', 'KZ'),
                profile_data.get('residence_country', 'KZ'),
                profile_data.get('is_individual', True),
                profile_data.get('is_pep', False),
                profile_data.get('is_foreign', False),
                profile_data.get('business_type'),
                profile_data.get('base_risk_level', 'LOW'),
                profile_data.get('country_risk', 1),
                profile_data.get('product_risk', 1),
                profile_data.get('behavior_risk', 1),
                profile_data.get('overall_risk_score', 1.0),
                profile_data.get('total_transaction_count', 0),
                profile_data.get('total_amount', 0.0),
                profile_data.get('avg_transaction', 0.0),
                profile_data.get('max_transaction', 0.0),
                profile_data.get('monthly_avg', 0.0),
                behavior_patterns,
                typical_counterparties,
                typical_purposes,
                profile_data.get('str_count', 0),
                profile_data.get('last_str_date'),
                profile_data.get('false_positive_count', 0),
                profile_data.get('confirmed_suspicious', 0)
            ))
            
            self.connection.commit()
            print(f"✅ Профиль клиента {profile_data['customer_id']} сохранен")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения профиля: {e}")
            self.connection.rollback()
            return False
    
    def get_customer_profile(self, customer_id: str) -> Optional[Dict]:
        """Получение клиентского профиля"""
        cursor = self.connection.cursor()
        
        cursor.execute('''
        SELECT * FROM customer_profiles WHERE customer_id = ?
        ''', (customer_id,))
        
        row = cursor.fetchone()
        if row:
            profile = dict(row)
            # Парсим JSON поля
            profile['behavior_patterns'] = json.loads(profile.get('behavior_patterns', '{}'))
            profile['typical_counterparties'] = json.loads(profile.get('typical_counterparties', '[]'))
            profile['typical_purposes'] = json.loads(profile.get('typical_purposes', '[]'))
            return profile
        
        return None
    
    # =====================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С ТРАНЗАКЦИЯМИ
    # =====================================================
    
    def save_transaction(self, transaction_data: Dict) -> bool:
        """Сохранение транзакции"""
        cursor = self.connection.cursor()
        
        try:
            # Конвертируем сложные объекты в JSON
            risk_indicators = json.dumps(transaction_data.get('risk_indicators', {}))
            rule_triggers = json.dumps(transaction_data.get('rule_triggers', []))
            
            cursor.execute('''
            INSERT OR REPLACE INTO transactions (
                transaction_id, amount, currency, amount_kzt, transaction_date, value_date, channel,
                sender_id, sender_name, sender_account, sender_bank_bic, sender_country,
                beneficiary_id, beneficiary_name, beneficiary_account, beneficiary_bank_bic, beneficiary_country,
                operation_code, operation_type, purpose_code, purpose_text, is_cash, is_international,
                final_risk_score, is_suspicious, str_generated, str_id,
                risk_indicators, rule_triggers
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                transaction_data['transaction_id'],
                transaction_data['amount'],
                transaction_data.get('currency', 'KZT'),
                transaction_data['amount_kzt'],
                transaction_data['transaction_date'],
                transaction_data.get('value_date'),
                transaction_data.get('channel'),
                transaction_data.get('sender_id'),
                transaction_data.get('sender_name'),
                transaction_data.get('sender_account'),
                transaction_data.get('sender_bank_bic'),
                transaction_data.get('sender_country', 'KZ'),
                transaction_data.get('beneficiary_id'),
                transaction_data.get('beneficiary_name'),
                transaction_data.get('beneficiary_account'),
                transaction_data.get('beneficiary_bank_bic'),
                transaction_data.get('beneficiary_country', 'KZ'),
                transaction_data.get('operation_code'),
                transaction_data.get('operation_type'),
                transaction_data.get('purpose_code'),
                transaction_data.get('purpose_text'),
                transaction_data.get('is_cash', False),
                transaction_data.get('is_international', False),
                transaction_data.get('final_risk_score', 0.0),
                transaction_data.get('is_suspicious', False),
                transaction_data.get('str_generated', False),
                transaction_data.get('str_id'),
                risk_indicators,
                rule_triggers
            ))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения транзакции: {e}")
            self.connection.rollback()
            return False
    
    # =====================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ СО СХЕМАМИ
    # =====================================================
    
    def save_detected_scheme(self, scheme_data: Dict) -> int:
        """Сохранение обнаруженной схемы"""
        cursor = self.connection.cursor()
        
        try:
            participants = json.dumps(scheme_data.get('participants', []))
            transactions = json.dumps(scheme_data.get('transactions', []))
            
            cursor.execute('''
            INSERT INTO detected_schemes (
                scheme_type, participants, transactions, total_amount,
                scheme_start_date, scheme_end_date, risk_score, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                scheme_data['scheme_type'],
                participants,
                transactions,
                scheme_data.get('total_amount', 0.0),
                scheme_data.get('scheme_start_date'),
                scheme_data.get('scheme_end_date'),
                scheme_data.get('risk_score', 0.0),
                scheme_data.get('confidence', 0.0)
            ))
            
            self.connection.commit()
            scheme_id = cursor.lastrowid
            print(f"✅ Схема {scheme_data['scheme_type']} сохранена с ID: {scheme_id}")
            return scheme_id
            
        except Exception as e:
            print(f"❌ Ошибка сохранения схемы: {e}")
            self.connection.rollback()
            return -1
    
    # =====================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С АЛЕРТАМИ
    # =====================================================
    
    def create_alert(self, alert_data: Dict) -> int:
        """Создание алерта"""
        cursor = self.connection.cursor()
        
        try:
            evidence = json.dumps(alert_data.get('evidence', {}))
            str_codes = json.dumps(alert_data.get('str_codes', []))
            
            cursor.execute('''
            INSERT INTO alerts (
                transaction_id, customer_id, scheme_id, alert_type, severity,
                title, description, evidence, risk_score, str_required, str_codes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert_data.get('transaction_id'),
                alert_data.get('customer_id'),
                alert_data.get('scheme_id'),
                alert_data['alert_type'],
                alert_data['severity'],
                alert_data['title'],
                alert_data.get('description'),
                evidence,
                alert_data.get('risk_score', 0.0),
                alert_data.get('str_required', False),
                str_codes
            ))
            
            self.connection.commit()
            alert_id = cursor.lastrowid
            print(f"⚠️ Алерт создан с ID: {alert_id}")
            return alert_id
            
        except Exception as e:
            print(f"❌ Ошибка создания алерта: {e}")
            self.connection.rollback()
            return -1
    
    # =====================================================
    # АНАЛИТИЧЕСКИЕ ЗАПРОСЫ
    # =====================================================
    
    def get_high_risk_customers(self, limit: int = 10) -> List[Dict]:
        """Получение клиентов с высоким риском"""
        cursor = self.connection.cursor()
        
        cursor.execute('''
        SELECT customer_id, full_name, overall_risk_score, str_count, 
               total_transaction_count, total_amount
        FROM customer_profiles
        WHERE overall_risk_score >= 5.0
        ORDER BY overall_risk_score DESC, str_count DESC
        LIMIT ?
        ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_suspicious_transactions(self, days: int = 7) -> List[Dict]:
        """Получение недавних подозрительных транзакций"""
        cursor = self.connection.cursor()
        
        cursor.execute('''
        SELECT t.*, 
               c1.full_name as sender_name_full,
               c2.full_name as beneficiary_name_full
        FROM transactions t
        LEFT JOIN customer_profiles c1 ON t.sender_id = c1.customer_id
        LEFT JOIN customer_profiles c2 ON t.beneficiary_id = c2.customer_id
        WHERE t.is_suspicious = 1
          AND t.transaction_date >= datetime('now', '-' || ? || ' days')
        ORDER BY t.transaction_date DESC
        ''', (days,))
        
        results = []
        for row in cursor.fetchall():
            tx = dict(row)
            tx['risk_indicators'] = json.loads(tx.get('risk_indicators', '{}'))
            tx['rule_triggers'] = json.loads(tx.get('rule_triggers', '[]'))
            results.append(tx)
        
        return results
    
    def get_corridor_statistics(self) -> List[Dict]:
        """Получение статистики по географическим коридорам"""
        cursor = self.connection.cursor()
        
        cursor.execute('''
        SELECT * FROM geographic_corridors
        WHERE transaction_count > 0
        ORDER BY suspicion_rate DESC, transaction_count DESC
        LIMIT 20
        ''')
        
        results = []
        for row in cursor.fetchall():
            corridor = dict(row)
            corridor['transit_countries'] = json.loads(corridor.get('transit_countries', '[]'))
            results.append(corridor)
        
        return results
    
    def get_active_schemes(self) -> List[Dict]:
        """Получение активных схем"""
        cursor = self.connection.cursor()
        
        cursor.execute('''
        SELECT * FROM detected_schemes
        WHERE status IN ('DETECTED', 'INVESTIGATING')
        ORDER BY risk_score DESC, detected_at DESC
        ''')
        
        results = []
        for row in cursor.fetchall():
            scheme = dict(row)
            scheme['participants'] = json.loads(scheme.get('participants', '[]'))
            scheme['transactions'] = json.loads(scheme.get('transactions', '[]'))
            results.append(scheme)
        
        return results
    
    def get_system_statistics(self) -> Dict:
        """Получение общей статистики системы"""
        cursor = self.connection.cursor()
        
        stats = {}
        
        # Статистика по клиентам
        cursor.execute('''
        SELECT 
            COUNT(*) as total_customers,
            COUNT(CASE WHEN overall_risk_score >= 7 THEN 1 END) as high_risk_customers,
            COUNT(CASE WHEN str_count > 0 THEN 1 END) as suspicious_customers,
            AVG(overall_risk_score) as avg_risk_score
        FROM customer_profiles
        ''')
        stats['customers'] = dict(cursor.fetchone())
        
        # Статистика по транзакциям
        cursor.execute('''
        SELECT 
            COUNT(*) as total_transactions,
            COUNT(CASE WHEN is_suspicious THEN 1 END) as suspicious_transactions,
            COUNT(CASE WHEN str_generated THEN 1 END) as str_generated,
            SUM(amount_kzt) as total_volume,
            AVG(final_risk_score) as avg_risk_score
        FROM transactions
        ''')
        stats['transactions'] = dict(cursor.fetchone())
        
        # Статистика по алертам
        cursor.execute('''
        SELECT 
            COUNT(*) as total_alerts,
            COUNT(CASE WHEN status = 'NEW' THEN 1 END) as new_alerts,
            COUNT(CASE WHEN severity = 'CRITICAL' THEN 1 END) as critical_alerts,
            COUNT(CASE WHEN str_required THEN 1 END) as str_required
        FROM alerts
        ''')
        stats['alerts'] = dict(cursor.fetchone())
        
        # Статистика по схемам
        cursor.execute('''
        SELECT 
            COUNT(*) as total_schemes,
            COUNT(CASE WHEN status = 'CONFIRMED' THEN 1 END) as confirmed_schemes,
            SUM(total_amount) as total_scheme_amount
        FROM detected_schemes
        ''')
        stats['schemes'] = dict(cursor.fetchone())
        
        return stats
    
    def get_all_transactions(self) -> List[Dict]:
        """Получение ВСЕХ транзакций из базы данных"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM transactions")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_db_cursor(self):
        """Получение курсора базы данных"""
        return self.connection.cursor()
    
    def commit(self):
        """Сохранение изменений в базе данных"""
        self.connection.commit()
    
    def close(self):
        """Закрытие соединения с базой данных"""
        if self.connection:
            self.connection.close()
            print("🔒 Соединение с базой данных закрыто")


# =====================================================
# ДЕМОНСТРАЦИЯ РАБОТЫ С БАЗОЙ ДАННЫХ
# =====================================================

def demonstrate_database():
    """Демонстрация работы с базой данных"""
    print("="*60)
    print("🚀 ДЕМОНСТРАЦИЯ БАЗЫ ДАННЫХ AML")
    print("="*60)
    
    # Создаем менеджер БД
    db = AMLDatabaseManager("aml_demo.db")
    
    # 1. Сохраняем клиентские профили
    print("\n📁 Сохранение клиентских профилей...")
    
    customer1 = {
        'customer_id': 'CLIENT_001',
        'full_name': 'Иванов Иван Иванович',
        'iin': '901231300123',
        'citizenship': 'KZ',
        'base_risk_level': 'MEDIUM',
        'overall_risk_score': 4.5,
        'behavior_patterns': {
            'usual_transaction_range': [50000, 500000],
            'typical_hours': [9, 10, 11, 14, 15, 16]
        },
        'typical_counterparties': ['ТОО Альфа', 'ИП Бета'],
        'total_transaction_count': 150,
        'total_amount': 25000000
    }
    
    customer2 = {
        'customer_id': 'OFFSHORE_001',
        'full_name': 'Offshore Holdings Ltd',
        'bin': '123456789012',
        'residence_country': 'KY',
        'is_individual': False,
        'is_foreign': True,
        'base_risk_level': 'HIGH',
        'overall_risk_score': 8.5,
        'str_count': 3
    }
    
    db.save_customer_profile(customer1)
    db.save_customer_profile(customer2)
    
    # 2. Сохраняем транзакции
    print("\n💸 Сохранение транзакций...")
    
    transaction1 = {
        'transaction_id': 'TX_001',
        'amount': 8500000,
        'amount_kzt': 8500000,
        'transaction_date': datetime.now(),
        'channel': 'internet',
        'sender_id': 'CLIENT_001',
        'sender_name': 'Иванов И.И.',
        'beneficiary_id': 'OFFSHORE_001',
        'beneficiary_name': 'Offshore Holdings',
        'beneficiary_country': 'KY',
        'operation_type': 'TRANSFER_INTERNATIONAL',
        'purpose_text': 'Оплата консультационных услуг',
        'is_international': True,
        'final_risk_score': 7.8,
        'is_suspicious': True,
        'risk_indicators': {
            'is_offshore': True,
            'is_round_amount': False,
            'is_high_risk_country': False
        },
        'rule_triggers': ['R005: Операция с офшорной юрисдикцией']
    }
    
    db.save_transaction(transaction1)
    
    # 3. Сохраняем обнаруженную схему
    print("\n🕸️ Сохранение обнаруженной схемы...")
    
    scheme = {
        'scheme_type': 'CIRCULAR',
        'participants': ['CLIENT_001', 'COMPANY_A', 'COMPANY_B', 'OFFSHORE_001'],
        'transactions': ['TX_001', 'TX_002', 'TX_003', 'TX_004'],
        'total_amount': 25000000,
        'scheme_start_date': datetime.now(),
        'risk_score': 9.2,
        'confidence': 0.85
    }
    
    scheme_id = db.save_detected_scheme(scheme)
    
    # 4. Создаем алерт
    print("\n⚠️ Создание алерта...")
    
    alert = {
        'transaction_id': 'TX_001',
        'customer_id': 'CLIENT_001',
        'scheme_id': scheme_id,
        'alert_type': 'NETWORK',
        'severity': 'HIGH',
        'title': 'Обнаружена круговая схема',
        'description': 'Клиент участвует в круговой схеме перевода средств через офшор',
        'risk_score': 9.2,
        'str_required': True,
        'str_codes': ['1054', '1041'],
        'evidence': {
            'scheme_type': 'CIRCULAR',
            'participants_count': 4,
            'total_amount': 25000000
        }
    }
    
    db.create_alert(alert)
    
    # 5. Получаем аналитику
    print("\n📊 АНАЛИТИКА:")
    
    # Клиенты высокого риска
    print("\n🎯 Клиенты с высоким риском:")
    high_risk = db.get_high_risk_customers(5)
    for customer in high_risk:
        print(f"  • {customer['customer_id']}: риск {customer['overall_risk_score']}, СПО: {customer['str_count']}")
    
    # Подозрительные транзакции
    print("\n💰 Недавние подозрительные транзакции:")
    suspicious_tx = db.get_recent_suspicious_transactions(30)
    for tx in suspicious_tx:
        print(f"  • {tx['transaction_id']}: {tx['amount']:,.0f} {tx['currency']} (риск: {tx['final_risk_score']})")
    
    # Общая статистика
    print("\n📈 Общая статистика системы:")
    stats = db.get_system_statistics()
    print(f"  • Клиентов: {stats['customers']['total_customers']}")
    print(f"  • Транзакций (30 дней): {stats['transactions']['total_transactions']}")
    print(f"  • Алертов (7 дней): {stats['alerts']['total_alerts']}")
    print(f"  • Обнаружено схем: {stats['schemes']['total_schemes']}")
    
    # Закрываем БД
    db.close()
    
    print("\n✅ Демонстрация завершена!")
    print(f"📁 База данных сохранена в файле: aml_demo.db")


if __name__ == "__main__":
    # Запускаем демонстрацию
    demonstrate_database()
