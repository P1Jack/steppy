import os
from datetime import datetime, timedelta
import uuid
import logging

from flask import Flask, render_template, request, jsonify, session
import requests
from dotenv import load_dotenv

from token_manager import GigaChatTokenManager

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

GIGACHAT_API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
GIGACHAT_AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

token_manager = None


def init_token_manager():
    global token_manager

    auth_key = os.getenv("GIGACHAT_AUTHORIZATION_KEY")

    if not auth_key:
        raise ValueError(
            "Не задан GIGACHAT_AUTHORIZATION_KEY. "
            "Укажите его в файле .env или переменных окружения."
        )

    token_manager = GigaChatTokenManager(
        auth_key=auth_key,
        token_file=os.getenv("TOKEN_FILE", "gigachat_token.json")
    )

    return token_manager


try:
    token_manager = init_token_manager()
except ValueError as e:
    print(f"Внимание: {e}")
    print("Работа без токена GigaChat невозможна.")


@app.before_request
def before_request():
    if request.endpoint and request.endpoint != 'static':
        if token_manager is None:
            return jsonify({
                'error': 'Сервис GigaChat не настроен. Проверьте переменные окружения.'
            }), 503


@app.route('/', methods=['GET'])
def index():
    if 'chat_history' not in session:
        session['chat_history'] = []
        session['session_id'] = str(uuid.uuid4())

    return render_template('test/chat.html',
                           chat_history=session['chat_history'],
                           session_id=session.get('session_id'),
                           token_status=token_manager is not None)


@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        user_message = request.json.get('message', '').strip()

        if not user_message:
            return jsonify({'error': 'Пустое сообщение'}), 400

        access_token = token_manager.get_token()
        if not access_token:
            return jsonify({'error': 'Не удалось получить токен GigaChat'}), 500

        chat_history = session.get('chat_history', [])
        chat_history.append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        messages_for_api = []
        for msg in chat_history[-10:]:
            messages_for_api.append({
                'role': msg['role'],
                'content': msg['content']
            })

        payload = {
            'model': 'GigaChat',
            'messages': messages_for_api,
            'temperature': 0.7,
            'max_tokens': 1024,
            'stream': False
        }

        response = requests.post(
            GIGACHAT_API_URL,
            headers=headers,
            json=payload,
            verify=False,  # ПОМЕНЯТЬ В ПРОДЕ
            timeout=30
        )

        if response.status_code == 200:
            response_data = response.json()
            assistant_response = response_data['choices'][0]['message']['content']

            chat_history.append({
                'role': 'assistant',
                'content': assistant_response,
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })

            session['chat_history'] = chat_history

            return jsonify({
                'response': assistant_response,
                'history': chat_history,
                'token_status': 'valid'
            })

        elif response.status_code == 401:
            app.logger.warning("Токен истек, пытаемся обновить...")
            access_token = token_manager.force_refresh()

            if access_token:
                headers['Authorization'] = f'Bearer {access_token}'
                response = requests.post(
                    GIGACHAT_API_URL,
                    headers=headers,
                    json=payload,
                    verify=False,
                    timeout=30
                )

                if response.status_code == 200:
                    response_data = response.json()
                    assistant_response = response_data['choices'][0]['message']['content']

                    chat_history.append({
                        'role': 'assistant',
                        'content': assistant_response,
                        'timestamp': datetime.now().strftime("%H:%M:%S")
                    })

                    session['chat_history'] = chat_history

                    return jsonify({
                        'response': assistant_response,
                        'history': chat_history,
                        'token_status': 'refreshed'
                    })

            return jsonify({
                'error': 'Ошибка аутентификации. Токен недействителен.',
                'details': 'Попробуйте обновить страницу или связаться с администратором.'
            }), 401

        else:
            app.logger.error(f"Ошибка API GigaChat: {response.status_code} - {response.text}")
            return jsonify({
                'error': f'Ошибка API GigaChat: {response.status_code}',
                'details': response.text[:200] if response.text else 'Нет деталей'
            }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Таймаут запроса к GigaChat API'}), 504
    except Exception as e:
        app.logger.error(f"Ошибка при обработке запроса: {str(e)}")
        return jsonify({'error': f'Внутренняя ошибка сервера: {str(e)}'}), 500


@app.route('/token/status', methods=['GET'])
def token_status():
    if not token_manager:
        return jsonify({
            'status': 'not_configured',
            'message': 'Менеджер токенов не инициализирован'
        })

    token_info = {
        'has_token': token_manager.access_token is not None,
        'expires_at': token_manager.expires_at.isoformat() if token_manager.expires_at else None,
        'is_valid': token_manager.expires_at > datetime.now() + timedelta(
            minutes=5) if token_manager.expires_at else False
    }

    return jsonify(token_info)


@app.route('/token/refresh', methods=['POST'])
def refresh_token():
    if not token_manager:
        return jsonify({'error': 'Менеджер токенов не инициализирован'}), 400

    new_token = token_manager.force_refresh()
    if new_token:
        return jsonify({
            'success': True,
            'message': 'Токен успешно обновлен'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Не удалось обновить токен'
        }), 500


@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    session['chat_history'] = []
    session['session_id'] = str(uuid.uuid4())
    return jsonify({'success': True})


@app.route('/export_chat', methods=['GET'])
def export_chat():
    chat_history = session.get('chat_history', [])
    export_data = {
        'session_id': session.get('session_id'),
        'exported_at': datetime.now().isoformat(),
        'messages': chat_history
    }

    return jsonify(export_data)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
