import xml.etree.ElementTree as ET
import os


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
        tree = Impeller.get_xml_tree(self, task)
        root = tree.getroot()

        # get main dimensions element
        main_dimensions_element = root[0][0][0][0][0][0]

        return main_dimensions_element

    def get_main_dimensions(self, task):
        '''
        Get main dimensions of impeller from MainDimensionsElement element and push it to dict
        :param task:
        :return: dict, e.g. main_dimensions = {'Tip clearance': 0.0, 'Hub diameter inlet dH1': 0.22}
        '''
        main_dimensions = {}
        main_dimensions_element = MainDimensions(task).get_main_dimensions_element(task)
        for child in main_dimensions_element:
            main_dimensions[child.attrib['Desc']] = child.text

        return main_dimensions

    def insert_main_dimensions(self, task):
        '''
        Insert main dimensions of impeller to the table of properties of cell#1
        :param task:
        :return:
        '''
        main_dimensions = self.get_main_dimensions(task)

        tip_clearance = self.group.Properties["TipClearance"]
        tip_clearance.Value = main_dimensions['Tip clearance']

        if 'Hub diameter dH' in main_dimensions:

            # properties for radial and mixed pumps
            self.hub_diameter.Value = main_dimensions['Hub diameter dH']
            self.suction_diameter.Value = main_dimensions['Suction diameter dS']
            self.impeller_diameter.Value = main_dimensions['Impeller diameter d2']
            self.impeller_outlet_width.Value = main_dimensions['Impeller outlet width b2']
        else:
            # properties for axial pump
            self.hub_diameter_inlet.Value = main_dimensions['Hub diameter inlet dH1']
            self.tip_diameter_inlet.Value = main_dimensions['Tip diameter inlet dS1']
            self.hub_diameter_outlet.Value = main_dimensions['Hub diameter outlet dH2']
            self.tip_diameter_outlet.Value = main_dimensions['Tip diameter outlet dS2']