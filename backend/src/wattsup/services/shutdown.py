from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from wattsup.models.remote_device import AutomationConfig, RemoteDevice
from wattsup.schemas.shutdown import SimulationRequest, SimulationResult
from wattsup.schemas.status import UpsStatus
from wattsup.shutdown.ssh import SshService


class ShutdownService:
    def __init__(self, sessions: async_sessionmaker[AsyncSession], ssh: SshService) -> None:
        self.sessions = sessions
        self.ssh = ssh
        self._triggered_devices: set[int] = set()

    async def list_devices(self, ups_name: str | None = None) -> list[RemoteDevice]:
        query = select(RemoteDevice).order_by(RemoteDevice.name)
        if ups_name is not None:
            query = query.where(RemoteDevice.ups_name == ups_name)
        async with self.sessions() as session:
            return list((await session.scalars(query)).all())

    async def get_device(self, device_id: int) -> RemoteDevice:
        async with self.sessions() as session:
            device = await session.get(RemoteDevice, device_id)
            if device is None:
                raise LookupError("Device not found")
            session.expunge(device)
            return device

    async def create_device(self, values: dict[str, object]) -> RemoteDevice:
        async with self.sessions() as session:
            device = RemoteDevice(**values)
            session.add(device)
            await session.commit()
            await session.refresh(device)
            session.expunge(device)
            return device

    async def update_device(self, device_id: int, values: dict[str, object]) -> RemoteDevice:
        async with self.sessions() as session:
            device = await session.get(RemoteDevice, device_id)
            if device is None:
                raise LookupError("Device not found")
            for name, value in values.items():
                setattr(device, name, value)
            await session.commit()
            await session.refresh(device)
            session.expunge(device)
            return device

    async def delete_device(self, device_id: int) -> None:
        async with self.sessions() as session:
            device = await session.get(RemoteDevice, device_id)
            if device is None:
                raise LookupError("Device not found")
            await session.delete(device)
            await session.commit()

    async def settings(self) -> AutomationConfig:
        async with self.sessions() as session:
            config = await session.get(AutomationConfig, 1)
            if config is None:
                config = AutomationConfig(id=1, enabled=False, dry_run=True)
                session.add(config)
                await session.commit()
                await session.refresh(config)
            session.expunge(config)
            return config

    async def update_settings(self, enabled: bool, dry_run: bool) -> AutomationConfig:
        async with self.sessions() as session:
            config = await session.get(AutomationConfig, 1)
            if config is None:
                config = AutomationConfig(id=1)
                session.add(config)
            config.enabled = enabled
            config.dry_run = dry_run
            await session.commit()
            await session.refresh(config)
            session.expunge(config)
            return config

    async def trust_host_key(self, device_id: int) -> tuple[str, str, str]:
        device = await self.get_device(device_id)
        algorithm, fingerprint, public_key = await self.ssh.inspect_host_key(
            device.host, device.port
        )
        await self.update_device(
            device_id,
            {
                "trusted_host_key": public_key,
                "host_key_fingerprint": fingerprint,
                "last_test_at": datetime.now(UTC),
                "last_result": "SSH host key trusted.",
            },
        )
        return algorithm, fingerprint, public_key

    async def test_device(self, device_id: int) -> tuple[bool, str]:
        device = await self.get_device(device_id)
        if not device.trusted_host_key:
            return False, "Approve the SSH host key first"
        command = "sudo -n -l" if device.use_sudo else "whoami"
        try:
            code, output = await self.ssh.run(
                host=device.host,
                port=device.port,
                username=device.username,
                trusted_host_key=device.trusted_host_key,
                command=command,
            )
            if code != 0:
                success = False
                message = output or f"Readiness check exited with status {code}"
            elif device.use_sudo:
                required_commands = (
                    "/usr/bin/systemctl poweroff",
                    "/usr/sbin/shutdown",
                    "/usr/sbin/poweroff",
                )
                missing = [item for item in required_commands if item not in output]
                if missing:
                    success = False
                    message = (
                        "SSH works, but required passwordless shutdown permissions "
                        "are incomplete."
                    )
                else:
                    success = True
                    message = "SSH and passwordless shutdown permissions are ready."
            else:
                success = True
                message = "SSH login is ready."
        except Exception as error:
            success, message = False, str(error)
        await self.update_device(
            device_id,
            {"last_test_at": datetime.now(UTC), "last_result": message},
        )
        return success, message

    @staticmethod
    def matches(device: RemoteDevice, simulation: SimulationRequest) -> tuple[bool, str]:
        if not device.enabled:
            return False, "Device automation is disabled"
        if device.mains_state != "any" and device.mains_state != simulation.mains_state:
            return False, "Mains state does not match"
        if device.battery_state != "any" and device.battery_state != simulation.battery_state:
            return False, "Battery state does not match"
        if simulation.battery_percentage > device.battery_threshold:
            return False, "Battery is above the configured threshold"
        return True, "All shutdown conditions match"

    async def simulate(self, request: SimulationRequest, ups_name: str) -> list[SimulationResult]:
        return [
            SimulationResult(
                device_id=device.id,
                name=device.name,
                matches=(result := self.matches(device, request))[0],
                reason=result[1],
            )
            for device in await self.list_devices(ups_name)
        ]

    async def evaluate_status(self, status: UpsStatus) -> None:
        if status.battery_charge is None:
            return
        codes = set((status.status or "").split())
        mains_state: Literal["online", "on_battery"] = "on_battery" if "OB" in codes else "online"
        if "DISCHRG" in codes or "OB" in codes:
            battery_state: Literal["charging", "discharging", "full"] = "discharging"
        elif "CHRG" in codes:
            battery_state = "charging"
        elif status.battery_charge >= 100:
            battery_state = "full"
        else:
            battery_state = "charging"
        condition = SimulationRequest(
            mains_state=mains_state,
            battery_state=battery_state,
            battery_percentage=int(status.battery_charge),
        )
        config = await self.settings()
        for device in await self.list_devices(status.ups_name):
            matches, reason = self.matches(device, condition)
            if not matches:
                self._triggered_devices.discard(device.id)
                continue
            if device.id in self._triggered_devices or not config.enabled:
                continue
            self._triggered_devices.add(device.id)
            if config.dry_run:
                await self.update_device(
                    device.id,
                    {
                        "last_test_at": datetime.now(UTC),
                        "last_result": f"Dry run: {reason}; shutdown was not executed",
                    },
                )
                continue
            await self._shutdown(device)

    async def _shutdown(self, device: RemoteDevice) -> None:
        if not device.trusted_host_key:
            await self.update_device(
                device.id,
                {"last_result": "Shutdown blocked: SSH host key is not trusted"},
            )
            return
        prefix = "sudo -n " if device.use_sudo else ""
        commands = (
            [device.custom_command]
            if device.custom_command
            else [
                f"{prefix}/usr/bin/systemctl poweroff",
                f"{prefix}/usr/sbin/shutdown -h now",
                f"{prefix}/usr/sbin/poweroff",
            ]
        )
        last_message = "No shutdown command succeeded"
        for command in commands:
            try:
                code, output = await self.ssh.run(
                    host=device.host,
                    port=device.port,
                    username=device.username,
                    trusted_host_key=device.trusted_host_key,
                    command=command,
                )
                if code == 0:
                    last_message = f"Shutdown command accepted: {command}"
                    break
                last_message = output or f"{command} exited with status {code}"
            except Exception as error:
                last_message = f"{command}: {error}"
                break
        await self.update_device(
            device.id,
            {"last_test_at": datetime.now(UTC), "last_result": last_message},
        )
