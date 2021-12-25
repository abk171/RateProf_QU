from datetime import datetime
from typing import List

import bot.utils.views as views
import discord
import pytz


class SuccessEmbed(discord.Embed):
    def __init__(self, *args, **kvargs):
        super().__init__(*args, **kvargs)
        self.color = discord.Colour.green()


class ErrorEmbed(discord.Embed):
    def __init__(self, *args, **kvargs):
        super().__init__(*args, **kvargs)
        self.color = discord.Colour.red()


class InformationEmbed(discord.Embed):
    def __init__(self, *args, **kvargs):
        super().__init__(*args, **kvargs)
        self.color = discord.Colour.blue()


class ConfirmationEmbed(discord.Embed):
    def __init__(self, *args, **kvargs):
        super().__init__(*args, **kvargs)
        self.color = discord.Colour.gold()


def chunkinate(l: list, chunk_size: int) -> List[List]:
    return [l[i: i+chunk_size] for i in range(0, len(l), max(1, chunk_size))]


async def paginator(self, ctx, embeds):
    if len(embeds) == 0:
        return

    if len(embeds) == 1:
        return await ctx.send(embed=embeds[0])

    total_pages = len(embeds)
    page = 0

    embeds[page].set_footer(text=f'Page {page+1}/{total_pages}')
    view = views.Page(ctx)
    message = await ctx.send(embed=embeds[page], view=view)

    while True:
        view_timeout = await view.wait()
        if view_timeout:
            try:
                await message.edit(view=None)
            except:
                pass
            break

        reaction = view.value
        view = views.Page(ctx)

        if reaction == '▶️':
            if page == total_pages-1:
                page = 0
            else:
                page += 1

            embeds[page].set_footer(text=f'Page {page+1}/{total_pages}')
            await message.edit(embed=embeds[page], view=view)

        elif reaction == '◀️':
            if page == 0:
                page = total_pages - 1
            else:
                page -= 1

            embeds[page].set_footer(text=f'Page {page+1}/{total_pages}')
            await message.edit(embed=embeds[page], view=view)


def time_difference(t1: datetime, t2: datetime):
    # https://stackoverflow.com/questions/1345827/how-do-i-find-the-time-difference-between-two-datetime-objects-in-python
    diff_seconds = (t2 - t1).total_seconds()

    years = divmod(diff_seconds, 31536000)
    months = divmod(years[1], 2592000)
    weeks = divmod(months[1], 604800)
    days = divmod(weeks[1], 86400)

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

    if days[0] > 1:
        time_diff += f'{int(days[0])} Days'

    if not time_diff:
        time_diff = '0 Days'

    return time_diff
