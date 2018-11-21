"""This module parses .cft-batch file (.xml), pulls parameters from it and inserts them to properties table in WB.

"""

import os
import math
import clr
import xml.etree.ElementTree as ET
clr.AddReference("Ans.UI.Toolkit")


class Impeller:
    def __init__(self, task):
        self.task = task

    def get_cft_batch_path(self, task):
        for cft_file in os.listdir(task.ActiveDirectory):
            if cft_file.endswith(".cft-batch"):
                cft_file_path = os.path.join(task.ActiveDirectory, cft_file)
                return cft_file_path

    def get_xml_tree(self, task):
        cft_batch_file_path = self.get_cft_batch_path(task)
        tree = ET.parse(cft_batch_file_path)
        return tree

    def get_xml_root(self, task):
        tree = self.get_xml_tree(task)
        root = tree.getroot()
        return root

    def get_main_element(self, task, node=0):
        root = self.get_xml_root(task)
        main_element = root[0][0][0][0][node]
        return main_element


class MainDimensions(Impeller):
    def __init__(self, task):
        Impeller.__init__(self, task)
        self.group = task.Properties["MainDimensions"]

        # properties for radial and mixed pumps
        self.hub_diameter = self.group.Properties["HubDiameter"]
        self.suction_diameter = self.group.Properties["SuctionDiameter"]
        self.impeller_diameter = self.group.Properties["ImpellerDiameter"]
        self.impeller_outlet_width = self.group.Properties["ImpellerOutletWidth"]

        # properties for axial pump
        self.hub_diameter_outlet = self.group.Properties["HubDiameterOutlet"]
        self.tip_diameter_outlet = self.group.Properties["TipDiameterOutlet"]


    def get_main_dimensions_element(self, task):
        main_element = Impeller(task).get_main_element(task, node=0)
        main_dimensions_element = main_element[0]
        return main_dimensions_element

    def main_dim_exist(self, task, tag, attrib, attribValue):
        main_dimensions_element = MainDimensions(task).get_main_dimensions_element(task)
        try:
            ds = main_dimensions_element.find(tag).attrib[attrib]
            if ds == '{}'.format(attribValue):
                return 1
        except AttributeError:
            pass

    def insert_main_dimensions(self, task):
        main_dimensions_element = MainDimensions(task).get_main_dimensions_element(task)

        for child in main_dimensions_element:

            # properties for axial pump
            if child.attrib["Caption"] == "Hub diameter outlet":
                self.hub_diameter_outlet.Value = child.text
            if child.attrib["Caption"] == "Tip diameter outlet":
                self.tip_diameter_outlet.Value = child.text

            # properties for radial and mixed pumps
            if child.attrib["Caption"] == "Hub diameter":
                self.hub_diameter.Value = child.text
            if child.attrib["Caption"] == "Suction diameter":
                self.suction_diameter.Value = child.text
            if child.attrib["Caption"] == "Impeller diameter":
                self.impeller_diameter.Value = child.text
            if child.attrib["Caption"] == "Outlet width":
                self.impeller_outlet_width.Value = child.text

    def write_main_dimensions(self, task):
        '''
        Updates parameters of main dimensions property group when user changes values in table and writes
        new .cft-batch file.
        :return: refreshed .cft-batch file

        '''

        # MainDimensions and Impeller classes from xml_parser.py module
        mainDim = MainDimensions(task)
        impeller = Impeller(task)

        tree = impeller.get_xml_tree(task)
        root = tree.getroot()

        # get main dimensions element
        main_dimensions_element = root[0][0][0][0][0][0]

        # the code bellow writes new values of parameter when update cell#2
        for child in main_dimensions_element:

            # properties for axial pump
            if child.attrib["Caption"] == "Hub diameter":
                child.text = str(mainDim.hub_diameter.Value)
            if child.attrib["Caption"] == "Suction diameter":
                child.text = str(mainDim.suction_diameter.Value)
            if child.attrib["Caption"] == "Hub diameter outlet":
                child.text = str(mainDim.hub_diameter_outlet.Value)
            if child.attrib["Caption"] == "Tip diameter outlet":
                child.text = str(mainDim.tip_diameter_outlet.Value)

            # properties for radial and mixed pumps
            if child.attrib["Caption"] == "Impeller diameter":
                child.text = str(mainDim.impeller_diameter.Value)
            if child.attrib["Caption"] == "Outlet width":
                child.text = str(mainDim.impeller_outlet_width.Value)

        target_dir = copy_cft_file(task)
        tree.write(target_dir + '-batch')


class BladeProperties(Impeller):
    def __init__(self, task):
        Impeller.__init__(self, task)
        self.group = task.Properties["BladeProperties"]
        self.number_blades = self.group.Properties["NumberBlades"]
        self.le_thickness_hub = self.group.Properties["BladeThicknessLeHub"]
        self.le_thickness_shroud = self.group.Properties["BladeThicknessLeShroud"]
        self.te_thickness_hub = self.group.Properties["BladeThicknessTeHub"]
        self.te_thickness_shroud = self.group.Properties["BladeThicknessTeShroud"]
        self.beta_1_h = self.group.Properties['beta1h']
        self.beta_1_s = self.group.Properties['beta1s']
        self.beta_2_h = self.group.Properties['beta2h']
        self.beta_2_s = self.group.Properties['beta2s']

    def get_blade_properties_element(self, task):
        main_element = Impeller(task).get_main_element(task, node=2)
        return main_element

    def get_main_blade_element(self, task):
        tread_array = self.get_blade_properties_element(task).find('TReadWriteArray_TBladeProps')
        main_blade_element = tread_array[0]
        return main_blade_element

    def beta_exist(self, task, tag):
        main_blade_element = self.get_main_blade_element(task)
        beta = main_blade_element.find(tag)
        if beta is None:
            return
        else:
            return 1


    def get_num_spans(self, task):

        main_blade_element = self.get_main_blade_element(task)
        spans = main_blade_element.find('Beta1').attrib['Count']

        return spans


    def get_blade_angles(self, task, node, betah, betas):

        spans = self.get_num_spans(task)

        blade_angles = {}
        for child in node:
            if child.attrib["Index"] == "0":
                blade_angles["{}".format(betah)] = child.text
            if child.attrib["Index"] == "{}".format(int(spans) - 1):
                blade_angles["{}".format(betas)] = child.text

        return blade_angles


    def join_blade_properties(self, task):
        '''
        Join beta_1_angles, beta_2_angles, blade_thickness_le and blade_thickness_te dicts.
        :return: blade_properties dict

        '''
        main_blade_element = self.get_main_blade_element(task)
        blade_properties = {}

        # try to extract blade angles from .cft-batch file. Check existence of Beta1 node
        try:
            main_blade_element.find('Beta1')
        except IndexError:
            pass
        else:
            beta1_node = main_blade_element.find('Beta1')
            beta2_node = main_blade_element.find('Beta2')

            beta_1_angles = self.get_blade_angles(task, beta1_node, 'beta1h', 'beta1s')
            beta_2_angles = self.get_blade_angles(task, beta2_node, 'beta2h', 'beta2s')
            blade_properties.update(beta_1_angles)
            blade_properties.update(beta_2_angles)

        return blade_properties


    def insert_blade_properties(self, task):
        blade_properties_element = self.get_blade_properties_element(task)
        main_blade_element = self.get_main_blade_element(task)

        number_of_blades = blade_properties_element.find('nBl').text
        self.number_blades.Value = number_of_blades

        for child in main_blade_element:
            if child.attrib["Caption"] == "Thickness LE@hub":
                self.le_thickness_hub.Value = child.text
            if child.attrib["Caption"] == "Thickness LE@shroud":
                self.le_thickness_shroud.Value = child.text
            if child.attrib["Caption"] == "Thickness TE@hub":
                self.te_thickness_hub.Value = child.text
            if child.attrib["Caption"] == "Thickness TE@shroud":
                self.te_thickness_shroud.Value = child.text

        blade_properties = self.join_blade_properties(task)

        if "beta1h" in blade_properties:

            # convert from radians to degree
            self.beta_1_h.Value = round((float(blade_properties["beta1h"]) * 180/math.pi), 1)
            self.beta_1_s.Value = round((float(blade_properties['beta1s']) * 180/math.pi), 1)
            self.beta_2_h.Value = round((float(blade_properties['beta2h']) * 180/math.pi), 1)
            self.beta_2_s.Value = round((float(blade_properties['beta2s']) * 180/math.pi), 1)


    def write_thickness(self, main_blade_element, paramValue, HubOrShroud):
        main_blade_element.find('{}'.format(HubOrShroud)).text = str(paramValue)


    def write_blade_angles(self, node, indexValue, paramValue):
        for child in node:
            if child.attrib["Index"] == "{}".format(indexValue):
                child.text = str(round(((float(paramValue) / 180) * math.pi), 7))


    def write_interpolated_blade_angles(self, task, node, betah, betas):
        '''
        Writes interpolated values of angles to the Beta1 and Beta2 nodes. By default linear interpolation works.

        '''
        spans = int(self.get_num_spans(task))

        main_blade_element = self.get_main_blade_element(task)
        beta_node = main_blade_element.find('Beta1')
        angles_quantity = len([i for i in beta_node])

        for i in range(angles_quantity):
            # if beta angles from hub and shroud are equal, writes all values = value of angles from hub side
            if betah == betas:
                node[i].text = str(round(((float(betah) / 180) * math.pi), 7))
            else:
                # make linear interpolation from beta hub angle to shroud angle
                node[i].text = str(
                    float(node[0].text) - i * (float(node[0].text) - float(node[angles_quantity - 1].text)) / (angles_quantity - 1))


class SkeletonLines(Impeller):
    def __init__(self, task):
        Impeller.__init__(self, task)
        self.group = task.Properties["BladeMeanLines"]
        self.phiLE = self.group.Properties['phiLE']
        self.phiTE = self.group.Properties['phiTE']


    def get_skeletonLines_element(self, task):
        main_element = Impeller(task).get_main_element(task, node=3)
        return main_element


    def get_phi_angles(self, task, phiLE, phiTE):
        phi_node = self.get_skeletonLines_element(task)[0][0][0][0]

        phi_angles = {}
        phi_angles[phiTE] = phi_node[0].find('tePos').text
        phi_angles[phiLE] = phi_node[0].find('lePos').text
        return phi_angles


    def join_phi_angles(self, task):
        skeletonLinesProp = {}
        phi = self.get_phi_angles(task, 'phiLE', 'phiTE')
        skeletonLinesProp.update(phi)
        return skeletonLinesProp


    def insert_skeletonLines_properties(self, task):
        skeletonLinesProp = self.join_phi_angles(task)

        # convert from radians to degree
        self.phiLE.Value = round((float(skeletonLinesProp["phiLE"]) * 180/math.pi), 1)
        self.phiTE.Value = round((float(skeletonLinesProp["phiTE"]) * 180/math.pi), 1)


    def writes_phi_angles( self, task, phiLEValue, phiTEValue ):
        impeller = Impeller(task)
        tree = impeller.get_xml_tree(task)
        root = tree.getroot()
        skeletonlines_element = root[0][0][0][0][3]
        phi_node = skeletonlines_element[0][0][0][0]

        for i in phi_node:
            i.find('lePos').text = str(round(((float(phiLEValue) / 180) * math.pi), 15))
            i.find('tePos').text = str(round(((float(phiTEValue) / 180) * math.pi), 15))

        target_dir = copy_cft_file(task)
        tree.write(target_dir + '-batch')


class Meridian(Impeller):
    def __init__(self, task):
        Impeller.__init__(self, task)
        self.group = task.Properties['Meridian']
        self.LePosHub = self.group.Properties['LePosHub']
        self.LePosShroud = self.group.Properties['LePosShroud']
        self.TePosHub = self.group.Properties['TePosHub']
        self.TePosShroud = self.group.Properties['TePosShroud']
        self.LePosHubSplitter = self.group.Properties['LePosHubSplitter']
        self.LePosShroudSplitter = self.group.Properties['LePosShroudSplitter']


    def get_meridian_element(self, task):
        main_element = Impeller(task).get_main_element(task, node=1)
        return main_element


    def get_positions(self, task):

        positions_attribs = [
            'LePosHub',
            'LePosShroud',
            'TePosHub',
            'TePosShroud',
            'LePosHubSplitter',
            'LePosShroudSplitter'
        ]

        positions_list = [
            'GeoLeadingEdge_u-Hub',
            'GeoLeadingEdge_u-Shroud',
            'GeoTrailingEdge_u-Hub',
            'GeoTrailingEdge_u-Shroud',
            'GeoSplitLeadingEdge_u-Hub',
            'GeoSplitLeadingEdge_u-Shroud'
        ]

        positions = dict(zip(positions_attribs, positions_list))
        main_element = self.get_meridian_element(task)

        for key, value in positions.items():
            if main_element.find(value) is None:
                del positions[key]
            else:
                positions[key] = main_element.find(value).text
        return positions


    def insert_meridian_properties(self, task):
        meridian_properties = self.get_positions(task)

        if 'LePosHub' in meridian_properties:
            self.LePosHub.Value = meridian_properties['LePosHub']
        if 'LePosShroud' in meridian_properties:
            self.LePosShroud.Value = meridian_properties['LePosShroud']
        if 'TePosHub' in meridian_properties:
            self.TePosHub.Value = meridian_properties['TePosHub']
        if 'TePosShroud' in meridian_properties:
            self.TePosShroud.Value = meridian_properties['TePosShroud']
        if 'LePosHubSplitter' in meridian_properties:
            self.LePosHubSplitter.Value = meridian_properties['LePosHubSplitter']
        if 'LePosShroudSplitter' in meridian_properties:
            self.LePosShroudSplitter.Value = meridian_properties['LePosShroudSplitter']


    def position_exist(self, task, key):
        meridian_properties = self.get_positions(task)
        if key not in meridian_properties:
            return
        else:
            return 1


    def writes_positions(self, task, posParam, HubOrShroud):
        impeller = Impeller(task)
        tree = impeller.get_xml_tree(task)
        root = tree.getroot()
        meridian_element = root[0][0][0][0][1]

        meridian_element.find('{}'.format(HubOrShroud)).text = str(posParam)

        target_dir = copy_cft_file(task)
        tree.write(target_dir + '-batch')


class BladeProfiles(Impeller):
    def __init__(self, task):
        Impeller.__init__(self, task)
        self.group = task.Properties['BladeProfiles']
        self.DstPresSideHub_1 = self.group.Properties['DstPresSideHub_1']
        self.DstPresSideHub_2 = self.group.Properties['DstPresSideHub_2']
        self.DstPresSideHub_3 = self.group.Properties['DstPresSideHub_3']
        self.DstPresSideHub_4 = self.group.Properties['DstPresSideHub_4']
        self.DstPresSideShroud_1 = self.group.Properties['DstPresSideShroud_1']
        self.DstPresSideShroud_2 = self.group.Properties['DstPresSideShroud_2']
        self.DstPresSideShroud_3 = self.group.Properties['DstPresSideShroud_3']
        self.DstPresSideShroud_4 = self.group.Properties['DstPresSideShroud_4']


    def get_blade_profiles_element(self, task):
        main_element = Impeller(task).get_main_element(task, node=4)
        return main_element


    def get_distances(self, task, HubShroud, DstPresSideHubShroud ):
        distances = {}
        main_ps_node = self.get_blade_profiles_element(task)[HubShroud]

        point_count = 1
        for child in main_ps_node:
            distances['{}_{}'.format(DstPresSideHubShroud, point_count)] = child.text
            point_count += 1
        return distances


    def join_distances_to_pres_side(self, task):
        bladeDistancesProps = {}

        DstPresSideHub = self.get_distances(task, 0, 'DstPresSideHub')
        DstPresSideShroud = self.get_distances(task, 1, 'DstPresSideShroud')

        bladeDistancesProps.update(DstPresSideHub)
        bladeDistancesProps.update(DstPresSideShroud)

        return bladeDistancesProps


    def insert_distances_to_pres_side(self, task):
        distances_to_pres_side = self.join_distances_to_pres_side(task)

        if 'DstPresSideHub_1' in distances_to_pres_side:
            self.DstPresSideHub_1.Value = distances_to_pres_side['DstPresSideHub_1']
        if 'DstPresSideHub_2' in distances_to_pres_side:
            self.DstPresSideHub_2.Value = distances_to_pres_side['DstPresSideHub_2']
        if 'DstPresSideHub_3' in distances_to_pres_side:
            self.DstPresSideHub_3.Value = distances_to_pres_side['DstPresSideHub_3']
        if 'DstPresSideHub_4' in distances_to_pres_side:
            self.DstPresSideHub_4.Value = distances_to_pres_side['DstPresSideHub_4']

        if 'DstPresSideShroud_1' in distances_to_pres_side:
            self.DstPresSideShroud_1.Value = distances_to_pres_side['DstPresSideShroud_1']
        if 'DstPresSideShroud_2' in distances_to_pres_side:
            self.DstPresSideShroud_2.Value = distances_to_pres_side['DstPresSideShroud_2']
        if 'DstPresSideShroud_3' in distances_to_pres_side:
            self.DstPresSideShroud_3.Value = distances_to_pres_side['DstPresSideShroud_3']
        if 'DstPresSideShroud_4' in distances_to_pres_side:
            self.DstPresSideShroud_4.Value = distances_to_pres_side['DstPresSideShroud_4']


    def dst_to_press_side_exist(self, task, key):
        distances = self.join_distances_to_pres_side(task)
        if key not in distances:
            return
        else:
            return 1


    def write_blade_distances(self, task, HubShroud, indexValue, paramValue):
        impeller = Impeller(task)
        tree = impeller.get_xml_tree(task)
        root = tree.getroot()
        blade_profiles_element = root[0][0][0][0][4]
        pressure_side_node = blade_profiles_element[HubShroud]

        for child in pressure_side_node:
            if child.attrib["Index"] == "{}".format(indexValue):
                child.text = str(paramValue)

        target_dir = copy_cft_file(task)
        tree.write(target_dir + '-batch')