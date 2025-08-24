import os
import discord
import yt_dlp
import asyncio

from dotenv import load_dotenv

def run_bot():
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    intents = discord.Intents.default()
    intents.message_content = True

    client = discord.Client(intents=intents)

    voice_clients = {}
    yt_dpl_options = {
        'format': 'bestaudio/best',
        'restrictfilenames': True,
    }
    ytdl = yt_dlp.YoutubeDL(yt_dpl_options)

    ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -filter:a "volume=0.25"'}

    @client.event
    async def on_ready():
        print(f'{client.user} has connected to Discord!')

    @client.event
    async def on_message(message):


        if message.content.startswith('?play'):
            if message.author.voice is None:
                await message.channel.send("❌ You need to be in a voice channel first!")
                return 0

            try:
                voice_client = await message.author.voice.channel.connect()
                voice_clients[voice_client.guild.id] = voice_client
            except Exception as e:
                await message.channel.send(f"⚠️ Error connecting: {e}")

            try:

                url = message.content.split()[1]
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

                song = data['url']
                player = discord.FFmpegPCMAudio(song, **ffmpeg_options)

                def after_play(err):
                    if err:
                        print(f"Player error: {err}")
                    asyncio.run_coroutine_threadsafe(voice_client.disconnect(), loop)

                voice_clients[message.guild.id].play(player, after=after_play)
                await message.channel.send(f"🎶 Now playing: **{data['title']}** {url}")

            except Exception as e:
                await message.channel.send(f"⚠️ Error connecting: {e}")

        if message.content.startswith('?pause'):
            try:
                voice_clients[message.guild.id].pause()
            except Exception as e:
                print(e)

        if message.content.startswith('?resume'):
            try:
                voice_clients[message.guild.id].resume()
            except Exception as e:
                print(e)

        if message.content.startswith('?stop'):
            try:
                voice_clients[message.guild.id].stop()
                await voice_clients[message.guild.id].disconnect()
            except Exception as e:
                print(e)

        if message.content.startswith('?help'):
            help_text = (
                "**🎵 Music Bot Commands**\n\n"
                "`?play <url>` - Play audio from a YouTube link\n"
                "`?pause` - Pause the current song\n"
                "`?resume` - Resume the paused song\n"
                "`?stop` - Stop the song and disconnect\n"
            )
            await message.channel.send(help_text)

    client.run(TOKEN)