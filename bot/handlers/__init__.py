from aiogram import Router
from . import commands
from . import expense_commands


def get_routers() -> list[Router]:
    return [
        commands.router,
        expense_commands.router
    ]