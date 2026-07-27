from typing import Annotated

from fastapi import Depends, Request

from wattsup.services.status import StatusService


def get_status_service(request: Request) -> StatusService:
    return request.app.state.status_service  # type: ignore[no-any-return]


StatusServiceDependency = Annotated[StatusService, Depends(get_status_service)]
