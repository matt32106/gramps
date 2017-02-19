#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2007  Donald N. Allingham
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

#-------------------------------------------------------------------------
#
# Standard Python modules
#
#-------------------------------------------------------------------------
from ....const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext

#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------
from .. import Rule
from ._matchesfilter import MatchesFilter

#-------------------------------------------------------------------------
#
# IsChildOfFilterMatch
#
#-------------------------------------------------------------------------
class IsChildOfFilterMatch(Rule):
    """Rule that checks for a person that is a child
    of someone matched by a filter"""

    labels      = [ _('Filter name:') ]
    name        = _('Children of <filter> match')
    category    = _('Family filters')
    description = _("Matches children of anybody matched by a filter")

    def prepare(self, db, user):
        self.db = db
        self.map = set()
        filt = MatchesFilter(self.list)
        filt.requestprepare(db, user)
        if user:
            user.begin_progress(self.category,
                                _('Retrieving all sub-filter matches'),
                                db.get_number_of_people())
        for person in db.iter_people():
            if user:
                user.step_progress()
            if filt.apply(db, person):
                self.init_list(person)
        if user:
            user.end_progress()
        filt.requestreset()

    def reset(self):
        self.map.clear()

    def apply(self,db,person):
        return person.handle in self.map

    def init_list(self,person):
        if not person:
            return
        for fam_id in person.get_family_handle_list():
            fam = self.db.get_family_from_handle(fam_id)
            if fam:
                self.map.update(child_ref.ref
                   for child_ref in fam.get_child_ref_list())
