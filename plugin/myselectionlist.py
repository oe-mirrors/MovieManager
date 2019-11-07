from Components.MenuList import MenuList
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN, SCOPE_PLUGINS
from enigma import eListboxPythonMultiContent, eListbox, gFont, getDesktop, RT_HALIGN_LEFT
from Tools.LoadPixmap import LoadPixmap
from plugin import plugin_path
import skin

resolution = ""
if getDesktop(0).size().width() <= 1280:
	resolution = "_sd"
select_png = None
select_png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, plugin_path + "/png/select_on%s.png" % resolution))
if select_png is None:
	select_png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "icons/select_on.png"))

def MySelectionEntryComponent(description, value, index, selected):
	dx, dy, dw, dh = skin.parameters.get("ImsSelectionListDescr",(35, 2, 650, 30))
	res = [
		(description, value, index, selected),
		(eListboxPythonMultiContent.TYPE_TEXT, dx, dy, dw, dh, 0, RT_HALIGN_LEFT, description)
	]
	if selected:
		ix, iy, iw, ih = skin.parameters.get("ImsSelectionListLock",(0, 0, 24, 24))
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, ix, iy, iw, ih, select_png))
	return res

class MySelectionList(MenuList):
	def __init__(self, list = None, enableWrapAround = False):
		MenuList.__init__(self, list or [], enableWrapAround, content = eListboxPythonMultiContent)
		font = skin.fonts.get("ImsSelectionList", ("Regular", 20, 30))
		self.l.setFont(0, gFont(font[0], font[1]))
		self.l.setItemHeight(font[2])

	def addSelection(self, description, value, index, selected = True):
		self.list.append(MySelectionEntryComponent(description, value, index, selected))
		self.setList(self.list)

	def toggleSelection(self):
		if len(self.list):
			idx = self.getSelectedIndex()
			item = self.list[idx][0]
			self.list[idx] = MySelectionEntryComponent(item[0], item[1], item[2], not item[3])
			self.setList(self.list)

	def getSelectionsList(self):
		return [ (item[0][0], item[0][1], item[0][2]) for item in self.list if item[0][3] ]

	def toggleAllSelection(self):
		for idx,item in enumerate(self.list):
			item = self.list[idx][0]
			self.list[idx] = MySelectionEntryComponent(item[0], item[1], item[2], not item[3])
		self.setList(self.list)

	def removeSelection(self, item):
		for it in self.list:
			if it[0][0:3] == item[0:3]:
				self.list.pop(self.list.index(it))
				self.setList(self.list)
				return

	def toggleItemSelection(self, item):
		for idx, i in enumerate(self.list):
			if i[0][0:3] == item[0:3]:
				item = self.list[idx][0]
				self.list[idx] = MySelectionEntryComponent(item[0], item[1], item[2], not item[3])
				self.setList(self.list)
				return

	def sort(self, sortType=False, flag=False):
		# sorting by sortType: # 0 - name, 1 - item, 2 - index, 3 - selected
		self.list.sort(key=lambda x: x[0][sortType],reverse=flag)
		self.setList(self.list)

	def len(self):
		return len(self.list)
