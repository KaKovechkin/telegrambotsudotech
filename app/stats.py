import matplotlib.pyplot as plt
import io

def draw_stats_chart(completed, pending, days_labels, tasks_per_day):
    """
    Рисует два графика на одной картинке:
    1. Круговая диаграмма (Выполнено vs В работе)
    2. Столбчатая диаграмма (Нагрузка по дням)
    """
    # Создаем фигуру с двумя зонами (1 строка, 2 колонки)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
    fig.suptitle('📊 Статистика МойРитм', fontsize=16)

    # --- 1. Круговая диаграмма (Общий прогресс) ---
    labels = ['Выполнено', 'В работе']
    sizes = [completed, pending]
    colors = ['#4CAF50', '#FF9800'] # Зеленый и Оранжевый
    explode = (0.1, 0)  # "Выдвигаем" первый кусочек

    # Если данных нет, рисуем заглушку
    if completed == 0 and pending == 0:
        sizes = [1]
        labels = ['Нет задач']
        colors = ['#B0BEC5']
        explode = (0,)

    ax1.pie(sizes, explode=explode, labels=labels, colors=colors,
            autopct='%1.1f%%', shadow=True, startangle=140)
    ax1.set_title('Общий прогресс')

    # --- 2. Столбчатая диаграмма (План на ближайшие дни) ---
    if days_labels:
        bars = ax2.bar(days_labels, tasks_per_day, color='#2196F3')
        ax2.set_title('Нагрузка на ближайшие дни')
        ax2.set_ylabel('Кол-во задач')
        ax2.grid(axis='y', linestyle='--', alpha=0.7)
        # Добавляем числа над столбцами
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                     f'{int(height)}', ha='center', va='bottom')
    else:
        ax2.text(0.5, 0.5, 'Нет планов', ha='center', va='center')
        ax2.set_title('Нагрузка')

    # Сохраняем в буфер (в память), а не в файл
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    return buf