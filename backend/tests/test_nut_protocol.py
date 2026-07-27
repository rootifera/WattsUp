import asyncio

from wattsup.nut.protocol import NutClient


async def test_lists_variables_from_nut_protocol() -> None:
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        assert (await reader.readline()).decode().startswith("LIST VAR")
        writer.write(
            b'BEGIN LIST VAR ups\nVAR ups ups.status "OL"\n'
            b'VAR ups battery.charge "100"\nEND LIST VAR ups\n'
        )
        await writer.drain()
        writer.close()

    server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    async with server:
        variables = await NutClient("127.0.0.1", port).get_variables("ups")

    assert variables == {"ups.status": "OL", "battery.charge": "100"}


async def test_discovers_all_ups_from_nut_protocol() -> None:
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        assert (await reader.readline()).decode().strip() == "LIST UPS"
        writer.write(
            b'BEGIN LIST UPS\nUPS apc "Rack UPS"\n' b'UPS office "Office UPS"\nEND LIST UPS\n'
        )
        await writer.drain()
        writer.close()

    server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    async with server:
        units = await NutClient("127.0.0.1", port).list_ups()

    assert units == {"apc": "Rack UPS", "office": "Office UPS"}
