import bpy

print("go")
for mat in bpy.data.materials:
    #if not material.users:
#    objs = []
#    for obj in bpy.data.objects:
#        for slot in obj.material_slots:
#            if slot.material == material:
#                objs.append(obj)
    
    print(mat.name)
    nodes = mat.node_tree.nodes
    
    im = None
    for node in nodes:
        if node.type == "TEX_IMAGE":
            print(node.image)
            im = node.image
            break
#    print(mat.node_tree.nodes.clear)
    nodes.clear()

    tex_node = nodes.new(type="ShaderNodeTexImage")
    tex_node.location = (-400, 0)
    tex_node.image = im
    
    shader_node = nodes.new(type="ShaderNodeBsdfPrincipled")
    shader_node.location = (0, 0)

    node_output = nodes.new(type='ShaderNodeOutputMaterial')   
    node_output.location = 400,0
    
    # link
    links = mat.node_tree.links
    
    links.new(tex_node.outputs[0], shader_node.inputs[0])
    links.new(shader_node.outputs[0], node_output.inputs[0])
