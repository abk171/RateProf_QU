from datetime import datetime
import io
import itertools
import textwrap
import traceback
from contextlib import redirect_stdout

import bot.utils as utils
import discord
from discord.ext import commands
from discord.utils import get


class PaginatedHelpCommand(commands.HelpCommand):

    async def send_bot_help(self, mapping):
        def key(c):
            return c.cog_name or 'No Category'

        entries = sorted(self.context.bot.commands,
                         key=key)
        embeds = []
        per_page = 5

        cog_commands = [
            (cog, list(commands))
            for cog, commands
            in itertools.groupby(entries, key=key)]

        cog_commands = sorted(
            cog_commands, key=lambda x: len(x[1]), reverse=True)

        for chunk in utils.chunkinate(cog_commands, per_page):
            embed = utils.InformationEmbed(title='Help')
            for cog, commands in chunk:
                commands = sorted(commands, key=lambda c: c.name)
                value = ''
                count = 0
                for command in commands:
                    if command.hidden:
                        continue
                    value += f'`{command.name}` '
                    count += 1
                    if count == 5:
                        count = 0
                        value += '\n'

                if value:
                    embed.add_field(
                        name=cog,
                        value=value,
                        inline=False)
            embeds.append(embed)

        await utils.paginator(self, self.context, embeds)

    async def send_cog_help(self, cog):
        commands = await self.filter_commands(cog.get_commands())
        pages = []
        per_page = 5
        for chunk in utils.chunkinate(
                sorted(commands, key=lambda x: x.name),
                per_page):
            embed = utils.InformationEmbed(title=type(cog).__name__)
            for command in chunk:
                value = ''
                value += f'{command.short_doc}\n' if command.help else ''
                value += f'`{(self.get_command_signature(command).strip())}`'
                embed.add_field(name=command.name, value=value, inline=False)
            pages.append(embed)

        await utils.paginator(self, self.context, pages)

    async def prepare_group_help(self, group):
        # filtered_commands = await self.filter_commands(group.commands)
        pages = []
        per_page = 5
        for chunk in utils.chunkinate(
            sorted(group.commands, key=lambda x: x.name),
                per_page):
            embed = utils.InformationEmbed(
                title=f'`{(self.get_command_signature(group).strip())}`',
                description=group.help + "\n\n**Subcommands:**")

            for command in chunk:
                value = ''
                value += command.short_doc + '\n'
                value += f'`{(self.get_command_signature(command).strip())}`'
                embed.add_field(
                    name=command.name,
                    value=value,
                    inline=False)

            pages.append(embed)
        return pages

    async def send_group_help(self, group):
        await utils.paginator(self, self.context, await self.prepare_group_help(group))

    async def prepare_command_help(self, command):
        embed = utils.InformationEmbed(
            title=f'`{(self.get_command_signature(command).strip())}`',
            description=command.help)
        return embed

    async def send_command_help(self, command):
        await self.context.send(embed=await self.prepare_command_help(command))

    async def send_error_message(self, error):
        pass

    def command_not_found(self, string):
        pass

    def subcommand_not_found(self, command, string):
        pass


class Meta(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None

    @commands.command(aliases=['disconnect', 'close', 'shutdown', 'dc'], hidden=True)
    @commands.is_owner()
    async def logout(self, ctx):
        """
        Disconnect the bot from discord.
        """
        if self.bot.db_conn:
            self.bot.db_conn.close()
        await ctx.send(f"Potate shutting down :wave:")
        await self.bot.close()

    @commands.group(aliases=['blist'], invoke_without_command=True)
    @commands.is_owner()
    async def blacklist(self, ctx):
        if not self.bot.db_conn:
            await ctx.send(utils.ErrorEmbed(description="Not connected to database!"))
        await ctx.send(embed=utils.SuccessEmbed(description="Blacklist data sent to console."))
        print(self.bot.blacklist)

    @blacklist.command(name='add')
    @commands.is_owner()
    async def blacklist_add(self, ctx, type, id: int):
        user_bl = self.bot.blacklist["users"]
        server_bl = self.bot.blacklist["servers"]

        if not self.bot.db_conn:
            await ctx.send(utils.ErrorEmbed(description="Not connected to database!"))

        cur = self.bot.db_conn.cursor()
        if type.lower() == "user":
            if id in user_bl:
                return await ctx.send(embed=utils.ErrorEmbed(description="User already blacklisted."))

            user_bl.append(id)
            cur.execute(f'INSERT INTO public.blacklist (users) VALUES ({id});')
            self.bot.db_conn.commit()
            cur.close()
            return await ctx.send(embed=utils.SuccessEmbed(description=f'Successfully blacklisted user {id}.'))

        elif type.lower() == "server":
            if id in server_bl:
                return await ctx.send(embed=utils.ErrorEmbed(description="Server already blacklisted."))

            server_bl.append(id)
            cur.execute(f'INSERT INTO public.blacklist VALUES ({id});')
            self.bot.db_conn.commit()
            cur.close()
            return await ctx.send(embed=utils.SuccessEmbed(description=f'Successfully blacklisted server {id}.'))

        else:
            return await ctx.send(embed=utils.ErrorEmbed(description="Invalid blacklist type."))

    @blacklist.command(name='remove')
    @commands.is_owner()
    async def blacklist_remove(self, ctx, type, id: int):
        user_bl = self.bot.blacklist["users"]
        server_bl = self.bot.blacklist["servers"]

        if not self.bot.db_conn:
            await ctx.send(embed=utils.ErrorEmbed(description="Not connected to database!"))

        cur = self.bot.db_conn.cursor()
        if type.lower() == "user":
            if id not in user_bl:
                return await ctx.send(embed=utils.ErrorEmbed(description="User not blacklisted."))

            user_bl.remove(id)
            cur.execute(f'DELETE FROM public.blacklist WHERE users={id};')
            self.bot.db_conn.commit()
            cur.close()
            return await ctx.send(embed=utils.SuccessEmbed(description=f'Successfully removed user {id} from the blacklist.'))

        elif type.lower() == "server":
            if id not in server_bl:
                return await ctx.send(embed=utils.ErrorEmbed(description="Server not blacklisted."))

            server_bl.remove(id)
            cur.execute(f'DELETE FROM public.blacklist WHERE servers={id};')
            self.bot.db_conn.commit()
            cur.close()
            return await ctx.send(embed=utils.SuccessEmbed(description=f'Successfully removed server {id} from the blacklist.'))

        else:
            return await ctx.send(embed=utils.ErrorEmbed(description="Invalid blacklist type."))

    @commands.command(aliases=['r'])
    @commands.is_owner()
    async def reload(self, ctx, cog=""):
        '''
        Reload all cogs / single cog.
        '''
        embed = utils.InformationEmbed(
            description="Reloading cog(s) <a:loading:743272480390643713>")
        msg = await ctx.send(embed=embed)

        if cog:
            cog = "bot.cogs." + cog.lower()

            try:
                self.bot.unload_extension(cog)
            except:
                pass

            try:
                self.bot.load_extension(cog)
                embed = utils.SuccessEmbed(
                    description=f"{utils.message.checkmark_emoji} Reloaded {cog}")
                await msg.delete()
                return await ctx.send(embed=embed)

            except commands.ExtensionError:
                traceback.print_exc()
                embed = utils.ErrorEmbed(
                    description=f"{utils.message.crossmark_emoji} Failed to reload {cog}")

                await msg.delete()
                return await ctx.send(embed=embed)

        successful_extensions = []
        failed_extensions = []

        for extension in self.bot.config["extensions"]:
            try:
                self.bot.unload_extension(extension)
            except:
                pass

            try:
                self.bot.load_extension(extension)
                successful_extensions.append(extension)
            except commands.ExtensionError:
                traceback.print_exc()
                failed_extensions.append(extension)

        embed = utils.SuccessEmbed(
            description=f"{utils.message.checkmark_emoji} Reload attempt complete.")

        if len(successful_extensions):
            embed.add_field(
                name="Reloaded", value="\n".join(successful_extensions))

        if len(failed_extensions):
            embed.add_field(
                name="Failed", value="\n".join(failed_extensions))

        await msg.delete()
        return await ctx.send(embed=embed)

    @commands.command(pass_context=True, hidden=True, name='eval')
    @commands.is_owner()
    async def _eval(self, ctx, *, body: str):
        """Evaluates a code"""

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())

        body = utils.message.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')

    @commands.command()
    async def invite(self, ctx):
        '''
        Get an invite link to add Potate to your server.
        '''
        link = "https://discord.com/api/oauth2/authorize?client_id=709016147676364812&permissions=268823782&scope=bot"
        embed = discord.Embed(colour=ctx.me.colour, title='Invite Potate!',
                              description=f'To add me to your server, [click here]({link})')
        return await ctx.send(embed=embed)

    @commands.command()
    async def support(self, ctx):
        '''
        Get invite link to the POTATE support server.
        '''
        supprtText = f'[POTATE | Support]({self.bot.config["support_server"]})\nJoin now to get help report bugs or suggest commands.'
        return await ctx.send(embed=utils.InformationEmbed(description=supprtText))

    @commands.command(aliases=['about'])
    async def info(self, ctx):
        '''
        Get information about the QU Rate My Prof bot.
        '''
        diff_seconds = (datetime.now() -
                        self.bot.bot_start_time).total_seconds()

        years = divmod(diff_seconds, 31536000)
        months = divmod(years[1], 2592000)
        weeks = divmod(months[1], 604800)
        days = divmod(weeks[1], 86400)
        hours = divmod(days[1], 3600)
        minutes = divmod(hours[1], 60)

        time_diff = ''

        if years[0]:
            if years[0] > 1:
                time_diff += f'{int(years[0])} Years '
            else:
                time_diff += f'{int(years[0])} Year '

        if months[0]:
            if months[0] > 1:
                time_diff += f'{int(months[0])} Months '
            else:
                time_diff += f'{int(months[0])} Month '

        if weeks[0]:
            if weeks[0] > 1:
                time_diff += f'{int(weeks[0])} Weeks '
            else:
                time_diff += f'{int(weeks[0])} Week '

        if days[0]:
            if days[0] > 1:
                time_diff += f'{int(days[0])} Days '
            else:
                time_diff += f'{int(days[0])} Day '

        if hours[0]:
            if hours[0] > 1:
                time_diff += f'{int(hours[0])} Hours '
            else:
                time_diff += f'{int(hours[0])} Hour '

        if minutes[0]:
            if minutes[0] > 1:
                time_diff += f'{int(minutes[0])} Minutes '
            else:
                time_diff += f'{int(minutes[0])} Minute '

        if not time_diff:
            time_diff = f'{int(diff_seconds)} Seconds'

        info_text = \
            '''
            Potate is a general purpose bot made by Got \'em#3239.\n\nIt is currently under active development and taking commmand suggestions from all users. If you have a command idea you would like to suggest, feel free to join the support server. I look forward to working with the community to create a bot everyone will love.
            '''
        embed = utils.InformationEmbed(title='Potate', description=info_text)

        embed.add_field(name='Uptime', value=time_diff, inline=False)
        embed.add_field(name='Users', value=len(self.bot.users))
        embed.add_field(name='Servers', value=len(self.bot.guilds))
        embed.add_field(
            name='Commands',
            value=sum(1 for _ in self.bot.walk_commands()))

        embed.add_field(
            name="Bot Invite",
            value=f'[Click here]({self.bot.config["invite_link"]})')
        embed.add_field(
            name="Support",
            value=f'[Click here]({self.bot.config["invite_link"]})')
        embed.add_field(
            name="Vote",
            value=f'[Click here](https://top.gg/bot/709016147676364812/vote)')

        return await ctx.send(embed=embed)

    # @commands.command(
    #     aliases=["h"],
    #     usage="command (or) cog"
    # )
    # async def help(self, ctx, command_or_cog=None):
    #     embeds = []
    #     embed = utils.InformationEmbed(title="Help")
    #     embeds.append(embed)
    #     return await utils.paginator(self, ctx, embeds)


def setup(bot):
    bot.add_cog(Meta(bot))
