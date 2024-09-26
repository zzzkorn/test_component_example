from __future__ import annotations
from typing import TYPE_CHECKING
import pytest
from component.helpers import get_first_stream_object
from component.helpers import read_page

# ===========================================================================
# Начало Пользовательские импорты
from tests.generator import generator
from tests.generator import create_not_active
from models.db.classifiers import EventType
# Конец Пользовательские импорты
# ===========================================================================


if TYPE_CHECKING:
    from typing import Any
    from typing import Callable
    from flaglib.apps.base import App
    from flaglib.models import Model
    from sqlalchemy.orm import Session
    # ===========================================================================
    # Начало Пользовательские типы

    # Конец Пользовательские типы
    # ===========================================================================


stream_name = "participants"
item_param = "participant_id"


# ===========================================================================
# Начало Пользовательские функции валидации фильтров

def validate_participant_event_filter(
        filter_: str,
        obj: Model,
        value: Any,
) -> bool:
    """Валидация фильтра участника по эвентам участника."""
    for event in obj.events:
        if (
            event.incoming_mail
            and getattr(event.incoming_mail, filter_) == value
        ):
            break
    else:
        return False
    return True

# Конец Пользовательские функции валидации фильтров
# ===========================================================================


@pytest.mark.parametrize(
    "user",
    [
        # ===========================================================================
        # Начало Тестируемые пользователи
        "mortgage__admin",
        # Конец Тестируемые пользователи
        # ===========================================================================
    ],
)
def test_read(
    app: App,
    session: Session,
    call_operation: Callable,
    user: str,
) -> None:
    """Тестируем получение объекта по идентификатору.

    Получаем объект по идентификатору.
    Проверяем, совпадает ли идентификатор объекта с запрашиваемым.
    """
    obj_id = get_first_stream_object(
        app,
        session,
        stream_name,
    )
    response_data = call_operation(
        f"{stream_name}_read",
        auth_header=user,
        path_params={item_param: obj_id},
    )
    assert response_data["item"]["id"] == obj_id


@pytest.mark.parametrize(
    "user",
    [
        # ===========================================================================
        # Начало Тестируемые пользователи
        "mortgage__admin",
        # Конец Тестируемые пользователи
        # ===========================================================================
    ],
)
def test_read_page_pagination(
    app: App,
    session: Session,
    call_operation: Callable,
    user: str,
    read_page_limit: int,
) -> None:
    """Тестируем чтение страницы списка объектов.

    Передаем страницу.
    Ожидаем получение страницы объектов.
    """
    read_page(
        app,
        session,
        stream_name,
        call_operation,
        user,
        read_page_limit,
    )


@pytest.mark.parametrize(
    "user",
    [
        # ===========================================================================
        # Начало Тестируемые пользователи
        "mortgage__admin",
        # Конец Тестируемые пользователи
        # ===========================================================================
    ],
)
class TestReadPageFilters:
    """Тестируем фильтрацию при чтении страницы списка объектов."""

    # ===========================================================================
    # Начало Генерации дополнительных данных для тестирования фильтров
    @staticmethod
    @generator.custom(count=1)
    def create_not_active(app: App, session: Session) -> None:
        """Генератор неактивного объекта, для теста фильтра not_active."""
        create_not_active(
            app,
            session,
        )
    # Конец Генерации дополнительных данных для тестирования фильтров
    # ===========================================================================

    @pytest.mark.parametrize(
        (
            "filter_",
            "filter_objects",
            "get_item_data",
            "get_filter_value",
            "validate_item",
        ),
        [
            # ===========================================================================
            # Начало Аргументов для тестирования фильтров
            (
                "number",
                None,
                lambda item: item.number,
                None,
                None,
            ),
            (
                "entry_operator_id",
                lambda item: item.include_events,
                lambda item: item.include_events[0].worker_id,
                None,
                validate_participant_event_filter,
            ),
            (
                "personal_card_id",
                lambda item: item.personal_card,
                lambda item: item.personal_card.id,
                None,
                None,
            ),
            (
                "not_active",
                None,
                lambda _item: 1,
                None,
                lambda _filter, obj, _value: not obj.is_active,
            ),
            (
                "excluded_with_savings_right",
                None,
                lambda item: int(item.savings_right),
                None,
                lambda _filter, obj, _value: (
                    obj.last_event_type == EventType.exclude
                    and obj.savings_right
                ),
            ),
            (
                "excluded_without_additional_payments_right",
                lambda item: item.last_event_type == EventType.exclude,
                lambda item: int(
                    item.exclude_events[0].additional_payments_right),
                None,
                lambda _filter, obj, _value: (
                    obj.last_event_type == EventType.exclude
                    and not obj.exclude_events[0].additional_payments_right
                ),
            ),
            # Конец Аргументов для тестирования фильтров
            # ===========================================================================
        ],
    )
    def test_filters(
        self,
        app: App,
        session: Session,
        call_operation: Callable,
        read_page_limit: int,
        user: str,
        filter_: str,
        filter_objects: Callable[[Model], bool] | None,
        get_item_data: Callable[[Model], Any] | None,
        get_filter_value: Callable[[Any], Any] | None,
        validate_item: Callable[[Any], bool] | None,
    ) -> None:
        """Тестируем чтение списка объектов с фильтром.

        Указываем значение фильтра.
        Ожидаем страницу объектов с данным значением поля.
        """
        get_filter_value = get_filter_value or (lambda value: value)
        obj = get_first_stream_object(
            app,
            session,
            stream_name,
            filter_objects=filter_objects,
            get_item_data=get_item_data,
        )
        filter_value = get_filter_value(obj)
        read_page(
            app,
            session,
            stream_name,
            call_operation,
            user,
            read_page_limit,
            filters={filter_: filter_value},
            validate_item=validate_item,
        )
