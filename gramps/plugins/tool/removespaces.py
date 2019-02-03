#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2007-2009   Stephane Charette
# Copyright (C) 2019-       Serge Noiraud
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"Find possible leading and/or trailing spaces in places name and people"

#------------------------------------------------------------------------
#
# GNOME/GTK modules
#
#------------------------------------------------------------------------
from gi.repository import (Gtk, Gdk)
from gi.repository import GObject

#------------------------------------------------------------------------
#
# Gramps modules
#
#------------------------------------------------------------------------
from gramps.gen.const import URL_MANUAL_PAGE
from gramps.gui.plug import tool
from gramps.gui.editors import (EditPlace, EditPerson)
from gramps.gen.errors import WindowActiveError
from gramps.gui.managedwindow import ManagedWindow
from gramps.gui.utils import ProgressMeter
from gramps.gui.display import display_help
from gramps.gui.glade import Glade
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.sgettext
ngettext = glocale.translation.ngettext

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
WIKI_HELP_PAGE = '%s_-_Tools' % URL_MANUAL_PAGE
WIKI_HELP_SEC = _('manual|Remove_leading_and_trailing_spaces')

#------------------------------------------------------------------------
#
# RemoveSpaces class
#
#------------------------------------------------------------------------
class RemoveSpaces(ManagedWindow):
    """
    Find leading and trailing spaces in Place names and person names
    """
    def __init__(self, dbstate, user, options_class, name, callback=None):
        uistate = user.uistate

        self.title = _('Remove leading and/or trailing spaces')
        ManagedWindow.__init__(self, uistate, [], self.__class__)
        self.dbstate = dbstate
        self.uistate = uistate
        self.db = dbstate.db

        top_dialog = Glade()

        top_dialog.connect_signals({
            "destroy_passed_object" : self.close,
            "on_help_clicked"       : self.on_help_clicked,
            "on_delete_event"       : self.close,
        })

        window = top_dialog.toplevel
        title = top_dialog.get_object("title")
        self.set_window(window, title, self.title)

        # start the progress indicator
        self.progress = ProgressMeter(self.title, _('Starting'),
                                      parent=uistate.window)
        self.progress.set_pass(_('Looking for possible names with leading or'
                                 ' trailing spaces'),
                               self.db.get_number_of_people())

        self.model = Gtk.ListStore(
            GObject.TYPE_STRING,    # 0==type
            GObject.TYPE_STRING,    # 1==handle
            GObject.TYPE_STRING,    # 2==name/firstname
            GObject.TYPE_STRING)    # 3==surname
        self.model.set_sort_column_id(
            Gtk.TREE_SORTABLE_UNSORTED_SORT_COLUMN_ID, 0)

        self.treeview = top_dialog.get_object("treeview")
        self.treeview.set_model(self.model)
        col1 = Gtk.TreeViewColumn(_('type'),
                                  Gtk.CellRendererText(), text=0)
        col2 = Gtk.TreeViewColumn(_('handle'),
                                  Gtk.CellRendererText(), text=1)
        renderer1 = Gtk.CellRendererText()
        renderer1.set_property('underline-set', True)
        renderer1.set_property('underline', 2) # 2=double underline
        col3 = Gtk.TreeViewColumn(_('name/firstname'), renderer1, text=2)
        renderer2 = Gtk.CellRendererText()
        renderer2.set_property('underline-set', True)
        renderer2.set_property('underline', 2) # 2=double underline
        col4 = Gtk.TreeViewColumn(_('surname'), renderer2, text=3)
        col1.set_resizable(True)
        col2.set_resizable(True)
        col3.set_resizable(True)
        col4.set_resizable(True)
        col1.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        col2.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        col3.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        col4.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        self.treeview.append_column(col1)
        self.treeview.append_column(col2)
        self.treeview.append_column(col3)
        self.treeview.append_column(col4)
        self.treeselection = self.treeview.get_selection()
        self.treeview.connect('row-activated', self.rowactivated_cb)

        self.places()
        self.people()

        # close the progress bar
        self.progress.close()

        self.show()

    def places(self):
        """
        For all places in the database, if the name contains leading or
        trailing spaces.
        """
        for place_handle in self.db.get_place_handles():
            place = self.db.get_place_from_handle(place_handle)
            place_name = place.get_name()
            pname = place_name.get_value()
            found = False
            if pname != pname.strip():
                found = True
            if found:
                value = ('Place', place_handle, pname, "")
                self.model.append(value)
        return True

    def people(self):
        """
        For all persons in the database, if the name contains leading or
        trailing spaces.
        """
        for person_handle in self.db.get_person_handles():
            person = self.db.get_person_from_handle(person_handle)
            primary_name = person.get_primary_name()
            fname = primary_name.get_first_name()
            found = False
            if fname != fname.strip():
                found = True
            sname = primary_name.get_primary_surname().get_surname()
            if sname != sname.strip():
                found = True
            if found:
                value = ('Person', person_handle, fname, sname)
                self.model.append(value)
        return True

    def rowactivated_cb(self, treeview, path, column):
        """
        Called when a row is activated.
        """
        iter_ = self.model.get_iter(path)
        obj_type = self.model.get_value(iter_, 0)
        if obj_type == 'Place':
            handle = self.model.get_value(iter_, 1)
            place = self.dbstate.db.get_place_from_handle(handle)
            if place:
                try:
                    EditPlace(self.dbstate, self.uistate, [], place)
                except WindowActiveError:
                    pass
                return True
        else:
            # obj_type == 'Person':
            handle = self.model.get_value(iter_, 1)
            person = self.dbstate.db.get_person_from_handle(handle)
            if person:
                try:
                    EditPerson(self.dbstate, self.uistate, [], person)
                except WindowActiveError:
                    pass
                return True
        return False

    def on_help_clicked(self, obj):
        """
        Display the relevant portion of Gramps manual.
        """
        display_help(webpage=WIKI_HELP_PAGE, section=WIKI_HELP_SEC)

    def close(self, *obj):
        ManagedWindow.close(self, *obj)

#------------------------------------------------------------------------
#
# RemoveSpacesOptions
#
#------------------------------------------------------------------------
class RemoveSpacesOptions(tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """
    def __init__(self, name, person_id=None):
        """ Initialize the options class """
        tool.ToolOptions.__init__(self, name, person_id)
