import os
import json
from flask import Flask, request, jsonify, send_file, make_response, Blueprint
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
import hashlib
import shutil
import random  # Для генерации тестовых данных
import threading # <-- 1. Импортируем threading
import sys
import glob

# Добавляем корневую папку в путь для импорта наших модулей
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aml_integration_system import run_full_analysis # <-- 2. Импортируем нашу функцию

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
latest_db_path = None  # будет обновляться после завершения анализа

test_transactions = []  # Для хранения тестовых транзакций

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
            db_path = os.path.join(os.path.dirname(__file__), f"aml_system_{task_id}.db") # БД в папке aml-backend
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
        
        # Запускаем тяжелую задачу
        report_path = run_full_analysis(json_filepath, db_filepath)
        
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
        # === НОВОЕ: сохраняем путь к последней успешно обработанной БД ===
        global latest_db_path
        latest_db_path = db_filepath

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
    """Получение данных для дашборда из реальной БД (если доступна)"""
    global latest_db_path
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
                'high': stats['transactions']['suspicious_transactions'],  # упрощённо
                'medium': 0,
                'low': stats['transactions']['total_transactions'] - stats['transactions']['suspicious_transactions']
            },
            'recent_alerts': [],  # TODO: добавить реальный список
            'trends': {},
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
        'trends': {},
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

@api_bp.route('/analytics/risk-analysis', methods=['GET'])
def get_risk_analysis():
    """Получение результатов анализа рисков из последней БД"""
    global latest_db_path
    
    if latest_db_path and os.path.exists(latest_db_path):
        from aml_database_setup import AMLDatabaseManager
        db = AMLDatabaseManager(db_path=latest_db_path)
        
        # Получаем статистику по рискам
        cursor = db.connection.cursor()
        
        # Подсчет транзакций по уровням риска
        cursor.execute('''
        SELECT 
            COUNT(CASE WHEN final_risk_score > 7 OR is_suspicious = 1 THEN 1 END) as high_risk,
            COUNT(CASE WHEN final_risk_score > 4 AND final_risk_score <= 7 AND is_suspicious = 0 THEN 1 END) as medium_risk,
            COUNT(CASE WHEN final_risk_score <= 4 AND is_suspicious = 0 THEN 1 END) as low_risk,
            COUNT(*) as total
        FROM transactions
        ''')
        
        risk_stats = dict(cursor.fetchone())
        
        # Получаем подозрительные транзакции
        cursor.execute('''
        SELECT 
            transaction_id,
            sender_name,
            beneficiary_name,
            amount_kzt,
            transaction_date,
            final_risk_score,
            risk_indicators,
            rule_triggers
        FROM transactions
        WHERE is_suspicious = 1 OR final_risk_score > 7
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
        
        # Получаем топ индикаторов риска
        risk_indicators_count = {}
        cursor.execute('SELECT risk_indicators FROM transactions WHERE risk_indicators IS NOT NULL')
        for row in cursor.fetchall():
            indicators = row['risk_indicators']
            if isinstance(indicators, str):
                try:
                    indicators = json.loads(indicators)
                    if isinstance(indicators, dict):
                        for key, value in indicators.items():
                            if value:
                                risk_indicators_count[key] = risk_indicators_count.get(key, 0) + 1
                except:
                    pass
        
        # Сортируем индикаторы по частоте
        top_indicators = sorted(risk_indicators_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        db.close()
        
        return jsonify({
            'risk_summary': {
                'high': risk_stats['high_risk'] or 0,
                'medium': risk_stats['medium_risk'] or 0,
                'low': risk_stats['low_risk'] or 0,
                'total': risk_stats['total'] or 0
            },
            'suspicious_transactions': suspicious_transactions,
            'top_risk_indicators': [{'name': name, 'count': count} for name, count in top_indicators],
            'last_updated': datetime.now().isoformat()
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
if os.path.exists(os.path.join(os.path.dirname(__file__), "aml_system_e840b2937714940f.db")):
    latest_db_path = os.path.join(os.path.dirname(__file__), "aml_system_e840b2937714940f.db")
    print(f"🎯 Явно установлена БД: {os.path.basename(latest_db_path)}")

if __name__ == '__main__':
    print("=" * 50)
    print("АФМ РК - Бэкенд для системы мониторинга транзакций")
    print("=" * 50)
    print("Сервер запущен на http://localhost:8000")
    print("API доступно на http://localhost:8000/api/")
    print("Фронтенд должен быть запущен на http://localhost:3000")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=8000, debug=True)