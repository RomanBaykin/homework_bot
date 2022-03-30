import os
import time
import requests
import telegram
import logging
import sys
import exceptions
from logging import StreamHandler
from dotenv import load_dotenv


logging.basicConfig(format='%(asctime)s, %(levelname)s, %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)
handler = StreamHandler(sys.stdout)
logger.addHandler(handler)
load_dotenv()


PRACTICUM_TOKEN = os.getenv('praktikum_token')
TELEGRAM_TOKEN = os.getenv('telegram_token')
TELEGRAM_CHAT_ID = os.getenv('telegram_chat_id')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Оправка сообщения."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except exceptions.MessageSendError as error:
        logger.error(f'Сообщение не отправлено. Причина {error}')
    logger.info('Сообщение отправлено')


def get_api_answer(current_timestamp):
    """Получение ответа от API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        logger.error(f'Эндпоинт {ENDPOINT} недоступен.'
                     f'Код сбоя {requests.get(ENDPOINT)}')
        raise exceptions.EndpointNotFound(f'Эндпоинт {ENDPOINT} недоступен.'
                                          f'Код сбоя {requests.get(ENDPOINT)}')
    return response.json()


def check_response(response):
    """Проверка ответа от API."""
    if not response['homeworks']:
        logger.error('Ответ API не содержит homeworks')
        raise KeyError('Ответ API не содержит homeworks')
    homework = response.get('homeworks')
    if not isinstance(homework, list):
        raise TypeError('Получен иной элемент, чем список')
    return homework


def parse_status(homework):
    """Проверка статуса работы."""
    if homework.get('homework_name') is None:
        logger.error('Ответ не содержит имя работы')
        raise KeyError('Ответ не содержит имя работы')
    else:
        homework_name = homework.get('homework_name')
    if homework.get('status') is None:
        logger.error('Ответ не содержит статус работы')
        raise KeyError('Ответ не содержит статус работы')
    else:
        homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        logger.error('Словарь не содержит такого статуса')
        raise KeyError('Словарь не содержит такого статуса')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка переменных доступа."""
    ENV_VARS = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for token in ENV_VARS:
        if not token:
            logger.critical('Один или несколько токенов отсутствуют')
            return False
    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise KeyError('Один или несколько токенов отсутствуют')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    compare_error = ''
    compare_message = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework[0])
            if compare_message != message:
                compare_message = message
                send_message(bot, message)
            else:
                logger.debug('Новые статусы отсуствуют')
            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if compare_error != message:
                compare_error = message
                send_message(bot, message)
            else:
                logger.debug('Ошибка повторяется')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
