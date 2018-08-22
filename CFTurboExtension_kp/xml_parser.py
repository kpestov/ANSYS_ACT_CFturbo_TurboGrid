import xml.etree.ElementTree as ET
import os
import math


class Impeller:
    def __init__(self, task):
        self.task = task

    def get_cft_batch_path(self, task):
        '''
        Extract .cft-batch file path from active directory .\ACT
        :param task:
        :return: path of .cft-batch file
        '''
        for cft_file in os.listdir(task.ActiveDirectory):
            if cft_file.endswith(".cft-batch"):
                cft_file_path = os.path.join(task.ActiveDirectory, cft_file)

                return cft_file_path

    def get_xml_tree(self, task):
        '''
        Parses .cft-batch file for parameters extraction
        :param task:
        :return: parsed tree object of .cft-batch file
        '''
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
        self.tip_clearance = self.group.Properties["TipClearance"]

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

    def get_main_dimensions_element(self, task):
        '''
        Gets access to MainDimensionsElement element
        :param task:
        :return: MainDimensionsElement node of .cft-batch file
        '''

        # get main dimensions element
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
        '''
        Insert main dimensions of impeller to the table of properties of cell#1
        :param task:
        :return:
        '''
        main_dimensions_element = MainDimensions(task).get_main_dimensions_element(task)

        for child in main_dimensions_element:

            if child.attrib["Desc"] == "Tip clearance":
                self.tip_clearance.Value = child.text

            # properties for axial pump
            if child.attrib["Desc"] == "Hub diameter inlet dH1":
                self.hub_diameter_inlet.Value = child.text
            if child.attrib["Desc"] == "Tip diameter inlet dS1":
                self.tip_diameter_inlet.Value = child.text
            if child.attrib["Desc"] == "Hub diameter outlet dH2":
                self.hub_diameter_outlet.Value = child.text
            if child.attrib["Desc"] == "Tip diameter outlet dS2":
                self.tip_diameter_outlet.Value = child.text

            # properties for radial and mixed pumps
            if child.attrib["Desc"] == "Hub diameter dH":
                self.hub_diameter.Value = child.text
            if child.attrib["Desc"] == "Suction diameter dS":
                self.suction_diameter.Value = child.text
            if child.attrib["Desc"] == "Impeller diameter d2":
                self.impeller_diameter.Value = child.text
            if child.attrib["Desc"] == "Impeller outlet width b2":
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
        '''
        Gets access to BladeProperties element
        :param task:
        :return: BladeProperties node of .cft-batch file
        '''
        # get blade properties element
        main_element = Impeller(task).get_main_element(task, node=2)

        return main_element

    def betaExist(self, task, tag):
        angles = self.get_blade_properties_element(task)[3][0]
        beta = angles.find(tag)
        if beta is None:
            return
        else:
            return 1

    def get_blade_thickness(self, task, node, thickness_hub, thickness_shroud):
        '''
        Get blade properties of impeller from BladeProperties element and push it to dict
        :param task:
        :return: dict, e.g. blade_properties
        '''
        blade_properties_element = self.get_blade_properties_element(task)
        le_thickness_node = self.get_blade_properties_element(task)[3][0][0]
        te_thickness_node = self.get_blade_properties_element(task)[3][0][1]

        blade_thickness = {}

        for child in node:
            if child.attrib["Index"] == "0":
                blade_thickness["{}".format(thickness_hub)] = child.text
            if child.attrib["Index"] == "1":
                blade_thickness["{}".format(thickness_shroud)] = child.text

        return blade_thickness

    def getNumSpans(self, task):
        '''
        Extract number of spans from BladeProperties node
        :param task:
        :return:number of spans
        '''
        blade_properties_element = self.get_blade_properties_element(task)
        spans = blade_properties_element.find('Count').text

        return spans

    def get_blade_angles(self, task, node, betah, betas):
        '''
        Extract blade angles beta1, beta2 and push it to the blade_angles dict
        :param task:
        :param node:
        :param betah: beta1h, beta1s
        :param betas: beta2h, beta2s
        :return: blade_angles = {'beta1h': 0.2515, ...}
        '''

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

        blade_properties = {}

        for child in blade_properties_element:
            if child.attrib["Desc"] == "Number of blades":
                blade_properties[child.attrib['Desc']] = child.text

        # try to extract blade angles from .cft-batch file. Check existence of Beta1 node
        try:
            blade_properties_element[3][0][2]
        except IndexError:
            pass
        else:
            beta1_node = blade_properties_element[3][0][2]
            beta2_node = blade_properties_element[3][0][3]
            beta_1_angles = self.get_blade_angles(task, beta1_node, 'beta1h', 'beta1s')
            beta_2_angles = self.get_blade_angles(task, beta2_node, 'beta2h', 'beta2s')
            blade_properties.update(beta_1_angles)
            blade_properties.update(beta_2_angles)
        finally:
            le_thickness_node = blade_properties_element[3][0][0]
            te_thickness_node = blade_properties_element[3][0][1]
            blade_thickness_le = self.get_blade_thickness(task, le_thickness_node, 'BladeThicknessLeHub',
                                                          'BladeThicknessLeShroud')
            blade_thickness_te = self.get_blade_thickness(task, te_thickness_node, 'BladeThicknessTeHub',
                                                          'BladeThicknessTeShroud')
            blade_properties.update(blade_thickness_le)
            blade_properties.update(blade_thickness_te)

        return blade_properties

    def insert_blade_properties(self, task):
        '''
        Insert blade properties of impeller to the table of properties of cell#1
        :param task:
        :return:
        '''
        blade_properties = self.join_blade_properties(task)

        if "beta1h" in blade_properties:
            self.number_blades.Value = blade_properties['Number of blades']
            self.le_thickness_hub.Value = blade_properties['BladeThicknessLeHub']
            self.le_thickness_shroud.Value = blade_properties['BladeThicknessLeShroud']
            self.te_thickness_hub.Value = blade_properties['BladeThicknessTeHub']
            self.te_thickness_shroud.Value = blade_properties['BladeThicknessTeShroud']

            self.beta_1_h.Value = round((float(blade_properties["beta1h"]) * 180/math.pi), 1)
            self.beta_1_s.Value = round((float(blade_properties['beta1s']) * 180/math.pi), 1)
            self.beta_2_h.Value = round((float(blade_properties['beta2h']) * 180/math.pi), 1)
            self.beta_2_s.Value = round((float(blade_properties['beta2s']) * 180/math.pi), 1)

        else:
            self.number_blades.Value = blade_properties['Number of blades']
            self.le_thickness_hub.Value = blade_properties['BladeThicknessLeHub']
            self.le_thickness_shroud.Value = blade_properties['BladeThicknessLeShroud']
            self.te_thickness_hub.Value = blade_properties['BladeThicknessTeHub']
            self.te_thickness_shroud.Value = blade_properties['BladeThicknessTeShroud']

    def writeThickness(self, node, indexValue, paramValue):
        for child in node:
            if child.attrib["Index"] == "{}".format(indexValue):
                child.text = str(paramValue)

    def writeBladeAngles(self, node, indexValue, paramValue):
        for child in node:
            if child.attrib["Index"] == "{}".format(indexValue):
                child.text = str(round(((float(paramValue) / 180) * math.pi), 7))

    def writeInterpolatedBladeAngles(self, task, node, betah, betas):
        '''
        Writes interpolated values of angles to the Beta1 and Beta2 nodes. By default linear interpolation works
        :param task:
        :param node:
        :param betah:
        :param betas:
        :return:
        '''
        blade_properties = self.join_blade_properties(task)
        spans = int(self.getNumSpans(task))

        for i in range(spans):
            # if beta angles from hub and shroud are equal, writes all values = value of angles from hub side
            if betah == betas:
                node[i].text = str(round(((float(betah) / 180) * math.pi), 7))
            else:
                # make linear interpolation from beta hub angle to shroud angle
                node[i].text = str(
                    float(node[0].text) - i * (float(node[0].text) - float(node[spans - 1].text)) / (spans - 1))


