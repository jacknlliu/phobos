#!/usr/bin/python
# coding=utf-8

"""
Copyright 2014, University of Bremen & DFKI GmbH Robotics Innovation Center

This file is part of Phobos, a Blender Add-On to edit robot models.

Phobos is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License
as published by the Free Software Foundation, either version 3
of the License, or (at your option) any later version.

Phobos is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with Phobos.  If not, see <http://www.gnu.org/licenses/>.

File sensors.py

Created on 6 Jan 2014

@author: Kai von Szadkowski
"""


import bpy
import mathutils
from phobos import defs
import phobos.utils.blender as bUtils
import phobos.utils.selection as sUtils
import phobos.utils.naming as nUtils


def createSensor(self, sensor):
    if 'link' in sensor:
        reference = [sensor['link']]
    elif 'joint' in sensor:
        reference = [sensor['joint']]
        pass
    elif 'links' in sensor:
        reference = sensor['links']
    elif 'joints' in sensor:
        reference = sensor['joints']
    elif 'motors' in sensor:
        reference = sensor['motors']
    else:
        reference = None

    # FIXME: This needs to be resolved in a generic way!
    createSensor(sensor, reference)
    attachSensor(sensor)


def attachSensor(self, sensor):
    """This function attaches a given sensor to its parent link.

    :param sensor: The sensor you want to attach to its parent link.
    :type sensor: dict

    """
    bpy.context.scene.layers = bUtils.defLayers([defs.layerTypes[t] for t in defs.layerTypes])
    #try:
    if 'pose' in sensor:
        urdf_geom_loc = mathutils.Matrix.Translation(sensor['pose']['translation'])
        urdf_geom_rot = mathutils.Euler(tuple(sensor['pose']['rotation_euler']), 'XYZ').to_matrix().to_4x4()
    else:
        urdf_geom_loc = mathutils.Matrix.Identity(4)
        urdf_geom_rot = mathutils.Matrix.Identity(4)
    sensorobj = bpy.data.objects[sensor['name']]
    if 'link' in sensor:
        parentLink = sUtils.getObjectByNameAndType(sensor['link'], 'link')
        #parentLink = bpy.data.objects['link_' + sensor['link']]
        sUtils.selectObjects([sensorobj, parentLink], True, 1)
        bpy.ops.object.parent_set(type='BONE_RELATIVE')
    else:
        #TODO: what?
        pass
    sensorobj.matrix_local = urdf_geom_loc * urdf_geom_rot
    #except KeyError:
    #    log("inconsistent data on sensor: "+ sensor['name'], "ERROR")


def cameraRotLock(object):
    """TODO: PLEASE ADD PYDOC. What should this do exactly?

    :param object: The object to lock the rotation for
    :type object: bpy_types.Object

    """
    sUtils.selectObjects([object], active=0)
    bpy.ops.transform.rotate(value=-1.5708, axis=(-1, 0, 0), constraint_axis=(False, False, True), constraint_orientation='LOCAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
    bpy.ops.transform.rotate(value=1.5708, axis=(0, -1, 0), constraint_axis=(True, False, False), constraint_orientation='LOCAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
    bpy.ops.object.constraint_add(type='LIMIT_ROTATION')
    object.constraints["Limit Rotation"].use_limit_x = True
    object.constraints["Limit Rotation"].use_limit_y = True
    object.constraints["Limit Rotation"].use_limit_z = True
    object.constraints["Limit Rotation"].min_x = object.rotation_euler[0]
    object.constraints["Limit Rotation"].max_x = object.rotation_euler[0]
    object.constraints["Limit Rotation"].min_y = object.rotation_euler[1]
    object.constraints["Limit Rotation"].max_y = object.rotation_euler[1]
    object.constraints["Limit Rotation"].min_z = object.rotation_euler[2]
    object.constraints["Limit Rotation"].max_z = object.rotation_euler[2]


def createSensor(sensor, reference, origin=mathutils.Matrix()):
    """This function creates a new sensor specified by its parameters.

    :param sensor: The phobos representation of the new sensor.
    :type sensor: dict
    :param reference: This is an object to add a parent relationship to.
    :type reference: bpy_types.Object
    :param origin: The new sensors origin.
    :type origin: mathutils.Matrix
    :return: The newly created sensor object

    """
    bUtils.toggleLayer(defs.layerTypes['sensor'], value=True)
    # create sensor object
    if 'Camera' in sensor['type']:
        bpy.ops.object.add(type='CAMERA', location=origin.to_translation(),
                           rotation=origin.to_euler(),
                           layers=bUtils.defLayers([defs.layerTypes['sensor']]))
        newsensor = bpy.context.active_object
        if reference is not None:
            sUtils.selectObjects([newsensor, reference], clear=True, active=1)
            bpy.ops.object.parent_set(type='BONE_RELATIVE')
    elif sensor['type'] in ['RaySensor', 'RotatingRaySensor', 'ScanningSonar', 'MultiLevelLaserRangeFinder']:
        # TODO: create a proper ray sensor scanning layer disc here
        newsensor = bUtils.createPrimitive(sensor['name'], 'disc', (0.5, 36),
                                            defs.layerTypes['sensor'], 'phobos_laserscanner',
                                            origin.to_translation(), protation=origin.to_euler())
        if reference is not None:
            sUtils.selectObjects([newsensor, reference], clear=True, active=1)
            bpy.ops.object.parent_set(type='BONE_RELATIVE')
    else:  # contact, force and torque sensors (or unknown sensors)
        newsensor = bUtils.createPrimitive(sensor['name'], 'sphere', 0.05,
                                            defs.layerTypes['sensor'], 'phobos_sensor',
                                            origin.to_translation(), protation=origin.to_euler())
        if sensor['type'] == 'Joint6DOF':
            pass #newsensor['sensor/nodes'] = nUtils.getObjectName(reference)
        elif 'Node' in sensor['type']:
            newsensor['sensor/nodes'] = sorted([nUtils.getObjectName(ref) for ref in reference])
        elif 'Joint' in sensor['type'] or 'Motor' in sensor['type']:
            newsensor['sensor/joints'] = sorted([nUtils.getObjectName(ref) for ref in reference])
        if reference is not None:
            sUtils.selectObjects([newsensor, reference], clear=True, active=1)
            bpy.ops.object.parent_set(type='BONE_RELATIVE')
    # set sensor properties
    newsensor.phobostype = 'sensor'
    newsensor.name = sensor['name']
    newsensor['sensor/type'] = sensor['type']

    #for prop in ['link', 'joint', 'links', 'joints', 'motors']:
    #    if prop in sensor:
    #        newsensor['sensor/'+prop] = sensor[prop]

    # add custom properties
    #for prop in sensor:
    #    if prop.startswith('$'):
    #        for tag in sensor[prop]:
    #            newsensor[prop[1:]+'/'+tag] = sensor[prop][tag]

    # throw warning if type is not known
    if sensor['type'] not in defs.sensortypes:
        print("### Warning: sensor", sensor['name'], "is of unknown/custom type.")
    sUtils.selectObjects([newsensor], clear=False, active=0)
    return newsensor





# class AddLegacySensorOperator(Operator):
#     """AddSensorOperator"""
#     bl_idname = "phobos.add_legacy_sensor"
#     bl_label = "Add/Update a sensor"
#     bl_options = {'REGISTER', 'UNDO'}
#
#     sensor_type = StringProperty(
#         name = "sensor_type",
#         default = "",
#         description = "type of the sensor to be created")
#
#     sensor_scale = FloatProperty(
#         name = "sensor_scale",
#         default = 0.05,
#         description = "scale of the sensor visualization")
#
#     def execute(self, context):
#         location = bpy.context.scene.cursor_location
#         if self.sensor_type in defs.sensortypes:
#             if "Node" in self.sensor_type or "Joint" in self.sensor_type or "Motor" in self.sensor_type:
#                 objects = []
#                 sensors = []
#                 for obj in bpy.context.selected_objects:
#                     if obj.phobostype == "sensor":
#                         sensors.append(obj)
#                         self.sensor_type = obj["sensor/type"]
#                     else:
#                         objects.append(obj)
#                 if len(sensors) <= 0:
#                     utility.createPrimitive(self.sensor_type, "sphere", self.sensor_scale, defs.layerTypes["sensor"], "sensor", location)
#                     sense = bpy.context.scene.objects.active
#                     sense.phobostype = "sensor"
#                     sense.name = self.sensor_type
#                     sense["sensor/type"] = self.sensor_type
#                     sensors.append(sense)
#                 for sensor in sensors:
#                     for key in sensor.keys():
#                         if key.find("index") >= 0:
#                             del sensor[key]
#                             print("Deleting " + key + " in " + sensor.name)
#                     i = 1
#                     if "Node" in sensor["sensor/type"]:
#                         for obj in objects:
#                             if obj.phobostype == "collision":
#                                 sensor["index"+(str(i) if i >= 10 else "0"+str(i))] = obj.name
#                                 i += 1
#                         print("Added nodes to new " + self.sensor_type)
#                     elif "Joint" in sensor["sensor/type"] or "Motor" in sensor["sensor/type"]:
#                         for obj in objects:
#                             if obj.phobostype == "link":
#                                 sensor["index"+(str(i) if i >= 10 else "0"+str(i))] = obj.name
#                                 i += 1
#                         print("Added nodes to new " + self.sensor_type)
#                     if len(objects) > 0:
#                         sensor.parent = utility.getRoot(objects[0])
#             else: #visual sensor
#                 if self.sensor_type == "RaySensor":
#                     print("Added nodes to new " + self.sensor_type)
#                 elif self.sensor_type == "CameraSensor":
#                     bpy.ops.object.add(type='CAMERA', location=bpy.context.scene.cursor_location)
#                     sensor = bpy.context.active_object
#                     print("Added nodes to new " + self.sensor_type)
#                 elif self.sensor_type == "ScanningSonar":
#                     print("Added nodes to new " + self.sensor_type)
#             # add the pre-defined sensor properties
#             for prop in defs.sensorProperties[self.sensor_type]:
#                 sensor[prop] = defs.sensorProperties[self.sensor_type][prop]
#         else:
#             print("Sensor could not be created: unknown sensor type.")
#         return {'FINISHED'}
