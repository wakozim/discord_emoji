import os
import sys
import asyncio
import argparse
from typing import List, Tuple
from pathlib import Path
from enum import IntEnum, auto

import aiohttp
from dotenv import load_dotenv

from discord_emoji.discord_http import DiscordAPI


PNG    = 1
APNG   = 2
LOTTIE = 3
GIF    = 4


load_dotenv()
TOKEN = os.environ['TOKEN']

BASE_DIR = (Path(__file__).parent / '..').resolve()


def parse_args() -> Tuple[argparse.ArgumentParser, argparse.Namespace]:
    parser = argparse.ArgumentParser(
        prog='discord_emoji',
        description='Discord stickers/emojis downloader'
    )

    parser.add_argument(
        'guild_id',
        help='guild ID for downloading stickers/emojis',
        type=int
    )

    parser.add_argument(
        '-d', '--dir',
        help='directory to save stickers/emojis',
        type=str
    )

    parser.add_argument(
        '-b', '--bot',
        help='using bot token',
        action='store_true',
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-e', '--emojis', help='download only emojis', action='store_true')
    group.add_argument('-s', '--stickers', help='download only stickers', action='store_true')

    return parser, parser.parse_args()


async def download_emojis(emojis: List[dict]):
    tasks = []
    for emoji in emojis:
        emoji_name = emoji["name"].strip().replace(" ", "_")
        if emoji['animated']:
            emoji_url = f'https://cdn.discordapp.com/emojis/{emoji["id"]}.gif?size=128'
            emoji_filename = f'{emoji_name}.gif'
        else:
            emoji_url = f'https://cdn.discordapp.com/emojis/{emoji["id"]}.png?size=128'
            emoji_filename = f'{emoji_name}.png'
        tasks.append(asyncio.create_task(download_discord_image(emoji_filename, emoji_url)))

    return await asyncio.gather(*tasks)


async def download_stickers(emojis: List[dict]):
    tasks = []
    for emoji in emojis:
        emoji_name = emoji["name"].strip().replace(" ", "_")
        if emoji['format_type'] == GIF:
            emoji_url = f'https://cdn.discordapp.com/stickers/{emoji["id"]}.gif'
            emoji_filename = f'{emoji_name}.gif'
        elif emoji['format_type'] == PNG:
            emoji_url = f'https://cdn.discordapp.com/stickers/{emoji["id"]}.png'
            emoji_filename = f'{emoji_name}.png'
        elif emoji['format_type'] == APNG:
            emoji_url = f'https://cdn.discordapp.com/stickers/{emoji["id"]}.png'
            emoji_filename = f'{emoji_name}.apng'
        else:
            print(f'[INFO] Skipped `{emoji["name"]}` due to unknown format. (format_type: {emoji["format_type"]})')
            continue
        tasks.append(asyncio.create_task(download_discord_image(emoji_filename, emoji_url)))

    return await asyncio.gather(*tasks)


async def download_discord_image(image_filename: str, image_url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url, params={'size': '128'}) as request:
            return image_filename, await request.read()


async def main(args: List[str]) -> int:
    args = args[1:]
    parser, args = parse_args()

    discord: DiscordAPI = DiscordAPI(TOKEN, bot=args.bot)

    only_emojis = args.emojis
    only_stickers = args.stickers
    guild_id = args.guild_id
    guild_dir = Path(args.dir).resolve() if args.dir else BASE_DIR / str(guild_id)

    is_download_stickers = True
    is_download_emojis = True
    if only_emojis:
        is_download_stickers = False
    if only_stickers:
        is_download_emojis = False

    if not guild_dir.exists():
        guild_dir.mkdir()

    if is_download_emojis:
        emoji_dir = guild_dir / 'emojis'
        if not emoji_dir.exists():
            emoji_dir.mkdir()

    if is_download_stickers:
        sticker_dir = guild_dir / 'stickers'
        if not sticker_dir.exists():
            sticker_dir.mkdir()

    emojis = await discord.get_guild_emojis(guild_id) if is_download_emojis else []
    stickers = await discord.get_guild_stickers(guild_id) if is_download_stickers else []

    tasks = [
        download_emojis(emojis),
        download_stickers(stickers)
    ]

    emojis_files, stickers_files = await asyncio.gather(*tasks)

    if is_download_emojis:
        for (filepath, content) in emojis_files:
            with open(emoji_dir / filepath, 'wb') as file:
                file.write(content)

    if is_download_stickers:
        for (filepath, content) in stickers_files:
            with open(sticker_dir / filepath, 'wb') as file:
                file.write(content)

    return 0


if __name__ == '__main__':
    exit(asyncio.run(main(sys.argv)))
