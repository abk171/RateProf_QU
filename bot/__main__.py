import asyncio
import json
import os
import pathlib
import sys
import traceback
from datetime import datetime
from pprint import pprint

import discord
import psycopg2
from discord.ext import commands

import bot.utils as utils

os.chdir(pathlib.Path(__file__).parents[1])
sys.dont_write_bytecode = True


class Bot(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.default()

        super().__init__(
            command_prefix=self.get_prefix_,
            intents=intents)

        self.bot_start_time = datetime.now()

        with open('config.json') as config_file:
            self.config = json.load(config_file)

        # Load command cogs
        successful_extensions = []
        failed_extensions = []

        for extension in self.config["extensions"]:
            try:
                self.load_extension(extension)
                successful_extensions.append(extension)
            except commands.ExtensionError:
                traceback.print_exc()
                failed_extensions.append(extension)

        print('The following extensions loaded successfully:')
        pprint(successful_extensions)

        if failed_extensions:
            print('\u001b[31;1m' + 'The following extensions failed to load: ')
            pprint(failed_extensions)
            print('\u001b[0m', end='')

        # Database stuff
        try:
            self.db_conn = psycopg2.connect(
                os.environ['RPROF_DATABASE_URL'], sslmode='require')
        except:
            self.db_conn = None
            print('DB connection failed.')
            return

        cur = self.db_conn.cursor()

        # Load blacklist
        self.blacklist = {'users': [], 'servers': []}
        cur.execute(f'SELECT users FROM public.blacklist')
        self.blacklist['users'] = [user[0] for user in cur.fetchall()]
        cur.execute(f'SELECT servers FROM public.blacklist')
        self.blacklist['servers'] = [server[0]
                                     for server in cur.fetchall()]

    async def get_prefix_(self, bot, message):
        default_prefix = self.config['default_command_prefix']

        cur = self.db_conn.cursor()
        cur.execute(
            f'SELECT prefix FROM public.servers WHERE id={message.guild.id}')
        db_prefix = cur.fetchone()
        cur.close()

        if not db_prefix:
            return commands.when_mentioned_or(*default_prefix)(bot, message)
        else:
            return commands.when_mentioned_or(db_prefix[0])(bot, message)

    def run(self):
        super().run(os.environ['RPROF_TOKEN'])

    async def on_ready(self):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="angry students"))
        print('Ready!')


if __name__ == '__main__':
    bot = Bot()

    @bot.check
    # Disable all DM commands.
    def check_commands(ctx):
        return True if ctx.guild else False

    @bot.event
    async def on_command(ctx):
        if not ctx.guild.id == 469979807099125789 and not ctx.author.id == 220951507070222337:
            log_text = f'**{ctx.guild.name} [{ctx.guild.id}]**```{ctx.author} [{ctx.author.id}] used {ctx.command.qualified_name}```'
            await bot.get_channel(833770044700753971).send(log_text)

    @bot.event
    async def on_guild_join(guild):
        log_text = f':tada: New Server! - Joined **{guild.name}** [{guild.id}]'
        await bot.get_channel(833770044700753971).send(log_text)

    @bot.event
    async def on_guild_remove(guild):
        log_text = f'Removed from - **{guild.name}** [{guild.id}]'
        await bot.get_channel(833770044700753971).send(log_text)

    @bot.event
    async def on_message(message):
        if message.author.id == bot.user.id:
            return
        if message.author.id in bot.blacklist['users']:
            return
        if message.guild.id in bot.blacklist['servers']:
            return

        ctx = await bot.get_context(message)
        if ctx.valid:
            return await bot.process_commands(message)

    # ERROR HANDLING
    @bot.event
    async def on_error(event, *args, **kwargs):
        exc_type, exc_value, exc_tb = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_tb)

    @bot.event
    async def on_command_error(ctx, error, *args, **kwargs):
        error = getattr(error, "original", error)

        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.BadUnionArgument):
            if hasattr(ctx.command, 'on_error'):
                return  # Ignores commands that have local error handlers defined

        # Ignore poll timeout errors.
        if isinstance(error, asyncio.TimeoutError):
            if hasattr(ctx.command, 'on_error'):
                return

        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(embed=utils.ErrorEmbed(
                title='Error').add_field(
                    name='Missing arguments:',
                    value=f'"{error.param.name}" is a required argument that is missing.'))

        if isinstance(error, commands.BadArgument):
            argument = list(ctx.command.clean_params)[
                len(ctx.args[2:] if ctx.command.cog else ctx.args[1:])]

            return await ctx.send(embed=utils.ErrorEmbed(title='Error').add_field(
                name='Invalid Input:',
                value=f'The value for "{argument}" given is invalid.'))

        if isinstance(error, commands.MissingPermissions):
            embed = utils.ErrorEmbed(
                title='Missing Permissions',
                description='You do not have the required permission to use this command.')

            embed.add_field(
                name='Permission required:',
                value=f'{error.missing_permissions[0]}')
            return await ctx.send(embed=embed)

        if isinstance(error, commands.BotMissingPermissions):
            embed = utils.ErrorEmbed(
                title='Missing Permissions',
                description='The bot does not have the required permission to use this command.')

            embed.add_field(
                name='Permission required:',
                value=f'{error.missing_permissions[0]}')
            return await ctx.send(embed=embed)

        if isinstance(error, commands.NotOwner):
            embed = utils.ErrorEmbed(
                title='Missing Permissions',
                description='This command is only available to bot owners.')
            return await ctx.send(embed=embed)

        if isinstance(error, commands.CheckAnyFailure):
            embed = utils.ErrorEmbed(
                title='Missing Permissions',
                description='You do not have the required permission to use this command.')

            embed.add_field(name='Permission required:',
                            value=f'{error.errors[0].missing_permissions[0]}')

            return await ctx.send(embed=embed)

        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(embed=utils.ErrorEmbed(
                title='COOLDOWN!',
                description=f'You are on cooldown. Retry after {round(error.retry_after,1)} seconds.'))

        else:
            traceback.print_exception(type(error), error, error.__traceback__)
            return await ctx.send(embed=utils.ErrorEmbed(title='Unknown Error', description=f'```{error}```'))
            # description='It looks like this command isn\'t working how it\'s supposed to. This has been logged and will be looked into.'))

    if bot.db_conn:
        bot.run()
