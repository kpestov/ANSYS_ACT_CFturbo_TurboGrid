import xml.etree.ElementTree as ET


FILE = r'C:\ansys_projects\act\kp\CFturbo_files\test-impeller.cft-batch'
# FILE = task.ActiveDirectory + r"\test-impeller.cft-batch"


# def get_xml_root():
#     tree = ET.parse(FILE)
#     root = tree.getroot()
#     return root
#
#
# def get_design_impeller_node(root):
#     cfturbo_batch_project_node = root.find('CFturboBatchProject')
#     updates_node = cfturbo_batch_project_node.find('Updates')
#     cfturbo_project_node = updates_node.find('CFturboProject')
#
#     for impeller_design_node in cfturbo_project_node:
#         return impeller_design_node
#
#
# def get_impeller_main_dimensions(impeller_design_node):
#     main_dimensions = {}
#     main_dimensions_node = impeller_design_node.find('MainDimensions')
#     main_dimensions_sub_node = main_dimensions_node.find('MainDimensionsElement')
#
#     # in future for dict keys use attribute names instead tags since they are unique and the tags can intersect
#     for child in main_dimensions_sub_node:
#         main_dimensions[child.tag] = child.text
#     return main_dimensions
#
#
# xml_root = get_xml_root()
# design_impeller_node = get_design_impeller_node(xml_root)
# impeller_main_dimensions = get_impeller_main_dimensions(design_impeller_node)
# print(impeller_main_dimensions)


tree = ET.parse(FILE)
root = tree.getroot()

cfturbo_batch_project_node = root.find('CFturboBatchProject')
updates_node = cfturbo_batch_project_node.find('Updates')
cfturbo_project_node = updates_node.find('CFturboProject')

for impeller_design_node in cfturbo_project_node:
    main_dimensions = {}
    main_dimensions_node = impeller_design_node.find('MainDimensions')
    main_dimensions_sub_node = main_dimensions_node.find('MainDimensionsElement')

    for child in main_dimensions_sub_node:
        main_dimensions[child.tag] = child.text

    print(main_dimensions)




























