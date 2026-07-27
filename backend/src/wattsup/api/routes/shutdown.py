from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from wattsup.core.auth import require_authenticated
from wattsup.schemas.shutdown import (
    AutomationSettings,
    DeviceInput,
    DeviceOutput,
    HostKeyInfo,
    SimulationRequest,
    SimulationResult,
    TestResult,
)
from wattsup.services.shutdown import ShutdownService

router = APIRouter(
    prefix="/shutdown",
    tags=["Shutdown automation"],
    dependencies=[Depends(require_authenticated)],
)


def get_service(request: Request) -> ShutdownService:
    return request.app.state.shutdown_service  # type: ignore[no-any-return]


Service = Annotated[ShutdownService, Depends(get_service)]


@router.get("/public-key")
async def public_key(service: Service) -> dict[str, str]:
    return {"public_key": service.ssh.public_key()}


@router.get("/devices", response_model=list[DeviceOutput])
async def list_devices(service: Service) -> list[DeviceOutput]:
    return [DeviceOutput.model_validate(device) for device in await service.list_devices()]


@router.post("/devices", response_model=DeviceOutput, status_code=status.HTTP_201_CREATED)
async def create_device(body: DeviceInput, service: Service) -> DeviceOutput:
    return DeviceOutput.model_validate(await service.create_device(body.model_dump()))


@router.put("/devices/{device_id}", response_model=DeviceOutput)
async def update_device(device_id: int, body: DeviceInput, service: Service) -> DeviceOutput:
    try:
        return DeviceOutput.model_validate(
            await service.update_device(device_id, body.model_dump())
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(device_id: int, service: Service) -> Response:
    try:
        await service.delete_device(device_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/devices/{device_id}/host-key", response_model=HostKeyInfo)
async def inspect_host_key(device_id: int, service: Service) -> HostKeyInfo:
    try:
        device = await service.get_device(device_id)
        algorithm, fingerprint, public_key = await service.ssh.inspect_host_key(
            device.host, device.port
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return HostKeyInfo(
        algorithm=algorithm,
        fingerprint=fingerprint,
        public_key=public_key,
        trusted=fingerprint == device.host_key_fingerprint,
    )


@router.post("/devices/{device_id}/trust-host-key", response_model=HostKeyInfo)
async def trust_host_key(device_id: int, service: Service) -> HostKeyInfo:
    try:
        algorithm, fingerprint, public_key = await service.trust_host_key(device_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return HostKeyInfo(
        algorithm=algorithm,
        fingerprint=fingerprint,
        public_key=public_key,
        trusted=True,
    )


@router.post("/devices/{device_id}/test", response_model=TestResult)
async def test_device(device_id: int, service: Service) -> TestResult:
    try:
        success, message = await service.test_device(device_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return TestResult(success=success, message=message)


@router.get("/settings", response_model=AutomationSettings)
async def settings(service: Service) -> AutomationSettings:
    return AutomationSettings.model_validate(await service.settings(), from_attributes=True)


@router.put("/settings", response_model=AutomationSettings)
async def update_settings(body: AutomationSettings, service: Service) -> AutomationSettings:
    return AutomationSettings.model_validate(
        await service.update_settings(body.enabled, body.dry_run),
        from_attributes=True,
    )


@router.post("/simulate", response_model=list[SimulationResult])
async def simulate(body: SimulationRequest, service: Service) -> list[SimulationResult]:
    return await service.simulate(body)
