#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gtk
import sys, math, os

plug_in_proc = "weahtr-guides"

def weaHTR_guides_run(procedure, run_mode, image, drawables, config, data):
  if len(drawables) > 1:
    return procedure.new_return_values(
         Gimp.PDBStatusType.CALLING_ERROR,
         GLib.Error(f"Procedure '{plug_in_proc}' works with zero or one layer.")
         )
  elif len(drawables) == 1:
    if not isinstance(drawables[0], Gimp.Layer):
      return procedure.new_return_values(
         Gimp.PDBStatusType.CALLING_ERROR,
         GLib.Error(f"Procedure '{plug_in_proc}' works with layers only.")
         )

  # GUI stuff -----
  if run_mode == Gimp.RunMode.INTERACTIVE:
    GimpUi.init(plug_in_proc)

    # setup GUI
    dialog = GimpUi.ProcedureDialog.new(procedure, config, "weaHTR Guides")
    dialog.fill(["dir", "text"])
    
    if not dialog.run():
      dialog.destroy()
      return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, None)
    else:
      dialog.destroy()

  # actual plugin functionality ------

  file         = config.get_property('text')
  directory    = config.get_property('dir')
  filename = os.path.join(directory, file)

  # open session
  Gimp.context_push()
  
  # create list elements to store guide details
  rows = []
  cols = []

  # collect all guide values
  index = Gimp.Image.find_next_guide(image,0)
  while index > 0:
    if Gimp.Image.get_guide_orientation(image, index) == Gimp.OrientationType.HORIZONTAL:
      rows.append(Gimp.Image.get_guide_position(image, index))
    else:
      cols.append(Gimp.Image.get_guide_position(image, index))
    
    # increment guide index
    index = Gimp.Image.find_next_guide(image, index)
  
  # sort the values incrementally
  rows = sorted(rows)
  cols = sorted(cols)
  
  # convert to strings
  img_name = '"filename" : "{}"'.format(os.path.basename(Gimp.Image.get_file(image)))
  rows = '"rows" : [{}]'.format(','.join(map(str,rows))) 
  cols = '"cols" : [{}]'.format(','.join(map(str,cols)))
  
  # save file as json format, manually formatted
  # to avoid too many libraries
  savefile = open( u'' + filename, 'w')
  guide_str_data = "{" + img_name + "," + rows + "," + cols + "}"
  savefile.write(guide_str_data + "\n")
  savefile.close()
  
  # close session
  Gimp.context_pop()
  Gimp.displays_flush()

  return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)

class weaHTR_guides (Gimp.PlugIn):
  def do_query_procedures(self):
    return [ plug_in_proc ]

  def do_create_procedure(self, name):
    procedure = None

    if name == plug_in_proc:
      procedure = Gimp.ImageProcedure.new(self, name,
                                          Gimp.PDBProcType.PLUGIN,
                                          weaHTR_guides_run, None)
      procedure.set_menu_label("_weahtr save guides ...")
      procedure.set_attribution("Koen Hufkens", "(c) BlueGreen Labs","2025")
      procedure.add_menu_path ("<Image>/Image/Guides/")
      procedure.set_documentation ("Plugin to save rows and columns for the weaHTR python workflow.")

      procedure.add_string_argument("text", "Filename", None, "guides.json",
                                      GObject.ParamFlags.READWRITE)
      procedure.add_file_argument("dir", "Directory", None,
                                      Gimp.FileChooserAction.SELECT_FOLDER, True, None,
                                      GObject.ParamFlags.READWRITE)
                                      
    return procedure

Gimp.main(weaHTR_guides.__gtype__, sys.argv)
