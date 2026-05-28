import cv2, pdqhash, time, os
import numpy as np
import discord
from discord.ext import commands

bot = commands.AutoShardedBot(
    command_prefix="h",
    help_command=None,
    chunk_guilds_at_startup=False,
    allowed_contexts=discord.app_commands.AppCommandContext(guild=True, dm_channel=False, private_channel=False),
    intents=discord.Intents(message_content=True, messages=True, guilds=True),
    member_cache_flags=discord.MemberCacheFlags.none(),
    allowed_mentions=discord.AllowedMentions.none(),
)

last_status_update = 0

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


@bot.event
async def on_guild_join(guild):
    def verify(ch):
        return ch and ch.permissions_for(guild.me).send_messages

    def find(patt, channels):
        for i in channels:
            if patt in i.name:
                return i

    ch = find("bot", guild.text_channels)
    if not verify(ch):
        ch = find("commands", guild.text_channels)
    if not verify(ch):
        ch = find("general", guild.text_channels)

    found = False
    if not verify(ch):
        for ch in guild.text_channels:
            if verify(ch):
                found = True
                break
        if not found:
            ch = guild.owner

    try:
        if ch.permissions_for(guild.me).send_messages:
            await ch.send(
                "Thanks for adding me!\nI will automatically detect and delete crypto scam images.\nTry sending [this one](<https://girl.taxi/cryptoexample>) to test!"
            )
    except Exception:
        pass

@bot.event
async def on_message(message):
    global last_status_update
    if last_status_update + 300 < time.time():
        await bot.change_presence(activity=discord.CustomActivity(name=f"nuking scams in {len(bot.guilds):,} servers"))
        last_status_update = time.time()
    if message.attachments and not message.author.bot and not message.webhook_id:
        for att in message.attachments:
            if "image" not in att.content_type:
                continue
            new_hash = await pdq_hash(att)
            distances = [hamming(new_hash, i) for i in hashes]
            if min(distances) < 50:
                await message.delete()
                try:
                    await message.channel.send(f"Deleted Crypto Casino Scam images by {message.author.mention}.")
                except Exception:
                    pass
                return


bot.run(os.environ["ambc_token"])
