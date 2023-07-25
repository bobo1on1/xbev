#!/usr/bin/env python3

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
from gi import pygtkcompat
pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')
from gi.repository import GLib
import gtk
import gobject
import socket
import errno
import getpass
import sys
import json

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

errormsg = \
"""
Zeroconf not supported, please pass the host as command-line argument.
example:
  xbev 127.0.0.1
"""

class EventWindow:
  def __init__(self, address):
    self.eventconnected = False;
    self.socketopen = False
    self.JSONactive = False
    self.intextentry = False

    self.eventlabel = gtk.Label(label="Waiting for XBMC")
    self.eventlabel.show()
    self.JSONlabel = gtk.Label()
    self.textentry = gtk.Entry()
    self.textentry.connect("changed", self.textevent)

    self.vbox = gtk.VBox()
    self.vbox.pack_start(self.eventlabel)
    self.vbox.pack_start(self.JSONlabel)
    self.vbox.pack_start(self.textentry)
    self.vbox.show()

    self.window = gtk.Window(type=gtk.WINDOW_TOPLEVEL)
    self.window.set_default_size(200, 200)
    self.window.set_title("xbev");
    self.window.connect("destroy", self.destroy)
    self.window.connect("key-press-event", self.keyevent)
    self.window.connect("key-release-event", self.keyevent)
    self.window.add(self.vbox)
    self.window.show()

#process gtk events to make the window show
    while gtk.events_pending():
       gtk.main_iteration()

    if (address == ""):
      try:
        self.browser = zeroconf.Browser({"_xbmc-events._udp" : self.service, "_xbmc-jsonrpc._tcp": self.service})
      except:
        print(errormsg)
        md = gtk.MessageDialog(None, 
             gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR, 
             gtk.BUTTONS_CLOSE, errormsg)
        md.run()
        md.destroy()
        exit()
    else:
      self.connectevent(address, address)
      self.JSONactivate(address)

    GLib.timeout_add_seconds(30, self.ping)

  def service(self, found, service):
    if (service["type"] == "_xbmc-events._udp"):
      if (found == zeroconf.SERVICE_FOUND):
        self.connectevent(service["hostname"], service["name"])
      elif (found == zeroconf.SERVICE_LOST):
        self.disconnectevent(service["name"])
    elif(service["type"] == "_xbmc-jsonrpc._tcp"):
      if (found == zeroconf.SERVICE_FOUND):
        self.JSONactivate(service["hostname"], service["name"])
      elif (found == zeroconf.SERVICE_LOST):
        self.JSONdeactivate(service["name"])

  def connectevent(self, address, name):
    if (not self.eventconnected):
      try:
        identifystr = getpass.getuser() + " on " + socket.gethostname();
      except:
        identifystr = "Unknown"
        pass

      self.xbmc = xbmcclient.XBMCClient(name = identifystr, ip = address)
      self.xbmc.connect()
      self.eventconnected = True;
      self.eventlabel.set_text("Connected to " + name)
      self.eventname = name

  def disconnectevent(self, name = ""):
    if (self.eventconnected and (name == "" or name == self.eventname)):
      self.xbmc.close()
      del self.xbmc
      del self.eventname
      self.eventconnected = False;
      self.eventlabel.set_text("Waiting for XBMC")

  def JSONactivate(self, address, name = ""):
    if (not self.JSONactive):
      self.JSONactive = True
      self.JSONaddress = address
      self.JSONname = name
      self.connectJSON()

  def JSONdeactivate(self, name):
    self.JSONlabel.hide()
    if (self.JSONactive and self.JSONname == name):
      self.disconnectJSON()
      self.JSONactive = False
      del self.JSONaddress
      del self.JSONname

  def connectJSON(self):
    if (self.JSONactive and not self.socketopen):
      try:
        self.socket = socket.create_connection((self.JSONaddress, 9090))
        self.socketopen = True
        self.JSONlabel.hide()
        GLib.io_add_watch(self.socket.fileno(), GLib.IO_IN, self.parseJSON)
      except socket.error as e:
        print(e)
        self.JSONlabel.set_text("JSON-RPC: " + e.args[1])
        self.JSONlabel.show()
        self.socketopen = True
        self.disconnectJSON()
        GLib.timeout_add_seconds(1, self.connectJSON)

    return False

  def disconnectJSON(self):
    self.inputfinished()
    if (self.socketopen):
      self.socket.close()
      del self.socket
      self.socketopen = False

  def parseJSON(self, source, condition):
    if (condition == GLib.IO_IN):
      try:
        jsondata = json.load(self)
        if (jsondata["method"] == "Input.OnInputRequested"):
          self.inputrequested(jsondata["params"]["data"]["value"])
        elif (jsondata["method"] == "Input.OnInputFinished"):
          self.inputfinished()
      except:
        pass

    return self.socketopen

  def read(self):
    data = self.socket.recv(1500)
    if (len(data) == 0):
      self.disconnectJSON()
      self.connectJSON()

    return data

#{ "jsonrpc" : "2.0", "method" : "Input.SendText", "params" : {"text" : "test", "done" : false}}

  def sendJSON(self, inputdone):
    if (self.socketopen):
      jsondict = dict(jsonrpc = "2.0", method = "Input.SendText", params = dict(text = self.textentry.get_text(), done = inputdone))
      self.socket.send(json.dumps(jsondict).encode('utf-8'))

  def inputrequested(self, text):
    self.intextentry = True
    self.textentry.show()
    self.textentry.grab_focus()
#set the text after grabbing focus, since when grabbing focus, all text will be selected
    self.textentry.set_text(text)
    self.textentry.set_position(len(text))

  def inputfinished(self):
    self.intextentry = False
    self.textentry.hide()

  def destroy(self, widget, data=None):
    self.disconnectevent()
    self.disconnectJSON()
    gtk.main_quit()

  def keyevent(self, widget, event):
    if (event.type == gtk.gdk.KEY_PRESS or event.type == gtk.gdk.KEY_RELEASE):
      keyvalstr = gtk.gdk.keyval_name(event.keyval).lower();
      if (self.intextentry and keyvalstr != "escape"):
        if (event.type == gtk.gdk.KEY_PRESS and (keyvalstr == "return" or keyvalstr == "kp_enter")):
          self.sendJSON(True)
      elif (self.eventconnected):
        for i in translate:
          if (i[0] == keyvalstr):
            keyvalstr = i[1]
            break
        print(keyvalstr)
        self.xbmc.send_button_state("KB", keyvalstr, 0, event.type == gtk.gdk.KEY_PRESS)

  def textevent(self, editable):
    self.sendJSON(False)

  def ping(self):
    if (self.eventconnected):
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

