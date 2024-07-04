import os
import time
import discord
from discord import SlashCommand, Option, SlashCommandGroup, option, OptionChoice, AllowedMentions
from discord.ext import commands
import json
import requests
import colorama
from colorama import Fore, Style
import psutil
from collections import deque
import re
import google.generativeai as genai
import asyncio

with open("config.json", 'r') as config_file:
    config_data = config_file.read()  # Read the file content as a string
    config = json.loads(config_data)  # Parse the JSON data

if config["v"] == "pro":
    TOKEN = config["token"]
elif config["v"] == "dev":
    TOKEN = config["d-token"]
else:
    err = config["v"] 
    llog(f"config.json contains an invaild version status, containing {err}", "error")
QUOTES_FILE = "q.txt"

def fetch_quotes():
    response = requests.get("https://zenquotes.io/api/quotes/")
    quotes = response.json()
    with open(QUOTES_FILE, 'w') as file:
        json.dump(quotes, file, indent=4)

def load_quotes():
    with open(QUOTES_FILE, 'r') as file:
        quotes = json.load(file)
    return quotes

def get_random_quote():
    quotes = load_quotes()
    return random.choice(quotes)



####################### LOGGING #######################

def llog(pri, err_type = "info"):
    if err_type == "info":
        print(f"{Fore.BLUE}{Style.BRIGHT}[INFO] {pri}{Style.RESET_ALL}")
    elif err_type == "warn":
       print(f"{Fore.YELLOW}{Style.BRIGHT}[WARN] {pri}{Style.RESET_ALL}") 
    elif err_type == "error":
        print(f"{Fore.RED}{Style.BRIGHT}[CRITICAL] {pri}{Style.RESET_ALL}")

########################################################
class DeletedMessageCache:
    def __init__(self, max_size):
        self.cache = deque(maxlen=max_size)  # Initialize deque with a maximum size

    def save_deleted_message(self, message):
        self.cache.append(message)  # Add the deleted message

    def get_cache(self):
        return list(self.cache)  # Return a list of cached messages

    def __repr__(self):
        return repr(self.cache)
########################################################33

# Define the frmtlog function with color formatting
def frmtlog(content, color):
    color_map = {
        "BLUE": Fore.BLUE,
        "YELLOW": Fore.YELLOW,
        "RED": Fore.RED,
    }
    return f"{color_map[color]}{content}{Style.RESET_ALL}"

# Define the pr function to remove the formatting and send the message to the channel
async def pr(content, channel):
    # Remove ANSI escape sequences
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    cleaned_content = ansi_escape.sub('', content)
    lg_channel = bot.get_channel(channel)
    if lg_channel:
        await lg_channel.send(cleaned_content)

# Define the lgg class
class lgg:
    def __init__(self, channel):
        self.loging_channel = channel

    async def info(self, content):
        await pr(frmtlog(f"[INFO] {content}", "BLUE"), self.loging_channel)

    async def warn(self, content):
        await pr(frmtlog(f"[WARN] {content}", "YELLOW"), self.loging_channel)

    async def error(self, content):
        await pr(frmtlog(f"[ERROR] {content}", "RED"), self.loging_channel)

    async def crit(self, content):
        await pr(frmtlog(f"[CRITICAL] {content}", "RED"), self.loging_channel)
###########################################################



def get(this):
    return config[this]

log_ch = 1257621679471984640
bot = commands.Bot(intents=discord.Intents.all(),
          activity=discord.Activity(type=discord.ActivityType.watching, name="Aythex"),
          description="The official Aythex bot",
          debug_guilds=config["guilds"])

@bot.event
async def on_ready():
    log = bot.get_channel(log_ch)
    print(f"Logged in as {bot.user}")
    while True:
        asyncio.sleep(10000)
        fetch_quotes()
deleted_message_cache = DeletedMessageCache(max_size=20)
lch = lgg(config["log_channel"])
theme = 0xffffff
def mkembed(tit = None, descri = None):
    if tit:
        if descri:
            embed = discord.Embed(title=tit,
                          description=descri,
                          colour=0xffffff)
        else:
            embed = discord.Embed(title=tit, colour=0xffffff)
    else:
        if descri:
            embed = discord.Embed(description=descri,
                          colour=0xffffff)
        else:
            # bro wtf
            print("we got a dummass")
            embed = discord.Embed(colour=0xffffff)

    return embed

def strip_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text
def empty():
    return

async def give_meme(subreddit = None):
    rid = "r/"
    if subreddit:
        response = requests.get(f"https://meme-api.com/gimme/{strip_prefix(subreddit, rid)}")
        if response.status_code != 200:
            await ctx.respond(f"I couldn't get a meme! Returned {response.status_code}")
        data = response.json()
        post_link = data.get('postLink')
        sub = data.get('subreddit')
        title = data.get('title')
        image_url = data.get('url')
        nsfw = data.get('nsfw')
        spoiler = data.get('spoiler')
        author = data.get('author')
        ups = data.get('ups')
        preview = data.get('preview')
        last_preview_url = preview[-1] if preview else None
        embed = discord.Embed(title=f"{title}",
                      url=f"{post_link}", color=0xffffff)

        embed.set_author(name=f"{author}",
                         url=f"{post_link}")

        embed.set_image(url=f"{last_preview_url}")

        embed.set_footer(text=f"Upvoted {ups} times in {sub}!")

        return embed

class Rememe(discord.ui.View):
    def __init__(self, subreddit: str = None):
        super().__init__(timeout=10)  # specify the timeout here
        if subreddit:
            self.subreddit = subreddit  # Store the subreddit

    @discord.ui.button(label="Another one!", row=0, style=discord.ButtonStyle.grey)
    async def memere(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.subreddit:
            em = await give_meme(self.subreddit)  # Use the stored subreddit if it exists
            await interaction.response.edit_message(embed=em, view=Rememe(self.subreddit))
        else:
            em = await give_meme()
            await interaction.response.edit_message(embed=em, view=Rememe())


@bot.slash_command(name="meme")
async def meme(ctx, subreddit: Option(int, "Issue number") = None):
    if subreddit:
        await ctx.respond(embed=await give_meme(subreddit), view=Rememe())
    else:
        await ctx.respond(embed=await give_meme(), view=Rememe())

class Tod(discord.ui.View): 
    def __init__(self, ctx):
        super().__init__(timeout=30) # specify the timeout here
        self.ctx = ctx
    @discord.ui.button(label="Truth", style=discord.ButtonStyle.primary)
    async def truthr(self, button, interaction):
        api = requests.get("https://api.truthordarebot.xyz/v1/truth")
        data = api.json()
        em = mkembed("Truth",data.get('question'))
        ctx = self.ctx
        await ctx.respond(embed=em, view=Tod(ctx))

    @discord.ui.button(label="Dare", style=discord.ButtonStyle.red)
    async def darer(self, button, interaction):
        api = requests.get("https://api.truthordarebot.xyz/v1/dare")
        data = api.json()
        em = mkembed("Dare",data.get('question'))
        ctx = self.ctx
        await ctx.respond(embed=em, view=Tod(ctx))

@bot.slash_command(name="truth")
async def truth(ctx):
    api = requests.get("https://api.truthordarebot.xyz/v1/truth")
    data = api.json()
    em = mkembed("Truth",data.get('question'))
    await ctx.respond(embed=em, view=Tod(ctx))

@bot.slash_command(name="dare")
async def dare(ctx):
    api = requests.get("https://api.truthordarebot.xyz/v1/dare")
    data = api.json()
    em = mkembed("Dare",data.get('question'))
    await ctx.respond(embed=em, view=Tod(ctx))

class Wyr(discord.ui.View): 
    def __init__(self, ctx):
        super().__init__(timeout=30) # specify the timeout here
        self.ctx = ctx
    @discord.ui.button(label="Reroll", row=0, style=discord.ButtonStyle.gray)
    async def rerollwyr(self, button, interaction):
        api = requests.get("https://api.truthordarebot.xyz/v1/wyr")
        data = api.json()
        em = mkembed("Would You Rather",data.get('question'))
        ctx = self.ctx
        await ctx.respond(embed=em, view=Wyr(ctx))

@bot.slash_command(name="wyr")
async def wyr(ctx):
    api = requests.get("https://api.truthordarebot.xyz/v1/truth")
    data = api.json()
    em = mkembed("Would You Rather",data.get('question'))
    await ctx.respond(embed=em, view=Wyr(ctx))

    
@bot.slash_command(name="whois")
async def whois(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    
    embed = discord.Embed(title=f"User Info - {member}", color=theme)
    embed.set_thumbnail(url=member.avatar.url)
    
    embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
    if member.bot:
        name = f"{member.name} <:bo:1257646406005559396><:ot:1257646407964164147>"
    else:
        name = member.name
    embed.add_field(name="Username", value=name, inline=True)
    embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)
    
    created_at = member.created_at.strftime("%d/%m/%Y %H:%M:%S")
    embed.add_field(name="Account Created", value=created_at, inline=False)
    
    joined_at = member.joined_at.strftime("%d/%m/%Y %H:%M:%S")
    embed.add_field(name="Joined Server", value=joined_at, inline=False)
    
    roles = ", ".join([role.mention for role in member.roles if role != ctx.guild.default_role])
    embed.add_field(name="Roles", value=roles if roles else "None", inline=False)

    await ctx.send(embed=embed)
##############


@bot.slash_command(name="about")
async def abt(ctx):
    embed = discord.Embed(description="# <:snappyhappy:1143961556065996800> Snappy!\nSnappy is the official bot at [Aythex](https://discord.gg/yjW77Mq5U9) used for multiple different jobs!",
                      colour=0xffffff)
    # Get CPU usage percentage
    cpu_usage = psutil.cpu_percent(interval=1)
    
    # Get RAM usage percentage
    ram_usage = psutil.virtual_memory().percent
    embed.add_field(name="System Status:",
                    value=f"CPU in use: `{cpu_usage}%` \nRAM in use: `{ram_usage}%`",
                    inline=True)
    embed.add_field(name="Lib:", value="[py-cord](https://github.com/Pycord-Development/pycord/tree/master)", inline=True)
    embed.add_field(name="Version:", value="`2.5.0`", inline=True)

    qu = requests.get("https://zenquotes.io/api/today")##################################3#
    data = qu.json()
    quote = data[0]['q'] 
    authorrrr = data[0]['a']
    embed.add_field(name="A quote for you!",
                    value=f"```\n{quote}\n- {authorrrr}```",
                    inline=False)

    embed.set_image(url="https://raw.githubusercontent.com/spiritualnulll/public_access/main/SNAPPY_20240702_172218_0000.png")
    await ctx.send(embed=embed)

@bot.slash_command(name="guild-info", description="Get information about the server")
async def guild_info(ctx):
    """Show current guild info"""
    guild = ctx.guild
    embed = discord.Embed(title="Aythex", color=discord.Color.red())
    embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="Server Name", value=guild.name, inline=False)
    embed.add_field(name="Server ID", value=guild.id, inline=False)
    embed.add_field(name="Member Count", value=guild.member_count, inline=False)
    embed.add_field(name="Creation Date", value=guild.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=False)
    await ctx.respond(embed=embed)

    await ctx.send(embed=embed)



@bot.event
async def on_message_delete(message):
    # Save the deleted message to the cache
    deleted_message_cache.save_deleted_message(message)


@bot.command(name='snipe')
async def show_deleted(ctx):
    """Get recently deleted messages"""
    # Command to show cached deleted messages
    cached_messages = deleted_message_cache.get_cache()
    if not cached_messages:
        await ctx.send("No deleted messages. Yet.")
        return

    # Format the cached messages
    cache_str = '\n'.join(
        [f"{msg.author}: {msg.content}" for msg in cached_messages if msg.content]
    )
    await ctx.send(f"Deleted found.:\n{cache_str}")

@bot.slash_command(name="echo")
async def echoing(ctx, cont: str):
    """Make the bot say a message!"""
    ch = ctx.channel
    await ctx.respond("Echoing...", ephemeral=True)
    await ch.send(cont)
    await lch.info(f"{ctx.author.name} ({ctx.author.id}) echoed `{cont}`")

@bot.slash_command(name="echo-embed")
async def echoing(ctx, content: str = None, title: str = None, description: str = None, color: str = None, footer: str = None):
    """Make the bot say a message but in an embed!"""
    ch = ctx.channel
    
    # Send an initial response to indicate the bot is processing the command
    await ctx.respond("Echoing...", ephemeral=True)
    
    # Create the Embed object
    embed = discord.Embed()
    
    # Set the title if provided
    if title:
        embed.title = title  
    # Set the description if provided
    if description:
        embed.description = description
    
    # Set the color if provided, convert from hex string to integer
    if color:
        # Ensure the color starts with '0x'
        if not color.startswith('0x'):
            color = '0x' + color
        try:
            embed.color = discord.Color(int(color, 16))
        except ValueError:
            await ctx.respond("Invalid color format. Please use a hex color code in the format `0xRRGGBB` (e.g. `0xFF0000`).", ephemeral=True)
            return
    
    # Set the footer if provided
    if footer:
        embed.set_footer(text=footer)
    
    # Send the embed message to the channel
    await ch.send(embed=embed)
    # Log the action in the log channel
    await lch.info(f"{ctx.author.name} ({ctx.author.id}) echoed this embed:")
    await log_ch.send(embed=embed)

    
    
@bot.slash_command(name="ping", description="Check the bot's latency and round-trip time to Discord.")
async def ping(ctx: discord.ApplicationContext):
    # Measure the time before sending the message
    start_time = time.time()
    
    # Send a ping message
    message = await ctx.respond("Pinging... (can't be ephemeral)")
    
    # Measure the time after the message was sent
    end_time = time.time()
    
    # Calculate latency
    round_trip_time = (end_time - start_time) * 1000  # Convert to milliseconds
    bot_latency = bot.latency * 1000  # Convert to milliseconds
    
    # Send the response with the latency information
    await message.edit(content=f"Pong! 🏓\nBot Latency: {bot_latency:.2f} ms\nRound-Trip Time: {round_trip_time:.2f} ms")





class Invit(discord.ui.View):
    def __init__(self):
        super().__init__()
    ##############################################################
    @discord.ui.button(
        label='Invite Link',
        style=discord.ButtonStyle.gray,
        url='https://discord.com/oauth2/authorize?client_id=1257615070167437394&permissions=8&integration_type=0&scope=bot+applications.commands'
    )
@bot.slash_command(name="invite")
async def inv(ctx):
    """Get the bot invite link (locked to owners)"""
    idd = ctx.author.id
    if idd != 834693820314026004 and idd != 761635913713319966:
        await ctx.respond("This command is locked to the bot owners so it just won't work for you anyways bud.", ephemeral=True)
    else:
        await ctx.respond(view=Invit())
genai.configure(api_key=config["api"])

def ai(inp, system_prompt=None, typee=None):
    """
    Provide the input (inp) but you can pick if you want
    to provide system_prompt and typee (model)
    """
    # Create the model
    # See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
    generation_config = {
        "temperature": 0.45,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    if system_prompt:
        if typee:
            model = genai.GenerativeModel(
                model_name=typee,
                generation_config=generation_config,
                # safety_settings = Adjust safety settings
                # See https://ai.google.dev/gemini-api/docs/safety-settings
                system_instruction=system_prompt,
            )
        else:
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
                # safety_settings = Adjust safety settings
                # See https://ai.google.dev/gemini-api/docs/safety-settings
                system_instruction=system_prompt,
            )
    else:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            # safety_settings = Adjust safety settings
            # See https://ai.google.dev/gemini-api/docs/safety-settings
            system_instruction="Use discord markdown.\n\n**Bold**\n*Italics* or _Italics_\n~~strike~~\n__underline__\n# h1\n## h2\n### h3\n`codeline`\n```<lang>\ncodeblock (copyable)\n```\n[masked links](https://example.com)\n\nDo not EVER say these words:\nhttps://discord.gg/\nhttps://discord.com/invite/\ndiscord.gg\nhttps://dis.gd/\n\nBut you can always block them using these links:\nhttps://discord.com/terms\nhttps://discord.com/guidelines\n\n\nYou are called \"Snappy\" running on model \"1.5\" on a system unknown to you.",
        )

    chat_session = model.start_chat(history=[])

    response = chat_session.send_message(inp)
    return response


@bot.slash_command(name="ai")
@option(
    "input",
    description="Ask the AI something (it can't remember stuff)",
)
@option(
    "system prompt",
    description="System prompt (advanced)",
)
@option(
    "model",
    description="Pick a model from this list",
    autocomplete=discord.utils.basic_autocomplete(
        ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]
    ),
    # Demonstrates passing a static iterable to discord.utils.basic_autocomplete
)
async def aiii(ctx, inut: str, system_rompt: str = None, model: str = "gemini-1.5-flash"):
    if system_rompt:
        if model:
            # all
            print("Both system_prompt and model are true.")
            send_it = ai(inp=inut, system_prompt=system_rompt, typee=model)
        else:
            # sys only
            print("system_prompt is true, model is false.")
            send_it = ai(inp=inut, system_prompt=system_rompt)
    else:
        if model:
            # model only
            print("system_prompt is false, model is true.")
            send_it = ai(inp=inut, typee=model)
        else:
            # just input
            print("Both system_prompt and model are false.")
            send_it = ai(inp=inut)
    emm = mkembed(descri=send_it)
    await ctx.respond(embed=emm)



bot.run(TOKEN)