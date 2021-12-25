import discord


class Confirm(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.value = None
        self.ctx = ctx

    @discord.ui.button(label='YES', style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(label='NO', style=discord.ButtonStyle.red)
    async def no(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = False
        self.stop()

    async def interaction_check(self, interaction):
        return True if interaction.user.id == self.ctx.author.id else False


class Page(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.value = None
        self.ctx = ctx

    @discord.ui.button(label='BACK', style=discord.ButtonStyle.grey)
    async def left(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = "◀️"
        self.stop()

    @discord.ui.button(label='NEXT', style=discord.ButtonStyle.grey)
    async def right(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = "▶️"
        self.stop()

    async def interaction_check(self, interaction):
        return True if interaction.user.id == self.ctx.author.id else False


class Details(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.value = None
        self.ctx = ctx

    @discord.ui.button(label='MORE INFO', style=discord.ButtonStyle.blurple)
    async def info(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = True
        self.stop()

    async def interaction_check(self, interaction):
        return True if interaction.user.id == self.ctx.author.id else False
