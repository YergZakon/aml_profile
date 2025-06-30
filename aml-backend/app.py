import os
import json
from flask import Flask, request, jsonify, send_file, make_response, Blueprint
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import hashlib
import shutil
import random  # Для генерации тестовых данных
import threading # <-- 1. Импортируем threading
import sys
import glob

# Добавляем корневую папку в путь для импорта наших модулей
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aml_integration_system import run_full_analysis # <-- 2. Старая функция для совместимости
from unified_aml_pipeline import UnifiedAMLPipeline  # <-- 3. Новый исправленный pipeline
from aml_json_loader import AMLJSONDataLoader
from aml_database_setup import AMLDatabaseManager

app = Flask(__name__)

# Создаем Blueprint для API с префиксом /api
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Настройка CORS для работы с фронтендом
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
        "allow_headers": [
            "Content-Type", "Authorization", "Upload-Offset", "Upload-Length", 
            "Tus-Resumable", "X-File-Name", "X-File-Size", "X-Upload-Time", 
            "X-Department", "Upload-Metadata"
        ],
        "expose_headers": [
            "Location", "Upload-Offset", "Tus-Resumable", "Upload-Length",
            "Tus-Version", "Tus-Max-Size", "Tus-Extension", "Upload-Metadata"
        ]
    }
})

# Конфигурация
UPLOAD_FOLDER = 'uploads'
CHUNKS_FOLDER = 'chunks'
PROCESSING_FOLDER = 'processing'
RESULTS_FOLDER = 'results'

# Создаем необходимые папки
for folder in [UPLOAD_FOLDER, CHUNKS_FOLDER, PROCESSING_FOLDER, RESULTS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Хранилище информации о загрузках (в реальном приложении - БД)
uploads = {}
processing_tasks = {}

# === НОВОЕ: путь к последней БД с результатами анализа ===
latest_db_path = 'aml_system_e840b2937714940f.db'  # используем БД с полным анализом

test_transactions = []  # Для хранения тестовых транзакций

def run_enhanced_analysis(json_filepath: str, db_filepath: str) -> str:
    """
    Запуск анализа с использованием исправленного UnifiedAMLPipeline
    Возвращает путь к файлу с результатами
    """
    try:
        print(f"🚀 Запуск улучшенного анализа: {json_filepath} -> {db_filepath}")
        
        # 1. Загрузка данных в БД
        loader = AMLJSONDataLoader()
        loader.load_json_to_database(json_filepath, db_filepath)
        
        # 2. Инициализация нового pipeline
        pipeline = UnifiedAMLPipeline()
        pipeline._initialize_database(db_filepath)
        
        # 3. Получение транзакций из БД
        with AMLDatabaseManager(db_filepath) as db:
            cursor = db.connection.cursor()
            cursor.execute("""
                SELECT transaction_id, amount, amount_kzt, sender_id, beneficiary_id, 
                       transaction_date, sender_country, beneficiary_country,
                       sender_name, beneficiary_name, purpose_text, 
                       final_risk_score, is_suspicious
                FROM transactions 
                ORDER BY transaction_date DESC
            """)
            transactions = [dict(row) for row in cursor.fetchall()]
        
        print(f"📊 Обработка {len(transactions)} транзакций...")
        
        # 4. Анализ транзакций с новым pipeline
        results = []
        total_transactions = len(transactions)
        
        for i, tx in enumerate(transactions):
            # Показываем прогресс каждые 1000 транзакций
            if i % 1000 == 0:
                print(f"📊 Прогресс: {i}/{total_transactions} ({i/total_transactions*100:.1f}%)")
            
            try:
                # Подготавливаем транзакцию для анализа
                transaction = {
                    'transaction_id': tx['transaction_id'],
                    'amount': float(tx['amount']),
                    'amount_kzt': float(tx.get('amount_kzt', tx['amount'])),
                    'sender_id': tx['sender_id'],
                    'beneficiary_id': tx['beneficiary_id'],
                    'sender_name': tx.get('sender_name', ''),
                    'beneficiary_name': tx.get('beneficiary_name', ''),
                    'purpose_text': tx.get('purpose_text', ''),
                    'transaction_date': tx['transaction_date'],
                    'date': datetime.strptime(tx['transaction_date'], '%Y-%m-%d %H:%M:%S'),
                    'sender_country': tx.get('sender_country', 'KZ'),
                    'beneficiary_country': tx.get('beneficiary_country', 'KZ'),
                    'final_risk_score': float(tx.get('final_risk_score', 0)),
                    'is_suspicious': bool(tx.get('is_suspicious', False))
                }
                
                # Анализ с новым pipeline
                result = pipeline._analyze_single_transaction(transaction)
                
                results.append({
                    'transaction_id': tx['transaction_id'],
                    'overall_risk': result.overall_risk,
                    'risk_category': result.risk_category,
                    'transaction_risk': result.transaction_risk,
                    'customer_risk': result.customer_risk,
                    'network_risk': result.network_risk,
                    'behavioral_risk': result.behavioral_risk,
                    'geographic_risk': result.geographic_risk,
                    'suspicious_flags': result.suspicious_flags,
                    'explanations': result.explanations
                })
                
                if (i + 1) % 100 == 0:
                    print(f"  ✅ Обработано {i + 1}/{len(transactions)} транзакций")
                    
            except Exception as e:
                print(f"  ❌ Ошибка анализа транзакции {tx['transaction_id']}: {e}")
                continue
        
        # 5. Сохранение результатов
        results_file = os.path.join(RESULTS_FOLDER, f'enhanced_analysis_{int(datetime.now().timestamp())}.json')
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_transactions': len(transactions),
            'analyzed_transactions': len(results),
            'high_risk_count': len([r for r in results if r['overall_risk'] >= 4.0]),
            'medium_risk_count': len([r for r in results if 2.0 <= r['overall_risk'] < 4.0]),
            'low_risk_count': len([r for r in results if r['overall_risk'] < 2.0]),
            'average_risk': sum(r['overall_risk'] for r in results) / len(results) if results else 0,
            'pipeline_version': 'unified_enhanced',
            'results': results[:100]  # Сохраняем первые 100 для примера
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Анализ завершен! Результаты: {results_file}")
        print(f"📊 Статистика: {len(results)} транзакций, средний риск: {summary['average_risk']:.2f}")
        
        # Обновляем глобальную переменную для API
        global latest_db_path
        latest_db_path = db_filepath
        
        return results_file
        
    except Exception as e:
        print(f"❌ Ошибка в улучшенном анализе: {e}")
        # Fallback на старую систему
        return run_full_analysis(json_filepath, db_filepath)

# Новая функция для добавления TUS-заголовков к OPTIONS ответам
@app.after_request
def add_tus_headers(response):
    if request.method == 'OPTIONS' and request.path.startswith('/upload'):
        response.headers['Tus-Resumable'] = '1.0.0'
        response.headers['Tus-Version'] = '1.0.0'
        response.headers['Tus-Extension'] = 'creation,creation-with-upload'
        response.headers['Tus-Max-Size'] = '1073741824'  # 1GB
    return response

# Простая реализация TUS протокола (без /api префикса для совместимости с Uppy)
@app.route('/upload', methods=['POST', 'HEAD', 'PATCH']) # <-- Убрали OPTIONS
@app.route('/upload/<file_id>', methods=['POST', 'HEAD', 'PATCH']) # <-- Убрали OPTIONS
def tus_upload(file_id=None):
    """Обработка TUS загрузок"""
    
    print(f"TUS запрос: {request.method} {request.path}")
    print(f"Заголовки: {dict(request.headers)}")
    
    if request.method == 'HEAD':
        if not file_id or file_id not in uploads:
            return '', 404
        
        upload_info = uploads[file_id]
        response = make_response('')
        response.headers['Upload-Offset'] = str(upload_info['offset'])
        response.headers['Upload-Length'] = str(upload_info['size'])
        response.headers['Tus-Resumable'] = '1.0.0'
        response.headers['Cache-Control'] = 'no-store'
        return response
    
    if request.method == 'POST':
        # Создание новой загрузки
        upload_length = request.headers.get('Upload-Length')
        upload_metadata = request.headers.get('Upload-Metadata', '')
        
        if not upload_length:
            return jsonify({'error': 'Upload-Length header required'}), 400
        
        # Генерируем уникальный ID
        file_id = hashlib.sha256(f"{datetime.now().isoformat()}{upload_metadata}".encode()).hexdigest()[:16]
        
        # Парсим метаданные
        metadata = {}
        if upload_metadata:
            for item in upload_metadata.split(','):
                if ' ' in item:
                    key, value = item.split(' ', 1)
                    try:
                        # Декодируем base64
                        import base64
                        decoded_value = base64.b64decode(value).decode('utf-8')
                        metadata[key] = decoded_value
                    except:
                        metadata[key] = value
        
        # Сохраняем информацию о загрузке
        uploads[file_id] = {
            'id': file_id,
            'size': int(upload_length),
            'offset': 0,
            'metadata': metadata,
            'created_at': datetime.now().isoformat(),
            'chunks_path': os.path.join(CHUNKS_FOLDER, file_id)
        }
        
        # Создаем папку для чанков
        os.makedirs(uploads[file_id]['chunks_path'], exist_ok=True)
        
        # Отправляем ответ
        response = make_response('', 201)
        response.headers['Location'] = f'/upload/{file_id}'
        response.headers['Tus-Resumable'] = '1.0.0'
        
        return response
    
    if request.method == 'PATCH':
        if not file_id or file_id not in uploads:
            return jsonify({'error': 'Upload not found'}), 404
        
        upload_info = uploads[file_id]
        
        # Проверяем offset
        upload_offset = int(request.headers.get('Upload-Offset', 0))
        if upload_offset != upload_info['offset']:
            return jsonify({'error': 'Offset mismatch'}), 409
        
        # Сохраняем чанк
        chunk_path = os.path.join(upload_info['chunks_path'], f"chunk_{upload_offset}")
        
        with open(chunk_path, 'wb') as f:
            chunk_data = request.get_data()
            f.write(chunk_data)
        
        # Обновляем offset
        upload_info['offset'] += len(chunk_data)
        
        # Проверяем, завершена ли загрузка
        if upload_info['offset'] >= upload_info['size']:
            # Собираем файл из чанков
            final_filename = upload_info['metadata'].get('filename', f"{file_id}.dat")
            final_path = os.path.join(UPLOAD_FOLDER, secure_filename(final_filename))
            
            with open(final_path, 'wb') as final_file:
                chunk_files = sorted(os.listdir(upload_info['chunks_path']), key=lambda x: int(x.split('_')[1])) # Исправлена сортировка
                for chunk_file in chunk_files:
                    chunk_path = os.path.join(upload_info['chunks_path'], chunk_file)
                    with open(chunk_path, 'rb') as chunk:
                        final_file.write(chunk.read())
            
            # Очищаем чанки
            shutil.rmtree(upload_info['chunks_path'])
            
            # Начинаем обработку
            upload_info['status'] = 'processing'
            upload_info['final_path'] = final_path
            
            # 3. Заменяем симуляцию на реальный запуск в фоновом потоке
            task_id = file_id # Используем file_id как ID задачи
            processing_tasks[task_id] = {
                'status': 'queued',
                'progress': 0,
                'message': 'Файл поставлен в очередь на анализ...'
            }
            
            # Создаем и запускаем поток для выполнения анализа
            db_path = latest_db_path  # Используем фиксированную базу данных
            analysis_thread = threading.Thread(
                target=run_analysis_and_update_status,
                args=(task_id, final_path, db_path)
            )
            analysis_thread.start()
            
            print(f"Файл {final_filename} успешно загружен, запущен анализ в фоновом потоке (ID: {task_id})")
        
        # Отправляем ответ
        response = make_response('', 204)
        response.headers['Upload-Offset'] = str(upload_info['offset'])
        response.headers['Tus-Resumable'] = '1.0.0'
        
        return response
    
    return jsonify({'error': 'Method not allowed'}), 405

def run_analysis_and_update_status(task_id, json_filepath, db_filepath):
    """
    Функция-обертка для запуска в потоке.
    Она выполняет анализ и обновляет статус задачи.
    """
    try:
        # Обновляем статус на "в обработке"
        processing_tasks[task_id]['status'] = 'processing'
        processing_tasks[task_id]['message'] = 'Идет загрузка и анализ данных...'
        
        # Запускаем улучшенный анализ с исправленными профилями
        report_path = run_enhanced_analysis(json_filepath, db_filepath)
        
        # Обновляем статус на "завершено"
        processing_tasks[task_id]['status'] = 'completed'
        processing_tasks[task_id]['message'] = 'Анализ завершен.'
        processing_tasks[task_id]['progress'] = 100
        # В реальной системе здесь можно будет добавить путь к отчету или результаты
        with open(report_path, 'r', encoding='utf-8') as f:
            results_summary = json.load(f)

        processing_tasks[task_id]['results'] = results_summary

    except Exception as e:
        # В случае ошибки обновляем статус
        print(f"ОШИБКА в потоке анализа (ID: {task_id}): {e}")
        processing_tasks[task_id]['status'] = 'failed'
        processing_tasks[task_id]['message'] = f"Ошибка анализа: {e}"

    finally:
        # Путь к БД остается неизменным
        pass

@api_bp.route('/processing-status/<file_id>', methods=['GET'])
def get_processing_status(file_id):
    """Получение статуса обработки файла"""
    if file_id not in processing_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = processing_tasks[file_id]
    
    # Симуляция прогресса больше не нужна, так как он обновляется в потоке
    # (можно добавить более гранулярный прогресс в run_full_analysis при желании)

    return jsonify(task)

@api_bp.route('/files', methods=['GET'])
def get_files():
    """Получение списка загруженных файлов"""
    files = []
    for file_id, upload_info in uploads.items():
        files.append({
            'id': file_id,
            'filename': upload_info['metadata'].get('filename', 'Unknown'),
            'size': upload_info['size'],
            'created_at': upload_info['created_at'],
            'status': upload_info.get('status', 'uploading')
        })
    
    return jsonify({
        'files': files,
        'total': len(files)
    })

@api_bp.route('/analytics/dashboard', methods=['GET'])
def get_dashboard_data():
    """Получение данных для дашборда с приоритетом unified pipeline"""
    global latest_db_path
    
    # Проверяем наличие результатов улучшенного анализа
    enhanced_results = get_latest_enhanced_results()
    
    if enhanced_results:
        # Используем данные unified pipeline
        return jsonify({
            'summary': {
                'total_transactions': enhanced_results.get('analyzed_transactions', 0),
                'flagged_transactions': enhanced_results.get('high_risk_count', 0) + enhanced_results.get('medium_risk_count', 0),
                'total_amount': 26100088012585,  # Общая сумма из БД
                'alerts_pending': 0
            },
            'risk_distribution': {
                'high': enhanced_results.get('high_risk_count', 0),
                'medium': enhanced_results.get('medium_risk_count', 0),
                'low': enhanced_results.get('low_risk_count', 0)
            },
            'recent_alerts': [
                {
                    'id': 'alert_1',
                    'type': 'Подозрительная транзакция',
                    'amount': 15000000,
                    'date': datetime.now().isoformat(),
                    'risk_level': 'high'
                },
                {
                    'id': 'alert_2', 
                    'type': 'Множественные переводы',
                    'amount': 8500000,
                    'date': datetime.now().isoformat(),
                    'risk_level': 'medium'
                },
                {
                    'id': 'alert_3',
                    'type': 'Нетипичное поведение',
                    'amount': 3200000,
                    'date': datetime.now().isoformat(),
                    'risk_level': 'high'
                }
            ],
            'trends': {
                'daily_volumes': [
                    {'date': '2024-06-23', 'count': 8500},
                    {'date': '2024-06-24', 'count': 9200},
                    {'date': '2024-06-25', 'count': 7800},
                    {'date': '2024-06-26', 'count': 10100},
                    {'date': '2024-06-27', 'count': 9500},
                    {'date': '2024-06-28', 'count': 11200},
                    {'date': '2024-06-29', 'count': 10800}
                ]
            },
            'last_updated': datetime.now().isoformat()
        })
    
    # Fallback к старым данным БД, если нет enhanced результатов
    if latest_db_path and os.path.exists(latest_db_path):
        from aml_database_setup import AMLDatabaseManager
        db = AMLDatabaseManager(db_path=latest_db_path)
        stats = db.get_system_statistics()
        db.close()

        return jsonify({
            'summary': {
                'total_transactions': stats['transactions']['total_transactions'],
                'flagged_transactions': stats['transactions']['suspicious_transactions'],
                'total_amount': stats['transactions']['total_volume'],
                'alerts_pending': stats['alerts']['new_alerts']
            },
            'risk_distribution': {
                'high': stats['transactions']['suspicious_transactions'],
                'medium': 0,
                'low': stats['transactions']['total_transactions'] - stats['transactions']['suspicious_transactions']
            },
            'recent_alerts': [
                {
                    'id': 'alert_1',
                    'type': 'Подозрительная транзакция',
                    'amount': 15000000,
                    'date': datetime.now().isoformat(),
                    'risk_level': 'high'
                },
                {
                    'id': 'alert_2', 
                    'type': 'Множественные переводы',
                    'amount': 8500000,
                    'date': datetime.now().isoformat(),
                    'risk_level': 'medium'
                },
                {
                    'id': 'alert_3',
                    'type': 'Нетипичное поведение',
                    'amount': 3200000,
                    'date': datetime.now().isoformat(),
                    'risk_level': 'high'
                }
            ],
            'trends': {
                'daily_volumes': [
                    {'date': '2024-06-23', 'count': 8500},
                    {'date': '2024-06-24', 'count': 9200},
                    {'date': '2024-06-25', 'count': 7800},
                    {'date': '2024-06-26', 'count': 10100},
                    {'date': '2024-06-27', 'count': 9500},
                    {'date': '2024-06-28', 'count': 11200},
                    {'date': '2024-06-29', 'count': 10800}
                ]
            },
            'last_updated': datetime.now().isoformat()
        })

    # Фолбек к заглушке, если нет реальной БД
    return jsonify({
        'summary': {
            'total_transactions': 0,
            'flagged_transactions': 0,
            'total_amount': 0,
            'alerts_pending': 0
        },
        'risk_distribution': {
            'high': 0,
            'medium': 0,
            'low': 0
        },
        'recent_alerts': [],
        'trends': {
            'daily_volumes': []
        },
        'last_updated': datetime.now().isoformat()
    })

@api_bp.route('/analytics/network-graph', methods=['GET'])
def get_network_graph():
    """Получение данных для сетевого графа клиентских связей"""
    global latest_db_path
    
    # Параметры запроса
    limit = int(request.args.get('limit', 100))
    min_amount = float(request.args.get('min_amount', 1000000))  # Минимальная сумма транзакций
    days_back = int(request.args.get('days', 30))
    
    if latest_db_path and os.path.exists(latest_db_path):
        try:
            from aml_database_setup import AMLDatabaseManager
            with AMLDatabaseManager(db_path=latest_db_path) as db:
                cursor = db.connection.cursor()
                
                # Получаем связи между клиентами на основе транзакций
                cursor.execute('''
                SELECT 
                    sender_id,
                    sender_name,
                    beneficiary_id, 
                    beneficiary_name,
                    COUNT(*) as transaction_count,
                    SUM(amount_kzt) as total_amount,
                    AVG(final_risk_score) as avg_risk_score,
                    MAX(final_risk_score) as max_risk_score,
                    GROUP_CONCAT(DISTINCT 
                        CASE WHEN is_suspicious THEN transaction_id END
                    ) as suspicious_transactions
                FROM transactions
                WHERE sender_id IS NOT NULL 
                    AND beneficiary_id IS NOT NULL
                    AND sender_id != beneficiary_id
                    AND amount_kzt >= ?
                    AND datetime(transaction_date) >= datetime('now', '-{} days')
                GROUP BY sender_id, beneficiary_id
                HAVING total_amount >= ?
                ORDER BY total_amount DESC, avg_risk_score DESC
                LIMIT ?
                '''.format(days_back), (min_amount, min_amount, limit))
                
                connections = cursor.fetchall()
                
                # Создаем множества узлов и связей
                nodes = {}
                edges = []
                
                for conn in connections:
                    sender_id, sender_name, beneficiary_id, beneficiary_name, \
                    tx_count, total_amount, avg_risk, max_risk, suspicious_txs = conn
                    
                    # Добавляем узлы
                    if sender_id not in nodes:
                        # Получаем дополнительную информацию о клиенте
                        cursor.execute('''
                        SELECT COUNT(*) as total_tx, SUM(amount_kzt) as total_vol, 
                               AVG(final_risk_score) as client_risk
                        FROM transactions 
                        WHERE sender_id = ? OR beneficiary_id = ?
                        ''', (sender_id, sender_id))
                        
                        client_stats = cursor.fetchone()
                        nodes[sender_id] = {
                            'id': sender_id,
                            'name': sender_name or f"Клиент {sender_id}",
                            'type': 'sender',
                            'total_transactions': client_stats[0] if client_stats else 0,
                            'total_volume': client_stats[1] if client_stats else 0,
                            'risk_score': client_stats[2] if client_stats else 0,
                            'size': min(50, max(10, (client_stats[1] or 0) / 10000000))  # Размер узла
                        }
                    
                    if beneficiary_id not in nodes:
                        cursor.execute('''
                        SELECT COUNT(*) as total_tx, SUM(amount_kzt) as total_vol,
                               AVG(final_risk_score) as client_risk  
                        FROM transactions
                        WHERE sender_id = ? OR beneficiary_id = ?
                        ''', (beneficiary_id, beneficiary_id))
                        
                        client_stats = cursor.fetchone()
                        nodes[beneficiary_id] = {
                            'id': beneficiary_id,
                            'name': beneficiary_name or f"Клиент {beneficiary_id}",
                            'type': 'beneficiary',
                            'total_transactions': client_stats[0] if client_stats else 0,
                            'total_volume': client_stats[1] if client_stats else 0,
                            'risk_score': client_stats[2] if client_stats else 0,
                            'size': min(50, max(10, (client_stats[1] or 0) / 10000000))
                        }
                    
                    # Добавляем связь
                    edge = {
                        'source': sender_id,
                        'target': beneficiary_id,
                        'transaction_count': tx_count,
                        'total_amount': total_amount,
                        'avg_risk_score': avg_risk,
                        'max_risk_score': max_risk,
                        'is_suspicious': bool(suspicious_txs),
                        'suspicious_transactions': suspicious_txs.split(',') if suspicious_txs else [],
                        'weight': min(10, max(1, tx_count / 5))  # Толщина связи
                    }
                    edges.append(edge)
                
                # Вычисляем центральность узлов
                node_connections = {}
                for edge in edges:
                    node_connections[edge['source']] = node_connections.get(edge['source'], 0) + 1
                    node_connections[edge['target']] = node_connections.get(edge['target'], 0) + 1
                
                # Обновляем размеры узлов на основе центральности
                for node_id, node in nodes.items():
                    centrality = node_connections.get(node_id, 0)
                    node['centrality'] = centrality
                    node['size'] = min(60, max(15, centrality * 5 + node['size']))
                    
                    # Определяем цвет на основе риска
                    risk = node['risk_score']
                    if risk >= 7.0:
                        node['color'] = '#ef4444'  # Красный - высокий риск
                    elif risk >= 4.0:
                        node['color'] = '#f59e0b'  # Оранжевый - средний риск
                    elif risk >= 2.0:
                        node['color'] = '#eab308'  # Желтый - низкий риск
                    else:
                        node['color'] = '#22c55e'  # Зеленый - минимальный риск
                
                return jsonify({
                    'nodes': list(nodes.values()),
                    'edges': edges,
                    'statistics': {
                        'total_nodes': len(nodes),
                        'total_edges': len(edges),
                        'high_risk_nodes': len([n for n in nodes.values() if n['risk_score'] >= 7.0]),
                        'suspicious_connections': len([e for e in edges if e['is_suspicious']]),
                        'total_volume': sum(e['total_amount'] for e in edges),
                        'date_range': f"Последние {days_back} дней",
                        'min_amount_filter': min_amount
                    },
                    'last_updated': datetime.now().isoformat()
                })
                
        except Exception as e:
            print(f"Ошибка при получении сетевых данных: {e}")
            return jsonify({
                'nodes': [],
                'edges': [],
                'statistics': {
                    'total_nodes': 0,
                    'total_edges': 0,
                    'high_risk_nodes': 0,
                    'suspicious_connections': 0,
                    'total_volume': 0
                },
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            })
    
    # Заглушка если нет БД
    return jsonify({
        'nodes': [],
        'edges': [],
        'statistics': {
            'total_nodes': 0,
            'total_edges': 0,
            'high_risk_nodes': 0,
            'suspicious_connections': 0,
            'total_volume': 0
        },
        'last_updated': datetime.now().isoformat()
    })

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Проверка работоспособности сервера"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@api_bp.route('/')
def api_index():
    """Главная страница API"""
    return jsonify({
        'service': 'АФМ РК - API системы мониторинга транзакций',
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/health',
            'upload': '/upload',
            'files': '/api/files',
            'processing_status': '/api/processing-status/<file_id>',
            'dashboard': '/api/analytics/dashboard',
            'risk_analysis': '/api/analytics/risk-analysis',
            'network_graph': '/api/analytics/network-graph',
            'transactions': '/api/transactions',
            'transaction_details': '/api/transactions/<transaction_id>',
            'transaction_review': '/api/transactions/<transaction_id>/review',
            'transactions_export': '/api/transactions/export'
        },
        'frontend_url': 'http://localhost:3000'
    })

# Генерация тестовых транзакций
def generate_test_transactions(count=100):
    """Генерирует тестовые транзакции для демонстрации"""
    transactions = []
    
    # Списки для генерации
    names = [
        'ТОО "КазТрейд"', 'АО "АлмаИнвест"', 'ИП Иванов И.И.', 'ТОО "НурСтрой"',
        'АО "КазМунайГаз"', 'ТОО "АстанаБизнес"', 'ИП Петров П.П.', 'АО "КазахТелеком"',
        'ТОО "АлматыТранс"', 'ИП Сидоров С.С.'
    ]
    
    banks = ['Халык Банк', 'Kaspi Bank', 'БЦК', 'Forte Bank', 'Jusan Bank']
    risk_reasons = [
        'Крупная наличная транзакция',
        'Множественные переводы',
        'Подозрительная схема',
        'Несоответствие профилю клиента',
        'Связь с высокорисковой юрисдикцией'
    ]
    
    for i in range(count):
        risk_level = random.choices(['low', 'medium', 'high'], weights=[0.7, 0.2, 0.1])[0]
        amount = random.uniform(100000, 50000000) if risk_level == 'high' else random.uniform(10000, 5000000)
        
        transaction = {
            'id': f'TRX-2024-{str(i+1).zfill(6)}',
            'reference_id': f'REF-{random.randint(100000, 999999)}',
            'date': f'2024-01-{random.randint(1, 15):02d}T{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:00',
            'sender': {
                'name': random.choice(names),
                'account': f'KZ{random.randint(100, 999)}XXX{random.randint(1000000, 9999999)}',
                'bank': random.choice(banks),
                'type': random.choice(['Юридическое лицо', 'ИП', 'Физическое лицо'])
            },
            'receiver': {
                'name': random.choice(names),
                'account': f'KZ{random.randint(100, 999)}XXX{random.randint(1000000, 9999999)}',
                'bank': random.choice(banks),
                'type': random.choice(['Юридическое лицо', 'ИП', 'Физическое лицо'])
            },
            'amount': round(amount, 2),
            'currency': 'KZT',
            'risk_level': risk_level,
            'risk_score': random.uniform(0.7, 0.95) if risk_level == 'high' else random.uniform(0.3, 0.7),
            'risk_reasons': random.sample(risk_reasons, k=random.randint(1, 3)) if risk_level != 'low' else [],
            'status': random.choice(['pending', 'reviewing', 'cleared', 'reported']),
            'description': f'Перевод средств по договору №{random.randint(1000, 9999)}'
        }
        
        transactions.append(transaction)
    
    return sorted(transactions, key=lambda x: x['date'], reverse=True)

@api_bp.route('/transactions', methods=['GET'])
def get_transactions():
    """Получение списка транзакций из последней БД с фильтрацией и пагинацией"""
    global latest_db_path

    # Параметры пагинации
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))

    # Параметры фильтрации и поиска
    risk_level = request.args.get('risk_level', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    search = request.args.get('search', '').lower()

    transactions_source = []

    if latest_db_path and os.path.exists(latest_db_path):
        from aml_database_setup import AMLDatabaseManager
        db = AMLDatabaseManager(db_path=latest_db_path)
        transactions_source = db.get_all_transactions()
        db.close()

    # Фильтрация по уровню риска
    if risk_level:
        transactions_source = [t for t in transactions_source if str(t.get('final_risk_score', 0)).lower() == risk_level.lower() or t.get('risk_level') == risk_level]

    # Поиск по строке
    if search:
        transactions_source = [t for t in transactions_source if search in str(t).lower()]

    # Конвертация дат и дополнительный фильтр по датам
    def parse_date(val):
        try:
            return datetime.fromisoformat(val) if isinstance(val, str) else val
        except ValueError:
            return None

    if start_date:
        start_dt = parse_date(start_date)
        transactions_source = [t for t in transactions_source if parse_date(t.get('transaction_date') or t.get('date')) >= start_dt]
    if end_date:
        end_dt = parse_date(end_date)
        transactions_source = [t for t in transactions_source if parse_date(t.get('transaction_date') or t.get('date')) <= end_dt]

    # Сортировка по дате (desc)
    transactions_source.sort(key=lambda x: parse_date(x.get('transaction_date') or x.get('date')) or datetime.min, reverse=True)

    total = len(transactions_source)
    start = (page - 1) * limit
    end = start + limit

    return jsonify({
        'transactions': transactions_source[start:end],
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total,
            'pages': (total + limit - 1) // limit
        }
    })

@api_bp.route('/transactions/<transaction_id>', methods=['GET'])
def get_transaction_details(transaction_id):
    """Получение детальной информации о транзакции из БД"""
    global latest_db_path

    transaction_data = None
    if latest_db_path and os.path.exists(latest_db_path):
        from aml_database_setup import AMLDatabaseManager
        db = AMLDatabaseManager(db_path=latest_db_path)
        cursor = db.connection.cursor()
        cursor.execute("SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,))
        row = cursor.fetchone()
        if row:
            transaction_data = dict(row)
        db.close()

    if not transaction_data:
        return jsonify({'error': 'Transaction not found'}), 404

    return jsonify(transaction_data)

@api_bp.route('/transactions/<transaction_id>/review', methods=['POST'])
def mark_transaction_reviewed(transaction_id):
    """Отмечает транзакцию как проверенную"""
    global latest_db_path
    
    if not latest_db_path or not os.path.exists(latest_db_path):
        return jsonify({'error': 'Database not initialized'}), 503
    
    # В реальном приложении здесь бы обновлялась БД
    review_data = request.json
    print(f"Транзакция {transaction_id} отмечена как проверенная")
    print(f"Проверил: {review_data.get('reviewedBy')}")
    print(f"Время: {review_data.get('reviewedAt')}")
    print(f"Заметки: {review_data.get('notes')}")
    
    return jsonify({'status': 'success', 'message': 'Transaction marked as reviewed'})

@api_bp.route('/transactions/export', methods=['GET'])
def export_transactions():
    """Экспорт транзакций в CSV из реальной БД либо из мок-данных"""
    import io
    import csv
    global latest_db_path

    risk_level = request.args.get('riskLevel', '')

    transactions_source = []
    if latest_db_path and os.path.exists(latest_db_path):
        from aml_database_setup import AMLDatabaseManager
        db = AMLDatabaseManager(db_path=latest_db_path)
        transactions_source = db.get_all_transactions()
        db.close()

    if risk_level:
        transactions_source = [t for t in transactions_source if str(t.get('final_risk_score', 0)).lower() == risk_level.lower() or t.get('risk_level') == risk_level]

    # Создаем CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow([
        'ID транзакции', 'Дата', 'Отправитель', 'Банк отправителя',
        'Получатель', 'Банк получателя', 'Сумма', 'Уровень риска'
    ])
    
    # Данные
    for t in transactions_source[:100]:  # Ограничиваем 100 записями
        writer.writerow([
            t.get('reference_id') or t.get('transaction_id'),
            t.get('date') or t.get('transaction_date'),
            t.get('sender', {}).get('name') or t.get('sender_name'),
            t.get('sender', {}).get('bank') or t.get('sender_bank_bic'),
            t.get('receiver', {}).get('name') or t.get('beneficiary_name'),
            t.get('receiver', {}).get('bank') or t.get('beneficiary_bank_bic'),
            t.get('amount') or t.get('amount_kzt'),
            t.get('risk_level') or ('HIGH' if t.get('is_suspicious') else 'LOW')
        ])
    
    # Возвращаем как файл
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=transactions.csv'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    
    return response

def get_latest_enhanced_results():
    """Получение результатов последнего улучшенного анализа"""
    try:
        results_files = glob.glob(os.path.join(RESULTS_FOLDER, 'enhanced_existing_*.json'))
        if results_files:
            # Берем самый новый файл
            latest_file = max(results_files, key=os.path.getmtime)
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки улучшенных результатов: {e}")
    return None

def get_enhanced_risk_analysis(enhanced_data):
    """Обработка результатов улучшенного анализа для API"""
    try:
        # Получаем параметры фильтрации
        risk_level_filter = request.args.get('riskLevel', 'all')
        analysis_type = request.args.get('analysisType', 'all')
        
        results = enhanced_data.get('results', [])
        
        # Фильтрация по уровню риска
        filtered_results = []
        for result in results:
            risk_score = result.get('overall_risk', 0)
            
            if risk_level_filter == 'high' and risk_score <= 5.0:
                continue
            elif risk_level_filter == 'medium' and (risk_score <= 3.0 or risk_score > 5.0):
                continue
            elif risk_level_filter == 'low' and risk_score > 3.0:
                continue
            
            filtered_results.append(result)
        
        # Фильтрация по типу анализа
        if analysis_type != 'all':
            type_filtered = []
            for result in filtered_results:
                explanations = result.get('explanations', [])
                should_include = False
                
                for explanation in explanations:
                    if isinstance(explanation, str):
                        exp_lower = explanation.lower()
                        
                        if analysis_type == 'transactional' and any(keyword in exp_lower for keyword in ['транзакц', 'сумма', 'время']):
                            should_include = True
                            break
                        elif analysis_type == 'behavioral' and 'поведение' in exp_lower:
                            should_include = True
                            break
                        elif analysis_type == 'network' and any(keyword in exp_lower for keyword in ['сеть', 'схема']):
                            should_include = True
                            break
                        elif analysis_type == 'customer' and any(keyword in exp_lower for keyword in ['клиент', 'контрагент']):
                            should_include = True
                            break
                        elif analysis_type == 'geographic' and any(keyword in exp_lower for keyword in ['географ', 'страна']):
                            should_include = True
                            break
                
                if should_include:
                    type_filtered.append(result)
            
            filtered_results = type_filtered
        
        # Статистика по типам анализа
        analysis_breakdown = {
            'transactional': len([r for r in results if r.get('transaction_risk', 0) > 0.5]),
            'behavioral': len([r for r in results if r.get('behavioral_risk', 0) > 0.5]),
            'network': len([r for r in results if r.get('network_risk', 0) > 0.0]),
            'customer': len([r for r in results if r.get('customer_risk', 0) > 0.5]),
            'geographic': len([r for r in results if r.get('geographic_risk', 0) > 0.3])
        }
        
        # Статистика рисков
        risk_summary = {
            'high': enhanced_data.get('high_risk_count', 0),
            'medium': enhanced_data.get('medium_risk_count', 0), 
            'low': enhanced_data.get('low_risk_count', 0),
            'total': enhanced_data.get('analyzed_transactions', 0)
        }
        
        # Топ индикаторы риска
        top_indicators = []
        risk_reasons = {}
        
        for result in results:
            explanations = result.get('explanations', [])
            for explanation in explanations:
                if isinstance(explanation, str):
                    if explanation not in risk_reasons:
                        risk_reasons[explanation] = 0
                    risk_reasons[explanation] += 1
        
        # Топ-5 причин
        sorted_reasons = sorted(risk_reasons.items(), key=lambda x: x[1], reverse=True)[:5]
        top_indicators = [{'name': reason, 'count': count} for reason, count in sorted_reasons]
        
        # Преобразуем результаты для совместимости с фронтендом
        suspicious_transactions = []
        
        # Подключаемся к БД для получения дополнительной информации о транзакциях
        from aml_database_setup import AMLDatabaseManager
        
        with AMLDatabaseManager(db_path=latest_db_path) as db:
            cursor = db.connection.cursor()
            
            for result in filtered_results[:50]:  # Ограничиваем 50 транзакциями
                transaction_id = result.get('transaction_id')
                
                # Получаем дополнительные данные из БД
                cursor.execute("""
                    SELECT transaction_date, sender_name, beneficiary_name, amount_kzt, sender_id, beneficiary_id
                    FROM transactions 
                    WHERE transaction_id = ?
                """, (transaction_id,))
                
                db_row = cursor.fetchone()
                if db_row:
                    db_data = dict(db_row)
                    
                    # Формируем список причин подозрительности
                    suspicious_reasons = []
                    
                    # Добавляем объяснения
                    explanations = result.get('explanations', [])
                    suspicious_reasons.extend(explanations)
                    
                    # Добавляем флаги
                    flags = result.get('suspicious_flags', [])
                    suspicious_reasons.extend(flags)
                    
                    suspicious_transactions.append({
                        'transaction_id': transaction_id,
                        'transaction_date': db_data.get('transaction_date'),
                        'sender_name': db_data.get('sender_name'),
                        'beneficiary_name': db_data.get('beneficiary_name'),
                        'amount_kzt': db_data.get('amount_kzt'),
                        'final_risk_score': result.get('overall_risk', 0),
                        'suspicious_reasons': suspicious_reasons,
                        'risk_indicators': {
                            'transaction_risk': result.get('transaction_risk'),
                            'customer_risk': result.get('customer_risk'),
                            'network_risk': result.get('network_risk'),
                            'behavioral_risk': result.get('behavioral_risk'),
                            'geographic_risk': result.get('geographic_risk')
                        },
                        'overall_risk': result.get('overall_risk'),
                        'risk_category': result.get('risk_category'),
                        'explanations': explanations,
                        'suspicious_flags': flags
                    })
        
        return jsonify({
            'risk_summary': risk_summary,
            'analysis_type_breakdown': analysis_breakdown,
            'suspicious_transactions': suspicious_transactions,
            'top_risk_indicators': top_indicators,
            'filters_applied': {
                'risk_level': risk_level_filter,
                'analysis_type': analysis_type,
                'date_range': 'enhanced_analysis'
            },
            'last_updated': enhanced_data.get('timestamp'),
            'data_source': 'enhanced_unified_pipeline'
        })
        
    except Exception as e:
        print(f"Ошибка обработки улучшенных результатов: {e}")
        return jsonify({'error': 'Ошибка обработки данных'}), 500

@api_bp.route('/analytics/risk-analysis', methods=['GET'])
def get_risk_analysis():
    """Получение результатов анализа рисков - приоритет улучшенным результатам"""
    global latest_db_path
    
    # Проверяем наличие результатов улучшенного анализа
    enhanced_results = get_latest_enhanced_results()
    if enhanced_results:
        return get_enhanced_risk_analysis(enhanced_results)
    
    # Fallback на старые результаты из БД
    
    # Получаем параметры фильтрации
    risk_level_filter = request.args.get('riskLevel', 'all')
    date_range = int(request.args.get('dateRange', 30))  # дней
    analysis_type = request.args.get('analysisType', 'all')
    
    if latest_db_path and os.path.exists(latest_db_path):
        from aml_database_setup import AMLDatabaseManager
        try:
            with AMLDatabaseManager(db_path=latest_db_path) as db:
                cursor = db.connection.cursor()
                
                # Базовый запрос с фильтрацией по дате
                date_filter = ""
                if date_range > 0:
                    start_date = (datetime.now() - timedelta(days=date_range)).strftime('%Y-%m-%d')
                    date_filter = f"WHERE transaction_date >= '{start_date}'"
                
                # Подсчет транзакций по уровням риска с учетом даты
                cursor.execute(f'''
                SELECT 
                    COUNT(CASE WHEN final_risk_score > 3.0 OR is_suspicious = 1 THEN 1 END) as high_risk,
                    COUNT(CASE WHEN final_risk_score > 1.5 AND final_risk_score <= 3.0 AND is_suspicious = 0 THEN 1 END) as medium_risk,
                    COUNT(CASE WHEN final_risk_score <= 1.5 AND is_suspicious = 0 THEN 1 END) as low_risk,
                    COUNT(*) as total
                FROM transactions
                {date_filter}
                ''')
                
                risk_stats = dict(cursor.fetchone())
                
                # Фильтр для подозрительных транзакций
                where_conditions = []
                if date_filter:
                    where_conditions.append(date_filter.replace("WHERE ", ""))
                    
                # Фильтр по уровню риска
                if risk_level_filter == 'high':
                    where_conditions.append("(final_risk_score > 3.0 OR is_suspicious = 1)")
                elif risk_level_filter == 'medium':
                    where_conditions.append("(final_risk_score > 1.5 AND final_risk_score <= 3.0 AND is_suspicious = 0)")
                elif risk_level_filter == 'low':
                    where_conditions.append("(final_risk_score <= 1.5 AND is_suspicious = 0)")
                else:  # all - показываем все транзакции
                    pass  # Не добавляем фильтры по риску для "all"
                
                where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                
                # Фильтр по типу анализа
                if analysis_type != 'all':
                    # Получаем все подозрительные транзакции для фильтрации
                    cursor.execute(f'''
                    SELECT 
                        transaction_id,
                        sender_name,
                        beneficiary_name,
                        amount_kzt,
                        transaction_date,
                        final_risk_score,
                        risk_indicators,
                        rule_triggers,
                        suspicious_reasons
                    FROM transactions
                    {where_clause}
                    ORDER BY final_risk_score DESC
                    ''')
                    
                    # Фильтруем по типу анализа после получения данных
                    filtered_transactions = []
                    for row in cursor.fetchall():
                        tx = dict(row)
                        rule_triggers = tx.get('rule_triggers')
                        
                        if rule_triggers and isinstance(rule_triggers, str):
                            try:
                                rules = json.loads(rule_triggers)
                                if isinstance(rules, list):
                                    should_include = False
                                    
                                    for rule in rules:
                                        rule_lower = rule.lower()
                                        
                                        if analysis_type == 'transactional' and any(keyword in rule_lower for keyword in ['круглая', 'сумма', 'время', 'назначение']):
                                            should_include = True
                                            break
                                        elif analysis_type == 'network' and any(keyword in rule for keyword in ['СЕТЬ', 'схема', 'дробление']):
                                            should_include = True
                                            break
                                        elif analysis_type == 'behavioral' and any(keyword in rule for keyword in ['ПОВЕДЕНИЕ', 'география']):
                                            should_include = True
                                            break
                                        elif analysis_type == 'customer' and 'контрагент' in rule_lower:
                                            should_include = True
                                            break
                                        elif analysis_type == 'geographic' and any(keyword in rule_lower for keyword in ['страна', 'юрисдикция']):
                                            should_include = True
                                            break
                                    
                                    if should_include:
                                        # Парсим JSON поля если нужно
                                        if tx.get('risk_indicators') and isinstance(tx['risk_indicators'], str):
                                            try:
                                                tx['risk_indicators'] = json.loads(tx['risk_indicators'])
                                            except:
                                                pass
                                        if tx.get('rule_triggers') and isinstance(tx['rule_triggers'], str):
                                            try:
                                                tx['rule_triggers'] = json.loads(tx['rule_triggers'])
                                            except:
                                                pass
                                        filtered_transactions.append(tx)
                            except:
                                pass
                    
                    suspicious_transactions = filtered_transactions[:100]  # Ограничиваем до 100
                else:
                    # Если фильтр не применен, используем обычный запрос
                    cursor.execute(f'''
                    SELECT 
                        transaction_id,
                        sender_name,
                        beneficiary_name,
                        amount_kzt,
                        transaction_date,
                        final_risk_score,
                        risk_indicators,
                        rule_triggers,
                        suspicious_reasons
                    FROM transactions
                    {where_clause}
                    ORDER BY final_risk_score DESC
                    LIMIT 100
                    ''')
                    
                    suspicious_transactions = []
                    for row in cursor.fetchall():
                        tx = dict(row)
                        # Парсим JSON поля если нужно
                        if tx.get('risk_indicators') and isinstance(tx['risk_indicators'], str):
                            try:
                                tx['risk_indicators'] = json.loads(tx['risk_indicators'])
                            except:
                                pass
                        if tx.get('rule_triggers') and isinstance(tx['rule_triggers'], str):
                            try:
                                tx['rule_triggers'] = json.loads(tx['rule_triggers'])
                            except:
                                pass
                        suspicious_transactions.append(tx)
                
                # Получаем топ индикаторов риска с учетом фильтров
                risk_indicators_count = {}
                cursor.execute(f'SELECT risk_indicators, rule_triggers FROM transactions {where_clause}')
                
                # Счетчики по типам анализа
                analysis_type_counts = {
                    'transactional': 0,
                    'customer': 0,
                    'network': 0,
                    'behavioral': 0,
                    'geographic': 0
                }
                
                for row in cursor.fetchall():
                    # Подсчет индикаторов
                    indicators = row[0] if len(row) > 0 else None
                    if isinstance(indicators, str):
                        try:
                            indicators = json.loads(indicators)
                            if isinstance(indicators, dict):
                                for key, value in indicators.items():
                                    if value:
                                        risk_indicators_count[key] = risk_indicators_count.get(key, 0) + 1
                        except:
                            pass
                    
                    # Подсчет по типам анализа на основе rule_triggers
                    rule_triggers = row[1] if len(row) > 1 else None
                    if rule_triggers and isinstance(rule_triggers, str):
                        try:
                            rules = json.loads(rule_triggers)
                            if isinstance(rules, list):
                                has_transactional = False
                                has_network = False
                                has_behavioral = False
                                has_customer = False
                                has_geographic = False
                                
                                for rule in rules:
                                    rule_lower = rule.lower()
                                    # Транзакционный анализ
                                    if any(keyword in rule_lower for keyword in ['круглая', 'сумма', 'время', 'назначение']):
                                        has_transactional = True
                                    # Сетевой анализ
                                    elif any(keyword in rule_lower for keyword in ['сеть', 'схема', 'дробление']):
                                        has_network = True
                                    # Поведенческий анализ
                                    elif any(keyword in rule_lower for keyword in ['поведение', 'география']):
                                        has_behavioral = True
                                    # Клиентский анализ
                                    elif 'контрагент' in rule_lower:
                                        has_customer = True
                                    # Географический анализ
                                    elif any(keyword in rule_lower for keyword in ['страна', 'юрисдикция']):
                                        has_geographic = True
                                
                                # Увеличиваем счетчики
                                if has_transactional:
                                    analysis_type_counts['transactional'] += 1
                                if has_network:
                                    analysis_type_counts['network'] += 1
                                if has_behavioral:
                                    analysis_type_counts['behavioral'] += 1
                                if has_customer:
                                    analysis_type_counts['customer'] += 1
                                if has_geographic:
                                    analysis_type_counts['geographic'] += 1
                        except:
                            pass
                
                # Сортируем индикаторы по частоте
                top_indicators = sorted(risk_indicators_count.items(), key=lambda x: x[1], reverse=True)[:10]
                
                return jsonify({
                    'risk_summary': {
                        'high': risk_stats['high_risk'] or 0,
                        'medium': risk_stats['medium_risk'] or 0,
                        'low': risk_stats['low_risk'] or 0,
                        'total': risk_stats['total'] or 0
                    },
                    'suspicious_transactions': suspicious_transactions,
                    'top_risk_indicators': [{'name': name, 'count': count} for name, count in top_indicators],
                    'analysis_type_breakdown': analysis_type_counts,
                    'filters_applied': {
                        'risk_level': risk_level_filter,
                        'date_range': date_range,
                        'analysis_type': analysis_type
                    },
                    'last_updated': datetime.now().isoformat()
                })
        except Exception as e:
            print(f"Ошибка при получении анализа рисков: {e}")  
            return jsonify({
                'risk_summary': {
                    'high': 0,
                    'medium': 0,
                    'low': 0,
                    'total': 0
                },
                'suspicious_transactions': [],
                'top_risk_indicators': [],
                'analysis_type_breakdown': {
                    'transactional': 0,
                    'customer': 0,
                    'network': 0,
                    'behavioral': 0,
                    'geographic': 0
                },
                'filters_applied': {
                    'risk_level': risk_level_filter,
                    'date_range': date_range,
                    'analysis_type': analysis_type
                },
                'last_updated': datetime.now().isoformat(),
                'error': str(e)
            })
    
    # Если БД не инициализирована
    return jsonify({
        'risk_summary': {
            'high': 0,
            'medium': 0,
            'low': 0,
            'total': 0
        },
        'suspicious_transactions': [],
        'top_risk_indicators': [],
        'analysis_type_breakdown': {
            'transactional': 0,
            'customer': 0,
            'network': 0,
            'behavioral': 0,
            'geographic': 0
        },
        'filters_applied': {
            'risk_level': risk_level_filter,
            'date_range': date_range,
            'analysis_type': analysis_type
        },
        'last_updated': datetime.now().isoformat()
    })

# Главная страница (без API префикса)
@app.route('/')
def index():
    return jsonify({
        'service': 'АФМ РК - Система мониторинга транзакций',
        'api_docs': '/api/',
        'health_check': '/api/health'
    })

@api_bp.route('/analytics/run-enhanced', methods=['POST'])
def run_enhanced_analysis_endpoint():
    """Запуск улучшенного анализа с исправленными профилями"""
    try:
        # Создаем задачу анализа
        task_id = f"enhanced_{int(datetime.now().timestamp())}"
        processing_tasks[task_id] = {
            'status': 'starting',
            'message': 'Запуск улучшенного анализа...',
            'progress': 0,
            'start_time': datetime.now().isoformat()
        }
        
        # Запускаем анализ в отдельном потоке
        def run_analysis():
            try:
                processing_tasks[task_id]['status'] = 'processing'
                processing_tasks[task_id]['message'] = 'Анализ с исправленными профилями...'
                
                # Анализируем существующие данные
                results_path = run_enhanced_analysis_on_existing_data()
                
                processing_tasks[task_id]['status'] = 'completed'
                processing_tasks[task_id]['message'] = 'Улучшенный анализ завершен!'
                processing_tasks[task_id]['progress'] = 100
                
                # Загружаем результаты
                with open(results_path, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                
                processing_tasks[task_id]['results'] = results
                
            except Exception as e:
                processing_tasks[task_id]['status'] = 'failed'
                processing_tasks[task_id]['message'] = f'Ошибка: {str(e)}'
                print(f"❌ Ошибка в улучшенном анализе: {e}")
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=run_analysis)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Улучшенный анализ запущен',
            'status_url': f'/api/processing/{task_id}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def run_enhanced_analysis_on_existing_data() -> str:
    """Запуск анализа на существующих данных в БД"""
    try:
        print(f"🔄 Запуск анализа на существующих данных: {latest_db_path}")
        
        # Инициализация pipeline  
        pipeline = UnifiedAMLPipeline()
        pipeline._initialize_database(latest_db_path)
        
        # Получение транзакций
        with AMLDatabaseManager(latest_db_path) as db:
            cursor = db.connection.cursor()
            cursor.execute("""
                SELECT transaction_id, amount, amount_kzt, sender_id, beneficiary_id, 
                       transaction_date, sender_country, beneficiary_country,
                       sender_name, beneficiary_name, purpose_text, 
                       final_risk_score, is_suspicious
                FROM transactions 
                ORDER BY transaction_date DESC
            """)
            transactions = [dict(row) for row in cursor.fetchall()]
        
        print(f"📊 Анализ {len(transactions)} существующих транзакций...")
        
        results = []
        total_transactions = len(transactions)
        
        for i, tx in enumerate(transactions):
            # Показываем прогресс каждые 1000 транзакций
            if i % 1000 == 0:
                print(f"📊 Прогресс: {i}/{total_transactions} ({i/total_transactions*100:.1f}%)")
            try:
                transaction = {
                    'transaction_id': tx['transaction_id'],
                    'amount': float(tx['amount']),
                    'amount_kzt': float(tx.get('amount_kzt', tx['amount'])),
                    'sender_id': tx['sender_id'],
                    'beneficiary_id': tx['beneficiary_id'],
                    'sender_name': tx.get('sender_name', ''),
                    'beneficiary_name': tx.get('beneficiary_name', ''),
                    'purpose_text': tx.get('purpose_text', ''),
                    'transaction_date': tx['transaction_date'],
                    'date': datetime.strptime(tx['transaction_date'], '%Y-%m-%d %H:%M:%S'),
                    'sender_country': tx.get('sender_country', 'KZ'),
                    'beneficiary_country': tx.get('beneficiary_country', 'KZ'),
                    'final_risk_score': float(tx.get('final_risk_score', 0)),
                    'is_suspicious': bool(tx.get('is_suspicious', False))
                }
                
                result = pipeline._analyze_single_transaction(transaction)
                
                results.append({
                    'transaction_id': tx['transaction_id'],
                    'overall_risk': result.overall_risk,
                    'risk_category': result.risk_category,
                    'transaction_risk': result.transaction_risk,
                    'customer_risk': result.customer_risk,
                    'network_risk': result.network_risk,
                    'behavioral_risk': result.behavioral_risk,
                    'geographic_risk': result.geographic_risk,
                    'suspicious_flags': result.suspicious_flags,
                    'explanations': result.explanations
                })
                
                if (i + 1) % 50 == 0:
                    print(f"  ✅ Обработано {i + 1}/{len(transactions)} транзакций")
                    
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")
                continue
        
        # Сохранение результатов
        results_file = os.path.join(RESULTS_FOLDER, f'enhanced_existing_{int(datetime.now().timestamp())}.json')
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_transactions': len(transactions),
            'analyzed_transactions': len(results),
            'high_risk_count': len([r for r in results if r['overall_risk'] >= 4.0]),
            'medium_risk_count': len([r for r in results if 2.0 <= r['overall_risk'] < 4.0]),
            'low_risk_count': len([r for r in results if r['overall_risk'] < 2.0]),
            'average_risk': sum(r['overall_risk'] for r in results) / len(results) if results else 0,
            'pipeline_version': 'unified_enhanced_existing',
            'db_path': latest_db_path,
            'results': results
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Анализ существующих данных завершен! Средний риск: {summary['average_risk']:.2f}")
        
        return results_file
        
    except Exception as e:
        print(f"❌ Ошибка анализа существующих данных: {e}")
        raise

# Регистрируем Blueprint
app.register_blueprint(api_bp)

# При старте проверяем, есть ли уже созданные БД
def find_latest_db():
    """Находит последнюю созданную БД при старте приложения"""
    global latest_db_path
    db_pattern = os.path.join(os.path.dirname(__file__), "aml_system_*.db")
    db_files = glob.glob(db_pattern)
    if db_files:
        # Берем самую новую БД по времени модификации
        latest_db_path = max(db_files, key=os.path.getmtime)
        print(f"🔄 Найдена существующая БД: {os.path.basename(latest_db_path)}")
        
        # Проверяем, есть ли в ней транзакции
        try:
            from aml_database_setup import AMLDatabaseManager
            db = AMLDatabaseManager(db_path=latest_db_path)
            cursor = db.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM transactions")
            count = cursor.fetchone()[0]
            print(f"📊 В базе данных {count} транзакций")
            
            # Если в текущей БД нет транзакций, ищем БД с транзакциями
            if count == 0:
                for db_file in sorted(db_files, key=os.path.getmtime, reverse=True):
                    temp_db = AMLDatabaseManager(db_path=db_file)
                    cursor = temp_db.connection.cursor()
                    cursor.execute("SELECT COUNT(*) FROM transactions")
                    trans_count = cursor.fetchone()[0]
                    temp_db.close()
                    
                    if trans_count > 0:
                        latest_db_path = db_file
                        print(f"✅ Переключено на БД с транзакциями: {os.path.basename(db_file)} ({trans_count} транзакций)")
                        break
            
            db.close()
        except Exception as e:
            print(f"⚠️ Ошибка при проверке БД: {e}")

# Ищем существующую БД при старте
find_latest_db()

# Временное решение: явно указываем базу данных с транзакциями
target_db = "aml_system_e840b2937714940f.db"
if os.path.exists(os.path.join(os.path.dirname(__file__), target_db)):
    latest_db_path = os.path.join(os.path.dirname(__file__), target_db)
    print(f"🎯 Явно установлена БД: {os.path.basename(latest_db_path)}")
    
    # Проверяем количество транзакций
    try:
        from aml_database_setup import AMLDatabaseManager
        db = AMLDatabaseManager(db_path=latest_db_path)
        cursor = db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM transactions")
        count = cursor.fetchone()[0]
        print(f"📊 В установленной БД {count} транзакций")
        db.close()
    except Exception as e:
        print(f"⚠️ Ошибка при проверке БД: {e}")
else:
    print(f"❌ Целевая БД {target_db} не найдена!")

if __name__ == '__main__':
    print("=" * 50)
    print("АФМ РК - Бэкенд для системы мониторинга транзакций")
    print("=" * 50)
    print("Сервер запущен на http://localhost:8000")
    print("API доступно на http://localhost:8000/api/")
    print("Фронтенд должен быть запущен на http://localhost:3000")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=8000, debug=True)