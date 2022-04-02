import os
import time
import requests
import telegram
import logging
import sys
import exceptions
from logging import StreamHandler
from dotenv import load_dotenv

load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Оправка сообщения."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except exceptions.MessageSendError as error:
        logging.error(f'Сообщение не отправлено. Причина {error}')
    logging.info('Сообщение отправлено')


def get_api_answer(current_timestamp):
    """Получение ответа от API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        logging.error(f'Эндпоинт {ENDPOINT} недоступен.'
                      f'Код сбоя {requests.get(ENDPOINT)}')
        raise exceptions.EndpointNotFound(f'Эндпоинт {ENDPOINT} недоступен.'
                                          f'Код сбоя {requests.get(ENDPOINT)}')
    return response.json()


def check_response(response):
    """Проверка ответа от API."""
    if not isinstance(response, dict):
        logging.error('Ответ API не содержит словарь')
        raise TypeError('Ответ API не содержит словарь')
    elif 'homeworks' not in response:
        logging.error('Ответ API не содержит homeworks')
        raise KeyError('Ответ API не содержит homeworks')
    elif not isinstance(response['homeworks'], list):
        raise TypeError('Получен иной элемент, чем список')
    homework = response.get('homeworks')
    return homework


def parse_status(homework):
    """Проверка статуса работы."""
    if homework.get('homework_name') is None:
        logging.error('Ответ не содержит имя работы')
        raise KeyError('Ответ не содержит имя работы')
    else:
        homework_name = homework.get('homework_name')
    if homework.get('status') is None:
        logging.error('Ответ не содержит статус работы')
        raise KeyError('Ответ не содержит статус работы')
    else:
        homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        logging.error('Словарь не содержит такого статуса')
        raise KeyError('Словарь не содержит такого статуса')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка переменных доступа."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise KeyError('Один или несколько токенов отсутствуют')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 1

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework and len(homework[0]):
                message = parse_status(homework[0])
                send_message(bot, message)
            else:
                logging.info('Новые статусы отсуствуют')
            current_timestamp = response.get('current_time')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(handlers=[logging.StreamHandler()],
                        level=logging.INFO,
                        format='%(asctime)s, %(levelname)s, %(message)s')
    handler = StreamHandler(sys.stdout)
    logger = logging.getLogger(__name__)
    main()
