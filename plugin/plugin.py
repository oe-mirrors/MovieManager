from Plugins.Plugin import PluginDescriptor

def main(session, service, **kwargs):
	import ui
	session.open(ui.MovieManager, service, session.current_dialog)

def Plugins(**kwargs):
	return PluginDescriptor(name=_("Movie manager"),description =_("Movie manager"), where=PluginDescriptor.WHERE_MOVIELIST, fnc=main)