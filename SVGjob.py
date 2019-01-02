import gc
import os
from PyQt5.QtCore import QObject, QTimer, pyqtSlot
import sys
from time import time
from typing import Any, cast, Dict, List, Optional, Set, TYPE_CHECKING

from UM.Backend.Backend import Backend, BackendState
from UM.Scene.SceneNode import SceneNode
from UM.Signal import Signal
from UM.Logger import Logger
from UM.Message import Message
from UM.PluginRegistry import PluginRegistry
from UM.Resources import Resources
from UM.Platform import Platform
from UM.Qt.Duration import DurationFormat
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Settings.Interfaces import DefinitionContainerInterface
from UM.Settings.SettingInstance import SettingInstance #For typing.
from UM.Tool import Tool #For typing.
from UM.Mesh.MeshData import MeshData #For typing.
from p3t import CDT,Point3
from UM.Job import Job
import matplotlib.pyplot as plt  #TODO:用作测试的 后期得删掉
import matplotlib.tri as tri
from mpl_toolkits.mplot3d import Axes3D

class ProcessSVGJob(Job):
    def __init__(self, polyLine,hole_polyLine):
        super().__init__()
        self._polyLine = polyLine
        self._hole_polyLine = hole_polyLine
        #self._layers = layers
        Logger.log('e',"SB----SB")
        print (polyLine,hole_polyLine)
       # self._scene = Application.getInstance().getController().getScene()
        #self._progress_message = Message(catalog.i18nc("@info:status", "Processing Layers"), 0, False, -1)
        self._abort_requested = False
        self._build_plate_number = None
        self._isTri = False #是否可以获得数据
        self._triangles = None

    ##  终止层的处理。
    #
    #   This abort is made on a best-effort basis, meaning that the actual
    #   job thread will check once in a while to see whether an abort is
    #   requested and then stop processing by itself. There is no guarantee
    #   that the abort will stop the job any time soon or even at all.
    def abort(self):
        self._abort_requested = True

    def setPolyLine(self, new_value):
        self._polyLine = new_value

    def getPolyLine(self):
        return self._polyLine

    def setHole_polyLine(self, new_value):
        self._hole_polyLine = new_value

    def getHole_polyLine(self):
        return self._hole_polyLine

    def getTriangles(self):
        if self._isTri:
            return self._triangles
        else:
            return None

    def run(self):
       # Logger.log('e', polyLine + hole_polyLine)
        start_time = time()
        cdt = CDT(self._polyLine)
        if hole_polyLine:
            cdt.add_hole(self._hole_polyLine)
        self._triangles = cdt.triangulate()
        self._isTri = True
        # fig = plt.figure()
        # ax = Axes3D(fig)
        # for t in triangles:
        #     p0 = [t.a.x, t.a.y, t.a.z]
        #     p1 = [t.b.x, t.b.y, t.b.z]
        #     p2 = [t.c.x, t.c.y, t.c.z]
        #     x = [t.a.x, t.b.x, t.c.x, t.a.x]
        #     y = [t.a.y, t.b.y, t.c.y, t.a.y]
        #     z = [t.a.z, t.b.z, t.c.z, t.a.z]
        #     # 绘制线型图
        #     ax.plot(x, y, z)
        #
        # # 显示图
        # plt.show()
        #return triangles

        #Logger.log("d", "Processing new layer for build plate %s..." % self._build_plate_number)

        # view = Application.getInstance().getController().getActiveView()
        # if view.getPluginId() == "SimulationView":
        #     view.resetLayerData()
        #     self._progress_message.show()
        #     Job.yieldThread()
        #     if self._abort_requested:
        #         if self._progress_message:
        #             self._progress_message.hide()
        #         return
        #
        # Application.getInstance().getController().activeViewChanged.connect(self._onActiveViewChanged)
        #
        # # The no_setting_override is here because adding the SettingOverrideDecorator will trigger a reslice
        # new_node = CuraSceneNode(no_setting_override = True)
        # new_node.addDecorator(BuildPlateDecorator(self._build_plate_number))
        #
        # # Force garbage collection.
        # # For some reason, Python has a tendency to keep the layer data
        # # in memory longer than needed. Forcing the GC to run here makes
        # # sure any old layer data is really cleaned up before adding new.
        # gc.collect()
        #
        # mesh = MeshData()
        # layer_data = LayerDataBuilder.LayerDataBuilder()
        # layer_count = len(self._layers)
        #
        # # Find the minimum layer number
        # # When disabling the remove empty first layers setting, the minimum layer number will be a positive
        # # value. In that case the first empty layers will be discarded and start processing layers from the
        # # first layer with data.
        # # When using a raft, the raft layers are sent as layers < 0. Instead of allowing layers < 0, we
        # # simply offset all other layers so the lowest layer is always 0. It could happens that the first
        # # raft layer has value -8 but there are just 4 raft (negative) layers.
        # min_layer_number = sys.maxsize
        # negative_layers = 0
        # for layer in self._layers:
        #     if layer.repeatedMessageCount("path_segment") > 0:
        #         if layer.id < min_layer_number:
        #             min_layer_number = layer.id
        #         if layer.id < 0:
        #             negative_layers += 1
        #
        # current_layer = 0
        #
        # for layer in self._layers:
        #     # If the layer is below the minimum, it means that there is no data, so that we don't create a layer
        #     # data. However, if there are empty layers in between, we compute them.
        #     if layer.id < min_layer_number:
        #         continue
        #
        #     # Layers are offset by the minimum layer number. In case the raft (negative layers) is being used,
        #     # then the absolute layer number is adjusted by removing the empty layers that can be in between raft
        #     # and the model
        #     abs_layer_number = layer.id - min_layer_number
        #     if layer.id >= 0 and negative_layers != 0:
        #         abs_layer_number += (min_layer_number + negative_layers)
        #
        #     layer_data.addLayer(abs_layer_number)
        #     this_layer = layer_data.getLayer(abs_layer_number)
        #     layer_data.setLayerHeight(abs_layer_number, layer.height)
        #     layer_data.setLayerThickness(abs_layer_number, layer.thickness)
        #
        #     for p in range(layer.repeatedMessageCount("path_segment")):
        #         polygon = layer.getRepeatedMessage("path_segment", p)
        #
        #         extruder = polygon.extruder
        #
        #         line_types = numpy.fromstring(polygon.line_type, dtype="u1")  # Convert bytearray to numpy array
        #         line_types = line_types.reshape((-1,1))
        #
        #         points = numpy.fromstring(polygon.points, dtype="f4")  # Convert bytearray to numpy array
        #         if polygon.point_type == 0: # Point2D
        #             points = points.reshape((-1,2))  # We get a linear list of pairs that make up the points, so make numpy interpret them correctly.
        #         else:  # Point3D
        #             points = points.reshape((-1,3))
        #
        #         line_widths = numpy.fromstring(polygon.line_width, dtype="f4")  # Convert bytearray to numpy array
        #         line_widths = line_widths.reshape((-1,1))  # We get a linear list of pairs that make up the points, so make numpy interpret them correctly.
        #
        #         line_thicknesses = numpy.fromstring(polygon.line_thickness, dtype="f4")  # Convert bytearray to numpy array
        #         line_thicknesses = line_thicknesses.reshape((-1,1))  # We get a linear list of pairs that make up the points, so make numpy interpret them correctly.
        #
        #         line_feedrates = numpy.fromstring(polygon.line_feedrate, dtype="f4")  # Convert bytearray to numpy array
        #         line_feedrates = line_feedrates.reshape((-1,1))  # We get a linear list of pairs that make up the points, so make numpy interpret them correctly.
        #
        #         # Create a new 3D-array, copy the 2D points over and insert the right height.
        #         # This uses manual array creation + copy rather than numpy.insert since this is
        #         # faster.
        #         new_points = numpy.empty((len(points), 3), numpy.float32)
        #         if polygon.point_type == 0:  # Point2D
        #             new_points[:, 0] = points[:, 0]
        #             new_points[:, 1] = layer.height / 1000  # layer height value is in backend representation
        #             new_points[:, 2] = -points[:, 1]
        #         else: # Point3D
        #             new_points[:, 0] = points[:, 0]
        #             new_points[:, 1] = points[:, 2]
        #             new_points[:, 2] = -points[:, 1]
        #
        #         this_poly = LayerPolygon.LayerPolygon(extruder, line_types, new_points, line_widths, line_thicknesses, line_feedrates)
        #         this_poly.buildCache()
        #
        #         this_layer.polygons.append(this_poly)
        #
        #         Job.yieldThread()
        #     Job.yieldThread()
        #     current_layer += 1
        #     progress = (current_layer / layer_count) * 99
        #     # TODO: Rebuild the layer data mesh once the layer has been processed.
        #     # This needs some work in LayerData so we can add the new layers instead of recreating the entire mesh.
        #
        #     if self._abort_requested:
        #         if self._progress_message:
        #             self._progress_message.hide()
        #         return
        #     if self._progress_message:
        #         self._progress_message.setProgress(progress)
        #
        # # We are done processing all the layers we got from the engine, now create a mesh out of the data
        #
        # # Find out colors per extruder
        # global_container_stack = Application.getInstance().getGlobalContainerStack()
        # manager = ExtruderManager.getInstance()
        # extruders = manager.getActiveExtruderStacks()
        # if extruders:
        #     material_color_map = numpy.zeros((len(extruders), 4), dtype=numpy.float32)
        #     for extruder in extruders:
        #         position = int(extruder.getMetaDataEntry("position", default="0"))  # Get the position
        #         try:
        #             default_color = ExtrudersModel.defaultColors[position]
        #         except IndexError:
        #             default_color = "#e0e000"
        #         color_code = extruder.material.getMetaDataEntry("color_code", default=default_color)
        #         color = colorCodeToRGBA(color_code)
        #         material_color_map[position, :] = color
        # else:
        #     # Single extruder via global stack.
        #     material_color_map = numpy.zeros((1, 4), dtype=numpy.float32)
        #     color_code = global_container_stack.material.getMetaDataEntry("color_code", default="#e0e000")
        #     color = colorCodeToRGBA(color_code)
        #     material_color_map[0, :] = color
        #
        # # We have to scale the colors for compatibility mode
        # if OpenGLContext.isLegacyOpenGL() or bool(Application.getInstance().getPreferences().getValue("view/force_layer_view_compatibility_mode")):
        #     line_type_brightness = 0.5  # for compatibility mode
        # else:
        #     line_type_brightness = 1.0
        # layer_mesh = layer_data.build(material_color_map, line_type_brightness)
        #
        # if self._abort_requested:
        #     if self._progress_message:
        #         self._progress_message.hide()
        #     return
        #
        # # Add LayerDataDecorator to scene node to indicate that the node has layer data
        # decorator = LayerDataDecorator.LayerDataDecorator()
        # decorator.setLayerData(layer_mesh)
        # new_node.addDecorator(decorator)
        #
        # new_node.setMeshData(mesh)
        # # Set build volume as parent, the build volume can move as a result of raft settings.
        # # It makes sense to set the build volume as parent: the print is actually printed on it.
        # new_node_parent = Application.getInstance().getBuildVolume()
        # new_node.setParent(new_node_parent)  # Note: After this we can no longer abort!
        #
        # settings = Application.getInstance().getGlobalContainerStack()
        # if not settings.getProperty("machine_center_is_zero", "value"):
        #     new_node.setPosition(Vector(-settings.getProperty("machine_width", "value") / 2, 0.0, settings.getProperty("machine_depth", "value") / 2))
        #
        # if self._progress_message:
        #     self._progress_message.setProgress(100)
        #
        # if self._progress_message:
        #     self._progress_message.hide()
        #
        # # Clear the unparsed layers. This saves us a bunch of memory if the Job does not get destroyed.
        # self._layers = None
        #
        Logger.log("d", "Processing layers took %s seconds", time() - start_time)

    def _onActiveViewChanged(self):
        if self.isRunning():
            if Application.getInstance().getController().getActiveView().getPluginId() == "SimulationView":
                if not self._progress_message:
                    self._progress_message = Message(catalog.i18nc("@info:status", "Processing Layers"), 0, False, 0, catalog.i18nc("@info:title", "Information"))
                if self._progress_message.getProgress() != 100:
                    self._progress_message.show()
            else:
                if self._progress_message:
                    self._progress_message.hide()
