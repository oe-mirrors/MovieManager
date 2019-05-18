#
#  MovieManager
#
#
#  Coded by ims (c) 2018-2019
#  Support: openpli.org
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# for localized messages
from . import _

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.Button import Button
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.SelectionList import SelectionList
from Screens.MessageBox import MessageBox
from Components.config import config
import skin
import os
from ui import PKLFILE, cfg

class pklMovieManager(Screen):
	skin = """
		<screen name="pklMovieManager" position="center,center" size="560,417" title="MovieManager - directory">
		<ePixmap name="red"    position="0,0"   zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on"/>
		<ePixmap name="green"  position="140,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on"/>
		<ePixmap name="yellow" position="280,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on"/>
		<ePixmap name="blue"   position="420,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on"/>
		<widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_green" position="140,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_yellow" position="280,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_blue" position="420,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="config" position="5,40" zPosition="2" size="550,275" itemHeight="30" font="Regular;20" foregroundColor="white" scrollbarMode="showOnDemand"/>
		<ePixmap pixmap="skin_default/div-h.png" position="5,320" zPosition="2" size="550,2"/>
		<widget name="text" position="5,325" zPosition="2" size="550,92" valign="center" halign="left" font="Regular;20" foregroundColor="white"/>
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Select directory"))

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button()
		self["key_blue"] = Button()
		self["key_yellow"] = Button()

		self.list = SelectionList([])

		self.reloadList()
		self["text"] = Label()

		self["actions"] = ActionMap(["OkCancelActions","ColorActions"],
			{
				"cancel": self.exit,
				"ok": self.list.toggleSelection,
				"red": self.exit,
				"blue": self.list.toggleAllSelection,
				"yellow": self.remove,
			})

		text = _("Select directory with 'OK' or 'Inversion' and remove it.")
		self["text"].setText(text)

	def reloadList(self):
		def lookDirs(path):
			paths = []
			for path, dirs, files in os.walk(path):
				if PKLFILE in files:
					paths.append(path)
			return paths
		def lookFile(path):
			if os.path.exists(path + PKLFILE):
				return True
			return False
		def readLists(current_dir=None):
			paths = []
			if cfg.manage_all.value and config.movielist.videodirs.saved_value:
				dirs = eval(config.movielist.videodirs.saved_value)
				dirs.append(current_dir)
				dirs = set(dirs)
				for path in dirs:
					if cfg.subdirs.value:
						paths += lookDirs(path)
					else:
						if lookFile(path):
							paths.append(path)
			elif current_dir:
				if cfg.subdirs.value:
					paths += lookDirs(current_dir)
				else:
					if lookFile(current_dir):
						paths.append(current_dir)
			else:
				print "[pklMovieManager] no valid bookmarks!"
			return paths

		self.l = self.list
		self.l.setList([])
		nr = 0
		for x in readLists(config.movielist.last_videodir.value.rstrip('/')):
			self.list.addSelection(x, "%s" % x, nr, False)
			nr += 1
		self["config"] = self.list
		if nr:
			self["key_blue"].setText(_("Inversion"))
			self["key_yellow"].setText(_("Remove"))
		else:
			self["key_blue"].setText("")
			self["key_yellow"].setText("")

	def remove(self):
		if self["config"].getCurrent():
			selected = len(self.list.getSelectionsList())
			if not selected:
				selected = 1
			self.session.openWithCallback(self.deleteSelected, MessageBox, _("Are You sure to delete %s selected file(s)?") % selected, type=MessageBox.TYPE_YESNO, default=False)

	def deleteSelected(self, choice):
		if choice:
			data = self.list.getSelectionsList()
			if not len(data):
				data = [self["config"].getCurrent()[0]]
			for item in data:
				try:
					os.unlink("%s/%s" % (item[0], PKLFILE))
				except:
					print "[pklMovieManager] error remove %s" % PKLFILE
			if not len(self.list.list):
				self.exit()
			else:
				self.reloadList()

	def exit(self):
		self.close()
