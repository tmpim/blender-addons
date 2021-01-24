bl_info = {
    "name": "Automatic MCS",
    "blender": (2, 90, 0),
    "category": "Mesh",
}


import bpy
import bmesh
import math

from bpy.props import *
from bpy.types import Panel, Operator
from mathutils import Vector, Matrix
 

#
# 812
# 7-3 0b12345678
# 654
#
noCornerWangs = {
    "dims": (4, 4),
    0b00000000: (0, 3),
    0b00000100: (1, 3),
    0b01000100: (2, 3),
    0b01000000: (3, 3),
    #b12345678
    0b00010000: (0, 2),
    0b00011100: (1, 2),
    0b01111100: (2, 2),
    0b01110000: (3, 2),
    #b12345678
    0b00010001: (0, 1),
    0b00011111: (1, 1),
    0b11111111: (2, 1),
    0b11110001: (3, 1),
    #b12345678
    0b00000001: (0, 0),
    0b00000111: (1, 0),
    0b11000111: (2, 0),
    0b11000001: (3, 0),

    # Edge Cases
    0b11100111: (2, 0),
    0b11001111: (2, 0),
    0b11111100: (2, 2),
    0b01111110: (2, 2)
}

#
# 812
# 7-3 0b12345678
# 654
#
lemmmyWangs = {
    "dims": (5, 4),
    #b12345678
    0b00000000: (0, 3),
    0b00000100: (1, 3),
    0b01000100: (2, 3),
    0b01000000: (3, 3),
    0b00010111: (4, 3),
    #b12345678
    0b00010000: (0, 2),
    0b00011100: (1, 2),
    0b01111100: (2, 2),
    0b01110000: (3, 2),
    0b11010001: (4, 2),
    #b12345678
    0b00010001: (0, 1),
    0b00011111: (1, 1),
    0b11111111: (2, 1),
    0b11110001: (3, 1),
    #b12345678
    0b00000001: (0, 0),
    0b00000111: (1, 0),
    0b11000111: (2, 0),
    0b11000001: (3, 0),

    # Edge Cases
    0b11100111: (2, 0),
    0b11001111: (2, 0),
    0b11111100: (2, 2),
    0b01111110: (2, 2)
}

#
# 812
# 7-3 0b12345678
# 654
#
lemmmysGlowingWang = {
    "dims": (5, 4),
    #b12345678
    0b00000000: (0, 3),
    0b00000100: (1, 3),
    0b01000100: (2, 3),
    0b01000000: (3, 3),
    0b00010100: (4, 3),
    #b12345678
    0b00010000: (0, 2),
    0b00011100: (1, 2),
    0b01111100: (2, 2),
    0b01110000: (3, 2),
    0b00000101: (4, 2),
    #b12345678
    0b00010001: (0, 1),
    0b00011111: (1, 1),
    0b11111111: (2, 1),
    0b11110001: (3, 1),
    0b01010000: (4, 1),
    #b12345678
    0b00000001: (0, 0),
    0b00000111: (1, 0),
    0b11000111: (2, 0),
    0b11000001: (3, 0),
    0b01000001: (4, 0),

    # Edge Cases
    0b11100111: (2, 0),
    0b11001111: (2, 0),
    0b11111100: (2, 2),
    0b01111110: (2, 2)
}

noWangsForYou = {
    "dims": (1, 1),
    0: (0, 0)
}

#
# 812
# 7-3 0b12345678
# 654
#
fullWangs = {
    "dims": (12, 4),
    0b00000000: (0, 3),
    0b00000100: (1, 3),
    0b01000100: (2, 3),
    0b01000000: (3, 3),
    0b00010100: (4, 3),
    0b01010000: (5, 3),
    0b00010101: (6, 3),
    0b01010100: (7, 3),
    0b01010111: (8, 3),
    0b01011101: (9, 3),
    0b10110101: (10, 3),
    0b11010111: (11, 3),
    0b00010000: (0, 2),
    0b00011100: (1, 2),
    0b01111100: (2, 2),
    0b01110000: (3, 2),
    0b00000101: (4, 2),
    0b01000001: (5, 2),
    0b01000101: (6, 2),
    0b01010001: (7, 2),
    0b11010101: (8, 2),
    0b01110101: (9, 2),
    0b01111101: (10, 2),
    0b01011111: (11, 2),
    0b00010001: (0, 1),
    0b00011111: (1, 1),
    0b11111111: (2, 1),
    0b11110001: (3, 1),
    0b00011101: (4, 1),
    0b01110100: (5, 1),
    0b00010111: (6, 1),
    0b01011100: (7, 1),
    0b11110111: (8, 1),
    0b11011111: (9, 1),
    0b01110111: (10, 1),
    0b11011101: (11, 1),
    0b00000001: (0, 0),
    0b00000111: (1, 0),
    0b11000111: (2, 0),
    0b11000001: (3, 0),
    0b01000111: (4, 0),
    0b11010001: (5, 0),
    0b11000101: (6, 0),
    0b01110001: (7, 0),
    0b11111101: (8, 0),
    0b01111111: (9, 0),
    0b01010101: (10, 0),
}

wangList = [
    { "name": "Normal Wangs", "value": fullWangs },
    { "name": "Reset Blocks", "value": noWangsForYou },
    { "name": "Marble", "value": lemmmyWangs },
    { "name": "Glowstone", "value": lemmmysGlowingWang },
    { "name": "Monitor", "value": noCornerWangs },
]

def getWang():
    scn = bpy.context.scene
    return wangList[int(scn.tmp_mcs_wangset.source)]["value"]

class WangSourceProperty(bpy.types.PropertyGroup):
   mode_options = [
        (str(i), ws["name"], "")
        for i, ws in enumerate(wangList)
   ]

   source: bpy.props.EnumProperty(
        items=mode_options,
        description="Wang Tileset",
        default="0",
        update=lambda x, y: print(x, y)
    )
    

def sign(x):
    """Returns the sign of x as 0 or 1"""
    return 1 if x > 0 else 0

def main(op, context):
    wangSource = getWang()
    
    # Grab a BMesh for editing
    obj = bpy.context.object
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    
    # Acting on selected faces only
    selectedQuads = [face for face in bm.faces if face.select]

    # Active view
    r3d = bpy.context.space_data.region_3d

    # View directions
    outVector   = r3d.view_rotation @ Vector((0.0, 0.0, 1.0))
    upVector    = r3d.view_rotation @ Vector((0.0, 1.0, 0.0))
    rightVector = r3d.view_rotation @ Vector((1.0, 0.0, 0.0))

    # All BMesh coordinates are in local space, but our view
    # is in global space, so we need to normalize the coordinate space.
    def localToWorld(vec):
        t = vec.to_4d()
        t.w = 0
        return (obj.matrix_world @ t).to_3d()
    
    # Misaligned quads almost definitely weren't meant 
    # to be selected and will be set incorrectly.
    # So, we check and alert if we find any.
    def checkAlignment(quad):
        norm = localToWorld(quad.normal)
        adj = norm @ outVector
        if adj < 0.5:
            return False # Misaligned
        
        return True

    oldLen = len(selectedQuads)
    selectedQuads = [q for q in selectedQuads if checkAlignment(q)]
    if len(selectedQuads) != oldLen:
        op.report({"ERROR"}, "The view is misaligned with some face(s), they will be skipped.")

    origin = localToWorld(selectedQuads[0].calc_center_median())
    
    planarTransform = Matrix.Translation(-origin)
    localizedCoords = [planarTransform @ localToWorld(f.calc_center_median()) for f in selectedQuads]

    # Snap the View Vectors to the closest plane
    # TODO: Snap to face normals so that diagonal/rotated geometry is possible
    outVector   = Vector((round(outVector.x  ), round(outVector.y  ), round(outVector.z  )))
    upVector    = Vector((round(upVector.x   ), round(upVector.y   ), round(upVector.z   )))
    rightVector = Vector((round(rightVector.x), round(rightVector.y), round(rightVector.z)))
    
    # Normalized coordinates that take rotation into account
    inlineCoords = [
        (round(upVector @ v), round(rightVector @ v), round(outVector @ v))
        for v in localizedCoords
    ]
    
    # Build the surface map
    mapping = {}
    for i in range(len(inlineCoords)):
        x, y, z = inlineCoords[i]
        mapping[str(x)+";"+str(y)+";"+str(z)] = i
    
    stepX, stepY = wangSource["dims"]
    stepX, stepY = 1 / stepX, 1 / stepY
    
    # Grab the UV layer so we can start editing
    uv_layer = bm.loops.layers.uv.active
    
    # Compute the wang tiles
    for i in range(len(inlineCoords)):
        x, y, z = inlineCoords[i]
        def check(dx, dy):
            return (str(x+dx)+";"+str(y+dy)+";"+str(z)) in mapping

        bitmask = (
            check( 1, -1) << 7 |
            check( 1,  0) << 0 |
            check( 1,  1) << 1 |
            check( 0, -1) << 6 |
            check( 0,  1) << 2 |
            check(-1, -1) << 5 |
            check(-1,  0) << 4 |
            check(-1,  1) << 3 )

        if bitmask in wangSource:
            mappedWang = wangSource[bitmask]
        else:
            # Strip corners on hard edges
            bareBitmask = bitmask
            if ~bitmask & 0b00000001: bareBitmask &= 0b01111101
            if ~bitmask & 0b00000100: bareBitmask &= 0b11110101
            if ~bitmask & 0b00010000: bareBitmask &= 0b11010111
            if ~bitmask & 0b01000000: bareBitmask &= 0b01011111


            if bareBitmask in wangSource:
                mappedWang = wangSource[bareBitmask]
            else:
                op.report({"WARNING"}, "Encountered an unmapped wang: " + bin(bitmask))

                # Substitute base case
                mappedWang = wangSource[0]

        # Reposition the mapping for this specific face
        singleOrigin = localToWorld(selectedQuads[i].calc_center_median())
        faceTransform = Matrix.Translation(-singleOrigin)
        
        for loop in selectedQuads[i].loops:
            wangX, wangY = mappedWang
            
            xp = rightVector @ (faceTransform @ localToWorld(loop.vert.co))
            yp = upVector @ (faceTransform @ localToWorld(loop.vert.co))
            
            u = round(stepX * (sign(xp) + wangX), 3)
            v = round(stepY * (sign(yp) + wangY), 3)
            
            uvDest = loop[uv_layer].uv
            uvDest.x, uvDest.y = u, v
    
    bm.to_mesh(bpy.context.object.data)
    


class UvMCSOperator(Operator):
    """UV Onperator description"""
    bl_idname = "uv.connect_mc_textures"
    bl_label = "Connect MC Textures"
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT'

    def execute(self, context):
        returnMode = None
        if bpy.context.active_object.mode != "OBJECT":
            returnMode = bpy.context.active_object.mode
            bpy.ops.object.mode_set(mode="OBJECT")
        
        main(self, context)
        
        if returnMode != None:
            bpy.ops.object.mode_set(mode=returnMode)
        
        return {'FINISHED'}
    
class MCSPanel(Panel):
    """"""
    bl_idname = "VIEW3D_PT_mcs"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Connected Tiles"
    bl_category = "TMPIM"
    
    wang_enum = bpy.props.EnumProperty(
        items = [
            ("wang-" + str(i), ws["name"], "")
            for i, ws in enumerate(wangList)
        ]
    )
    
    def draw(self, context):
        layout = self.layout
        
        if not bpy.context.active_object or bpy.context.active_object.mode != "EDIT":
            row = layout.row()
            row.label(text="Please enter edit mode to use this tool.")
        else:
            obj = bpy.context.edit_object
            me = obj.data
            bm = bmesh.from_edit_mesh(me)
            faceCnt = len([face for face in bm.faces if face.select])
            
            col = layout.column()
            col.label(text="Faces selected for joining: " + str(faceCnt))
            row = col.row(align=True)
            row.label(text="WangSet")
            row.prop(bpy.context.scene.tmp_mcs_wangset, "source", text="")
            
            col.separator()
            
            col = col.column()
            col.scale_y = 1.5
            col.operator("uv.connect_mc_textures", text="Join Faces", icon="OUTLINER_DATA_LATTICE")

def register():
    bpy.utils.register_class(WangSourceProperty)
    bpy.types.Scene.tmp_mcs_wangset = PointerProperty(type=WangSourceProperty)
    bpy.utils.register_class(UvMCSOperator)
    bpy.utils.register_class(MCSPanel)


def unregister():
    del bpy.types.Scene.tmp_mcs_wangset
    bpy.utils.unregister_class(WangSourceProperty)
    bpy.utils.unregister_class(UvMCSOperator)
    bpy.utils.unregister_class(MCSPanel)
    
if __name__ == "__main__":
    self = bpy.data.texts["AMCS"].as_module()
    self.register()
