from __future__ import annotations

from typing import Any, Dict, Optional, List

import discord
from discord.ext import menus

from common.database import Group


class NumberedPageModal(discord.ui.Modal, title='Go to page'):
    page = discord.ui.TextInput(label='Page', placeholder='Enter a number', min_length=1)

    def __init__(self, max_pages: Optional[int]) -> None:
        super().__init__()
        if max_pages is not None:
            as_string = str(max_pages)
            self.page.placeholder = f'Enter a number between 1 and {as_string}'
            self.page.max_length = len(as_string)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.interaction = interaction
        self.stop()


class InteractionPages(discord.ui.View):
    def __init__(
            self,
            source: menus.PageSource,
            *,
            interaction: discord.Interaction,
    ):
        super().__init__()
        self.source: menus.PageSource = source
        self.interaction: discord.Interaction = interaction
        self.message: Optional[discord.Message] = None
        self.current_page: int = 0
        self.clear_items()
        self.fill_items()

    def fill_items(self) -> None:
        self.numbered_page.row = 1
        self.stop_pages.row = 1

        if self.source.is_paginating():
            max_pages = self.source.get_max_pages()
            use_last_and_first = max_pages is not None and max_pages >= 2
            if use_last_and_first:
                self.add_item(self.go_to_first_page)
            self.add_item(self.go_to_previous_page)
            self.add_item(self.go_to_current_page)
            self.add_item(self.go_to_next_page)
            if use_last_and_first:
                self.add_item(self.go_to_last_page)

            self.add_item(self.numbered_page)
            self.add_item(self.stop_pages)

    async def _get_kwargs_from_page(self, page: int) -> Dict[str, Any]:
        value = await discord.utils.maybe_coroutine(self.source.format_page, self, page)
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            return {'content': value, 'embed': None}
        elif isinstance(value, discord.Embed):
            return {'embed': value, 'content': None}
        else:
            return {}

    async def show_page(self, interaction: discord.Interaction, page_number: int) -> None:
        page = await self.source.get_page(page_number)
        self.current_page = page_number
        kwargs = await self._get_kwargs_from_page(page)
        self._update_labels(page_number)
        if kwargs:
            if interaction.response.is_done():
                if self.message:
                    await self.message.edit(**kwargs, view=self)
            else:
                await interaction.response.edit_message(**kwargs, view=self)

    def _update_labels(self, page_number: int) -> None:
        self.go_to_first_page.disabled = page_number == 0
        self.go_to_current_page.label = str(page_number + 1)
        self.go_to_previous_page.label = str(page_number)
        self.go_to_next_page.label = str(page_number + 2)
        self.go_to_next_page.disabled = False
        self.go_to_previous_page.disabled = False
        self.go_to_first_page.disabled = False

        max_pages = self.source.get_max_pages()
        if max_pages is not None:
            self.go_to_last_page.disabled = (page_number + 1) >= max_pages
            if (page_number + 1) >= max_pages:
                self.go_to_next_page.disabled = True
                self.go_to_next_page.label = '…'
            if page_number == 0:
                self.go_to_previous_page.disabled = True
                self.go_to_previous_page.label = '…'

    async def show_checked_page(self, interaction: discord.Interaction, page_number: int) -> None:
        max_pages = self.source.get_max_pages()
        try:
            if max_pages is None:
                # If it doesn't give maximum pages, it cannot be checked
                await self.show_page(interaction, page_number)
            elif max_pages > page_number >= 0:
                await self.show_page(interaction, page_number)
        except IndexError:
            # An error happened that can be handled, so ignore it.
            pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id in (self.interaction.client.owner_id, self.interaction.user.id):
            return True
        await interaction.response.send_message('This pagination menu cannot be controlled by you, sorry!',
                                                ephemeral=True)
        return False

    async def on_timeout(self) -> None:
        if self.message:
            for item in self.children:
                item.disabled = True
            await self.message.edit(view=self)

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        await self.interaction.client.log.error(error)
        print(error)
        if interaction.response.is_done():
            await interaction.followup.send('An unknown error occurred, sorry', ephemeral=True)
        else:
            await interaction.response.send_message('An unknown error occurred, sorry', ephemeral=True)

    async def start(self, *, content: Optional[str] = None, ephemeral: bool = False) -> None:
        await self.source._prepare_once()
        page = await self.source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        if content:
            kwargs.setdefault('content', content)

        self._update_labels(0)
        self.message = await self.interaction.followup.send(**kwargs, view=self, ephemeral=ephemeral)

    @discord.ui.button(label='≪', style=discord.ButtonStyle.grey)
    async def go_to_first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """go to the first page"""
        await self.show_page(interaction, 0)

    @discord.ui.button(label='Back', style=discord.ButtonStyle.blurple)
    async def go_to_previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """go to the previous page"""
        await self.show_checked_page(interaction, self.current_page - 1)

    @discord.ui.button(label='Current', style=discord.ButtonStyle.grey, disabled=True)
    async def go_to_current_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label='Next', style=discord.ButtonStyle.blurple)
    async def go_to_next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """go to the next page"""
        await self.show_checked_page(interaction, self.current_page + 1)

    @discord.ui.button(label='≫', style=discord.ButtonStyle.grey)
    async def go_to_last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """go to the last page"""
        # The call here is safe because it's guarded by skip_if
        await self.show_page(interaction, self.source.get_max_pages() - 1)  # type: ignore

    @discord.ui.button(label='Skip to page...', style=discord.ButtonStyle.grey)
    async def numbered_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """lets you type a page number to go to"""
        if self.message is None:
            return

        modal = NumberedPageModal(self.source.get_max_pages())
        await interaction.response.send_modal(modal)
        timed_out = await modal.wait()

        if timed_out:
            await interaction.followup.send('Took too long', ephemeral=True)
            return
        elif self.is_finished():
            await modal.interaction.response.send_message('Took too long', ephemeral=True)
            return

        value = str(modal.page.value)
        if not value.isdigit():
            await modal.interaction.response.send_message(f'Expected a number not {value!r}', ephemeral=True)
            return

        value = int(value)
        await self.show_checked_page(modal.interaction, value - 1)
        if not modal.interaction.response.is_done():
            error = modal.page.placeholder.replace('Enter', 'Expected')  # type: ignore # Can't be None
            await modal.interaction.response.send_message(error, ephemeral=True)

    @discord.ui.button(label='Quit', style=discord.ButtonStyle.red)
    async def stop_pages(self, interaction: discord.Interaction, button: discord.ui.Button):
        """stops the pagination session."""
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)
        self.stop()


class GroupPages(discord.ui.View):
    def __init__(
            self,
            source: GroupsPageSource,
            *,
            interaction: discord.Interaction,
    ):
        super().__init__()
        self.source: GroupsPageSource = source
        self.interaction: discord.Interaction = interaction
        self.message: Optional[discord.Message] = None
        self.current_page: int = 0
        self.clear_items()
        self.fill_items()

    def fill_items(self) -> None:
        self.numbered_page.row = 2
        self.stop_pages.row = 2

        if self.source.is_paginating():
            max_pages = self.source.get_max_pages()
            use_last_and_first = max_pages is not None and max_pages >= 2
            if use_last_and_first:
                self.add_item(self.go_to_first_page)
            self.add_item(self.go_to_previous_page)
            self.add_item(self.go_to_current_page)
            self.add_item(self.go_to_next_page)
            if use_last_and_first:
                self.add_item(self.go_to_last_page)
            self.add_item(self.group_option_one)
            self.add_item(self.group_option_two)
            self.add_item(self.group_option_three)
            self.add_item(self.group_option_four)
            self.add_item(self.group_option_five)
            self.add_item(self.numbered_page)
            self.add_item(self.stop_pages)
        else:
            self.add_item(self.group_option_one)
            self.add_item(self.group_option_two)
            self.add_item(self.group_option_three)
            self.add_item(self.group_option_four)
            self.add_item(self.group_option_five)

    async def _get_kwargs_from_page(self, page: int) -> Dict[str, Any]:
        value = await discord.utils.maybe_coroutine(self.source.format_page, self, page)
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            return {'content': value, 'embed': None}
        elif isinstance(value, discord.Embed):
            return {'embed': value, 'content': None}
        else:
            return {}

    async def show_page(self, interaction: discord.Interaction, page_number: int) -> None:
        page = await self.source.get_page(page_number)
        self.current_page = page_number
        kwargs = await self._get_kwargs_from_page(page)
        await self._update_labels(page_number)
        if kwargs:
            # noinspection PyUnresolvedReferences
            if interaction.response.is_done():
                if self.message:
                    await self.message.edit(**kwargs, view=self)
            else:
                # noinspection PyUnresolvedReferences
                await interaction.response.edit_message(**kwargs, view=self)

    async def _update_labels(self, page_number: int) -> None:
        self.go_to_first_page.disabled = page_number == 0
        self.go_to_current_page.label = str(page_number + 1)
        self.go_to_previous_page.label = str(page_number)
        self.go_to_next_page.label = str(page_number + 2)
        self.go_to_next_page.disabled = False
        self.go_to_previous_page.disabled = False
        self.go_to_first_page.disabled = False

        group_number = (page_number + 1) * 5
        self.group_option_one.label = group_number - 4
        self.group_option_two.label = group_number - 3
        self.group_option_three.label = group_number - 2
        self.group_option_four.label = group_number - 1
        self.group_option_five.label = group_number

        total_groups = await self.source.get_total_entries()
        self.group_option_one.disabled = (group_number - 4) > total_groups
        self.group_option_two.disabled = (group_number - 3) > total_groups
        self.group_option_three.disabled = (group_number - 2) > total_groups
        self.group_option_four.disabled = (group_number - 1) > total_groups
        self.group_option_five.disabled = group_number > total_groups

        max_pages = self.source.get_max_pages()
        if max_pages is not None:
            self.go_to_last_page.disabled = (page_number + 1) >= max_pages
            if (page_number + 1) >= max_pages:
                self.go_to_next_page.disabled = True
                self.go_to_next_page.label = '…'
            if page_number == 0:
                self.go_to_previous_page.disabled = True
                self.go_to_previous_page.label = '…'

    async def show_checked_page(self, interaction: discord.Interaction, page_number: int) -> None:
        max_pages = self.source.get_max_pages()
        try:
            if max_pages is None:
                # If it doesn't give maximum pages, it cannot be checked
                await self.show_page(interaction, page_number)
            elif max_pages > page_number >= 0:
                await self.show_page(interaction, page_number)
        except IndexError:
            # An error happened that can be handled, so ignore it.
            pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id in (self.interaction.client.owner_id, self.interaction.user.id):
            return True
        await interaction.response.send_message('This pagination menu cannot be controlled by you, sorry!',
                                                ephemeral=True)
        return False

    async def on_timeout(self) -> None:
        if self.message:
            for item in self.children:
                item.disabled = True
            await self.message.edit(view=self)

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        self.interaction.client.log.error(error)
        # noinspection PyUnresolvedReferences
        if interaction.response.is_done():
            await interaction.followup.send('An unknown error occurred, sorry', ephemeral=True)
        else:
            await interaction.response.send_message('An unknown error occurred, sorry', ephemeral=True)

    async def start(self, *, content: Optional[str] = None, ephemeral: bool = False) -> None:
        await self.source._prepare_once()
        page = await self.source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        if content:
            kwargs.setdefault('content', content)

        await self._update_labels(0)
        self.message = await self.interaction.followup.send(**kwargs, view=self, ephemeral=ephemeral)

    @discord.ui.button(label='≪', style=discord.ButtonStyle.grey)
    async def go_to_first_page(self, interaction: discord.Interaction, _button: discord.ui.Button):
        """go to the first page"""
        await self.show_page(interaction, 0)

    @discord.ui.button(label='Back', style=discord.ButtonStyle.blurple)
    async def go_to_previous_page(self, interaction: discord.Interaction, _button: discord.ui.Button):
        """go to the previous page"""
        await self.show_checked_page(interaction, self.current_page - 1)

    @discord.ui.button(label='Current', style=discord.ButtonStyle.grey, disabled=True)
    async def go_to_current_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label='Next', style=discord.ButtonStyle.blurple)
    async def go_to_next_page(self, interaction: discord.Interaction, _button: discord.ui.Button):
        """go to the next page"""
        await self.show_checked_page(interaction, self.current_page + 1)

    @discord.ui.button(label='≫', style=discord.ButtonStyle.grey)
    async def go_to_last_page(self, interaction: discord.Interaction, _button: discord.ui.Button):
        """go to the last page"""
        # The call here is safe because it's guarded by skip_if
        await self.show_page(interaction, self.source.get_max_pages() - 1)  # type: ignore


    @discord.ui.button(label="1", style=discord.ButtonStyle.grey)
    async def group_option_one(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.defer()
        from common.functions.groups import build_group_info
        group_data = (await self.source.get_page(self.current_page))[0]
        em, view = await build_group_info(self.interaction, group_data)
        await interaction.followup.send(embed=em, view=view, ephemeral=True)

    @discord.ui.button(label="2", style=discord.ButtonStyle.grey)
    async def group_option_two(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.defer()
        from common.functions.groups import build_group_info
        group_data = (await self.source.get_page(self.current_page))[1]
        em, view = await build_group_info(self.interaction, group_data)
        await interaction.followup.send(embed=em, view=view, ephemeral=True)

    @discord.ui.button(label="3", style=discord.ButtonStyle.grey)
    async def group_option_three(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.defer()
        from common.functions.groups import build_group_info
        group_data = (await self.source.get_page(self.current_page))[2]
        em, view = await build_group_info(self.interaction, group_data)
        await interaction.followup.send(embed=em, view=view, ephemeral=True)

    @discord.ui.button(label="4", style=discord.ButtonStyle.grey)
    async def group_option_four(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.defer()
        from common.functions.groups import build_group_info
        group_data = (await self.source.get_page(self.current_page))[3]
        em, view = await build_group_info(self.interaction, group_data)
        await interaction.followup.send(embed=em, view=view, ephemeral=True)

    @discord.ui.button(label="5", style=discord.ButtonStyle.grey)
    async def group_option_five(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.defer()
        from common.functions.groups import build_group_info
        group_data = (await self.source.get_page(self.current_page))[4]
        em, view = await build_group_info(self.interaction, group_data)
        await interaction.followup.send(embed=em, view=view, ephemeral=True)

    @discord.ui.button(label='Skip to page...', style=discord.ButtonStyle.grey)
    async def numbered_page(self, interaction: discord.Interaction, _button: discord.ui.Button):
        """lets you type a page number to go to"""
        if self.message is None:
            return

        modal = NumberedPageModal(self.source.get_max_pages())
        # noinspection PyUnresolvedReferences
        await interaction.response.send_modal(modal)
        timed_out = await modal.wait()

        if timed_out:
            await interaction.followup.send('Took too long', ephemeral=True)
            return
        elif self.is_finished():
            await modal.interaction.response.send_message('Took too long', ephemeral=True)
            return

        value = str(modal.page.value)
        if not value.isdigit():
            await modal.interaction.response.send_message(f'Expected a number not {value!r}', ephemeral=True)
            return

        value = int(value)
        await self.show_checked_page(modal.interaction, value - 1)
        # noinspection PyUnresolvedReferences
        if not modal.interaction.response.is_done():
            error = modal.page.placeholder.replace('Enter', 'Expected')  # type: ignore # Can't be None
            await modal.interaction.response.send_message(error, ephemeral=True)

    @discord.ui.button(label='Quit', style=discord.ButtonStyle.red)
    async def stop_pages(self, interaction: discord.Interaction, _button: discord.ui.Button):
        """stops the pagination session."""
        await interaction.response.defer()
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)
        self.stop()


class GroupsPageSource(menus.ListPageSource):
    async def get_total_entries(self):
        return len(self.entries)

    async def get_entries(self):
        return self.entries

    # noinspection PyUnresolvedReferences
    async def format_page(self, menu, entries: List[Group]):
        pages = []
        for index, entry in enumerate(entries, start=menu.current_page * self.per_page):
            pages.append(
                f'## {index + 1}. {entry.name}\n'
                f'{entry.description}\n'
                f'**Members:** {len(entry.members)}\n'
                f'**Creator:** <@{entry.creator}>'
            )

        maximum = self.get_max_pages()
        if maximum > 1:
            footer = f'Page {menu.current_page + 1}/{maximum} ({len(self.entries)} groups)'
            menu.embed.set_footer(text=footer)

        menu.embed.description = '\n'.join(pages)
        return menu.embed


class IndexedPageSource(menus.ListPageSource):
    async def format_page(self, menu, entries):
        pages = []
        for index, entry in enumerate(entries, start=menu.current_page * self.per_page):
            pages.append(f'{index + 1}. {entry}')

        maximum = self.get_max_pages()
        if maximum > 1:
            footer = f'Page {menu.current_page + 1}/{maximum} ({len(self.entries)} entries)'
            menu.embed.set_footer(text=footer)

        menu.embed.description = '\n'.join(pages)
        return menu.embed


class IndexedGroupPages(GroupPages):
    def __init__(self, entries, *, interaction: discord.Interaction, embed: discord.Embed = None):
        super().__init__(GroupsPageSource(entries, per_page=5), interaction=interaction)
        self.embed = embed or discord.Embed(color=discord.Color.blurple())


class IndexedPagesInteraction(InteractionPages):
    def __init__(self, entries, *, interaction: discord.Interaction, embed: discord.Embed = None, per_page: int = 12):
        super().__init__(IndexedPageSource(entries, per_page=per_page), interaction=interaction)
        self.embed = embed or discord.Embed(color=discord.Color.blurple())
