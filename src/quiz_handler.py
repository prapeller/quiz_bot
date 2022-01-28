import logging
from typing import Dict

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext, MessageHandler, Filters, CommandHandler, ConversationHandler

from .api_auth import AuthAPI
from .api_quiz import QuizAPI

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)
quiz_api = QuizAPI()
user_data = {}

(
    AUTH_CHOOSING,
    USERNAME_PASSWORD_CHOOSING,
    USERNAME_PASSWORD_WRITING,

    BIZFUNC_CHOOSING,
    ANSWER_CHOOSING,
    REPEAT_CHOOSING,
) = range(6)

auth_type_markup = ReplyKeyboardMarkup(
    [
        ['Login'],
        ['Anonymous'],
        ['/end'],
    ],
    one_time_keyboard=True,
    input_field_placeholder='')

username_password_markup = ReplyKeyboardMarkup(
    [
        ['Username', 'Password'],
        ['/end'],
    ],
    one_time_keyboard=True,
)


def get_bizfunc_markup():
    bizfunc_title_list = [bizfunc['title'] for bizfunc in quiz_api.bizfuncs]
    return ReplyKeyboardMarkup(
        [[bizfunc] for bizfunc in bizfunc_title_list]
        + [['/end']],
        one_time_keyboard=True,
        input_field_placeholder='')


def get_option_markup():
    option_title_list = [option['title'] for option in quiz_api.options]
    return ReplyKeyboardMarkup(
        [[option] for option in option_title_list]
        + [['/end']],
        one_time_keyboard=True,
        input_field_placeholder='')


def user_data_to_str(user_data: Dict[str, str]) -> str:
    facts = [f'{key} - {value}' for key, value in user_data.items()]
    return "\n".join(facts).join(['\n', '\n'])


def start(update: Update, context: CallbackContext) -> int:
    logger.info(
        f'started chat: {update.message.chat}'
    )

    update.message.reply_text(
        f'auth login/anonymous or /end to stop',
        reply_markup=auth_type_markup,
    )
    return AUTH_CHOOSING


def auth_choose(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    auth_type = update.message.text.lower()
    user_data['auth_type'] = auth_type

    if auth_type == 'login':
        update.message.reply_text(
            'ok, put or update your username/password'
            # + user_data_to_str(user_data),
            ,
            reply_markup=username_password_markup,
        )
        return USERNAME_PASSWORD_CHOOSING

    elif auth_type == 'anonymous':
        auth_api = AuthAPI()
        auth_api.login_anonymous()
        user_data['token'] = auth_api.token
        quiz_api.set_headers(auth_api.token)
        quiz_api.get_bizfuncs()
        update.message.reply_text(
            f'enter your bizfunc?'
            # + user_data_to_str(user_data)
            ,
            reply_markup=get_bizfunc_markup()
        )
        return BIZFUNC_CHOOSING


def username_password_choose(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    user_data['choice'] = update.message.text.lower()

    update.message.reply_text(
        f'enter {user_data["choice"]}'
        # + user_data_to_str(user_data)
        ,
        reply_markup=ReplyKeyboardRemove(),
    )
    return USERNAME_PASSWORD_WRITING


def username_password_write(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    text = update.message.text
    choice = user_data['choice']
    user_data[choice] = text
    del user_data['choice']

    update.message.reply_text(
        'ok, choose another credential'
        # user_data_to_str(user_data)
        ,
        reply_markup=username_password_markup)

    username = user_data.get('username')
    password = user_data.get('password')
    if username and password:
        auth_api = AuthAPI()
        auth_api.login(username, password)
        user_data['token'] = auth_api.token
        quiz_api.set_headers(auth_api.token)
        quiz_api.get_bizfuncs()
        update.message.reply_text(
            f'enter your bizfunc?'
            # + user_data_to_str(user_data)
            ,
            reply_markup=get_bizfunc_markup()
        )
        return BIZFUNC_CHOOSING

    return USERNAME_PASSWORD_CHOOSING


def bizfunc_choose(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    bizfunc_title = update.message.text
    for b in quiz_api.bizfuncs:
        if b['title'] == bizfunc_title:
            quiz_api.bizfunc_choice = b
            break
    user_data['bizfunc'] = quiz_api.bizfunc_choice
    quiz_api.get_questions()
    if len(quiz_api.questions) < 1:
        update.message.reply_text(
            f'seems you\'ve answered all our question about this bizfunc, any other bizfunc?',
            reply_markup=get_bizfunc_markup()
        )
        return BIZFUNC_CHOOSING
    quiz_api.question_choice = quiz_api.questions[0]
    quiz_api.options = quiz_api.question_choice.get('options')

    update.message.reply_text(
        f'{quiz_api.question_choice.get("text")}'
        # + user_data_to_str(user_data)
        ,
        reply_markup=get_option_markup()
    )
    return ANSWER_CHOOSING


def answer_choose(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    answer_title = update.message.text

    question_title = quiz_api.question_choice['title']
    user_data[question_title] = answer_title

    for o in quiz_api.options:
        if o['title'] == answer_title:
            quiz_api.option_choice = o
            break
    quiz_api.post_answer()

    update.message.reply_text(
        'ok! reply another question?'
        # + user_data_to_str(user_data)
        ,
        reply_markup=ReplyKeyboardMarkup(
            [['yes'], ['/end']],
            one_time_keyboard=True,
            input_field_placeholder='')
    )
    return REPEAT_CHOOSING


def end(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    update.message.reply_text(
        f'Bye-bye!\n'
        f'Here your quiz results:\n'
        f'{user_data_to_str(user_data)}\n'
        f'/start to chat again',
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    logger.info(
        f'ended chat: {update.message.chat}'
    )
    return ConversationHandler.END


quiz_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        AUTH_CHOOSING: [
            MessageHandler(Filters.regex('^(Login|Register|Anonymous)$'), auth_choose),
        ],
        USERNAME_PASSWORD_CHOOSING: [
            MessageHandler(Filters.regex('^(Username|Password)$'), username_password_choose),
        ],
        USERNAME_PASSWORD_WRITING: [
            MessageHandler(Filters.text & ~(Filters.command), username_password_write),
        ],
        BIZFUNC_CHOOSING: [
            MessageHandler(Filters.text & ~(Filters.command), bizfunc_choose),
        ],
        ANSWER_CHOOSING: [
            MessageHandler(Filters.text & ~(Filters.command), answer_choose),
        ],
        REPEAT_CHOOSING: [
            MessageHandler(Filters.regex('^(yes)$'), bizfunc_choose),
        ],

    },
    fallbacks=[CommandHandler('end', end)],
)
