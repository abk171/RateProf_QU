import os
import urllib
from datetime import datetime
from operator import attrgetter

import bot.utils as utils
import bot.utils.views as views
import discord
import geocoder
import httpx
import pytz
from discord.ext import commands
from discord.utils import get
from PyDictionary import PyDictionary
from timezonefinder import TimezoneFinder


class General(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['pong'])
    async def ping(self, ctx):
        '''
        Show the bot's latency.
        '''
        await ctx.send(embed=utils.SuccessEmbed(description=f'Pong! {int(self.bot.latency*1000)}ms'))

    @commands.group(invoke_without_command=True)
    async def prefix(self, ctx):
        '''
        View the current command prefix for the server.
        '''
        if not self.bot.db_conn:
            return await ctx.send(embed=utils.ErrorEmbed(description="Prefix database currently unavailable."))

        cur = self.bot.db_conn.cursor()
        cur.execute(
            f'SELECT prefix FROM public.servers WHERE id={ctx.guild.id}')
        prefix_db = cur.fetchone()

        if not prefix_db:
            prefix = self.bot.config['default_command_prefix']
        else:
            prefix = prefix_db[0]

        embed = utils.InformationEmbed(
            description=f'The command prefix for this server is `{prefix}`')
        embed.set_footer(text="To change prefix use prefix set")

        await ctx.send(embed=embed)
        cur.close()

    @prefix.command(name='set')
    @commands.has_permissions(manage_guild=True)
    async def prefix_set(self, ctx, *, prefix: str):
        '''
        Set the command prefix for the server.
        '''
        if not self.bot.db_conn:
            return await ctx.send(embed=utils.ErrorEmbed(description="Prefix database currently unavailable."))

        if len(prefix) > 5:
            return await ctx.send(embed=utils.ErrorEmbed(description='Bot prefix cannot be longer than 5 characters.'))

        cur = self.bot.db_conn.cursor()
        cur.execute(
            f'INSERT INTO public.servers values ({ctx.guild.id},\'{prefix}\') ON CONFLICT (id) DO UPDATE SET prefix = \'{prefix}\';')

        await ctx.send(embed=utils.SuccessEmbed(description=f'Server prefix set to `{prefix}`'))
        self.bot.db_conn.commit()
        cur.close()

    @commands.command()
    async def rate(self, ctx):
        '''Submit rating for a professor.'''
        pass


def setup(bot):
    bot.add_cog(General(bot))
