"""Example theme plugin using only the stable plugin interfaces."""

from dataclasses import dataclass

from src.plugins import Plugin, PluginContext, THEME


@dataclass(frozen=True)
class PlainTheme:
    """Small immutable theme value for host application interpretation."""

    name: str = "plain"
    foreground: str = "#111111"
    background: str = "#ffffff"


class PlainThemePlugin(Plugin):
    """Register an immutable theme without touching the rendering pipeline."""

    def activate(self, context: PluginContext) -> None:
        """Register the theme through the plugin-scoped registrar."""
        context.registrar.register(THEME, PlainTheme())
