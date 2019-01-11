import xml.etree.ElementTree as ET
import os
import math

cft_batch_file_path = 'radial_pump_10_3.cft-batch'
current_dir = os.getcwd()
target_dir = os.path.join(current_dir, cft_batch_file_path)

tree = ET.parse(cft_batch_file_path)
root = tree.getroot()

def write_blade_distances(HubShroud, indexValue, paramValue):
        blade_profiles_element = root[0][0][0][0][4]

        pressure_side_node = blade_profiles_element[HubShroud]
        for child in pressure_side_node:
            if child.attrib["Index"] == "{}".format(indexValue):
                child.text = str(paramValue)

        tree.write(target_dir)


def update():
    write_blade_distances(0, 0, 300)

update()