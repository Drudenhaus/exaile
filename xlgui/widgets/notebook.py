# Copyright (C) 2010 Adam Olsen
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
#
# The developers of the Exaile media player hereby grant permission
# for non-GPL compatible GStreamer and Exaile plugins to be used and
# distributed together with GStreamer and Exaile. This permission is
# above and beyond the permissions granted by the GPL license by which
# Exaile is covered. If you modify this code, you may extend this
# exception to your version of the code, but you are not obligated to
# do so. If you do not wish to do so, delete this exception statement
# from your version.


import gtk, gobject, pango
from xl.nls import gettext as _
from xlgui.widgets import menu

class SmartNotebook(gtk.Notebook):
    def __init__(self):
        gtk.Notebook.__init__(self)
        self.set_scrollable(True)
        self.connect('button-press-event', self.on_button_press)

    def get_current_tab(self):
        return self.get_nth_page(self.get_current_page())

    def add_tab(self, tab, page, position=-1, switch=True):
        """
            Add a tab to the notebook. It will be given focus.

            :param tab: The tab to use
            :type tab: NotebookTab
            :param page: The page to use
            :type page: NotebookPage
            :param position: index to insert page at, or -1 for append
            :type position: int
        """
        self.insert_page(page, tab, position=position)
        self.set_tab_reorderable(page, page.reorderable)
        if switch:
            self.set_current_page(self.page_num(page))

    def add_default_tab(self):
        """
            Action taken when a generic "new tab" option is triggered.
            Subclasses need to override this if they want new tab
            functionality to work automatically.

            :return: The NotebookTab created, or None
        """
        pass

    def remove_page(self, page_num):
        gtk.Notebook.remove_page(self, page_num)
        if self.get_n_pages() == 0:
            self.add_default_tab()

    def on_button_press(self, widget, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 2:
            self.add_default_tab()

# Reduce the notebook tabs' close button padding size.
gtk.rc_parse_string("""
    style "thinWidget" {
        xthickness = 0
        ythickness = 0
    }
    widget "*.tabCloseButton" style "thinWidget"
    """)
class NotebookTab(gtk.EventBox):
    """
        Class to represent a generic tab in a gtk.Notebook.
    """
    menu_provider_name = 'notebooktab' # Change this in subclasses!
    reorderable = True
    def __init__(self, notebook, page):
        """
            :param notebook: The notebook this tab will belong to
            :param page: The page this tab will be associated with
        """
        gtk.EventBox.__init__(self)
        self.set_visible_window(False)

        self.closable = True

        self.notebook = notebook
        self.page = page

        self.menu = menu.ProviderMenu(self.menu_provider_name, self)

        self.connect('button-press-event', self.on_button_press)

        box = gtk.HBox(False, 2)
        self.add(box)

        self.icon = gtk.Image()
        self.icon.set_property("visible", False)
        box.pack_start(self.icon, False, False)

        self.label = gtk.Label(self.page.get_name())
        self.label.set_max_width_chars(20)
        self.label.set_ellipsize(pango.ELLIPSIZE_END)
        box.pack_start(self.label, False, False)

        self.entry = gtk.Entry()
        self.entry.set_width_chars(self.label.get_max_width_chars())
        self.entry.set_text(self.label.get_text())
        self.entry.set_inner_border(gtk.Border(left=1, right=1))
        self.entry.connect('activate', self.on_entry_activate)
        self.entry.connect('focus-out-event', self.on_entry_focus_out_event)
        self.entry.connect('key-press-event', self.on_entry_key_press_event)
        self.entry.set_no_show_all(True)
        box.pack_start(self.entry, False, False)

        self.button = button = gtk.Button()
        button.set_name("tabCloseButton")
        button.set_relief(gtk.RELIEF_NONE)
        button.set_focus_on_click(False)
        button.set_tooltip_text(_("Close tab"))
        button.add(gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU))
        button.connect('clicked', self.close)
        button.connect('button-press-event', self.on_button_press)
        box.pack_end(button, False, False)

        page.set_tab(self)
        page.connect('name-changed', self.on_name_changed)
        self.show_all()

    def set_icon(self, pixbuf):
        """
            Set the primary icon for the tab.

            :param pixbuf: The icon to use, or None to hide
            :type pixbuf: :class:`gtk.gdk.Pixbuf`
        """
        if pixbuf is None:
            self.icon.set_property("visible", False)
        else:
            self.icon.set_from_pixbuf(pixbuf)
            self.icon.set_property("visible", True)

    def set_closable(self, closable):
        self.closable = closable
        self.button.set_sensitive(closable)

    def on_button_press(self, widget, event):
        """
            Handles mouse button events on the tab.

            Typically triggers renaming, closing and menu.
        """
        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            self.start_rename()
        elif event.button == 2:
            self.close()
        elif event.button == 3:
            self.page.tab_menu.popup( None, None, None,
                    event.button, event.time)
            return True

    def on_entry_activate(self, entry):
        """
            Handles end of editing and triggers the actual rename.
        """
        self.entry.props.editing_canceled = False
        self.end_rename()

    def on_entry_focus_out_event(self, widget, event):
        """
            Make defocusing the rename box equivalent to activating it.
        """
        if not self.entry.props.editing_canceled:
            widget.activate()

    def on_entry_key_press_event(self, widget, event):
        """
            Cancel rename if Escape is pressed
        """
        if event.keyval == gtk.keysyms.Escape:
            self.entry.props.editing_canceled = True
            self.end_rename()
            return True

    def on_name_changed(self, *args):
        self.label.set_text(self.page.get_name())

    def start_rename(self):
        """
            Initiates the renaming of a tab, if the page supports this.
        """
        if not self.can_rename():
            return
        self.entry.set_text(self.page.get_name())
        self.label.hide()
        self.button.hide()
        self.entry.show()
        self.entry.select_region(0, -1)
        self.entry.grab_focus()

    def end_rename(self, cancel=False):
        """
            Finishes or cancels the renaming
        """
        name = self.entry.get_text()

        if name.strip() != "" and not self.entry.props.editing_canceled:
            self.page.set_name(name)
            self.label.set_text(name)

        self.entry.hide()
        self.label.show()
        self.button.show()

        self.entry.props.editing_canceled = False

    def can_rename(self):
        return hasattr(self.page, 'set_name')

    def close(self, *args):
        if self.closable and not self.page.emit('closing'):
            self.notebook.remove_page(self.notebook.page_num(self.page))


class NotebookPage(gtk.VBox):
    """
        Base class representing a page. Should never be used directly.

        Subclasses will also need to inherit from gtk.VBox or some
        other gtk widget, as Pages are generally directly added to the
        Notebook.
    """
    menu_provider_name = 'tab-context' #override this in subclasses
    reorderable = True
    __gsignals__ = {
        'name-changed': (
            gobject.SIGNAL_RUN_LAST,
            gobject.TYPE_NONE,
            ()
        ),
        'closing': (
            gobject.SIGNAL_RUN_LAST,
            gobject.TYPE_BOOLEAN,
            ()
        )
    }
    def __init__(self):
        gtk.VBox.__init__(self)
        self.tab = None
        self.tab_menu = menu.ProviderMenu(self.menu_provider_name, self)

    def get_name(self):
        """
            Returns the name of this tab. Should be overriden in subclasses.

            Subclasses can also implement set_name(self, name) to allow
            renaming, but this is not mandatory.
        """
        return "UNNAMED PAGE"

    def set_tab(self, tab):
        """
            Set the tab that holds this page.  This will be called directly
            from the tab itself when it is created, and should not be used
            outside of that.
        """
        self.tab = tab

    def is_current_page(self):
        """
            Returns True if this page is the currently-visible page in
            the Notebook.
        """
        return self.tab.get_nth_page(self.tab.get_current_page()) == self

    def name_changed(self):
        self.emit('name-changed')
