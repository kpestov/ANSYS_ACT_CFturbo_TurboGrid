import xml.etree.ElementTree as ET
import os
import math
import clr
clr.AddReference("Ans.UI.Toolkit")
from Ansys.UI.Toolkit import *


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

        # this property is the same for all types of pumps
        # I've commented it because it is possible to parameterized tip clearance in TurboGrid
        # self.tip_clearance = self.group.Properties["TipClearance"]

        # properties for radial and mixed pumps
        self.hub_diameter = self.group.Properties["HubDiameter"]
        self.suction_diameter = self.group.Properties["SuctionDiameter"]
        self.impeller_diameter = self.group.Properties["ImpellerDiameter"]
        self.impeller_outlet_width = self.group.Properties["ImpellerOutletWidth"]

        # properties for axial pump
        self.hub_diameter_inlet = self.group.Properties["HubDiameterInlet"]
        self.tip_diameter_inlet = self.group.Properties["TipDiameterInlet"]
        self.hub_diameter_outlet = self.group.Properties["HubDiameterOutlet"]
        self.tip_diameter_outlet = self.group.Properties["TipDiameterOutlet"]

    # I've commented it because it is possible to parameterized tip clearance in TurboGrid
    # def tipClearanceExist(self, task):
    #     cft_file_path = self.get_cft_batch_path(task, '')
    #
    #     tree = ET.parse(cft_file_path)
    #     root = tree.getroot()
    #     main_dimensions_element = root[0][8].find('MainDimensions')
    #     unshrouded_element = main_dimensions_element.find('MainDimensionsElement').find('UnShrouded')
    #
    #     return unshrouded_element.text

    def get_main_dimensions_element(self, task):
        main_element = Impeller(task).get_main_element(task, node=0)
        main_dimensions_element = main_element[0]
        return main_dimensions_element

    def mainDimExist(self, task, tag, attrib, attribValue):
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
            if child.attrib["Caption"] == "Hub diameter":
                self.hub_diameter_inlet.Value = child.text
            if child.attrib["Caption"] == "Suction diameter":
                self.tip_diameter_inlet.Value = child.text
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


    def betaExist(self, task, tag):
        main_blade_element = self.get_main_blade_element(task)
        beta = main_blade_element.find(tag)
        if beta is None:
            return
        else:
            return 1

    # def get_blade_thickness(self, task, node, thickness_hub, thickness_shroud):
    #     '''
    #     Get blade properties of impeller from BladeProperties element and push it to dict
    #     :param task:
    #     :return: dict, e.g. blade_properties
    #     '''
    #     blade_thickness = {}
    #
    #     for child in node:
    #         if child.attrib["Index"] == "0":
    #             blade_thickness["{}".format(thickness_hub)] = child.text
    #         if child.attrib["Index"] == "1":
    #             blade_thickness["{}".format(thickness_shroud)] = child.text
    #
    #     return blade_thickness

    def getNumSpans(self, task):

        main_blade_element = self.get_main_blade_element(task)
        spans = main_blade_element.find('Beta1').attrib['Count']

        return spans

    def get_blade_angles(self, task, node, betah, betas):

        spans = self.getNumSpans(task)

        blade_angles = {}
        for child in node:
            if child.attrib["Index"] == "0":
                blade_angles["{}".format(betah)] = child.text
            if child.attrib["Index"] == "{}".format(int(spans) - 1):
                blade_angles["{}".format(betas)] = child.text

        return blade_angles

    def join_blade_properties(self, task):
        '''
        Join beta_1_angles, beta_2_angles, blade_thickness_le and blade_thickness_te dicts
        :param task:
        :return: blade_properties dict
        '''
        blade_properties_element = self.get_blade_properties_element(task)
        main_blade_element = self.get_main_blade_element(task)
        blade_properties = {}

        # for child in blade_properties_element:
        #     if child.attrib["Caption"] == "Number of blades":
        #         blade_properties[child.attrib['Caption']] = child.text

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
        # finally:
        #
        #     le_thickness_node = blade_properties_element[3][0][0]
        #     te_thickness_node = blade_properties_element[3][0][1]
        #
        #     blade_thickness_le = self.get_blade_thickness(task, le_thickness_node, 'BladeThicknessLeHub',
        #                                                   'BladeThicknessLeShroud')
        #     blade_thickness_te = self.get_blade_thickness(task, te_thickness_node, 'BladeThicknessTeHub',
        #                                                   'BladeThicknessTeShroud')
        #     blade_properties.update(blade_thickness_le)
        #     blade_properties.update(blade_thickness_te)
        return blade_properties

    def insert_blade_properties(self, task):
        blade_properties_element = self.get_blade_properties_element(task)
        main_blade_element = self.get_main_blade_element(task)

        number_of_blades = blade_properties_element.find('nBl').text
        self.number_blades.Value = number_of_blades

        # for child in blade_properties_element:
        #     if child.attrib["Caption"] == "Number of blades":
        #         self.number_blades.Value = child.text

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


    # def writeThickness(self, node, indexValue, paramValue):
    #     for child in node:
    #         if child.attrib["Index"] == "{}".format(indexValue):
    #             child.text = str(paramValue)

    def writeBladeAngles(self, node, indexValue, paramValue):
        for child in node:
            if child.attrib["Index"] == "{}".format(indexValue):
                child.text = str(round(((float(paramValue) / 180) * math.pi), 7))

    def writeInterpolatedBladeAngles(self, task, node, betah, betas):
        '''
        Writes interpolated values of angles to the Beta1 and Beta2 nodes. By default linear interpolation works
        '''
        spans = int(self.getNumSpans(task))

        for i in range(spans):
            # if beta angles from hub and shroud are equal, writes all values = value of angles from hub side
            if betah == betas:
                node[i].text = str(round(((float(betah) / 180) * math.pi), 7))
            else:
                # make linear interpolation from beta hub angle to shroud angle
                node[i].text = str(
                    float(node[0].text) - i * (float(node[0].text) - float(node[spans - 1].text)) / (spans - 1))


class SkeletonLines(Impeller):
    def __init__(self, task):
        Impeller.__init__(self, task)
        self.group = task.Properties["BladeMeanLines"]
        self.phiLEhub = self.group.Properties['phiLEhub']
        self.phiLEshroud = self.group.Properties['phiLEshroud']
        self.phiTEhub = self.group.Properties['phiTEhub']
        self.phiTEshroud = self.group.Properties['phiTEshroud']

    def get_skeletonLines_element(self, task):

        main_element = Impeller(task).get_main_element(task, node=3)

        return main_element

    def get_phi_angles(self, task, number, phiLE, phiTE):

        phi_node = self.get_skeletonLines_element(task)[0][0][0][0]

        phi_angles = {}
        phi_angles[phiTE] = phi_node[number].find('tePos').text
        phi_angles[phiLE] = phi_node[number].find('lePos').text
        return phi_angles

    def join_phi_angles(self, task):

        skeletonLinesProp = {}
        phi_hub = self.get_phi_angles(task, 0, 'phiLEhub', 'phiTEhub')
        phi_shroud = self.get_phi_angles(task, - 1, 'phiLEshroud', 'phiTEshroud')

        skeletonLinesProp.update(phi_hub)
        skeletonLinesProp.update(phi_shroud)

        return skeletonLinesProp

    def insert_skeletonLines_properties(self, task):

        skeletonLinesProp = self.join_phi_angles(task)

        # convert from radians to degree
        self.phiLEhub.Value = round((float(skeletonLinesProp["phiLEhub"]) * 180/math.pi), 1)
        self.phiLEshroud.Value = round((float(skeletonLinesProp["phiLEshroud"]) * 180/math.pi), 1)
        self.phiTEhub.Value = round((float(skeletonLinesProp["phiTEhub"]) * 180/math.pi), 1)
        self.phiTEshroud.Value = round((float(skeletonLinesProp["phiTEshroud"]) * 180/math.pi), 1)

    def writes_phi_angles(self, task, number, phiLEValue, phiTEValue):
        impeller = Impeller(task)

        tree = impeller.get_xml_tree(task)
        root = tree.getroot()

        check_node = self.get_skeletonLines_element(task)[0]
        splitter_node = check_node.find('RelativeSplitterPosition')

        if splitter_node is None:
            index = 0
        else:
            index = 1

        skeletonlines_element = root[0][0][0][0][3]
        Bezier3SL_element = skeletonlines_element[0][index][number]
        num_of_points = Bezier3SL_element[0].attrib['Count']
        anglesLe = Bezier3SL_element[0][0]
        anglesTe = Bezier3SL_element[0][int(num_of_points) - 1]

        anglesLe[0].text = str(round(((float(phiLEValue) / 180) * math.pi), 7))
        anglesTe[0].text = str(round(((float(phiTEValue) / 180) * math.pi), 7))

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

    def positionExist(self, task, key):

        meridian_properties = self.get_positions(task)

        if key not in meridian_properties:
            return
        else:
            return 1

    def writes_positions(self, task, numCurve, posParam, HubOrShroud):
        impeller = Impeller(task)
        tree = impeller.get_xml_tree(task)
        root = tree.getroot()
        meridian_element = root[0][0][0][0][1]

        pos_elements = meridian_element[0][numCurve]
        pos_elements.find('{}'.format(HubOrShroud)).text = str(posParam)

        target_dir = copy_cft_file(task)
        tree.write(target_dir + '-batch')


class BladeProfiles(Impeller):
    def __init__(self, task):
        Impeller.__init__(self, task)
        self.group = task.Properties['BladeProfiles']
        self.BladeThickHub_1 = self.group.Properties['BladeThickHub_1']
        self.BladeThickHub_2 = self.group.Properties['BladeThickHub_2']
        self.BladeThickHub_3 = self.group.Properties['BladeThickHub_3']
        self.BladeThickHub_4 = self.group.Properties['BladeThickHub_4']
        self.BladeThickShroud_1 = self.group.Properties['BladeThickShroud_1']
        self.BladeThickShroud_2 = self.group.Properties['BladeThickShroud_2']
        self.BladeThickShroud_3 = self.group.Properties['BladeThickShroud_3']
        self.BladeThickShroud_4 = self.group.Properties['BladeThickShroud_4']

    def get_blade_profiles_element(self, task):

        main_element = Impeller(task).get_main_element(task, node=4)

        return main_element

    def get_blade_thickness(self, task, HubShroud, BladeThickHubSroud):
        blade_thickness = {}
        node = self.get_blade_profiles_element(task)[0][HubShroud]
        points_nodes = node[0][0].findall('Point')[1:-1]
        j = 1
        for i in points_nodes:
            thickness = i.find('y').text
            blade_thickness['{}_{}'.format(BladeThickHubSroud, j)] = 2 * float(thickness)
            j += 1
        return blade_thickness

    def join_blade_thickness(self, task):
        bladeThicknessProps = {}

        BladeThickHub = self.get_blade_thickness(task, 0, 'BladeThickHub')
        BladeThickShroud = self.get_blade_thickness(task, 1, 'BladeThickShroud')

        bladeThicknessProps.update(BladeThickHub)
        bladeThicknessProps.update(BladeThickShroud)

        return bladeThicknessProps

    def insert_blade_thickness(self, task):
        blade_thickness = self.join_blade_thickness(task)

        if 'BladeThickHub_1' in blade_thickness:
            self.BladeThickHub_1.Value = blade_thickness['BladeThickHub_1']
        if 'BladeThickHub_2' in blade_thickness:
            self.BladeThickHub_2.Value = blade_thickness['BladeThickHub_2']
        if 'BladeThickHub_3' in blade_thickness:
            self.BladeThickHub_3.Value = blade_thickness['BladeThickHub_3']
        if 'BladeThickHub_4' in blade_thickness:
            self.BladeThickHub_4.Value = blade_thickness['BladeThickHub_4']

        if 'BladeThickShroud_1' in blade_thickness:
            self.BladeThickShroud_1.Value = blade_thickness['BladeThickShroud_1']
        if 'BladeThickShroud_2' in blade_thickness:
            self.BladeThickShroud_2.Value = blade_thickness['BladeThickShroud_2']
        if 'BladeThickShroud_3' in blade_thickness:
            self.BladeThickShroud_3.Value = blade_thickness['BladeThickShroud_3']
        if 'BladeThickShroud_4' in blade_thickness:
            self.BladeThickShroud_4.Value = blade_thickness['BladeThickShroud_4']

    def bladeThicknessExist(self, task, key):
        blade_thickness = self.join_blade_thickness(task)
        if key not in blade_thickness:
            return
        else:
            return 1

    # def BladeProfilesExist(self, task):
    #     '''
    #     Visibility of all property group BladeProfiles
    #     :param task:
    #     :return:
    #     '''
    #     num_points = self.get_blade_profiles_element(task)
    #     if num_points == 2:
    #         return
    #     else:
    #         return 1

    def write_blade_thickness(self, task, HubShroud, indexValue, paramValue):
        impeller = Impeller(task)
        tree = impeller.get_xml_tree(task)
        root = tree.getroot()
        blade_profiles_element = root[0][0][0][0][4]

        node = blade_profiles_element[0][HubShroud]
        for i in range(2):
            points_nodes = node[i][0]
            for child in points_nodes:
                if child.attrib["Index"] == "{}".format(indexValue):
                    if i == 1:
                        child[1].text = str(-float(paramValue) / 2)
                    else:
                        child[1].text = str(float(paramValue) / 2)

        target_dir = copy_cft_file(task)
        tree.write(target_dir + '-batch')