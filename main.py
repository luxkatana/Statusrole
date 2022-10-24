import discord
from discord.ext import commands
import aiomysql
bot = commands.Bot(command_prefix="./", intents=discord.Intents.all())
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.pool = await aiomysql.create_pool(
        host="localhost",
        user="root",
        password="",
        db=""
    )
    
@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member) -> None:
    if before.status != after.status:
        return
    async def get_date() -> bool | dict:
        async with bot.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                cursor = await conn.cursor(aiomysql.DictCursor)
                await cursor.execute(f"SELECT * FROM statusrole WHERE guildID = %s", (after.guild.id,))
                fetch = await cursor.fetchall()
                if fetch  == ():
                    return False
                return fetch[0]
    data = await get_date()
    if data == False:
        return
        #
    custom = list(filter(lambda
                         j:isinstance(j, discord.CustomActivity), after.activities))
    if custom == []:
        ROLE = data["roleID"]
        channel = bot.get_channel(data["channelID"])
        ROLE = channel.guild.get_role(ROLE)
        if ROLE in after.roles:
            await after.remove_roles(ROLE, reason="Changed status")

            embed = discord.Embed(title=after, description=f"<@{after.id}> removed his status.", colour=discord.Color.red(), timestamp=discord.utils.utcnow())
            await channel.send(embed=embed)
        return

    custom = custom[0]

    if data == False or data["listen"] == 0:
        return

    if (text := data["statustext"]) == custom.name:
        channel = bot.get_channel(data["channelID"])

        ROLE = channel.guild.get_role(data["roleID"])

        await after.add_roles(ROLE)

        embedchannel = discord.Embed(title=after, description=f"Found someone with the status **{text}**", colour=discord.Color.green(), timestamp=discord.utils.utcnow())
        await channel.send(embed=embedchannel)
    else:
        channel = bot.get_channel(data["channelID"])
        ROLE = channel.guild.get_role(data["roleID"])
        if ROLE in after.roles:
            await after.remove_roles(ROLE, reason="Changed status")
            embed = discord.Embed(title=after, description=f"<@{after.id}> changed his status to **{custom.name}**", colour=discord.Color.red(), timestamp=discord.utils.utcnow())
            await channel.send(embed=embed)
            
            

@bot.slash_command(name="statusrole", guild_ids=[941803156633956362])
@discord.option(name="switch", description="Set on or off", required=True, choices=["on", "off"], type=str)
@discord.option(name="statustext", description="the text of the status",type=str , required=False)
@discord.option(name="logchannel", description="The channel to log each member", required=False, type=discord.TextChannel)
@discord.option(name="role", description="The role to role the member", required=False, type=discord.Role)
async def statusrole(            
    ctx: discord.ApplicationContext,
    switch: str,
    statustext: str = None,
    logchannel: discord.TextChannel = None,
    role: discord.Role = None,
    
) -> None:
    
    await ctx.defer()
    async def update_data() -> None:
        async with bot.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                cursor = await conn.cursor(aiomysql.DictCursor)
                await cursor.execute(f"UPDATE statusrole SET roleID = %s, channelID = %s, statustext = %s WHERE guildID = %s", (role.id, logchannel.id, statustext, ctx.guild.id))
                await conn.commit()            
    async def create_new_shit() -> None:
        async with bot.pool.acquire() as conn:
            async with conn.cursor()as cursor:
                cursor = await conn.cursor(aiomysql.DictCursor)
                await cursor.execute(f"INSERT INTO statusrole (guildID, channelID, listen, roleID, statustext) VALUES (%s, %s, %s, %s, %s)", (ctx.guild.id, logchannel.id, True, role.id, statustext))
                await conn.commit()
                return     
    async def validate_it() -> bool | dict:
        async with bot.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                cursor = await conn.cursor(aiomysql.DictCursor)
                await cursor.execute(f"SELECT * FROM statusrole WHERE guildID = %s", (ctx.guild.id,))
                fetch = await cursor.fetchall()
                if fetch == ():
                    return False
                return fetch[0]
    validation = await validate_it()
    if switch == "off":
        if isinstance(validation, bool):
            await ctx.respond(embed=discord.Embed(title="Nope", description="It was never on...", colour=discord.Color.red()))
            return
        async with bot.pool.acquire() as conn:
            async with conn.cursor()as cursor:
                cursor = await conn.cursor(aiomysql.DictCursor)
                await cursor.execute(f"UPDATE statusrole SET listen = 0 WHERE guildID = %s", (ctx.guild_id,))
                await conn.commit()
        await ctx.respond(embed=discord.Embed(title="Off", description="It's off now!"))
        return
    if not None in (statustext, logchannel, role) and logchannel.can_send() == False:
        embed = discord.Embed(title="Failed", description=f"I don't have permission to send messages in <#{logchannel.id}>")
        await ctx.respond(embed=embed)
        return
    else:
        if None in (statustext, logchannel, role):
            embed = discord.Embed(title="Error", description="Some of the arguments were Not passed D:", colour=discord.Colour.red())
            await ctx.respond(embed=embed)
            return
        # for each
        if role.is_assignable() ==  False:
            await ctx.respond(embed=discord.Embed(title="RIP", description=f"I cannot role people with the role <@&{role.id}>", colour=discord.Color.red()))
            return
        embed = discord.Embed(title="Started", description=f"Starting Roling people and logging in <#{logchannel.id}>\nText: **{statustext}** ", colour=discord.Color.green())
        await ctx.respond(embed=embed)
        if isinstance(validation, bool):
            await create_new_shit()
            
        else:
            await update_data()
        for member in ctx.guild.members:
            custom_status = list(filter(lambda j: isinstance(j, discord.CustomActivity), member.activities))
            if custom_status == []:
                continue
            custom_status = custom_status[0]
            if custom_status.name == statustext:
                
                await member.add_roles(role)
                embedchannel = discord.Embed(title=f"{member}", description=f"Found someone with the status **{statustext}**", colour=discord.Color.green(), timestamp=discord.utils.utcnow())
                await logchannel.send(embed=embedchannel)