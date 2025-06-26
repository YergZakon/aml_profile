# Визуализация архитектуры системы AML
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

# Создаем фигуру
fig, ax = plt.subplots(1, 1, figsize=(14, 10))

# Цвета для компонентов
colors = {
    'input': '#E8F4F8',
    'profiles': '#D4E6F1',
    'integration': '#AED6F1',
    'output': '#85C1E2',
    'flow': '#3498DB'
}

# 1. ВХОДНЫЕ ДАННЫЕ
input_box = FancyBboxPatch((0.5, 8), 2.5, 1.2, 
                          boxstyle="round,pad=0.1",
                          facecolor=colors['input'],
                          edgecolor='black',
                          linewidth=2)
ax.add_patch(input_box)
ax.text(1.75, 8.6, 'ТРАНЗАКЦИЯ', ha='center', va='center', fontsize=12, fontweight='bold')
ax.text(1.75, 8.3, 'от банка', ha='center', va='center', fontsize=10)

# 2. ПРОФИЛИ (5 компонентов)
profiles = [
    {'name': 'Транзакционный\nпрофиль', 'x': 0, 'y': 5.5, 'desc': '• Пороги АФМ\n• Коды операций\n• Правила'},
    {'name': 'Клиентский\nпрофиль', 'x': 3, 'y': 5.5, 'desc': '• История\n• Риск-скор\n• Паттерны'},
    {'name': 'Географический\nпрофиль', 'x': 6, 'y': 5.5, 'desc': '• FATF списки\n• Офшоры\n• Санкции'},
    {'name': 'Поведенческий\nпрофиль', 'x': 9, 'y': 5.5, 'desc': '• Изменения\n• Аномалии\n• Тренды'},
    {'name': 'Сетевой\nпрофиль', 'x': 12, 'y': 5.5, 'desc': '• Связи\n• Схемы\n• Графы'}
]

profile_patches = []
for profile in profiles:
    # Основной блок профиля
    box = FancyBboxPatch((profile['x'], profile['y']), 2, 1.8,
                        boxstyle="round,pad=0.05",
                        facecolor=colors['profiles'],
                        edgecolor='darkblue',
                        linewidth=2)
    ax.add_patch(box)
    profile_patches.append(box)
    
    # Название профиля
    ax.text(profile['x'] + 1, profile['y'] + 1.5, profile['name'], 
           ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Описание
    ax.text(profile['x'] + 1, profile['y'] + 0.6, profile['desc'], 
           ha='center', va='center', fontsize=8, style='italic')

# 3. ИНТЕГРАЦИОННЫЙ СЛОЙ
integration_box = FancyBboxPatch((3.5, 2.5), 7, 1.5,
                               boxstyle="round,pad=0.1",
                               facecolor=colors['integration'],
                               edgecolor='darkblue',
                               linewidth=3)
ax.add_patch(integration_box)
ax.text(7, 3.6, 'ИНТЕГРАЦИОННАЯ СИСТЕМА AML', ha='center', va='center', 
       fontsize=14, fontweight='bold')
ax.text(7, 3.1, 'Объединение всех профилей • Расчет итогового риска • Принятие решений', 
       ha='center', va='center', fontsize=10)

# 4. ВЫХОДНЫЕ ДАННЫЕ
outputs = [
    {'name': 'ПРОПУСК', 'x': 1, 'y': 0.3, 'color': '#27AE60'},
    {'name': 'ПРОВЕРКА\n(EDD)', 'x': 4.5, 'y': 0.3, 'color': '#F39C12'},
    {'name': 'СПО\n(STR)', 'x': 8, 'y': 0.3, 'color': '#E74C3C'},
    {'name': 'АЛЕРТЫ', 'x': 11.5, 'y': 0.3, 'color': '#9B59B6'}
]

for output in outputs:
    box = FancyBboxPatch((output['x'], output['y']), 2, 1,
                        boxstyle="round,pad=0.05",
                        facecolor=output['color'],
                        edgecolor='black',
                        linewidth=2,
                        alpha=0.8)
    ax.add_patch(box)
    ax.text(output['x'] + 1, output['y'] + 0.5, output['name'], 
           ha='center', va='center', fontsize=10, fontweight='bold', color='white')

# СТРЕЛКИ - Поток данных
# От входа к профилям
for i, profile in enumerate(profiles):
    arrow = ConnectionPatch((1.75, 8), (profile['x'] + 1, profile['y'] + 1.8),
                          "data", "data",
                          arrowstyle="->",
                          shrinkA=5, shrinkB=5,
                          mutation_scale=20,
                          fc=colors['flow'],
                          ec=colors['flow'],
                          linewidth=2)
    ax.add_artist(arrow)

# От профилей к интеграции
for profile in profiles:
    arrow = ConnectionPatch((profile['x'] + 1, profile['y']), (7, 4),
                          "data", "data",
                          arrowstyle="->",
                          shrinkA=5, shrinkB=5,
                          mutation_scale=20,
                          fc=colors['flow'],
                          ec=colors['flow'],
                          linewidth=2,
                          alpha=0.7)
    ax.add_artist(arrow)

# От интеграции к выходам
for output in outputs:
    arrow = ConnectionPatch((7, 2.5), (output['x'] + 1, output['y'] + 1),
                          "data", "data",
                          arrowstyle="->",
                          shrinkA=5, shrinkB=5,
                          mutation_scale=20,
                          fc=colors['flow'],
                          ec=colors['flow'],
                          linewidth=2,
                          alpha=0.7)
    ax.add_artist(arrow)

# ДОПОЛНИТЕЛЬНЫЕ ЭЛЕМЕНТЫ
# Риск-шкала справа
risk_scale_x = 14.5
ax.text(risk_scale_x + 0.5, 7, 'РИСК', ha='center', fontsize=12, fontweight='bold')
risk_levels = [
    {'level': '9-10', 'color': '#E74C3C', 'action': 'СПО'},
    {'level': '7-8', 'color': '#E67E22', 'action': 'Высокий'},
    {'level': '5-6', 'color': '#F39C12', 'action': 'Средний'},
    {'level': '3-4', 'color': '#F1C40F', 'action': 'Низкий'},
    {'level': '0-2', 'color': '#27AE60', 'action': 'Минимум'}
]

for i, risk in enumerate(risk_levels):
    y_pos = 6 - i * 0.8
    rect = FancyBboxPatch((risk_scale_x, y_pos), 1, 0.6,
                         boxstyle="round,pad=0.02",
                         facecolor=risk['color'],
                         edgecolor='black',
                         linewidth=1)
    ax.add_patch(rect)
    ax.text(risk_scale_x + 0.5, y_pos + 0.3, risk['level'], 
           ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(risk_scale_x + 1.7, y_pos + 0.3, risk['action'], 
           ha='left', va='center', fontsize=8)

# Процесс обработки (слева)
process_x = -2.5
ax.text(process_x + 0.5, 7, 'ПРОЦЕСС', ha='center', fontsize=12, fontweight='bold')
steps = [
    '1. Получение данных',
    '2. Проверка порогов',
    '3. Анализ участников',
    '4. Проверка географии',
    '5. Анализ поведения',
    '6. Поиск схем',
    '7. Расчет рисков',
    '8. Принятие решения'
]

for i, step in enumerate(steps):
    y_pos = 6.5 - i * 0.5
    ax.text(process_x, y_pos, step, ha='left', va='center', fontsize=8)
    # Маленький круг с номером
    circle = plt.Circle((process_x - 0.3, y_pos), 0.15, 
                       facecolor=colors['flow'], edgecolor='black')
    ax.add_patch(circle)

# Заголовок
ax.text(7, 9.5, 'СИСТЕМА МОНИТОРИНГА ТРАНЗАКЦИЙ АФМ РК', 
       ha='center', va='center', fontsize=16, fontweight='bold')
ax.text(7, 9.1, 'Интеграция 5 профилей для комплексного анализа', 
       ha='center', va='center', fontsize=12, style='italic')

# Настройки осей
ax.set_xlim(-3, 17)
ax.set_ylim(-0.5, 10)
ax.axis('off')

# Легенда внизу
legend_text = ('Система анализирует каждую транзакцию через 5 специализированных профилей,\n'
              'объединяет результаты и принимает решение на основе итогового риск-скора')
ax.text(7, -0.3, legend_text, ha='center', va='center', fontsize=9, 
       style='italic', bbox=dict(boxstyle="round,pad=0.3", facecolor='lightyellow'))

plt.tight_layout()
plt.show()
