from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    choice_item = State()
    choice_type_news = State()
    choice_time_news = State()
    choice_data = State()
    choice_time = State()
    choice_time_selected = State()
    news_text = State()
    button_link = State()
    step_to_link = State()
    go_to_publish = State()
    news_media = State()
    media_handle_state = State()
    adding_link_button = State()
    adding_link_url = State()
    go_to_publish_media = State()