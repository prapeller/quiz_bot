import logging
import requests
import json

from .exceptions import BotException
from .settings.base import BASE_URL

logger = logging.getLogger(__name__)


class QuizAPI:

    def __init__(self, token=None):
        self.headers = {"Authorization": "token {0}".format(token)}
        self.bizfuncs = []
        self.bizfunc_choice = None
        self.questions = []
        self.question_choice = None
        self.options = []
        self.option_choice = None

    def set_headers(self, token):
        self.headers = {"Authorization": "token {0}".format(token)}

    def get_bizfuncs(self):
        try:
            response = requests.get(url=BASE_URL + "api/supplier/bizfunc/", headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise BotException(error=response.text, message="Ошибка при получении бизнес-функций, мы скоро её исправим.")
        self.bizfuncs = json.loads(response.content)
        if len(self.bizfuncs) < 1:
            raise BotException(error="len(self.bizfuncs) < 1", message="Ошибка при получении списка бизнес-функций, мы скоро её исправим.")

    def get_questions(self):
        args_str = "?bizfunc_slug={0}".format(self.bizfunc_choice.get("slug"))
        try:
            response = requests.get(url=BASE_URL + "api/audit/question/" + args_str, headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise BotException(error=response.text, message="Ошибка при получении бизнес-функций, мы скоро её исправим.")
        self.questions = json.loads(response.content)

    def post_answer(self):
        data = {
            "option": self.option_choice.get('slug')
        }
        try:
            response = requests.post(url=BASE_URL + "api/audit/answer/", headers=self.headers, json=data)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise BotException(error=response.text, message="Ошибка при отправке ответа, мы скоро её исправим.")
