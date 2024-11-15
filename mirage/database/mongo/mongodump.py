import asyncio


async def run_mongodump(mongo_backup_dir: str):
    proc = await asyncio.create_subprocess_exec(
        "mongodump", "-o", mongo_backup_dir
    )
    await proc.wait()
