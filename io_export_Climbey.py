bl_info = {
    "name": "Export Climbey custom level",
    "category": "Import-Export",
    "author": "Chris Pratt",
    "version": (1, 0, 0),
    "blender": (2, 79, 0),
    "location": "File > Export > Climbey custom level",
    "description": "Export current scene to a Climbey custom level",
    "warning": "",
}

import bpy
import os
import mathutils
import math

def make_level(file_handle):
    """Turn the active blender scene into a Climbey custom level
    Loops through all the objects in the current blender project (everything in bpy.context.scene.objects) and creates climbey objects from them based off their custom properties"""
    #Initializing
    set_material_color()
    level_dic = {}
    level_dic['ZiplinesArray'] = []
    level_dic['LevelArray'] = []
    level_dic['LightsArray'] = []
    level_dic['GroupsArray'] = []
    level_dic['LevelSettings'] = {}
    level_dic['MovingArray'] = []
    level_dic['SignsArray'] = []
    cur_types = make_level_types(level_dic)

    for itt_object, cur_object in enumerate(bpy.context.scene.objects):
        #Loop through all objects in the currect blender project
        
        if 'type' in cur_object.keys():
            #If the current object has a 'type' custom object property retrieve it
            cur_type = cur_object['type'].lower()

            if callable(getattr(cur_types, cur_type, None)):
                #If there is a matching function to the objects type call it
                getattr(cur_types, cur_type)(level_dic, cur_object, itt_object)

    #Save the created level dictionary to a file.
    file_string = str(level_dic)
    file_string = file_string.replace('False', 'false')
    file_string = file_string.replace('True', 'true')
    file_string = file_string.replace("'", '"')
    file_handle.write(file_string)

class make_level_types():
    """Functions to be run based off the type custom property"""

    def __init__(self, level_dic):
        self.level_dic = level_dic

    def add_position(self, cur_object, dic):
        """add the position data from 'cur_object' into 'dic'. Blender uses the z-axis as up while climbey uses the y-axes as up"""
        dic['Position'] = {}
        dic['Position']['x'] = cur_object.location[0]
        dic['Position']['y'] = cur_object.location[2]
        dic['Position']['z'] = cur_object.location[1]

    def add_rotation(self, cur_object, dic):
        """add the rotation data from 'cur_object' into 'dic'. Blender uses the z-axis as up while climbey uses the y-axes as up"""
        cur_object.rotation_mode = 'QUATERNION'
        dic['Rotation'] = {}
        dic['Rotation']['w'] = cur_object.rotation_quaternion[0]
        dic['Rotation']['x'] = -cur_object.rotation_quaternion[1]
        dic['Rotation']['y'] = -cur_object.rotation_quaternion[3]
        dic['Rotation']['z'] = -cur_object.rotation_quaternion[2]

    def add_size(self, cur_object, dic):
        """add the size data from 'cur_object' into 'dic'. Blender uses the z-axis as up while climbey uses the y-axes as up"""
        dic['Size'] = {}
        dic['Size']['x'] = cur_object.scale[0]
        dic['Size']['y'] = cur_object.scale[2]
        dic['Size']['z'] = cur_object.scale[1]

    def add_RGB(self, cur_object, dic):
        """add the color data from the first material of 'cur_object' into 'dic'."""
        material_name = cur_object.data.materials.keys()[0]
        dic['R'] = cur_object.data.materials[material_name].diffuse_color[0]
        dic['G'] = cur_object.data.materials[material_name].diffuse_color[1]
        dic['B'] = cur_object.data.materials[material_name].diffuse_color[2]

    def add_lock_xyz(self, cur_object, dic, lock):
        """Add the lock x, y, or z of data of 'dic' to 'lock'"""
        dic['LockX'] = lock
        dic['LockY'] = lock
        dic['LockZ'] = lock

    def add_all_position(self, cur_object, dic):
        """add all the positional data of 'cur_object' into 'dic'."""
        self.add_position(cur_object, dic)
        self.add_rotation(cur_object, dic)
        self.add_size(cur_object, dic)
        self.add_lock_xyz(cur_object, dic, False)

    def add_object(self, level_dic, cur_object, material_to_type):
        """Add the 'cur_object' to 'level_dic' based on the names in 'material_to_type'"""
        new_dic = {}
        self.add_position(cur_object, new_dic)
        self.add_rotation(cur_object, new_dic)
        self.add_size(cur_object, new_dic)
        self.add_lock_xyz(cur_object, new_dic, False)
        new_material = None

        if 'material' in cur_object.keys():
            #If the current object has a 'material' custom object property retrieve it
            new_material = cur_object['material']

        if new_material in material_to_type.keys():
            #If it is one of the recognized materials, use it
            new_dic['Type'] = material_to_type[new_material]

        else:
            #If no material was found, default to Metal
            new_dic['Type'] = 'Metal'

        if (new_material == 'light') and ('light' in material_to_type.keys()):
            #Find the red, green, blue, and B (whatever that is) values if this is a light, and add it to the lights
            self.add_RGB(cur_object, new_dic)
            level_dic['LightsArray'].append(new_dic)

        else:
            #Add the object
            level_dic['LevelArray'].append(new_dic)

    def cube(self, level_dic, cur_object, itt_object):
        """create a cube shape with the data from cur_object and add it to level_dic"""
        material_to_type = {'grabbable': 'Grabbable', 'metal': 'Metal', 'glass': 'Glass', 'ice': 'Icy', 'light': 'Lamp', 'gravity_field': 'GravityField'}
        self.add_object(level_dic, cur_object, material_to_type)

    def sphere(self, level_dic, cur_object, itt_object):
        material_to_type = {'grabbable': 'SphereGrip', 'metal': 'SphereNoGrip', 'glass': 'SphereSeeThrough', 'ice': 'SphereIce', 'light': 'SphereLight'}
        self.add_object(level_dic, cur_object, material_to_type)

    def half_sphere(self, level_dic, cur_object, itt_object):
        material_to_type = {'grabbable': 'HemiGrip', 'metal': 'HemiNoGrip', 'glass': 'HemiSeeThrough', 'ice': 'HemiIce', 'light': 'HemiLight'}
        self.add_object(level_dic, cur_object, material_to_type)
    
    def pipe(self, level_dic, cur_object, itt_object):
        material_to_type = {'grabbable': 'PipeGrip', 'metal': 'PipeNoGrip', 'glass': 'PipeSeeThrough', 'ice': 'PipeIce', 'light': 'PipeLight'}
        self.add_object(level_dic, cur_object, material_to_type)
    
    def pyramid(self, level_dic, cur_object, itt_object):
        material_to_type = {'grabbable': 'PyramidGrip', 'metal': 'PyramidNoGrip', 'glass': 'PyramidSeeThrough', 'ice': 'PyramidIce', 'light': 'PyramidLight'}
        self.add_object(level_dic, cur_object, material_to_type)
    
    def prism(self, level_dic, cur_object, itt_object):
        material_to_type = {'grabbable': 'PrismGrip', 'metal': 'PrismNoGrip', 'glass': 'PrismSeeThrough', 'ice': 'PrismIce', 'light': 'PrismLight'}
        self.add_object(level_dic, cur_object, material_to_type)
    
    def half_pipe(self, level_dic, cur_object, itt_object):
        material_to_type = {'grabbable': 'HalfPipeGrip', 'metal': 'HalfPipeNoGrip', 'glass': 'HalfPipeSeeThrough', 'ice': 'HalfPipeIce', 'light': 'HalfPipeLight'}
        self.add_object(level_dic, cur_object, material_to_type)

    def sign(self, level_dic, cur_object, itt_object):
        new_dic = {}
        self.add_position(cur_object, new_dic)
        self.add_rotation(cur_object, new_dic)
        self.add_size(cur_object, new_dic)
        self.add_lock_xyz(cur_object, new_dic, False)
        new_dic['Invisible'] = False
        new_dic['text'] = cur_object['text']
        new_dic['Type'] = 'Sign'
        level_dic['SignsArray'].append(new_dic)

    def gravity_anti(self, level_dic, cur_object, itt_object):
        new_dic = {}
        self.add_all_position(cur_object, new_dic)
        new_dic['Type'] = 'GravityField'
        level_dic['LevelArray'].append(new_dic)

    def gravity_directional(self, level_dic, cur_object, itt_object):
        new_dic = {}
        self.add_all_position(cur_object, new_dic)
        new_dic['Type'] = 'GravityFieldLocal'
        level_dic['LevelArray'].append(new_dic)

    def gravity_up(self, level_dic, cur_object, itt_object):
        new_dic = {}
        self.add_all_position(cur_object, new_dic)
        new_dic['Type'] = 'GravityFieldUpward'
        level_dic['LevelArray'].append(new_dic)

    def gravity_down(self, level_dic, cur_object, itt_object):
        new_dic = {}
        self.add_all_position(cur_object, new_dic)
        new_dic['Type'] = 'GravityFieldDownward'
        level_dic['LevelArray'].append(new_dic)

    def lava(self, level_dic, cur_object, itt_object):
        new_dic = {}
        self.add_all_position(cur_object, new_dic)
        new_dic['Type'] = 'Lava'
        level_dic['LevelArray'].append(new_dic)

    def spikes(self, level_dic, cur_object, itt_object):
        new_dic = {}
        self.add_all_position(cur_object, new_dic)
        new_dic['Size']['y'] = 1.0
        new_dic['Type'] = 'Spikes'
        level_dic['LevelArray'].append(new_dic)

    def trampoline(self, level_dic, cur_object, itt_object):
        new_dic = {}
        self.add_all_position(cur_object, new_dic)
        new_dic['Type'] = 'Jumpy'
        level_dic['LevelArray'].append(new_dic)

    def player_start(self, level_dic, cur_object, itt_object):
        """Add the camera rig (where the character spawns) to 'level_dic'"""
        new_dic = {}
        self.add_position(cur_object, new_dic)
        self.add_lock_xyz(cur_object, new_dic, False)
        #(2018-1-31) I dont think you are supposed to set either the camera rigs rotation or scale, so those are hard coded.
        new_dic['Rotation'] = {}
        new_dic['Rotation']['w'] = 1
        new_dic['Rotation']['x'] = 0
        new_dic['Rotation']['y'] = 0
        new_dic['Rotation']['z'] = 0
        new_dic['Size'] = {}
        new_dic['Size']['x'] = 1
        new_dic['Size']['y'] = 1
        new_dic['Size']['z'] = 1
        new_dic['Type'] = '[CameraRig]'
        level_dic['LevelArray'].append(new_dic)

    def finishline(self, level_dic, cur_object, itt_object):
        """Add the finish line to 'level_dic'"""
        new_dic = {}
        self.add_position(cur_object, new_dic)
        self.add_lock_xyz(cur_object, new_dic, False)
        #(2018-1-31) I dont think you are supposed to set either the camera rigs rotation or scale, so those are hard coded.
        new_dic['Rotation'] = {}
        new_dic['Rotation']['w'] = 1
        new_dic['Rotation']['x'] = 0
        new_dic['Rotation']['y'] = 0
        new_dic['Rotation']['z'] = 0
        new_dic['Size'] = {}
        new_dic['Size']['x'] = .5
        new_dic['Size']['y'] = 1
        new_dic['Size']['z'] = .5
        new_dic['Type'] = 'Finishline'
        level_dic['LevelArray'].append(new_dic)

    def level_settings(self, level_dic, cur_object, itt_object):
        """Create the level settings object"""
        level_dic['LevelSettings'] = {}
        self.add_position(cur_object, level_dic['LevelSettings'])
        self.add_lock_xyz(cur_object, level_dic['LevelSettings'], False)
        level_dic['LevelSettings']['Gamemode'] = int(cur_object['game_mode'])
        level_dic['LevelSettings']['Checkpoints'] = int(cur_object['checkpoints'])
        #(2018-1-31) I dont think you are supposed to set either the level setting's rotation or scale, so those are hard coded.
        level_dic['LevelSettings']['Rotation'] = {}
        level_dic['LevelSettings']['Rotation']['w'] = 1
        level_dic['LevelSettings']['Rotation']['x'] = 0
        level_dic['LevelSettings']['Rotation']['y'] = 0
        level_dic['LevelSettings']['Rotation']['z'] = 0
        level_dic['LevelSettings']['Size'] = {}
        level_dic['LevelSettings']['Size']['x'] = 1
        level_dic['LevelSettings']['Size']['y'] = 1
        level_dic['LevelSettings']['Size']['z'] = 1
        level_dic['LevelSettings']['Type'] = 'LevelSign'

def set_material_color():
    """Set all blender object's material color based on their climbey material type"""

    #Define the types and how their material colors will be set.
    material_to_color = {'grabbable': [.96, 1, .35], 'metal': [.18, .25, .25], 'glass': [.6, .8, .8], 'ice': [.19, .65, .8], 'gravity_field': [.96, 1, .8]}
    material_to_alpha = {'grabbable': 1, 'metal': 1, 'glass': .3, 'ice': 1, 'gravity_field':.3}
    
    types = {}
    types['cube'] = {}
    types['cube']['property_name'] = 'material'
    types['cube']['set_color'] = material_to_color
    types['cube']['set_alpha'] = material_to_alpha
    types['pyramid'] = types['cube']
    types['prism'] = types['cube']
    types['pipe'] = types['cube']
    types['half_pipe'] = types['cube']
    types['sphere'] = types['cube']
    types['half_sphere'] = types['cube']

    types['gravity_anti'] = {}
    types['gravity_anti']['property_name'] = ''
    types['gravity_anti']['set_color'] = [1, 1, .5]
    types['gravity_anti']['set_alpha'] = .7

    types['gravity_directional'] = {}
    types['gravity_directional']['property_name'] = ''
    types['gravity_directional']['set_color'] = [.38, 1, .27]
    types['gravity_directional']['set_alpha'] = .7

    types['gravity_up'] = {}
    types['gravity_up']['property_name'] = ''
    types['gravity_up']['set_color'] = [.14, .14, .7]
    types['gravity_up']['set_alpha'] = .7

    types['gravity_down'] = {}
    types['gravity_down']['property_name'] = ''
    types['gravity_down']['set_color'] = [.7, .14, .14]
    types['gravity_down']['set_alpha'] = .7

    types['lava'] = {}
    types['lava']['property_name'] = ''
    types['lava']['set_color'] = [1, .04, 0]
    types['lava']['set_alpha'] = 1

    types['spikes'] = {}
    types['spikes']['property_name'] = ''
    types['spikes']['set_color'] = [.1, .1, .3]
    types['spikes']['set_alpha'] = 1

    types['trampoline'] = {}
    types['trampoline']['property_name'] = ''
    types['trampoline']['set_color'] = [.01, .64, .01]
    types['trampoline']['set_alpha'] = 1

    types['sign'] = {}
    types['sign']['property_name'] = ''
    types['sign']['set_color'] = [.32, .14, .06]
    types['sign']['set_alpha'] = 1

    types['finishline'] = {}
    types['finishline']['property_name'] = ''
    types['finishline']['set_color'] = [.43, .8, .26]
    types['finishline']['set_alpha'] = 1

    types['player_start'] = {}
    types['player_start']['property_name'] = ''
    types['player_start']['set_color'] = [.19, .65, .8]
    types['player_start']['set_alpha'] = .5

    types['level_settings'] = {}
    types['level_settings']['property_name'] = ''
    types['level_settings']['set_color'] = [1, .1, .75]
    types['level_settings']['set_alpha'] = 1
    
    for itt_object, cur_object in enumerate(bpy.data.objects):
        #Loop through all objects in the currect blender project

        if 'type' in cur_object.keys():
            #If the current object has a 'type' custom object property retrieve it
            cur_type = cur_object['type']

            if cur_type in types.keys():
                #If this is a known type, try to set its color and alpha

                if types[cur_type]['property_name'] == '':
                    set_color = types[cur_type]['set_color']
                    set_alpha = types[cur_type]['set_alpha']

                else:
                    property_name = types[cur_type]['property_name']

                    if property_name in cur_object.keys():
                        property_value = cur_object[property_name]

                        if property_value == 'light':
                            #lights dont have a set color
                            continue

                        if property_value in types[cur_type]['set_color'].keys():
                            set_color = types[cur_type]['set_color'][property_value]
                            set_alpha = types[cur_type]['set_alpha'][property_value]

                        else:
                            continue

                    else:
                        continue

                materials = cur_object.data.materials.keys()

                if len(materials) > 0:
                    #If the object alread has a material edit it
                    material_name = materials[0]

                else:
                    #If the object dosen't have a material, create one.
                    cur_object.data.materials.append(bpy.data.materials.new(name="Material"))
                    material_name = cur_object.data.materials.keys()[0]

                cur_object.data.materials[material_name].diffuse_color[0] = set_color[0]
                cur_object.data.materials[material_name].diffuse_color[1] = set_color[1]
                cur_object.data.materials[material_name].diffuse_color[2] = set_color[2]
                cur_object.show_transparent = True
                cur_object.data.materials[material_name].use_transparency = True
                cur_object.data.materials[material_name].alpha = set_alpha

#==============================================================================
# Blender Operator class
#==============================================================================

class EXPORT_TO_Climbey(bpy.types.Operator):
    """Export current scene to a Climbey custom level"""
    bl_idname = 'export_scene.climbey'
    bl_label = 'Export scene as Climbey txt'
    bl_options = {'REGISTER'}

    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    # invoke is called when the user picks the Export menu entry.
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    # execute is called when the user is done using the modal file-select window.
    def execute(self, context):

        if self.filepath[-4:].lower() != '.txt':
            #Ensure the file type is .txt
            self.filepath += '.txt'
        file_handle = open(self.filepath, 'w')
        make_level(file_handle)
        return {'FINISHED'}


#==============================================================================
# Register plugin with Blender
#==============================================================================

# Only needed if you want to add into a dynamic menu
def menu_func(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(EXPORT_TO_Climbey.bl_idname, text="Climbey (.txt)")

def register():
    bpy.utils.register_class(EXPORT_TO_Climbey)
    bpy.types.INFO_MT_file_export.append(menu_func)

def unregister():
    bpy.utils.unregister_class(EXPORT_TO_Climbey)
    bpy.types.INFO_MT_file_export.remove(menu_func)

if __name__ == '__main__':
    register()