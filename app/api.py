from aiohttp import web
import json
from app.db import get_all_tasks_json, add_task, delete_task, mark_task_completed
from app.ai_agent import ai_answer

# Настройка CORS (чтобы сайт с GitHub мог обращаться к локальному боту)
import aiohttp_cors

async def get_tasks_handler(request):
    """Отдает список задач для пользователя"""
    try:
        user_id = int(request.query.get('user_id'))
        tasks = get_all_tasks_json(user_id)
        return web.json_response({"tasks": tasks})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)

async def add_task_handler(request):
    """Добавляет задачу"""
    try:
        data = await request.json()
        user_id = int(data.get('user_id'))
        title = data.get('title')
        due_datetime = data.get('due_datetime')
        
        add_task(user_id, title, due_datetime)
        return web.json_response({"status": "ok"})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)

async def update_task_handler(request):
    """Обновляет статус (выполнено) или удаляет"""
    try:
        data = await request.json()
        action = data.get('action')
        task_id = int(data.get('id'))
        
        if action == 'complete':
            mark_task_completed(task_id)
        elif action == 'delete':
            delete_task(task_id)
            
        return web.json_response({"status": "ok"})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)

async def ai_chat_handler(request):
    """Чат с ИИ внутри Mini App"""
    try:
        data = await request.json()
        message = data.get('message')
        user_id = int(data.get('user_id'))
        
        # Получаем контекст задач для умного ответа
        tasks = get_all_tasks_json(user_id)
        tasks_ctx = "\n".join([f"- {t['title']} ({t['due_datetime']})" for t in tasks if t['status'] != 'done'])
        
        # Генерируем ответ
        response_text = await ai_answer(message, tasks_context=tasks_ctx)
        
        return web.json_response({"response": response_text})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)

def setup_api_routes(app):
    # Настройка CORS (разрешаем запросы с любого сайта)
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    # Добавляем маршруты
    cors.add(app.router.add_get('/api/tasks', get_tasks_handler))
    cors.add(app.router.add_post('/api/tasks/add', add_task_handler))
    cors.add(app.router.add_post('/api/tasks/update', update_task_handler))
    cors.add(app.router.add_post('/api/ai', ai_chat_handler))