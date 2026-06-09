import cv2, pdqhash, time, os
import numpy as np
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger('discord')

bot = commands.Bot(
    command_prefix="h",
    help_command=None,
    chunk_guilds_at_startup=False,
    allowed_contexts=discord.app_commands.AppCommandContext(guild=True, dm_channel=False, private_channel=False),
    intents=discord.Intents(message_content=True, messages=True, guilds=True),
    member_cache_flags=discord.MemberCacheFlags.none(),
    allowed_mentions=discord.AllowedMentions.none(),
)

with open("hashes.txt", "r") as f:
    hashes = f.read().splitlines()


async def pdq_hash(attachment):
    img_bytes = await attachment.read()
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    image = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    bits, _ = pdqhash.compute(image)
    n = ((len(bits) + 7) // 8) * 8
    padded = np.pad(bits, (0, n - len(bits)), constant_values=0)
    bytes_arr = np.packbits(padded.reshape(-1, 8), axis=1, bitorder='big').flatten()
    return str(bytes_arr.tobytes().hex())


def hamming(a, b):
    a = int(a, 16)
    b = int(b, 16)
    return (a ^ b).bit_count()


def verify_channel_perms(guild, ch):
    return ch and ch.permissions_for(guild.me).send_messages


def find_bot_channel(guild):
    def find(patt, channels):
        for i in channels:
            if patt in i.name:
                return i
    channel_names = ['scam-bot', 'log', 'bot', 'moderator', 'commands']
    for name in channel_names:
        channel = find(name, guild.text_channels)
        if verify_channel_perms(guild, channel):
            return channel
    return None


@bot.event
async def on_guild_join(guild):
    channel = find_bot_channel(guild)
    if not channel:
        for ch in guild.text_channels:
            if verify_channel_perms(guild, ch):
                channel = ch
                break

    try:
        await channel.send(
            'Thanks for adding me!\n' \
            'I will automatically detect and delete crypto scam images.\n' \
            'Try sending [this one](<https://girl.taxi/cryptoexample>) to test!'
        )
    except Exception as e:
        logger.exception(e)


@bot.event
async def on_message(message):
    if message.attachments and not message.author.bot and not message.webhook_id:
        filenames = [f'`{att.filename}`' for att in message.attachments]
        for att in message.attachments:
            if "image" not in att.content_type:
                continue
            new_hash = await pdq_hash(att)
            distances = [hamming(new_hash, i) for i in hashes]
            if min(distances) < 50:
                await message.delete()
                try:
                    channel = find_bot_channel(message.guild) or message.channel
                    await channel.send(
                        f'Deleted Crypto Casino Scam images by {message.author.mention} in {message.channel.mention}.\n' \
                        f'-# Attached filenames: {", ".join(filenames)}'
                    )
                except Exception as e:
                    logger.exception(e)
                return


bot.run(os.getenv("BOT_TOKEN"))
