import os
import discord
import yt_dlp
import asyncio
import requests

from dotenv import load_dotenv

def run_bot():
    load_dotenv()
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    G_API_KEY = os.getenv('API_KEY')
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

            voice_client = voice_clients.get(message.guild.id)

            if voice_client is None or not voice_client.is_connected():
                try:
                    voice_client = await message.author.voice.channel.connect()
                    voice_clients[message.guild.id] = voice_client
                except Exception as e:
                    await message.channel.send(f"⚠️ Error connecting: {e}")

            try:
                if (message.content.split()[1].startswith('?play')):
                    url = message.content.split()[1]

                else:
                    search = message.content[6:] + 'lyrics'
                    res = requests.get(
                        f'https://www.googleapis.com/youtube/v3/search?type=video&part=snippet&q={search.replace(' ', '+')}=video&key={G_API_KEY}&maxResults=1')
                    output = res.json()
                    url= 'https://www.youtube.com/watch?v=' + output['items'][0]['id']['videoId']

                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
                song = data['url']
                player = discord.FFmpegPCMAudio(song, **ffmpeg_options)

                if voice_client.is_playing():
                    voice_client.stop()


                voice_clients[message.guild.id].play(player)
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
            embed = discord.Embed(
                title="🎵 Styl'sBox Help",
                description="Here are the commands you can use:",
                color=discord.Color.blurple()  # You can change the color
            )

            embed.add_field(name="?play <url>", value="Play audio from a YouTube link", inline=False)
            embed.add_field(name="?pause", value="Pause the current song", inline=False)
            embed.add_field(name="?resume", value="Resume the paused song", inline=False)
            embed.add_field(name="?stop", value="Stop the song and disconnect", inline=False)

            embed.set_footer(text="Enjoy the music! 🎶")

            await message.channel.send(embed=embed)

    client.run(DISCORD_TOKEN)