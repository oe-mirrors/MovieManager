from __future__ import absolute_import
from __future__ import print_function
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
from . import _, ngettext

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.Button import Button
from Components.Label import Label
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Components.config import config
import skin
import os
from .myselectionlist import MySelectionList
from .ui import PKLFILE, cfg

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
		<widget name="description" position="5,325" zPosition="2" size="550,92" valign="center" halign="left" font="Regular;20" foregroundColor="white"/>
	</screen>"""

	def __init__(self, session, pkl_paths):
		Screen.__init__(self, session)
		self.setTitle(_("Directories with local setting"))

		self.skinName = ["pklMovieManager", "Setup"]

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button()
		self["key_blue"] = Button()
		self["key_yellow"] = Button()

		self.list = MySelectionList([])
		self.pklPaths = pkl_paths
		self.reloadList()
		self["description"] = Label()

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"cancel": self.exit,
				"ok": self.list.toggleSelection,
				"red": self.exit,
				"blue": self.list.toggleAllSelection,
				"yellow": self.remove,
			})

		text = _("Remove current item or select items with 'OK' or 'Inversion' and then use remove.")
		self["description"].setText(text)

	def reloadList(self):
		self.pklPaths.sort()
		for idx, x in enumerate(self.pklPaths):
			self.list.addSelection(x, "%s" % x, idx, False)

		self["config"] = self.list
		if self.list.len():
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
			text = ngettext("Are You sure to delete %s setting?", "Are You sure to delete %s settings?", selected) % selected
			self.session.openWithCallback(self.deleteSelected, MessageBox, text, type=MessageBox.TYPE_YESNO, default=False)

	def deleteSelected(self, choice):
		if choice:
			data = self.list.getSelectionsList()
			if not len(data):
				data = [self["config"].getCurrent()[0]]
			for item in data:
				try:
					os.unlink("%s/%s" % (item[0], PKLFILE))
					self.list.removeSelection(item)
					self.pklPaths.pop(item[0])
				except:
					print("[pklMovieManager] error remove %s" % PKLFILE)
			if not len(self.list.list):
				self.exit()

	def exit(self):
		self.close()
