import asyncio


CODE_SUCCESS = 0
# If ctrl+c was pressed during execution usually this code should be returned
CODE_SIGINT_BY_USER = 130


async def run_command_async(cmd: str) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout.decode().strip(), stderr.decode().strip()
