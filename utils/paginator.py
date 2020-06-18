import asyncio
import discord
from discord.ext.commands import Paginator as BasePaginator
from discord.ext import commands
import typing as t
from discord.ext.commands import Bot, Context


class CannotPaginate(Exception):
    """
    Base Exception Class for Custom error 'Cannot Paginate'
    """

    pass


class Paginator:
    """
    Implements a paginator that queries the user for the
    pagination interface.
    Pages are 1-index based, not 0-index based.
    If the user does not reply within 2 minutes then the pagination
    interface exits automatically.

    

     
    """

    def __init__(self, ctx: commands.Context, entries: t.List[str], max_size: int = 500, show_page_length: bool = True,) -> None:

        self.ctx = ctx
        self.bot: Bot = self.ctx.bot
        self.entries = entries
        self.max_size = max_size
        self.show_page_length = show_page_length

        # Checking permissions, will raise CannotPaginate if missing a permission
        if ctx.guild is not None:
            self.permissions = ctx.channel.permissions_for(ctx.guild.me)
        else:
            self.permissions = ctx.channel.permissions_for(ctx.bot.user)

        self.permissions = ctx.channel.permissions_for(ctx.guild.me if ctx.guild is not None else ctx.bot.user)

        perms = self.permissions
        mandatory_permissions = [
            perms.send_messages,
            perms.embed_links,
            perms.add_reactions,
            perms.read_message_history,
        ]

        for permission in mandatory_permissions:
            if not permission:
                raise CannotPaginate(
                    f"""
            Bot lacks a mandatory permission to paginate:\n\t
            Permission: {permission}\n\t
            Server: {self.guild.name} ({self.guild.id})\n\t
            Command & Author: {ctx.command.name} ({ctx.author.id}) & {ctx.author.name}
            """
                )

        self.page = 0
        self.embed = discord.Embed()

        # Instanciating a base paginator and adding lines
        self.paginator = paginator = BasePaginator(max_size=self.max_size, prefix="", suffix="")

        for entry in entries:
            paginator.add_line(entry)

    async def send(self, timeout: t.Union[int, float] = 300.0, **kwargs: t.Union[str, discord.Emoji],) -> None:
        """
    Sends a paginator and processes it according to the reactions passed by the author.

  
        """

        ctx: Context = self.ctx
        page = self.page
        embed = self.embed
        paginator = self.paginator

        embed.description = paginator.pages[page]

        # Check if show_page_length is True before adding a footer to show page length
        if self.show_page_length:
            embed.set_footer(text=f"Page {page + 1}/{len(paginator.pages)}")

        # Reaction emojis. Can be overridden by kwargs.
        reaction_emojis = {
            "first_page_emoji": "⏮️",  # First page
            "prev_page_emoji": "⬅️",  # Previous Page
            "next_page_emoji": "➡️",  # Next Page
            "last_page_emoji": "⏭️",  # Last Page
            "exit_emoji": "<:trashcan:722035312238526505>",  # Stop paginator and delete message (trashcan)
        }
        for key in reaction_emojis.keys():
            if key in [str(_key) for _key in kwargs]:
                reaction_emojis[key] = kwargs[key]

        # Sending the initial message
        message: discord.Message = await ctx.send(embed=embed)

        for value in reaction_emojis.values():
            await message.add_reaction(value)

        # Reaction checker
        def check(reaction: discord.Reaction, user: t.Union[discord.Member, discord.User]) -> bool:
            return all(
                (
                    reaction.message.id == message.id,  # The reaction was made on the initial message
                    str(reaction.emoji) in reaction_emojis.values(),  # Reaction emoji is one of the emojis inside of reaction_emojis
                    user.id != ctx.bot.user.id,  # User is not this bot
                    user.bot is False,  # User is not a bot
                    user.id == ctx.author.id,  # User is the command invoker, we don't want random people to scroll the pages for us.
                )
            )

        embed.description = paginator.pages[page]

        if self.show_page_length:
            embed.set_footer(text=f"Page {page + 1}/{len(paginator.pages)}")

        # Looping over to see if the user responds with a reaction before the timeout
        # Will break if the timeout is reached
        while True:
            try:
                reaction, user = await ctx.bot.wait_for("reaction_add", timeout=timeout, check=check)
            except asyncio.TimeoutError:
                # Timeup!
                # Clearing all the reactions on the initial messages and breaking out
                await message.clear_reactions()
                break

            if str(reaction.emoji) == reaction_emojis["exit_emoji"]:
                # Delete the message and exit if the reaction is trashcan
                return await message.delete()

            if reaction.emoji == reaction_emojis["first_page_emoji"]:
                # Changes the page to the first page of the paginator and updates the initial message

                await message.remove_reaction(reaction.emoji, user)
                page = 0
                embed.description = paginator.pages[page]
                if self.show_page_length:
                    embed.set_footer(text=f"Page {page + 1}/{len(paginator.pages)}")
                await message.edit(embed=embed)

            if reaction.emoji == reaction_emojis["last_page_emoji"]:
                # Changes the page to the last page of the paginator and updates the initial message

                await message.remove_reaction(reaction.emoji, user)
                page = len(paginator.pages) - 1

                embed.description = paginator.pages[page]
                if self.show_page_length:
                    embed.set_footer(text=f"Page {page + 1}/{len(paginator.pages)}")
                await message.edit(embed=embed)

            if reaction.emoji == reaction_emojis["prev_page_emoji"]:
                # Goes back a page and updates the initial message
                # Continues/Ignores the reaction if the page is already at the first paginator
                # page since it cannot go past the first page

                await message.remove_reaction(reaction.emoji, user)
                if page == 0:
                    continue
                page -= 1

                embed.description = paginator.pages[page]
                if self.show_page_length:
                    embed.set_footer(text=f"Page {page + 1}/{len(paginator.pages)}")
                await message.edit(embed=embed)

            if reaction.emoji == reaction_emojis["next_page_emoji"]:
                # Goes forward a page and updates the initial message
                # Continues/Ignores the reaction if the page is already at the last paginator
                # page since it cannot go past the last page

                await message.remove_reaction(reaction.emoji, user)
                if page == len(paginator.pages) - 1:
                    continue
                page += 1

                embed.description = paginator.pages[page]
                if self.show_page_length:
                    embed.set_footer(text=f"Page {page + 1}/{len(paginator.pages)}")
                await message.edit(embed=embed)
