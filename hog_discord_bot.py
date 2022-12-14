#imports
import discord
from discord import Colour, Option
from random import randint
from datetime import timedelta
from discord.ext.commands import MissingPermissions
from discord.ext import commands
import string
import youtube_dl
import asyncio
from dataclasses import dataclass
youtube_dl.utils.bug_reports_message = lambda: ''

@dataclass
class User:
    id:str
    message_count:int
    message_level:int
    
    def __str__(self) -> str:
        return f'Your current level is {self.message_level}, you sent {self.message_count} messages'
    
    def __eq__(self,id:str):
        return self.id == id
ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename

bot = discord.Bot()

rand_number = randint(0,10)

warns = {}

users = []

message_levels = [10,20,50,100,200,300,500,1000]
@bot.event
async def on_ready():
    print(f'logged in as {bot.user}')
    
@bot.event
async def on_message(message):
    global users,message_levels
    if message.author.id == bot.user.id:
        return
    user = User(str(message.author.id),1,0)
    if len(users)!=0:
        for _user in users:
            if _user.__eq__(user.id):
                _user.message_count +=1
                for ind,level in enumerate(message_levels):
                    if _user.message_count > level and _user.message_level<ind:
                        _user.message_count +=1
    else:
        users.append(user)
        print('added user')
                    
@bot.slash_command(name = 'ddos',description = 'Execute order 66')
@commands.has_permissions(administrator = True)
async def test(ctx,name, amount,starting_message):
    try:
        for i in range(int(amount)):
            message = await ctx.send(starting_message)
            await message.create_thread(name = name)
    except ValueError:
        await ctx.respond('One of inputs is incorrect type')
    except Exception as e:
        await ctx.respond('Something went wrong')
        await ctx.respond(f'Debug info: {e.__class__.__name__} {e.args}')
       
@bot.slash_command(name = 'timeout', description ='timeout a user')
@commands.has_permissions(moderate_members = True)
async def timeout(ctx, member:Option(discord.Member, required = True), reason:Option(str,required = False), days:Option(int,max_value = 28 ,required = False),hours:Option(int,required = False), minutes:Option(int,required = False)):
    if member.id == ctx.author.id:
        await ctx.respond("You can't timeout yourself")
        return
    if member.guild_permissions.moderate_members:
        await ctx.respond("You can't timeout a moderator!")
        return
    days = 0 if days == None else days
    hours = 0 if hours == None else hours
    minutes = 0 if minutes == None else minutes
    duration = timedelta(days = days,minutes = minutes, hours = hours, seconds = 0)
    if reason == None:
        await member.timeout_for(duration)
        await ctx.respond(f"User <@{member.id}> has been timed out for {days} days, {hours} hours, {minutes} minutes")
    else:
        await member.timeout_for(duration,reason = reason)
        await ctx.respond(f"User <@{member.id}> has timed out for {days} days, {hours} hours, {minutes} minutes for {reason}")

@timeout.error
async def timeouterror(ctx,error):
    if isinstance(error,MissingPermissions):
        await ctx.respond("You don't have the rights to do that!")
    else:
        await ctx.respond(f"Something went wrong, debug info: {error}")
   
@bot.slash_command(name = 'unmute', description = 'unmute/untimeout a user')
@commands.has_permissions(moderate_members = True)
async def unmute(ctx,member:Option(discord.Member,required = True)):
    await member.remove_timeout()
    await ctx.respond(f"User {member.id} has been unmuted by {ctx.author.id}")

@unmute.error
async def unmuteerror(ctx,error):
    if isinstance(error,MissingPermissions):
        await ctx.respond("You don't have the rights for that!")
    else:
        await ctx.respond(f"Something went wrong!, debug info: {error}")

@bot.slash_command(name = 'ban', description = 'Ban a user')
@commands.has_permissions(ban_members = True, administrator = True)
async def ban(ctx,member:Option(discord.Member, required = True),reason:Option(str, required = False)):
    if member.id == ctx.author.id:
        await ctx.respond('BRUH')
        return
    elif member.guild_permissions.administrator:
        await ctx.respond("BRUH, don't try to ban an admin")
        return
    else:
        if reason == None:
            reason = 'No reason provided'
        await member.ban(reason = reason)
        await ctx.respond(f"User {member.id} has been banned by {ctx.author.id}")
        
@ban.error
async def banerror(ctx,error):
    if isinstance(error,MissingPermissions):
        await ctx.respond("You don't have permission to ban users")
    else:
        await ctx.respond("Something went wrong")
        
@bot.slash_command(name = 'kick', description = 'Kick a user')
@commands.has_permissions(kick_members = True, administrator = True)
async def kick(ctx,member:Option(discord.Member, required = True),reason:Option(str, required = False)):
    if member.id == ctx.author.id:
        await ctx.respond("BRUH")
        return
    elif member.guild_permissions.administrator:
        await ctx.respond("BRUH, don't try to kick an admin")
    
    else:
        if reason == None:
            reason = 'No reason provided'
            await member.kick(reason = reason)
            await ctx.respond("User {member.id} has been kicked by {ctx.author.id}")
            
        else:
            await member.kick(reason = reason)
            await ctx.respond("User {member.id} has been kicked by {ctx.author.id}")
        
@bot.slash_command(name = 'guess_the_number',description = 'Guess the neumber game')
async def gtn(ctx,number:Option(int,required = True)):
    global rand_number
    if number == rand_number:
        await ctx.respond('Correct!')
        rand_number = randint(0,10)
    else:
        await ctx.respond('Try again')

@bot.slash_command(name = 'caesar_encrypt',description = 'Encrypt any message with the Caesar chypher')
async def caesar_encrypt(ctx,message:Option(str,required = True), offset:Option(int,required = True)):
    outputText = ''
    for letter in message:
        if ord(letter) == 32 or ord(letter) == 9:
            encodedWord = ord(letter)
        
        elif letter in string.punctuation:
            encodedWord = ord(letter)
            
        elif letter.islower():
            encodedWord = ord(letter)+offset
            if encodedWord >122:
                encodedWord = (encodedWord - 122) +96
        else:
            encodedWord = ord(letter)+offset
            if encodedWord > 96:
                encodedWord = (encodedWord - 96) +64
        outputText = outputText + chr(encodedWord) 
    await ctx.respond(outputText) 
    
@bot.slash_command(name = 'caesar_decrypt', description = 'Decrypts a Caesar chypher')     
async def caesar_decrypt(ctx,message:Option(str, required = True), offset:Option(int, required = True)):
    outputText = ''
    for letter in message:
        if ord(letter) == 32 or ord(letter) == 9:
            encodedWord = ord(letter)
        
        elif letter in string.punctuation:
            encodedWord = ord(letter)
            
        elif letter.islower():
            encodedWord = ord(letter)-offset
            if encodedWord >122:
                encodedWord = (encodedWord - 122) +96
        else:
            encodedWord = ord(letter)-offset
            if encodedWord > 96:
                encodedWord = (encodedWord - 96) +64
        outputText = outputText + chr(encodedWord)
    await ctx.respond(outputText)    
    
@bot.slash_command(name = 'warn', description = 'warn user')
@commands.has_permissions(moderate_members = True)
async def warn(ctx,member:Option(discord.Member, required = True)):
    
    if member.id == ctx.author.id:
        await ctx.respond('BRUH')
        return
    else:
        if str(member.id) not in warns:
            warns[str(member.id)] = 1
            await ctx.respond(f'user {member.id} has been warned')
        else:
            warns[str(member.id)] +=1
            await ctx.respond(f'user {member.id} has been warned {warns[str(member.id)]} times')
        if warns[str(member.id)] == 3:
            await ctx.respond('3 warns')
            
@bot.slash_command(name='play_song', help='To play song')
async def play(ctx,url):
    
    try :
        server = ctx.guild
        voice_channel = server.voice_client

        async with ctx.typing():
            filename = await YTDLSource.from_url(url, loop=bot.loop)
            voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))
        await ctx.send('**Now playing:** {}'.format(filename))
    except Exception as e:
        await ctx.send(f"The bot is not connected to a voice channel. {e.__class__.__name__} {e.args}")


@bot.slash_command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.author.voice:
        await ctx.send("You are not connected to a voice channel".format(ctx.author.name))
        return
    else:
        channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.send('joined')


@bot.slash_command(name='pause', help='This slash_command pauses the song')
async def pause(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client.is_playing():
        await voice_client.pause()
        await ctx.send('Paused')
    else:
        await ctx.send("The bot is not playing anything at the moment.")
    
@bot.slash_command(name='resume', help='Resumes the song')
async def resume(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
        await ctx.send('resumed playing')
    else:
        await ctx.send("The bot was not playing anything before this. Use play_song slash_command")
    
@bot.slash_command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
        await ctx.send('Disconnected from VC')
    else:
        await ctx.send("The bot is not connected to a voice channel.")

@bot.slash_command(name='stop', help='Stops the song')
async def stop(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client.is_playing():
        await voice_client.stop()
    else:
        await ctx.send("The bot is not playing anything at the moment.")

@bot.slash_command(name = 'server_info', description = 'Server information')
async def server_info(ctx):
    embed = discord.Embed(
        title = 'Hearts of Game',
        description='lorem ipsum',
        color = Colour.blurple()
    )
    embed.add_field(name = '???????????????? ??????????????',value = 'lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet consectetur adipisicing elit. Maxime mollitia, molestiae quas vel sint commodi repudiandae consequuntur voluptatum laborum numquam blanditiis harum quisquam eius sed odit fugiat iusto fuga praesentiumoptio, eaque rerum! Provident similique accusantium nemo autem. **Veritatisobcaecati tenetur iure eius earum ut molestias architecto voluptate aliquamnihil, eveniet aliquid culpa officia aut! Impedit sit sunt quaerat, odit,tenetur error, harum nesciunt ipsum debitis quas aliquid**.',inline = False) 
    embed.add_field(name = '???????????????????? ????????????????????', value = str(ctx.guild.member_count))  
    embed.add_field(name = '?????????????? ???????? ???? ??????????????', value = 'R6, CS:GO, Dota 2, GTA 5, Minecraft, PUBG, Civ 6, WOT', inline = True)
    embed.set_author(name = 'HoG Team',icon_url='https://sun9-69.userapi.com/impg/0XZSvANhOv2ZiiSgUZwf_9n1jpGuhFNSz1EScg/g-th_a-8prE.jpg?size=1000x1000&quality=95&sign=eaa1bee581f0bbabede3d96215fce2e4&type=album')   
    embed.set_thumbnail(url = 'https://sun9-69.userapi.com/impg/0XZSvANhOv2ZiiSgUZwf_9n1jpGuhFNSz1EScg/g-th_a-8prE.jpg?size=1000x1000&quality=95&sign=eaa1bee581f0bbabede3d96215fce2e4&type=album')
    
    await ctx.respond('Welcome!', embed = embed)
    
@bot.slash_command(name = 'my_level')
async def show_level(ctx):
    for user in users:
        if str(ctx.author.id) == user.id:
            await ctx.respond(f'You are currently at level {user.message_level}, you sent {user.message_count} messages')
        
@bot.slash_command(name = 'add_messages')
@commands.has_permissions(administrator = True)
async def add_messages(ctx,amount:Option(int, required = True)):
    for user in users:
        if user.id == ctx.author.id:
            user.message_count+=amount
            await ctx.respond('Added {amount} messages')
         
        
 
