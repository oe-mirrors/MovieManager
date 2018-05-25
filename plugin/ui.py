# -*- coding: utf-8 -*-
# for localized messages
from . import _

#
#  Movie Manager - Plugin E2 for OpenPLi
VERSION = "1.57"
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
from Components.MovieList import MovieList, StubInfo, IMAGE_EXTENSIONS, resetMoviePlayState
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
config.moviemanager.add_bookmark = ConfigYesNo(default=False)
config.moviemanager.clear_bookmarks = ConfigYesNo(default=True)
config.moviemanager.manage_all = ConfigYesNo(default=False)
cfg = config.moviemanager

class MovieManager(Screen, HelpableScreen):
	skin="""
	<screen name="MovieManager" position="center,center" size="600,415" title="List of files">
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
		<widget name="number" position="5,372" size="135,20" zPosition="1" foregroundColor="green" font="Regular;16"/>
		<widget name="size" position="5,392" size="135,20" zPosition="1" foregroundColor="green" font="Regular;16"/>
		<widget name="description" position="140,368" zPosition="2" size="470,46" valign="center" halign="left" font="Regular;16" foregroundColor="white"/>
	</screen>
	"""
	def __init__(self, session, list, current=None):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.session = session
		self.current = current
		self.mainList = list
		self.setTitle(_("List of files") + ":  %s" % config.movielist.last_videodir.value)

		self.original_selectionpng = None
		self.changePng()

		self.accross = False
		self.position = 0
		self.size = 0
		self.list = SelectionList([])
		self["config"] = self.parseMovieList( list, self.list)

		self["description"] = Label()

		self["size"] = Label()
		self["number"] = Label()

		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
			{
			"cancel": (self.exit, _("Exit plugin")),
			"ok": (self.toggleSelection,_("Add or remove item of selection")),
			})
		### CSFDRunActions can be defined in keytranslation.xml
		self["CSFDRunActions"] = ActionMap(["CSFDRunActions"],
			{
				"csfd": self.csfd,
			})
		###
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
			"yellow": (self.sortIndex, _("Sort list")),
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
		self.onShown.append(self.setService)
		self.onLayoutFinish.append(self.moveSelector)

	def parseMovieList(self, movielist, list):
		self.position = 0
		index = 0
		suma=0
		for i, record in enumerate(movielist):
			if record:
				item = record[0]
				if not item.flags & eServiceReference.mustDescent:
					if item == self.current:
						self.position = index
					info = record[1]
					name = info and info.getName(item)
					size = 0
					if info:
						if isinstance(info, StubInfo): # picture
							size = info.getInfo(item, iServiceInformation.sFileSize)
						else:
							size = info.getInfoObject(item, iServiceInformation.sFileSize)
					list.addSelection(name, (item, size), index, False) # movie
					index += 1
					suma+=size
		print "[MovieMnager} list filled with %s items. Size: %s" % (index, self.convertSize(suma))
		self.size = 0
		return list

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
			if not cfg.sensitive.value:
				searchString = searchString.lower()
			for item in self.list.list:
				if cfg.sensitive.value:
					exist = item[0][0].decode('UTF-8', 'replace').startswith(searchString)
				else:
					exist = item[0][0].decode('UTF-8', 'replace').lower().startswith(searchString)
				if exist:
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
		menu.append((_("Rename"),2))
		keys += ["2"]
		if config.usage.setup_level.index == 2:
			menu.append((_("Delete"),8))
			keys += ["8"]
		if cfg.clear_bookmarks.value:
			menu.append((_("Clear bookmarks..."),10))
			keys += [""]
		menu.append((_("Reset playback position"),15))
		keys+=[""]
		menu.append((_("Sort by..."),17))
		keys+=["yellow"]
		if cfg.manage_all.value:
			menu.append((_("Manage files in active bookmarks..."),18))
			keys += ["red"]
		menu.append((_("Options..."),20))
		keys += ["menu"]

		text = _("Select operation:")
		self.session.openWithCallback(self.menuCallback, ChoiceBox, title=text, list=menu, keys=keys)

	def menuCallback(self, choice):
		if choice is None:
			return
		if choice[1] == 2:
			self.renameItem()
		if choice[1] == 5:
			self.copySelected()
		elif choice[1] == 6:
			self.moveSelected()
		elif choice[1] == 8:
			self.deleteSelected()
		elif choice[1] == 10:
			self.session.open(MovieManagerClearBookmarks)
		elif choice[1] == 15:
			self.resetSelected()
		elif choice[1] == 17:
			self.selectSortby()
		elif choice[1] == 18:
			self.accross = True
			self.runManageAll()
		elif choice[1] == 20:
			self.session.open(MovieManagerCfg)

	def selectSortby(self):
		menu = []
		menu.append((_("Original list"), "0"))
		menu.append((_("A-z sort"), "1"))
		menu.append((_("Z-a sort"), "2"))
		if len(self.list.getSelectionsList()):
			menu.append((_("Selected top"), "3"))
		menu.append((_("Original list - reverted"), "4"))
		self.session.openWithCallback(self.sortbyCallback, ChoiceBox, title=_("Sort list:"), list=menu, selection=self.sort)

	def sortbyCallback(self, choice):
		if choice is None:
			return
		self.sort = int(choice[1])
		self.sortList(self.sort)

	def renameItem(self):
		# item ... (name, (service, size), index, status)
		self.extension = ""
		item = self["config"].getCurrent()[0]
		if item:
			name = item[0]
			full_name = os.path.split(item[1][0].getPath())
			if full_name == name: # split extensions for files without metafile
				name, self.extension = os.path.splitext(name)
		self.session.openWithCallback(self.renameCallback, VirtualKeyBoard, title = _("Rename"), text = name)

	def renameCallback(self, name):
		def renameItemInList(list, item, newname):
			a = []
			for list_item in list.list:
				if list_item[0] == item:
					list_item[0] = (newname,) + list_item[0][1:]
					self.position = list_item[0][2]
				a.append(list_item)
			return a
		def reloadNewList(newlist, list):
			index = 0
			for item in newlist:
				list.addSelection(item[0][0], item[0][1], index, item[0][3])
				index+=1
			return list
		def renameItem(item, newname, list):
			new = renameItemInList(list, item, newname)
			self.clearList()
			return reloadNewList(new, self.list)
		def reloadMainList(item):
			if item[1][0].getPath().rpartition('/')[0] == config.movielist.last_videodir.value[0:-1]:
				self.mainList.reload()

		if not name:
			return
		name = "".join((name.strip(), self.extension))
		item = self["config"].getCurrent()[0]
		if item and item[1][0]:
			try:
				path = item[1][0].getPath().rstrip('/')
				meta = path + '.meta'
				if os.path.isfile(meta):
					metafile = open(meta, "r+")
					sid = metafile.readline()
					oldtitle = metafile.readline()
					rest = metafile.read()
					metafile.seek(0)
					metafile.write("%s%s\n%s" %(sid, name, rest))
					metafile.truncate()
					metafile.close()
				else:
					pathname,filename = os.path.split(path)
					newpath = os.path.join(pathname, name)
					print "[ML] rename", path, "to", newpath
					os.rename(path, newpath)
				msg = None
				idx = self.getItemIndex(item)
				self.list = renameItem(item, name, self.list)
				self["config"].moveToIndex(idx)
				reloadMainList(item)

			except OSError, e:
				print "Error %s:" % e.errno, e
				if e.errno == 17:
					msg = _("The path %s already exists.") % name
				else:
					msg = _("Error") + '\n' + str(e)
			except Exception, e:
				import traceback
				print "[ML] Unexpected error:", e
				traceback.print_exc()
				msg = _("Error") + '\n' + str(e)
			if msg:
				self.session.open(MessageBox, msg, type = MessageBox.TYPE_ERROR, timeout = 5)

	def runManageAll(self):
		self.current = self["config"].getCurrent()[0][1][0]
		def setCurrentRef(path):
			self.current_ref = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + path)
			self.current_ref.setName('16384:jpg 16384:png 16384:gif 16384:bmp')
		def readDirectory(bookmark):
			selected_tags = []
			list = MovieList(None, sort_type=MovieList.SORT_GROUPWISE)
			list.reload(self.current_ref, selected_tags)
			return list
		def readLists():
			files = []
			for path in eval(config.movielist.videodirs.saved_value):
				setCurrentRef(path)
				files += readDirectory(path)
				print "[MovieManager] + added files from %s" % path
			print "[MovieManager] readed items from directories in bookmarks"
			return files

		self.clearList()
		self.list = self.parseMovieList(readLists(), self.list)
		self.moveSelector()

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
			if self.accross:
				self.setTitle(_("List of files") + ":  %s" % os.path.realpath(item[0][1][0].getPath()).rpartition('/')[0])
		else:
			self["Service"].newService(None)

	def changePng(self):
		path = resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/mark_select.png")
		if os.path.exists(path):
			import Components.SelectionList
			self.original_selectionpng = Components.SelectionList.selectionpng
			Components.SelectionList.selectionpng = LoadPixmap(cached=True, path=path)

	def getItemIndex(self,item):
		index = 0
		for i in self["config"].list:
			if i[0] == item:
				return index
			index += 1
		return 0

	def clearList(self):
		self.l = self.list
		self.l.setList([])

	def sortIndex(self):
		self.sort +=1
		if self.sort == 3 and  not len(self.list.getSelectionsList()):
			self.sort +=1
		self.sort %=5
		self.sortList(self.sort)

	def sortList(self, sort):
		item = self["config"].getCurrent()[0]
		if sort == 0:	# original input list
			self.list.sort(sortType=2)
		elif sort == 1:	# a-z
			self.list.sort(sortType=0)
		elif sort == 2:	# z-a
			self.list.sort(sortType=0, flag=True)
		elif sort == 3:	# selected top
			self.list.sort(sortType=3, flag=True)
		elif sort == 4:	# original input list reverted
			self.list.sort(sortType=2, flag=True)
		idx = self.getItemIndex(item)
		self["config"].moveToIndex(idx)

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

	def resetSelected(self):
		if self["config"].getCurrent():
			toggle = True
			data = self.list.getSelectionsList()
			if len(data) == 0:
				data = [self["config"].getCurrent()[0]]
				toggle = False
			if len(data):
				for item in data:
					# 0 - name, 1(0 - item, 1-size), 2-index
					current = item[1][0]
					resetMoviePlayState(current.getPath() + ".cuts", current)
					if toggle:
						self.list.toggleItemSelection(item)
					self.mainList.reload()
			self.displaySelectionPars()

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

	def csfd(self):
		def isCSFD():
			try:
				from Plugins.Extensions.CSFD.plugin import CSFD
			except ImportError:
				self.session.open(MessageBox, _("The CSFD plugin is not installed!\nPlease install it."), type = MessageBox.TYPE_INFO,timeout = 5 )
				return False
			else:
				return True
		if isCSFD():
			event = self["config"].getCurrent()
			if event:
				from Plugins.Extensions.CSFD.plugin import CSFD
				self.session.open(CSFD, event[0][0])

def MyMovieLocationBox(session, text, dir, filename = "", minFree = None):
	config.movielist.videodirs.load()
	return LocationBox(session, text = text,  filename = filename, currDir = dir, bookmarks = config.movielist.videodirs, autoAdd = cfg.add_bookmark.value, editDir = True, inhibitDirs = defaultInhibitDirs, minFree = minFree)

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
		self.MovieManagerCfg.append(getConfigListEntry(_("Use target directory as bookmark"), cfg.add_bookmark, _("Set 'yes' if You want add target directories into bookmarks.")))
		self.MovieManagerCfg.append(getConfigListEntry(_("Enable 'Clear bookmark...'"), cfg.clear_bookmarks, _("Enable in menu utility for delete bookmarks in menu.")))
		self.MovieManagerCfg.append(getConfigListEntry(_("Enable 'Manage files in active bookmarks...'"), cfg.manage_all, _("Enable in menu item for manage movies in all active bookmarks as one list.")))

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

class MovieManagerClearBookmarks(Screen, HelpableScreen):
	skin="""
	<screen name="MovieManager" position="center,center" size="600,390" title="List of bookmarks">
		<ePixmap name="red"    position="0,0"   zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on"/>
		<ePixmap name="green"  position="140,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on"/>
		<ePixmap name="yellow" position="280,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on"/>
		<ePixmap name="blue"   position="420,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on"/>
		<widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_green" position="140,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_yellow" position="280,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_blue" position="420,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="config" position="5,50" zPosition="2" size="590,300" foregroundColor="white" scrollbarMode="showOnDemand"/>
		<ePixmap pixmap="skin_default/div-h.png" position="5,355" zPosition="2" size="590,2"/>
		<widget name="description" position="5,360" zPosition="2" size="590,25" valign="center" halign="left" font="Regular;22" foregroundColor="white"/>
	</screen>
	"""
	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.skinName = ["MovieManagerCfg", "Setup"]
		self.session = session

		self.setTitle(_("List of bookmarks"))

		self.list = SelectionList([])
		index = 0
		self.loadAllMovielistVideodirs()
		for bookmark in eval(config.movielist.videodirs.saved_value):
			self.list.addSelection(bookmark, bookmark, index, False)
			index += 1
		self["config"] = self.list

		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
			{
			"cancel": (self.exit, _("Close")),
			"ok": (self.list.toggleSelection, _("Add or remove item of selection")),
			})
		self["MovieManagerActions"] = HelpableActionMap(self, "MovieManagerActions",
			{
			"red": (self.exit, _("Close")),
			"green": (self.deleteSelected, _("Delete selected")),
			"yellow": (self.sortList, _("Sort list")),
			"blue": (self.list.toggleAllSelection, _("Invert selection")),
			}, -2)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Delete"))
		self["key_yellow"] = Button(_("Sort"))
		self["key_blue"] = Button(_("Inversion"))

		self.sort = 0
		self["description"] = Label(_("Select with 'OK' and then remove with 'Delete'."))
		self["config"].onSelectionChanged.append(self.bookmark)

	def loadAllMovielistVideodirs(self):
		sv = config.movielist.videodirs.saved_value
		tmp = eval(sv)
		locations = [[x, None, False, False] for x in tmp]
		for x in locations:
			x[1] = x[0]
			x[2] = True
		config.movielist.videodirs.locations = locations

	def bookmark(self):
		item = self["config"].getCurrent()
		if item:
			text = "%s" % item[0][0]
			self["description"].setText(text)

	def sortList(self):
		if self.sort == 0:	# z-a
			self.list.sort(sortType=0, flag=True)
			self.sort += 1
		elif self.sort == 1 and len(self.list.getSelectionsList()):	# selected top
			self.list.sort(sortType=3, flag=True)
			self.sort += 1
		else:			# a-z
			self.list.sort(sortType=0)
			self.sort = 0

	def deleteSelected(self):
		if self["config"].getCurrent():
			selected = len(self.list.getSelectionsList())
			if not selected:
				selected = 1
			self.session.openWithCallback(self.delete, MessageBox, _("Are You sure to delete %s selected bookmark(s)?") % selected, type=MessageBox.TYPE_YESNO, default=False)

	def delete(self, choice):
		if choice:
			bookmarks = config.movielist.videodirs.value
			data = self.list.getSelectionsList()
			selected = len(data)
			if not selected:
				data = [self["config"].getCurrent()[0]]
				selected = 1
			for item in data:
				# item ... (name, name, index, status)
				self.list.removeSelection(item)
				bookmarks.remove(item[0])
			config.movielist.videodirs.value = bookmarks
			config.movielist.videodirs.save()

	def exit(self):
		self.close()