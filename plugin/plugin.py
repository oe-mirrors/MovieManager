from __future__ import absolute_import
from Plugins.Plugin import PluginDescriptor

plugin_path = None

def main(session, service, **kwargs):
	from . import ui
	session.open(ui.MovieManager, service, session.current_dialog)

def Plugins(path, **kwargs):
	global plugin_path
	plugin_path = path
	return PluginDescriptor(name=_("Movie manager"), description =_("Movie manager"), where=PluginDescriptor.WHERE_MOVIELIST, fnc=main)