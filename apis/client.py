import requests
from django.contrib.contenttypes.models import ContentType

from apis.models import ApiCall


def api_request(
    provider,
    url,
    method="GET",
    params=None,
    headers=None,
    payload=None,
    extra=None,
    related=None,
):
    method = method.upper()
    request_data = {
        "params": params,
        "headers": headers,
        "payload": payload,
    }

    response = None
    response_code = None
    response_body = None
    exception_text = ""

    try:
        response = requests.request(
            method,
            url,
            params=params,
            headers=headers,
            json=payload,
            timeout=60,
        )
        response_code = response.status_code
        response_body = response.json()
    except requests.RequestException as exc:
        exception_text = str(exc)

    content_type = None
    object_id = None
    if related is not None:
        content_type = ContentType.objects.get_for_model(related)
        object_id = related.pk

    ApiCall.objects.create(
        provider=provider,
        method=method,
        url=url,
        request=request_data,
        response_code=response_code,
        response=response_body,
        exception=exception_text,
        extra=extra or {},
        content_type=content_type,
        object_id=object_id,
    )

    return response
