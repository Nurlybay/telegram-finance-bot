# send_welcome
def get_start_texts(name: str, is_new: bool):
    if is_new:
        start_text0 = f"🥳 I'm so excited to see you here{name}!"
    else:
        start_text0 = f"🙋‍♀️ Привет{name}!"

    start_text = f'''{start_text0}\n🎯 Давай болтать, используя голосовые сообщения?!'''
    start_text1 = f'''{start_text}\n💬 Я поддержу беседу любой сложности, давая подсказки'''
    start_text2 = f'''{start_text1}\n🧩 Со мной ты закрепишь сотни разговорных фраз'''
    start_text3 = f'''{start_text2}\n👌 Ты избавишься от ошибок в речи и улучшишь произношение!'''
    start_text4 = f'''{start_text3}\n🏃‍♂️ Всего 15 минут ежедневного общения со мной прокачают твой английский за месяц!'''

    if is_new:
        start_text5 = f'''{start_text4}\n\n🗯 Запиши голосовое, как прошел твой день или что ты ел сегодня на завтрак на английском!'''
        return start_text0, start_text, start_text1, start_text2, start_text3, start_text4, start_text5

    # start_text5 = f'''{start_text4}\n<b>Кстати, боту можно задать тему для разговора 👉 /topics</b>'''
    return start_text0, start_text, start_text1, start_text2, start_text3, start_text4,


# send_help
help_message = (

    '🚀 Я Chatodor, создан для эффективной практики вашего английского. Я погружаю в реальную разговорную среду с носителем.\n'
    'Я сделан на базе GigaChat, передовой российской llm, разработанной командой Сбербанка\n\n'
    '👩‍💻 Наши исследования показали; чтобы заметно улучшить свои навыки устной и письменной речи, вам достаточно всего недели работы со мной (от 15 минут в день)! 🚀'
    '📈 Вы можете легко отслеживать свой прогресс /rating.\n\n'
)


hints_text = ('You can use these options to continue the conversation:\n'
              'Можете воспользоваться этими вариантами продолжения разговора:')


# keyboard markup
en_transcript_text = '🇬🇧 Text the same in English'
ru_transcript_text = '🇷🇺 Написать то же самое на Русском'
sos_text = "🆘 I'm stuck! Hints, please"
rating_text = "🕰 Сколько я наговорил?"
finish_text = '🏁 Finish & get feedback'
