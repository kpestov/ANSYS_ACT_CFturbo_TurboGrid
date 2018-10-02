import math
import xml.etree.ElementTree as ET
import os
from pprint import pprint

# FILE = r'RP nq23 inducer.xml'
FILE = r'AP nq120.xml'
# FILE = r'MP nq94 coolant (generic).xml'
# FILE = r'CC pi2.4 impeller (generic).xml'

tree = ET.parse(FILE)
root = tree.getroot()

blade_properties_element = root[0][0][0][0][2]

spans = int(blade_properties_element[1].text)
main_element = root[0][0][0][0][0]
main_dimensions_element = main_element[0]

skeletonlines_element = root[0][0][0][0][3]
num_of_bezier_curves = len(skeletonlines_element[0][0])
print(num_of_bezier_curves)

# def get_phi_angles(number, phiLE, phiTE):
#     phi_angles = {}
#
#     Bezier3SL_element = skeletonlines_element[0][0][number]
#     num_of_points = Bezier3SL_element[0].attrib['Count']
#     anglesLe = Bezier3SL_element[0][0]
#     anglesTe = Bezier3SL_element[0][int(num_of_points)-1]
#     phi_angles[phiLE] = anglesLe[0].text
#     phi_angles[phiTE] = anglesTe[0].text
#
#     return phi_angles


def writes_phi_angles(number, phiLEValue, phiTEValue):

    Bezier3SL_element = skeletonlines_element[0][0][number]
    num_of_points = Bezier3SL_element[0].attrib['Count']
    anglesLe = Bezier3SL_element[0][0]
    anglesTe = Bezier3SL_element[0][int(num_of_points)-1]
    anglesLe[0].text = phiLEValue
    anglesTe[0].text = phiTEValue


writes_phi_angles(0, '1.0', '2.0')
writes_phi_angles(1, '3.0', '4.0')


tree.write(FILE)























