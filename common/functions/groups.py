import discord

from common.components.buttons.groupjoin import GroupJoin
from common.components.buttons.groupleave import GroupLeave
from common.components.buttons.groupmembers import GroupMembers
from common.components.buttons.grouprefresh import GroupRefresh
from common.database import Group


async def build_group_info(interaction: discord.Interaction, group: Group):
    group = await interaction.client.db.get_group(str(interaction.guild.id), group.id)
    members = group.get_members(interaction.guild)
    em = discord.Embed(color=interaction.client.config.colors["main"], title=group.name,
                       description=group.description)
    em.set_thumbnail(url=interaction.guild.icon.with_static_format("png").with_size(512).url)
    em.add_field(name="Members:", value=f"{len(members)}")
    em.add_field(name="Creator:", value=f"<@{group.creator}>")
    view = discord.ui.View(timeout=None)
    view.add_item(GroupRefresh(interaction.client.db, group.id))
    view.add_item(GroupJoin(interaction.client.db, group.id))
    view.add_item(GroupLeave(interaction.client.db, group.id))
    view.add_item(GroupMembers(interaction.client.db, group.id))
    return em, view
