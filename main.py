import discord
from discord.ext import commands
import random
import os
from keep_alive import keep_alive

# Get token from environment variables
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # ✅ This is the key fix!
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

MOD_LOG_CHANNEL_ID = 1260914595107835926  # 🔹 Replace this with your actual log channel ID!
JOIN_LOG_CHANNEL_ID = 1260913011862798359

MUTE_ROLE_ID = 1345120789455699989


async def log_action(message, channel_id):
    log_channel = bot.get_channel(channel_id)  # Get the right channel
    if log_channel:
        await log_channel.send(message)  # Send the log message


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.command()
async def hello(ctx):
    """Sends a friendly space greeting."""
    responses = [
        "Greetings, Earthling!", "Simply stellar to see you!",
        "Hi and welcome to the cosmic adventure!",
        "May the stars align for your day!",
        "Hope you're having a celestial day!",
        "Howdy Space-Cowboys, -gals and nonbinary pals!"
    ]

    await ctx.send(random.choice(responses)
                   )  # ✅ This safely picks and sends a random response


@bot.event
async def on_message(message):
    print(f"Received message: {message.content}")  # Debugging
    await bot.process_commands(message)  # Ensures commands still work


@bot.command()
async def ping(ctx):
    """Checks if the bot is online."""
    await ctx.send("Pong!")


@bot.command()
async def testlog(ctx):
    """Sends a message to the log channel."""
    log_channel = bot.get_channel(MOD_LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(
            "✅ Log test: This message confirms logging works!")
    else:
        await ctx.send(
            "❌ Logging failed! Check if MOD_LOG_CHANNEL_ID is correct.")


@bot.event
async def on_member_join(member):
    await log_action(
        f"✅ One small step for man, one giant leap for mankind! {member.mention} **joined** the server.",
        JOIN_LOG_CHANNEL_ID)


@bot.event
async def on_member_remove(member):
    await log_action(
        f"❌ 3... 2... 1... blast off! {member.mention} **left** the server.",
        JOIN_LOG_CHANNEL_ID)


@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    """Kicks a member from the server."""
    await member.kick(reason=reason)
    await ctx.send(f"{member.mention} has been kicked. Reason: {reason}")
    await log_action(
        f"🚨 {member} was **kicked** by {ctx.author}. Reason: {reason}",
        MOD_LOG_CHANNEL_ID)


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    """Bans a member from the server."""
    await member.ban(reason=reason)
    await ctx.send(f"{member.mention} has been banned. Reason: {reason}")
    await log_action(
        f"🚨 {member} was **banned** by {ctx.author}. Reason: {reason}",
        MOD_LOG_CHANNEL_ID)


@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member_name):
    """Unbans a member from the server."""
    banned_users = await ctx.guild.bans()
    for banned_entry in banned_users:
        user = banned_entry.user
        if f"{user.name}#{user.discriminator}" == member_name:
            await ctx.guild.unban(user)
            await ctx.send(f"{user.mention} has been unbanned.")
            return
    await ctx.send("User not found.")


@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    """Clears a specified number of messages from the active channel."""
    await ctx.channel.purge(limit=amount + 1
                            )  # +1 to remove the command itself
    await ctx.send(f"Deleted {amount} messages.", delete_after=3)
    await log_action(
        f"🧹 {ctx.author} cleared **{amount}** messages in {ctx.channel.mention}.",
        MOD_LOG_CHANNEL_ID)


@bot.command()
@commands.has_permissions(manage_messages=True)
async def mute(ctx,
               member: discord.Member,
               duration: int,
               *,
               reason="No reason provided"):
    """Mutes a user for a set duration in minutes."""
    mute_role = ctx.guild.get_role(MUTE_ROLE_ID)
    mod_log = bot.get_channel(MOD_LOG_CHANNEL_ID)

    if not mute_role:
        await ctx.send("❌ Muted role not found! Check MUTE_ROLE_ID.")
        return

    mute_seconds = duration * 60  # Convert minutes to seconds

    try:
        await member.add_roles(mute_role)

        # Embed for mute notification
        embed = discord.Embed(title="🔇 User Muted", color=discord.Color.red())
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Duration",
                        value=f"{duration} minutes",
                        inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Muted by {ctx.author}")

        await ctx.send(embed=embed)  # Send in the channel
        if mod_log:
            await mod_log.send(embed=embed)  # Log to mod channel

        await asyncio.sleep(mute_seconds)  # Wait for mute duration

        # Unmute after time is up
        await member.remove_roles(mute_role)
        unmute_embed = discord.Embed(title="🔊 User Unmuted",
                                     color=discord.Color.green())
        unmute_embed.add_field(name="User", value=member.mention, inline=True)
        await ctx.send(embed=unmute_embed)
        if mod_log:
            await mod_log.send(embed=unmute_embed)

    except Exception as e:
        await ctx.send(f"❌ Failed to mute {member}: {e}")


@bot.command()
@commands.has_permissions(manage_messages=True)
async def unmute(ctx, member: discord.Member):
    """Unmutes a user manually."""
    mute_role = ctx.guild.get_role(MUTE_ROLE_ID)
    mod_log = bot.get_channel(MOD_LOG_CHANNEL_ID)

    if not mute_role:
        await ctx.send("❌ Muted role not found! Check MUTE_ROLE_ID.")
        return

    if mute_role not in member.roles:
        await ctx.send(f"❌ {member.mention} is not muted.")
        return

    try:
        await member.remove_roles(mute_role)

        # Embed for unmute notification
        embed = discord.Embed(title="🔊 User Unmuted",
                              color=discord.Color.green())
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.set_footer(text=f"Unmuted by {ctx.author}")

        await ctx.send(embed=embed)  # Send in the channel
        if mod_log:
            await mod_log.send(embed=embed)  # Log to mod channel

    except Exception as e:
        await ctx.send(f"❌ Failed to unmute {member}: {e}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            f"{ctx.author.mention}, you don't have permission to use this command."
        )
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing arguments! Check the command usage.")
    else:
        raise error


import asyncio  # Required for timing messages

# Dictionary to track user messages
user_messages = {}


@bot.event
async def on_message(message):
    if message.author.bot:  # Ignore bot messages
        return

    user_id = message.author.id
    now = asyncio.get_event_loop().time()  # Get the current time

    # If user isn't in the dictionary, add them
    if user_id not in user_messages:
        user_messages[user_id] = []

    # Add message timestamp to the user's record
    user_messages[user_id].append(now)

    # Remove messages older than 2 seconds
    user_messages[user_id] = [t for t in user_messages[user_id] if now - t < 5]

    # 🚨 Spam Detection: If user sends 5+ messages in 2 seconds, delete & warn
    if len(user_messages[user_id]) >= 5:
        await message.channel.purge(limit=5,
                                    check=lambda m: m.author == message.author)
        await message.channel.send(
            f"🚨 {message.author.mention}, stop spamming!", delete_after=5)
        await log_action(
            f"⚠️ **Anti-Spam**: {message.author} was warned for spamming.",
            MOD_LOG_CHANNEL_ID)

    await bot.process_commands(message)  # Ensure commands still work


@bot.command()
async def roleid(ctx, *, role_name):
    """Finds and prints the Role ID based on the role name."""
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if role:
        await ctx.send(f"✅ Role '{role_name}' ID: `{role.id}`")
    else:
        await ctx.send(f"❌ Role '{role_name}' not found!")


@bot.event
async def on_error(event, *args, **kwargs):
    import traceback
    error_message = traceback.format_exc()
    print(f"Error detected:\n{error_message}")


keep_alive()

bot.run(TOKEN)
