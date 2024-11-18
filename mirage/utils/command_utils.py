import asyncio
from asyncio import subprocess


async def run_command_async(cmd: str) -> str:
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode == 0:
        return stdout.decode().strip()

    raise subprocess.CalledProcessError(proc.returncode, cmd, stderr.decode().strip())
