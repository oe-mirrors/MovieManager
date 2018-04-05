# -*- coding: utf-8 -*-
# for localized messages
from . import _

#
#  Movie Manager - Plugin E2 for OpenPLi
VERSION = "1.46"
#  by ims (c) 2018 ims21@users.sourceforge.net
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

from Components.config import ConfigSubsection, config, ConfigYesNo, ConfigSelection, getConfigListEntry
from Screens.Screen import Screen
from Tools.Directories import SCOPE_CURRENT_SKIN, resolveFilename
from Tools.LoadPixmap import LoadPixmap
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.Button import Button
from Components.ActionMap import ActionMap, HelpableActionMap
from Screens.HelpMenu import HelpableScreen
from Components.ConfigList import ConfigListScreen
from enigma import eServiceReference, iServiceInformation, eServiceCenter
from Components.SelectionList import SelectionList
from Components.Sources.ServiceEvent import ServiceEvent
from Screens.ChoiceBox import ChoiceBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.MovieSelection import buildMovieLocationList, copyServiceFiles, moveServiceFiles, last_selected_dest
from Screens.LocationBox import LocationBox, defaultInhibitDirs
from Components.MovieList import MovieList, StubInfo, IMAGE_EXTENSIONS
from Tools.BoundFunction import boundFunction
import os

config.moviemanager = ConfigSubsection()
config.moviemanager.sensitive = ConfigYesNo(default=False)
choicelist = []
for i in range(1, 11, 1):
	choicelist.append(("%d" % i))
choicelist.append(("15","15"))
choicelist.append(("20","20"))
config.moviemanager.length = ConfigSelection(default = "0", choices = [("0", _("No"))] + choicelist + [("255", _("All"))])
config.moviemanager.bookmark = ConfigYesNo(default=False)
config.moviemanager.current_item = ConfigYesNo(default=True)
cfg = config.moviemanager

class MovieManager(Screen, HelpableScreen):
	skin="""
	<screen name="MovieManager" position="center,center" size="600,410" title="List of files">
		<ePixmap name="red"    position="0,0"   zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on"/>
		<ePixmap name="green"  position="140,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on"/>
		<ePixmap name="yellow" position="280,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on"/>
		<ePixmap name="blue"   position="420,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on"/>
		<widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_green" position="140,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_yellow" position="280,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_blue" position="420,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<ePixmap pixmap="skin_default/buttons/key_menu.png" position="560,8" size="40,30" zPosition="2" alphatest="on"/>
		<widget name="config" position="5,50" zPosition="2" size="590,280" itemHeight="28" font="Regular;20" foregroundColor="white" scrollbarMode="showOnDemand"/>
		<ePixmap pixmap="skin_default/div-h.png" position="5,335" zPosition="2" size="590,2"/>
		<widget source="Service" render="Label" position="5,342" size="590,28" transparent="1" foregroundColor="grey" font="Regular;18">
			<convert type="MovieInfo">RecordServiceName</convert>
		</widget>
		<widget source="Service" render="Label" position="5,342" size="590,28" transparent="1" font="Regular;18" foregroundColor="grey"  halign="right">
			<convert type="MovieInfo">FileSize</convert>
		</widget>
		<widget source="Service" render="Label" position="5,342" size="590,28" transparent="1" font="Regular;18" foregroundColor="grey" halign="center">
			<convert type="ServiceTime">StartTime</convert>
			<convert type="ClockToText">Format:%a %d.%m.%Y, %H:%M</convert>
		</widget>
		<ePixmap pixmap="skin_default/div-h.png" position="5,363" zPosition="2" size="590,2"/>
		<widget name="number" position="5,372" size="120,20" zPosition="1" foregroundColor="green" font="Regular;16"/>
		<widget name="size" position="5,392" size="120,20" zPosition="1" foregroundColor="green" font="Regular;16"/>
		<widget name="description" position="125,368" zPosition="2" size="470,46" valign="center" halign="left" font="Regular;20" foregroundColor="white"/>
	</screen>
	"""
	def __init__(self, session, list, current=None):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.session = session
		self.mainList = list
		self.setTitle(_("List of files") + ":  %s" % config.movielist.last_videodir.value)

		self.original_selectionpng = None
		self.changePng()

		self.list = SelectionList([])
		index = 0
		self.position = 0
		for i, record in enumerate(list):
			if record:
				item = record[0]
				if not item.flags & eServiceReference.mustDescent:
					if cfg.current_item.value and item == current:
						self.position = index
					info = record[1]
					name = info and info.getName(item)
					size = 0
					if info:
						if isinstance(info, StubInfo): # picture
							size = info.getInfo(item, iServiceInformation.sFileSize)
						else:
							size = info.getInfoObject(item, iServiceInformation.sFileSize)
					self.list.addSelection(name, (item, size), index, False) # movie
					index += 1

		self["config"] = self.list
		self["description"] = Label()
		self.size = 0
		self["size"] = Label()
		self["number"] = Label()

		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
			{
			"cancel": (self.exit, _("Exit plugin")),
			"ok": (self.toggleSelection,_("Add or remove item of selection")),
			})

		tPreview = _("Preview")
		tFwd = _("Skip forward") + " (" + tPreview +")"
		tBack= _("Skip backward") + " (" + tPreview +")"
		sfwd = lambda: self.seekRelative(1, config.seek.selfdefined_46.value * 90000)
		ssfwd = lambda: self.seekRelative(1, config.seek.selfdefined_79.value * 90000)
		sback = lambda: self.seekRelative(-1, config.seek.selfdefined_46.value * 90000)
		ssback = lambda: self.seekRelative(-1, config.seek.selfdefined_79.value * 90000)
		self["MovieManagerActions"] = HelpableActionMap(self, "MovieManagerActions",
			{
			"menu": (self.selectAction, _("Select action")),
			"red": (self.exit, _("Exit plugin")),
			"green": (self.selectAction, _("Select action")),
			"yellow": (self.sortList, _("Sort list")),
			"blue": (self.toggleAllSelection, _("Invert selection")),
			"preview": (self.preview, _("Preview")),
			"stop": (self.stop, _("Stop")),
			"seekFwd": (sfwd, tFwd),
			"seekFwdManual": (ssfwd, tFwd),
			"seekBack": (sback, tBack),
			"seekBackManual": (ssback, tBack),	
			"groupSelect": (boundFunction(self.selectGroup, True), _("Group selection - add")),
			"groupUnselect": (boundFunction(self.selectGroup, False), _("Group selection - remove")),
			}, -2)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Action"))
		self["key_yellow"] = Button(_("Sort"))
		self["key_blue"] = Button(_("Inversion"))

		self.playingRef = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		self.sort = 0
		self["description"].setText(_("Select files with 'OK' or use 'CH+/CH-' and then use 'Menu' or 'Action' for select operation."))

		self["Service"] = ServiceEvent()
		self["config"].onSelectionChanged.append(self.setService)
		self.onShown.append(self.moveSelector)

	def moveSelector(self):
		self["config"].moveToIndex(self.position)
		self.setService()

	def seekRelative(self, direction, amount):
		seekable = self.getSeek()
		if seekable is None:
			return
		seekable.seekRelative(direction, amount)

	def getSeek(self):
		service = self.session.nav.getCurrentService()
		if service is None:
			return None
		seek = service.seek()
		if seek is None or not seek.isCurrentlySeekable():
			return None
		return seek

	def preview(self):
		item = self["config"].getCurrent()
		if item:
			path = item[0][1][0].getPath()
			ext = os.path.splitext(path)[1].lower()
			if ext in IMAGE_EXTENSIONS:
				try:
					from Plugins.Extensions.PicturePlayer import ui
					self.session.open(ui.Pic_Full_View, [((path, False), None)], 0, path)
				except Exception, ex:
					print "[MovieManager] Cannot display", str(ex)
					return
			else:
				self.session.nav.playService(item[0][1][0])

	def stop(self):
		self.session.nav.playService(self.playingRef)

	def selectGroup(self, mark=True):
		if mark:
			txt = _("Add to selection (starts with...)")
		else:
			txt = _("Remove from selection (starts with...)")
		item = self["config"].getCurrent()
		length = int(cfg.length.value)
		name = ""
		if item and length:
			name = item[0][0].decode('UTF-8', 'replace')[0:length]
			txt += "\t%s" % length
		self.session.openWithCallback(boundFunction(self.changeItems, mark), VirtualKeyBoard, title = txt, text = name)

	def changeItems(self, mark, searchString = None):
		if searchString:
			searchString = searchString.decode('UTF-8', 'replace')
			if cfg.sensitive.value:
					for item in self.list.list:
						if item[0][0].decode('UTF-8', 'replace').startswith(searchString):
							if mark:
								if not item[0][3]:
									self.list.toggleItemSelection(item[0])
							else:
								if item[0][3]:
									self.list.toggleItemSelection(item[0])
			else:
				searchString = searchString.lower()
				for item in self.list.list:
					if item[0][0].decode('UTF-8', 'replace').lower().startswith(searchString):
						if mark:
							if not item[0][3]:
								self.list.toggleItemSelection(item[0])
						else:
							if item[0][3]:
								self.list.toggleItemSelection(item[0])
		self.displaySelectionPars()

	def selectAction(self):
		menu = []
		menu.append((_("Copy to..."),5))
		menu.append((_("Move to..."),6))
		keys = ["5","6"]
		if config.usage.setup_level.index == 2:
			menu.append((_("Delete"),8))
			keys+=["8"]
		menu.append((_("Options..."),20))
		keys+=["menu"]

		text = _("Select operation:")
		self.session.openWithCallback(self.menuCallback, ChoiceBox, title=text, list=menu, keys=keys)

	def menuCallback(self, choice):
		if choice is None:
			return
		if choice[1] == 5:
			self.copySelected()
		elif choice[1] == 6:
			self.moveSelected()
		elif choice[1] == 8:
			self.deleteSelected()
		elif choice[1] == 20:
			self.session.open(MovieManagerCfg)

	def toggleAllSelection(self):
		self.list.toggleAllSelection()
		self.displaySelectionPars()

	def toggleSelection(self):
		self.list.toggleSelection()
		item = self["config"].getCurrent()
		if item:
			if item[0][3]:
				self.size += item[0][1][1]
			else:
				self.size -= item[0][1][1]
		self.displaySelectionPars(True)

	def displaySelectionPars(self, singleToggle=False):
		size = ""
		number = ""
		selected = len(self.list.getSelectionsList())
		if selected:
			if singleToggle:
				size = self.convertSize(self.size)
			else:
				size = self.countSizeSelectedItems()
			size = _("Size: %s") % size
			number = _("Selected: %s") % selected
		self["number"].setText(number)
		self["size"].setText(size)

	def countSizeSelectedItems(self):
		self.size = 0
		data = self.list.getSelectionsList()
		if len(data):
			for item in data:
				self.size += item[1][1]
			return "%s" % self.convertSize(self.size)
		return ""

	def setService(self):
		item = self["config"].getCurrent()
		if item:
			self["Service"].newService(item[0][1][0])
		else:
			self["Service"].newService(None)

	def changePng(self):
		path = resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/mark_select.png")
		if os.path.exists(path):
			import Components.SelectionList
			self.original_selectionpng = Components.SelectionList.selectionpng
			Components.SelectionList.selectionpng = LoadPixmap(cached=True, path=path)

	def sortList(self):
		if self.sort == 0:	# reversed
			self.list.sort(sortType=2, flag=True)
			self.sort += 1
		elif self.sort == 1:	# a-z
			self.list.sort(sortType=0)
			self.sort += 1
		elif self.sort == 2:	# z-a
			self.list.sort(sortType=0, flag=True)
			self.sort += 1
		elif self.sort == 3:	# selected top
			self.list.sort(sortType=3, flag=True)
			self.sort += 1
		else:			# default
			self.list.sort(sortType=2)
			self.sort = 0

	def deleteSelected(self):
		def firstConfirmForDelete(choice):
			if choice:
				self.session.openWithCallback(self.delete, MessageBox, _("Plugin does not use the trash or check a running recording!\nDo You want continue and delete %s selected files?") % selected, type=MessageBox.TYPE_YESNO, default=False)
		if self["config"].getCurrent():
			selected = len(self.list.getSelectionsList())
			if not selected:
				selected = 1
			self.session.openWithCallback(firstConfirmForDelete, MessageBox, _("Are You sure to delete %s selected file(s)?") % selected, type=MessageBox.TYPE_YESNO, default=False)

	def delete(self, choice):
		if choice:
			data = self.list.getSelectionsList()
			selected = len(data)
			if not selected:
				data = [self["config"].getCurrent()[0]]
				self.size = data[0][1][1]
				selected = 1
			deleted = 0
			for item in data:
				# item ... (name, (service, size), index, status)
				if self.deleteConfirmed(item):
					deleted += 1
			self.displaySelectionPars()
			self.session.open(MessageBox, _("Sucessfuly deleted %s of %s files...") % (selected, deleted), type=MessageBox.TYPE_INFO, timeout=5)
			if not len(self.list.list):
				self.exit()

	def deleteConfirmed(self, item):
		name = item[0]
		serviceHandler = eServiceCenter.getInstance()
		offline = serviceHandler.offlineOperations(item[1][0])
		try:
			if offline is None:
			        from enigma import eBackgroundFileEraser
			        eBackgroundFileEraser.getInstance().erase(os.path.realpath(item[1][0].getPath()))
			else:
				if offline.deleteFromDisk(0):
					raise Exception, "Offline delete failed"
			self.list.removeSelection(item)
			self.mainList.removeService(item[1][0])
			from Screens.InfoBarGenerics import delResumePoint
			delResumePoint(item[1][0])
			return True
		except Exception, ex:
			self.session.open(MessageBox, _("Delete failed!") + "\n" + name + "\n" + str(ex), MessageBox.TYPE_ERROR, timeout=3)
			return False

	def copySelected(self):
		if self["config"].getCurrent():
			self.selectMovieLocation(title=_("Select destination for copy selected files..."), callback=self.gotCopyMovieDest)

	def gotCopyMovieDest(self, choice):
		if not choice:
			return
		dest = os.path.normpath(choice)
		if dest == config.movielist.last_videodir.value[0:-1]:
			self.session.open(MessageBox, _("Same source and target directory!"), MessageBox.TYPE_ERROR, timeout=3)
			return

		toggle = True
		data = self.list.getSelectionsList()
		if len(data) == 0:
			data = [self["config"].getCurrent()[0]]
			self.size = data[0][1][1]
			toggle = False
		if not self.isFreeSpace(dest):
			return
		if len(data):
			for item in data:
				try:
					# item ... (name, (service, size), index, status)
					copyServiceFiles(item[1][0], dest, item[0])
					if toggle:
						self.list.toggleItemSelection(item)

				except Exception, e:
					self.session.open(MessageBox, str(e), MessageBox.TYPE_ERROR, timeout=2)
		self.displaySelectionPars()

	def moveSelected(self):
		if self["config"].getCurrent():
			self.selectMovieLocation(title=_("Select destination for move selected files..."), callback=self.gotMoveMovieDest)

	def gotMoveMovieDest(self, choice):
		if not choice:
			return
		dest = os.path.normpath(choice)
		src = config.movielist.last_videodir.value
		if dest == src[0:-1]:
			self.session.open(MessageBox, _("Same source and target directory!"), MessageBox.TYPE_ERROR, timeout=3)
			return
		data = self.list.getSelectionsList()
		if len(data) == 0:
			data = [self["config"].getCurrent()[0]]
			self.size = data[0][1][1]
		if not self.isSameDevice(src, dest):
			if not self.isFreeSpace(dest):
				return
		if len(data):
			for item in data:
				try:
					# item ... (name, (service, size), index, status)
					moveServiceFiles(item[1][0], dest, item[0])
					self.list.removeSelection(item)
					self.mainList.removeService(item[1][0])
				except Exception, e:
					self.session.open(MessageBox, str(e), MessageBox.TYPE_ERROR, timeout=3 )
		self.displaySelectionPars()
		if not len(self.list.list):
			self.exit()

	def isSameDevice(self, src, dest):
		if os.stat(src).st_dev != os.stat(dest).st_dev:
			return False
		return True

	def freeSpace(self, path):
		dev = os.statvfs(path)
		return dev.f_bfree * dev.f_bsize

	def isFreeSpace(self, dest):
		free_space = self.freeSpace(dest)
		if free_space <= self.size:
			self.session.open(MessageBox, _("On destination '%s' is %s free space only!") % (dest, self.convertSize(free_space)), MessageBox.TYPE_ERROR, timeout=5)
			return False
		return True

	def exit(self):
		if self.original_selectionpng:
			import Components.SelectionList
			Components.SelectionList.selectionpng = self.original_selectionpng
		self.session.nav.playService(self.playingRef)
		self.close()

	def selectMovieLocation(self, title, callback):
		bookmarks = [("("+_("Other")+"...)", None)]
		buildMovieLocationList(bookmarks)
		self.onMovieSelected = callback
		self.movieSelectTitle = title
		self.session.openWithCallback(self.gotMovieLocation, ChoiceBox, title=title, list=bookmarks)

	def gotMovieLocation(self, choice):
		if not choice:
			# cancelled
			self.onMovieSelected(None)
			del self.onMovieSelected
			return
		if isinstance(choice, tuple):
			if choice[1] is None:
				# Display full browser, which returns string
				self.session.openWithCallback(self.gotMovieLocation, MyMovieLocationBox, self.movieSelectTitle, config.movielist.last_videodir.value)
				return
			choice = choice[1]
		choice = os.path.normpath(choice)

		self.rememberMovieLocation(choice)
		self.onMovieSelected(choice)
		del self.onMovieSelected

	def rememberMovieLocation(self, where):
		if where in last_selected_dest:
			last_selected_dest.remove(where)
		last_selected_dest.insert(0, where)
		if len(last_selected_dest) > 5:
			del last_selected_dest[-1]

	def convertSize(self, filesize):
		if filesize:
			if filesize >= 104857600000:
				return _("%.0f GB") % (filesize / 1073741824.0)
			elif filesize >= 1073741824:
				return _("%.2f GB") % (filesize / 1073741824.0)
			elif filesize >= 1048576:
				return _("%.0f MB") % (filesize / 1048576.0)
			elif filesize >= 1024:
				return _("%.0f kB") % (filesize / 1024.0)
			return _("%d B") % filesize
		return ""

def MyMovieLocationBox(session, text, dir, filename = "", minFree = None):
	config.movielist.videodirs.load()
	return LocationBox(session, text = text,  filename = filename, currDir = dir, bookmarks = config.movielist.videodirs, autoAdd = cfg.bookmark.value, editDir = True, inhibitDirs = defaultInhibitDirs, minFree = minFree)

class MovieManagerCfg(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = ["MovieManagerCfg", "Setup"]
		self.setup_title = _("Options...")
		self.setTitle(self.setup_title)

		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("OK"))
		self["description"] = Label("")

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.save,
			"ok": self.save,
			"red": self.exit,
			"cancel": self.exit
		}, -2)

		self.MovieManagerCfg = []
		self.MovieManagerCfg.append(getConfigListEntry(_("Compare case sensitive"), cfg.sensitive, _("Sets whether to distinguish between uper case and lower case for searching.")))
		self.MovieManagerCfg.append(getConfigListEntry(_("Pre-fill first 'n' filename chars to virtual keyboard"), cfg.length, _("You can set the number of letters from the beginning of the current file name as the text pre-filled into virtual keyboard for easier input via group selection. For 'group selection' use 'CH+/CH-' buttons.")))
		self.MovieManagerCfg.append(getConfigListEntry(_("Use target directory as bookmark"), cfg.bookmark, _("Set 'yes' if You want add target directories into bookmarks.")))
		self.MovieManagerCfg.append(getConfigListEntry(_("Cursor on start to current item"), cfg.current_item, _("If You want on plugin start set cursor to same item as it was on current file in movieplayer list.")))
		ConfigListScreen.__init__(self, self.MovieManagerCfg, on_change = self.changedEntry)
		self.onChangedEntry = []

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()
	def getCurrentEntry(self):
		self["description"].setText(self["config"].getCurrent()[2])
		return self["config"].getCurrent()[0]
	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())
	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary
	###

	def save(self):
		self.keySave()

	def exit(self):
		self.keyCancel()