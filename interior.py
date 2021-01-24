bl_info = {
    "name": "ExteriorDeselector",
    "blender": (2, 90, 0),
    "category": "Mesh",
}

import bpy
import bmesh
from bpy.props import *
from bpy.types import Panel, Operator, PropertyGroup
from mathutils import Vector

class RaycasterList(PropertyGroup):
    ob: PointerProperty(
        name='Current Object',
        type=bpy.types.Object)
    ob_id: IntProperty(default=0)
    used: BoolProperty(default=True)


class TMP_UL_Interior_List(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item.ob, 'name', text='', icon='META_CUBE', emboss=False)

        if item.used:
            icon = 'CHECKBOX_HLT'
        else:
            icon = 'CHECKBOX_DEHLT'
        row.operator('tmp_seli.raycast_switch', text='', icon=icon).list_id = index
        row.operator('tmp_seli.frame_selected', text='', icon="RESTRICT_SELECT_OFF").list_id = index

    def invoke(self, context, event):
        pass


def registerProps():
    bpy.utils.register_class(RaycasterList)
    bpy.utils.register_class(TMP_UL_Interior_List)
    bpy.types.Scene.tmp_seli_ob_data = CollectionProperty(type=RaycasterList)
    bpy.types.Scene.tmp_seli_ob_data_id = IntProperty(default=0)

def unregisterProps():
    bpy.utils.unregister_class(RaycasterList)
    bpy.utils.register_class(TMP_UL_Interior_List)
    del bpy.types.Scene.tmp_seli_ob_data
    del bpy.types.Scene.tmp_seli_ob_data_id

#scene.objects.active = current_mesh

# Blender's "select interior faces" doesn't actually select interior faces, it
# selects faces that share edges with 2 or more other faces. In my case this
# erroneously selects some faces that are visible but connect to multiple other
# faces. The solution is to select interior faces, then ignore any faces that
# the camera (positioned at 0,0,10) can see, and delete the remaining ones
# See http//blender.stackexchange.com/questions/57540/automated-way-to-make-select-interior-faces-ignore-select-faces-that-are-visib
def removeInteriorFaces():
    ops = bpy.ops
    scene = bpy.context.scene
    mesh = bpy.ops.mesh
    viewLayer = bpy.context.view_layer

    current_mesh = bpy.context.active_object
    mesh_data = current_mesh.data

    # First do the built in selection
    # mesh.select_interior_faces()
    
    items = scene.tmp_seli_ob_data
    cameraOrigins = list(map(lambda x: x.ob.location, items))
    
    # Use the current selection

    def localToWorld(vec):
        t = vec.to_4d()
        t.w = 0
        return (current_mesh.matrix_world @ t).to_3d()

    # And store all faces inside that selection
    indices = []
    while len(indices) == 0:
        bm = bmesh.from_edit_mesh( mesh_data )
        for index, face in enumerate( bm.faces ):
            if face.select:
                indices.append( ( index, localToWorld(face.calc_center_median_weighted()) ) )

        # Deselect everything...
        mesh.select_all()

    # Switch to object mode to do scene raycasting (doesn't work in edit mode
    # I don't think, got error "has no mesh data to be used for ray casting"
    ops.object.mode_set( mode = 'OBJECT' )
    outside = []
    for index_data in indices:
        for cameraOrigin in cameraOrigins:
            index = index_data[ 0 ]
            center = index_data[ 1 ]
            direction = center - cameraOrigin;
            direction.normalize()

            # Cast a ray from the "camera" position to the face we think is interior
            result, location, normal, faceIndex, object, matrix = scene.ray_cast( viewLayer, cameraOrigin, direction )

            # If the ray actually hit the face, as in the face index from the
            # selection matches the face index from the raycast, then this face
            # *is* visible to the camera, so don't remove it!
            if faceIndex == index:
                outside.append( faceIndex )
                break # Since we already know its visible we don't have to keep checking it against the other raycasts

    # Build a list of the "true" interior face indices, which is the original
    # indices from Blender's built in "select interior faces", but without the
    # faces we know the camera can see
    invisible_interior_faces = [ data[ 0 ] for data in indices if data[ 0 ] not in outside ]

    print( 'Removing ',len( invisible_interior_faces ),'invisible faces' )

    # Select the faces (in object mode this is easy, strangely)...
    if len( invisible_interior_faces ) > 0:

        for index in invisible_interior_faces:
            mesh_data.polygons[ index ].select = True

    ops.object.mode_set( mode = 'EDIT' )

    # Then delete them
    if len( invisible_interior_faces ) > 0:
        #mesh.delete( type = 'FACE' )
        pass

class RaycastSwitch(Operator):
    bl_idname = 'tmp_seli.raycast_switch'
    bl_label = 'Add Item'
    bl_description = 'Selected objects will be used as raycasting origins'

    list_id: IntProperty(default=0)

    def execute(self, context):
        scn = context.scene
        items = scn.tmp_seli_ob_data
        
        if self.list_id < 0:
            for item in items:
                if self.list_id == -1:
                    item.used = True
                else:
                    item.used = False
        else:
            item = items[self.list_id]
                    
            if item.used:
                item.used = False
            else:
                item.used = True
            
        return {'FINISHED'}

class FrameSelected(Operator):
    bl_idname = 'tmp_seli.frame_selected'
    bl_label = 'Frame Selected'
    bl_description = 'Go to this object in the viewport'
    
    list_id: IntProperty(default=0)
    
    def execute(self, context):
        scn = context.scene
        items = scn.tmp_seli_ob_data
        item = items[self.list_id]
        
        bpy.ops.object.select_all(action='DESELECT')
        item.ob.select = True
        bpy.ops.view3d.view_selected()
        return {'FINISHED'}

class SelectInternal(Operator):
    """Deselects external faces via raycasting points"""      # Use this as a tooltip for menu items and buttons.
    bl_idname = "tmp_seli.deselect_external"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Deselect External Faces"         # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.
    
    def execute(self, context):        # execute() is called when running the operator.        
        bpy.ops.object.mode_set( mode = 'EDIT' )
        removeInteriorFaces()

        return {'FINISHED'}            # Lets Blender know the operator finished successfully.

class SelectInteriorPanel(Panel):
    """"""
    bl_idname = "VIEW3D_PT_int"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Interior Faces"
    bl_category = "TMPIM"
    
    
    def draw(self, context):
        scn = bpy.context.scene
        layout = self.layout
        
        col = layout.column(align=True)
        col.label(text="Objects for raycasting origins: ")
        
        col.template_list('TMP_UL_Interior_List', 'raycast_list', scn, 'tmp_seli_ob_data',
                                scn, 'tmp_seli_ob_data_id', rows=12, type='DEFAULT')
        
        row = col.row(align=True)
        row.operator('tmp_seli.raycast_switch', text='Select All').list_id = -1
        row.operator('tmp_seli.raycast_switch', text='Deselect All').list_id = -2
        
        col = col.column(align=True)
        col.scale_y = 1.2
        col.operator("tmp_seli.refresh_ob_data")
        
        col.separator()
        col.separator()
        
        col = col.column(align=True)
        col.scale_y = 2
        col.operator("tmp_seli.deselect_external")

def get_obs(obs):
    return [ob for ob in obs if ob.type == 'EMPTY']

class RefreshObData(bpy.types.Operator):
    bl_idname = 'tmp_seli.refresh_ob_data'
    bl_label = 'Update Raycaster List'
    bl_description = 'Updates the raycaster list'

    def execute(self, context):
        scn = context.scene
        ob_list = get_obs(scn.objects)
        ob_list.sort(key=lambda k: k.name)
        
        scn.tmp_seli_ob_data.clear()
        for ob_id, ob in enumerate(ob_list):
            item = scn.tmp_seli_ob_data.add()
            item.ob = ob
            item.ob_id = ob_id
            item.used = True
            
        return {'FINISHED'}

def register():
    bpy.utils.register_class(FrameSelected)
    bpy.utils.register_class(RaycastSwitch)
    bpy.utils.register_class(RefreshObData)
    bpy.utils.register_class(SelectInternal)
    bpy.utils.register_class(SelectInteriorPanel)
    registerProps()


def unregister():
    bpy.utils.unregister_class(FrameSelected)
    bpy.utils.unregister_class(RaycastSwitch)
    bpy.utils.unregister_class(RefreshObData)
    bpy.utils.unregister_class(SelectInternal)
    bpy.utils.unregister_class(SelectInteriorPanel)
    unregisterProps()

if __name__ == "__main__":
    self = bpy.data.texts["Select Interior"].as_module()
    self.register()
