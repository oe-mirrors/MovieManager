# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from os import environ as os_environ
import gettext

def localeInit():
	localedir = resolveFilename(SCOPE_PLUGINS, "Extensions/MovieManager/locale")
	gettext.bindtextdomain('MovieManager', localedir )

def _(txt):
	t = gettext.dgettext("MovieManager", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)