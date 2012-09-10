#!/usr/bin/env python

#
# xbev
# Copyright (C) Bob 2012
# 
# xbev is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# xbev is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import socket
import getpass
import sys

import xbmcclient
import zeroconf

translate =\
("quotedbl", "doublequote"),\
("numbersign", "hash"),\
("apostrophe", "quote"),\
("parenleft", "leftbracket"),\
("parenright", "rightbracket"),\
("slash", "forwardslash"),\
("less", "lessthan"),\
("equal", "equals"),\
("greater", "greaterthan"),\
("question", "questionmark"),\
("bracketleft", "opensquarebracket"),\
("bracketright", "closesquarebracket"),\
("asciicircum", "caret"),\
("underscore", "underline"),\
("grave", "leftquote"),\
("braceleft", "openbrace"),\
("bar", "pipe"),\
("braceright", "closebrace"),\
("asciitilde", "tilde"),\
("kp_0", "numpadzero"),\
("kp_1", "numpadone"),\
("kp_2", "numpadtwo"),\
("kp_3", "numpadthree"),\
("kp_4", "numpadfour"),\
("kp_5", "numpadfive"),\
("kp_6", "numpadsize"),\
("kp_7", "numpadseven"),\
("kp_8", "numpadeight"),\
("kp_9", "numpadnine"),\
("kp_divide", "numpaddivide"),\
("kp_multiply", "numpadtimes"),\
("kp_subtract", "numpadminus"),\
("kp_add", "numpadplus"),\
("kp_enter", "enter"),\
("kp_decimal", "numpadperiod"),\
("num_lock", "numlock"),\
("caps_lock", "capslock"),\
("shift_r", "rightshift"),\
("shift_l", "leftshift"),\
("control_r", "rightctrl"),\
("control_l", "leftctrl"),\
("alt_l", "leftalt"),\
("scroll_lock", "scrolllock"),\
("page_up", "pageup"),\
("page_down", "pagedown"),\
("xf86audiomute", "volume_mute"),\
("xf86audiolowervolume", "volume_down"),\
("xf86audioraisevolume", "volume_up"),\
("xf86audioplay", "play_pause"),\
("xf86audiostop", "stop"),\
("xf86audionext", "next_track"),\
("xf86audioprev", "prev_track"),\
("xf86audiopause", "play_pause"),\

#these don't appear to be mapped in XBMC:
#XF86AudioRecord
#XF86AudioRewind

class EventWindow:
  def __init__(self, address):
    self.connected = False;
    self.label = gtk.Label("Waiting for XBMC")

    if (address == ""):
      self.browser = zeroconf.Browser({"_xbmc-events._udp" : self.service})
    else:
      self.connect(address, address)

    self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.window.set_title("xbev");
    self.window.connect("destroy", self.destroy)
    self.window.connect("key-press-event", self.event)
    self.window.connect("key-release-event", self.event)
    self.window.show()
    self.window.add(self.label)
    self.label.show();

    gobject.timeout_add_seconds(30, self.ping)

  def service(self, found, service):
    if (found == zeroconf.SERVICE_FOUND):
      self.connect(service["address"], service["hostname"])
    elif (found == zeroconf.SERVICE_LOST):
      self.disconnect()

  def connect(self, address, name):
    if (not self.connected):
      try:
        identifystr = getpass.getuser() + " on " + socket.gethostname();
      except:
        identifystr = "Unknown"

      self.xbmc = xbmcclient.XBMCClient(name = identifystr, ip = address)
      self.xbmc.connect()
      self.connected = True;
      self.label.set_text("Connected to " + name)

  def disconnect(self):
    if (self.connected):
      self.xbmc.close()
      del self.xbmc
      self.connected = False;
      self.label.set_text("Waiting for XBMC")

  def destroy(self, widget, data=None):
    self.disconnect()
    gtk.main_quit()

  def event(self, widget, event):
    if (self.connected and (event.type == gtk.gdk.KEY_PRESS or event.type == gtk.gdk.KEY_RELEASE)):
      keyvalstr = gtk.gdk.keyval_name(event.keyval).lower();
      for i in translate:
        if (i[0] == keyvalstr):
          keyvalstr = i[1]
          break

      self.xbmc.send_button_state("KB", keyvalstr, 0, event.type == gtk.gdk.KEY_PRESS)

  def ping(self):
    if (self.connected):
      self.xbmc.ping();
    return True

  def main(self):
    gtk.main()

if __name__ == "__main__":
  address = ""
  if (len(sys.argv) > 1):
    address = sys.argv[1]

  eventwindow = EventWindow(address)
  eventwindow.main()

