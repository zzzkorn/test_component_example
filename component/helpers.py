import math


def last_page(response_data, page=1):
    count = response_data['count']
    limit = response_data['limit']
    if not len(response_data['items']):
        return True

    page_count = math.ceil(count / limit)
    if page >= page_count:
        return True


def validate_filters(
    app,
    session,
    stream_name,
    filters,
    response,
    validate_item,
):
    assert response['items'], (
        'Не было прочитано ни одного объекта. Скорее всего, это '
        'означает, что тест был написан неправильно.'
    )
    crud = app.streams[stream_name].crud
    for filter_, value in filters.items():
        for item in response['items']:
            obj = crud.read(session, item['id'])
            assert validate_item(filter_, obj, value)


def read_page(
    app,
    session,
    stream_name,
    call_operation,
    user,
    read_page_limit,
    filters=None,
    validate_item=None,
):
    filters = filters or dict()
    validate_item = validate_item or (
        lambda filter_, obj, value:
        hasattr(obj, filter_) and getattr(obj, filter_) == value
    )
    page = 1
    while page <= read_page_limit:
        response_data = call_operation(
            f'{stream_name}_read_page',
            auth_header=user,
            query_params=dict(
                page=page,
                **filters,
            ),
        )
        validate_filters(
            app,
            session,
            stream_name,
            filters,
            response_data,
            validate_item,
        )
        if last_page(response_data, page):
            break
        page += 1


def get_first_stream_object(
    app,
    session,
    stream_name,
    *,
    limit=5,
    filter_objects=None,
    get_item_data=lambda item: item.id,
):
    stream = app.streams.get(stream_name)
    if not stream:
        raise ValueError(f"{stream_name} not found")
    page_number, read_page_limit = 1, 1
    while page_number <= read_page_limit:
        page = stream.crud.read_page(session, page=page_number, limit=limit)
        read_page_limit = page.paginator.page_count
        page_number += 1
        items = filter(filter_objects, page.items)
        try:
            return get_item_data(next(items))
        except StopIteration:
            pass
    raise Exception(
        'Не было прочитано ни одного объекта. Скорее всего, это '
        'означает, что данные для теста не были правильно сгенерированы.'
    )
