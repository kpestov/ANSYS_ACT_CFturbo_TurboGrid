import math

import clr
import os
import xml.etree.ElementTree as ET

clr.AddReference("Ans.UI.Toolkit")
clr.AddReference("Ans.UI.Toolkit.Base")
clr.AddReference('Ansys.ACT.Interfaces')
from Ansys.ACT.Interfaces.Workflow import *
from Ansys.UI.Toolkit import *
from shutil import copyfile
from ntpath import basename
from os import remove, path, environ
from System.IO import Path
from System.Diagnostics import Process

clr.AddReference("Ans.ProjectSchematic")
import Ansys.ProjectSchematic


def resetParameters(task, propGroup):
    '''
    Called when try to replace .cft-batch file and resets all parameters to the 0.0 from right table of properties
    Improvements: add ability to work with rest parameters in the table, not only for Main Dimensions
    :param task:
    :return:
    '''
    Group = task.Properties["{}".format(propGroup)].Properties
    for i in range(len(Group)):
        Group[i].Value = 0.0


def status(task):
    '''
    Changes status of the cell if there is no .cft-file in the working directory
    :param task:
    :return: status of the cell = Unfulfilled
    '''
    dir_list = os.listdir(task.ActiveDirectory)

    # write a more relible condition in the future
    if len(dir_list) < 2:
        # status = [Ansys.ACT.Interfaces.Common.State.Unfulfilled, 'cannot copy .cft file']
        status = Ansys.ProjectSchematic.Queries.ComponentState(Ansys.ProjectSchematic.State.Unfulfilled,
                                                               "cannot copy .cft file")
        return status
    else:
        return None


def InFileValid(task, property):
    '''
    Check whether the file path exists in the cell property 'Input File Name'
    :param task:
    :param property:
    :return: bool
    '''
    if path.exists(property.Value):
        return True
    return False


def get_cft_batch_path(task):
    '''
    Extract .cft-batch file path from property 'Input File Name'
    :param task:
    :return: file path ..\*.cft-batch
    '''
    group = task.Properties["CFTurbo batch file"]
    cft_batch_file_path = group.Properties["InputFileName"]

    return cft_batch_file_path


def copy_cft_file(task):
    '''
    Copy .cft file from user_files dir to .\ACT dir of the project. If there is no .cft file if use_files dir raises
    :except IOError
    :param task:
    :return: working directory of the task group
    '''
    container = task.InternalObject

    # obtain user_files directory
    start_dir = GetUserFilesDirectory()

    filePath = get_cft_batch_path(task)

    # get_xml_root
    tree = ET.parse(filePath.Value)
    root = tree.getroot()

    # get_design_impeller_node
    cfturbo_batch_project_node = root.find('CFturboBatchProject')
    input_file = cfturbo_batch_project_node.attrib['InputFile']

    # obtain .cft file name with extension
    file_name = path.basename(input_file)
    source_dir = Path.Combine(start_dir, file_name)
    target_dir = Path.Combine(task.ActiveDirectory, file_name)
    try:
        copyfile(source_dir, target_dir)
    except IOError:
        pass
        MessageBox.Show(Window.MainWindow,
                        'Failed to copy .cft file to the working directory! Please place the .cft file '
                        'in the user_files directory', 'Warning', MessageBoxType.Error, MessageBoxButtons.OK)

        # remain yellow color in Input File Name field
        group = task.Properties["CFTurbo batch file"]
        file_path = group.Properties["InputFileName"]
        file_path.Value = "No file chosen!"
        return None

    # changes .cft file dir in .cft-batch file when copy .cft-batch to ActiveDirectory
    cfturbo_batch_project_node.attrib['InputFile'] = target_dir

    # find first and second BatchAction nodes
    batch_action_node = root[0][1]
    batch_action_2nd_node = root[0][2]

    # write values for selected attribs
    batch_action_node.attrib['ExportInterface'] = "TurboGrid"
    batch_action_node.attrib['WorkingDir'] = ""
    batch_action_2nd_node.attrib['OutputFile'] = ""

    # check if ExportComponents element exist in .cft-batch file in parent element BatchAction
    # (element 'BatchAction' = root[0][1])
    if list(root[0][1]) == []:
        pass
    else:
        export_components_node = root[0][1].find('ExportComponents')
        root[0][1].remove(export_components_node)

    tree.write(target_dir + '-batch')

    file_ref = RegisterFile(FilePath=target_dir)
    AssociateFileWithContainer(file_ref, container)

    return target_dir


def edit(task):
    '''
    Called when click RMB on the cell 'CFTurbo Design'. User selects file .cft-batch in opened window and if attempt is
    successful copies .cft-batch file from user_files dir to .\ACT dir of the project. If there is an error raises
    :except IOError
    :param task:
    :return:
    '''
    fileRef = None

    # obtain data container reference
    container = task.InternalObject

    # prepare arguments and open file selection dialog starting in user_files
    Filters = "CFTurbo batch (*.cft-batch)|*.cft-batch|All files (*.*)|*.*"
    FilterIndex = 0
    startDir = GetUserFilesDirectory()
    diagResult = FileDialog.ShowOpenDialog(Window.MainWindow, startDir, Filters, FilterIndex, "", "")

    if diagResult[0] == DialogResult.OK:
        group = task.Properties["CFTurbo batch file"]
        filePath = get_cft_batch_path(task)

        # check if choosing file for the first time by file path property value
        if filePath.Value == "No file chosen!":
            sourcePath = path.abspath(diagResult[1])
            dest = Path.Combine(task.ActiveDirectory, path.basename(diagResult[1]))
            source = diagResult[1]

            try:
                copyfile(source, dest)
            except IOError:
                MessageBox.Show(Window.MainWindow, "Failed to copy file to the working directory!",
                                'Warning', MessageBoxType.Error, MessageBoxButtons.OK)
                return

            filePath.Value = dest
            fileRef = RegisterFile(FilePath=filePath.Value)
            AssociateFileWithContainer(fileRef, container)

        # if file already chosen
        else:
            messg = "Would you like to replace existing file?"

            overwriteDialogResult = MessageBox.Show(Window.MainWindow, messg, "", MessageBoxType.Question,
                                                    MessageBoxButtons.YesNo)

            if overwriteDialogResult == DialogResult.Yes:

                # reset parameters in propertygroups
                propGroupList = ['MainDimensions', 'BladeProperties', 'BladeMeanLines', 'Meridian']
                for i in propGroupList:
                    resetParameters(task, i)

                dest = Path.Combine(task.ActiveDirectory, path.basename(diagResult[1]))
                source = diagResult[1]
                remove(filePath.Value)
                try:
                    copyfile(source, dest)
                except IOError:
                    MessageBox.Show(Window.MainWindow, "Failed to copy file to the working directory!",
                                    'Warning', MessageBoxType.Error, MessageBoxButtons.OK)
                    return

                filePath.Value = dest
                fileRef = RegisterFile(FilePath=filePath.Value)
                AssociateFileWithContainer(fileRef, container)

    # function which copies .cft file to active directory
    copy_cft_file(task)

    # function which takes values from a file .cft-batch
    insert_dimensions(task)


def HubDiameterVisible(task, property):
    HubDiameter = MainDimensions(task).mainDimExist(task, 'dN', 'Desc', 'Hub diameter dH')
    if HubDiameter is None:
        return False
    return True

def SuctionDiameterVisible(task, property):
    SuctionDiameter = MainDimensions(task).mainDimExist(task, 'dS', 'Desc', 'Suction diameter dS')
    if SuctionDiameter is None:
        return False
    return True

def ImpellerDiameterVisible(task, property):
    ImpellerDiameter = MainDimensions(task).mainDimExist(task, 'd2', 'Desc', 'Impeller diameter d2')
    if ImpellerDiameter is None:
        return False
    return True

def ImpellerOutWidthVisible(task, property):
    ImpellerOutWidth = MainDimensions(task).mainDimExist(task, 'b2', 'Desc', 'Impeller outlet width b2')
    if ImpellerOutWidth is None:
        return False
    return True

def HubDiameterInletVisible(task, property):
    HubDiameterInlet = MainDimensions(task).mainDimExist(task, 'dN', 'Desc', 'Hub diameter inlet dH1')
    if HubDiameterInlet is None:
        return False
    return True

def TipDiameterInletVisible(task, property):
    TipDiameterInlet = MainDimensions(task).mainDimExist(task, 'dS', 'Desc', 'Tip diameter inlet dS1')
    if TipDiameterInlet is None:
        return False
    return True

def HubDiameterOutVisible(task, property):
    HubDiameterOut = MainDimensions(task).mainDimExist(task, 'dH2', 'Desc', 'Hub diameter outlet dH2')
    if HubDiameterOut is None:
        return False
    return True

def TipDiameterOutVisible(task, property):
    TipDiameterOut = MainDimensions(task).mainDimExist(task, 'dS2', 'Desc', 'Tip diameter outlet dS2')
    if TipDiameterOut is None:
        return False
    return True

def beta1Visible(task, property):
    beta1 = BladeProperties(task).betaExist(task, 'Beta1')
    if beta1 is None:
        return False
    return True

def beta2Visible(task, property):
    beta1 = BladeProperties(task).betaExist(task, 'Beta2')
    if beta1 is None:
        return False
    return True

def LePosHubVisible(task, property):
    LePosHub = Meridian(task).positionExist(task, 'LePosHub')
    if LePosHub is None:
        return False
    return True

def TePosHubVisible(task, property):
    TePosHub = Meridian(task).positionExist(task, 'TePosHub')
    if TePosHub is None:
        return False
    return True


def LePosHubSplitterVisible(task, property):
    LePosHubSplitter = Meridian(task).positionExist(task, 'LePosHubSplitter')
    if LePosHubSplitter is None:
        return False
    return True


def insert_dimensions(task):
    '''
    Insert main dimensions of impeller to the table of properties of cell#1
    :param task:
    :return:
    '''
    try:
        # if there is no .cft-file in user_files directory raise exception
        copy_cft_file(task)
        MainDimensions(task).insert_main_dimensions(task)
        BladeProperties(task).insert_blade_properties(task)
        SkeletonLines(task).insert_skeletonLines_properties(task)
        Meridian(task).insert_meridian_properties(task)
    except IOError:
        pass


def update_main_dimensions(task):
    '''
    Updates parameters of main dimensions property group when user changes values in table and writes new .cft-batch file
    :param task:
    Improvements: maybe it is better add separated functions for updating main dimensions, blade profiles, etc and write
    classes, e.g. class MainDimensions, class BladeProfiles.
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
        if child.attrib["Desc"] == "Tip clearance":
            child.text = str(mainDim.tip_clearance.Value)

        # properties for axial pump
        if child.attrib["Desc"] == "Hub diameter inlet dH1":
            child.text = str(mainDim.hub_diameter_inlet.Value)
        if child.attrib["Desc"] == "Tip diameter inlet dS1":
            child.text = str(mainDim.tip_diameter_inlet.Value)
        if child.attrib["Desc"] == "Hub diameter outlet dH2":
            child.text = str(mainDim.hub_diameter_outlet.Value)
        if child.attrib["Desc"] == "Tip diameter outlet dS2":
            child.text = str(mainDim.tip_diameter_outlet.Value)

        # properties for radial and mixed pumps
        if child.attrib["Desc"] == "Hub diameter dH":
            child.text = str(mainDim.hub_diameter.Value)
        if child.attrib["Desc"] == "Suction diameter dS":
            child.text = str(mainDim.suction_diameter.Value)
        if child.attrib["Desc"] == "Impeller diameter d2":
            child.text = str(mainDim.impeller_diameter.Value)
        if child.attrib["Desc"] == "Impeller outlet width b2":
            child.text = str(mainDim.impeller_outlet_width.Value)

    target_dir = copy_cft_file(task)
    tree.write(target_dir + '-batch')


def update_blade_properties(task):

    #BladeProperties  and Impeller classes from xml_parser.py module
    bladeProp = BladeProperties(task)
    impeller = Impeller(task)

    tree = impeller.get_xml_tree(task)
    root = tree.getroot()

    # get blade properties element
    blade_properties_element = root[0][0][0][0][2]
    le_thickness_node = blade_properties_element[3][0][0]
    te_thickness_node = blade_properties_element[3][0][1]

    spans = bladeProp.getNumSpans(task)
    check_node = blade_properties_element[3][0]

    # the code bellow writes new values of parameter when update cell#2
    blade_properties_element.find('nBl').text = str(bladeProp.number_blades.Value)

    bladeProp.writeThickness(le_thickness_node, '0', bladeProp.le_thickness_hub.Value)
    bladeProp.writeThickness(le_thickness_node, '1', bladeProp.le_thickness_shroud.Value)
    bladeProp.writeThickness(te_thickness_node, '0', bladeProp.te_thickness_hub.Value)
    bladeProp.writeThickness(te_thickness_node, '1', bladeProp.te_thickness_shroud.Value)

    beta1 = check_node.find('Beta1')
    if beta1 is None:
        pass
    else:
        beta1_node = blade_properties_element[3][0][2]
        bladeProp.writeBladeAngles(beta1_node, '0', bladeProp.beta_1_h.Value)
        bladeProp.writeBladeAngles(beta1_node, (int(spans) - 1), bladeProp.beta_1_s.Value)
        bladeProp.writeInterpolatedBladeAngles(task, beta1_node, bladeProp.beta_1_h.Value, bladeProp.beta_1_s.Value)

    beta2 = check_node.find('Beta2')
    if beta2 is None:
        pass
    else:
        beta2_node = blade_properties_element[3][0][3]
        bladeProp.writeBladeAngles(beta2_node, '0', bladeProp.beta_2_h.Value)
        bladeProp.writeBladeAngles(beta2_node, (int(spans) - 1), bladeProp.beta_2_s.Value)
        bladeProp.writeInterpolatedBladeAngles(task, beta2_node, bladeProp.beta_2_h.Value, bladeProp.beta_2_s.Value)

    target_dir = copy_cft_file(task)
    tree.write(target_dir + '-batch')


def update_skeletonLines(task):

    skeletonLines = SkeletonLines(task)
    impeller = Impeller(task)

    tree = impeller.get_xml_tree(task)
    root = tree.getroot()
    skeletonlines_element = root[0][0][0][0][3]
    num_of_bezier_curves = len(skeletonlines_element[0][0])

    skeletonLines.writes_phi_angles(task, 0, skeletonLines.phiLEhub.Value, skeletonLines.phiTEhub.Value)
    skeletonLines.writes_phi_angles(task, num_of_bezier_curves - 1, skeletonLines.phiLEshroud.Value, skeletonLines.phiTEshroud.Value)

def update_meridian(task):
    meridian = Meridian(task)
    meridian_properties = meridian.join_positions(task)
    bezierCurvesList = meridian.get_bezierCurvesList(task)

    if 'LePosHub' in meridian_properties:
        meridian.writes_positions(task, 0, meridian.LePosHub.Value, 'u-Hub')
    if 'LePosShroud' in meridian_properties:
        meridian.writes_positions(task, 0, meridian.LePosShroud.Value, 'u-Shroud')
    if 'TePosHub' in meridian_properties:
        meridian.writes_positions(task, 1, meridian.TePosHub.Value, 'u-Hub')
    if 'TePosShroud' in meridian_properties:
        meridian.writes_positions(task, 1, meridian.TePosShroud.Value, 'u-Shroud')
    if 'LePosHubSplitter' in meridian_properties:
        meridian.writes_positions(task, len(bezierCurvesList) - 1, meridian.LePosHubSplitter.Value, 'u-Hub')
    if 'LePosShroudSplitter' in meridian_properties:
        meridian.writes_positions(task, len(bezierCurvesList) - 1, meridian.LePosShroudSplitter.Value, 'u-Shroud')


def update(task):
    update_main_dimensions(task)
    update_meridian(task)
    update_blade_properties(task)
    update_skeletonLines(task)
    # update_blade_profiles(task)


def launch_cfturbo(task):
    cft_env = 'CFturbo10_root'
    cft_path = environ.get(cft_env)
    launch_cft_path = os.path.join(cft_path, 'cfturbo.exe')
    cft_batch_file = Impeller(task).get_cft_batch_path(task)

    # this is for files with spaces in the name
    quoted_cft_batch_file = '"{}"'.format(cft_batch_file)

    start_cfturbo = Process.Start(launch_cft_path, '-batch' + ' ' + quoted_cft_batch_file)
    start_cfturbo.WaitForExit()
    exit_code = start_cfturbo.ExitCode

    if exit_code != 1:
        raise Exception('Failed to launch CFTurbo!')


def obtain_cft_file_name(task):
    cft_file_path = Impeller(task).get_cft_batch_path(task)
    cft_file_name = basename(cft_file_path).split('.cft')[0]

    return cft_file_name


def obtain_tse_file(task):
    cft_file_name = obtain_cft_file_name(task)
    file_name = cft_file_name + '.tse'
    tse_file = os.path.join(task.ActiveDirectory, file_name)

    return tse_file


def extract_attribs(task, start, end):
    '''
    Extracts parameters from .tse file. When it finds certain lines, e.g. 'MACHINE DATA:', and 'END' the parameters are
    added to the dictionary 'attribs'.
    :param task:
    :param start:
    :param end:
    :return: dict, attribs = {'Bladeset Count': 7, 'Rotation Axis Type': 'Principal Axis', ...}
    '''
    tse_file = obtain_tse_file(task)
    attribs = {}

    with open(tse_file) as f:
        for line in f:
            if line.strip() == start:
                break

        for line in f:
            if line.strip() == end:
                break

            data = line.strip().split(' = ')
            attribs[data[0]] = data[1]

    return attribs


def extract_machine_data_attribs(task):
    machine_data_attribs = extract_attribs(task, 'MACHINE DATA:', 'END')

    return machine_data_attribs


def extract_hub_attribs(task):
    hub_attribs = extract_attribs(task, 'HUB:', 'END')

    return hub_attribs


def extract_shroud_attribs(task):
    shroud_attribs = extract_attribs(task, 'SHROUD:', 'END')

    return shroud_attribs


def extract_main_blade_attribs(task):
    main_blade_attribs = extract_attribs(task, 'BLADE:Main blade', 'END')

    return main_blade_attribs


def extract_splitter_blade_attribs(task):
    splitter_blade_attribs = extract_attribs(task, 'BLADE:Splitter blade', 'END')

    return splitter_blade_attribs


def make_s4(task):
    '''
    Makes string 'Number of Blades Per Set:' for .inf file. The value is written as number of blades per passage.
    If there is splitter blade in machine, add 'Blade Number' value of BLADE:Splitter blade + 1, else assign
    'Number of Blades Per Set: 'Blade Number' value of BLADE:Main blade
    :param task:
    :return: 'Number of Blades Per Set: 0'
    '''
    splitter_blade_attribs = extract_splitter_blade_attribs(task)
    main_blade_attribs = extract_main_blade_attribs(task)

    if splitter_blade_attribs == {}:
        blades_per_set = int(main_blade_attribs['Blade Number'])
        s4 = 'Number of Blades Per Set: {}'.format(blades_per_set + 1)
    else:
        blades_per_set = int(splitter_blade_attribs['Blade Number'])
        s4 = 'Number of Blades Per Set: {}'.format(blades_per_set + 1)

    return s4


def make_s8(task):
    '''
    Makes string 'Blade 0 LE:' for .inf file.
    :param task:
    :return: 'Blade 0 LE:  EllipseEnd' or 'Blade 0 LE:  CutOffEnd'
    '''

    main_blade_attribs = extract_main_blade_attribs(task)

    blade_0_le_type = main_blade_attribs['Leading Edge Type']
    if blade_0_le_type == 'Single':
        blade_0_le_type = 'EllipseEnd'
    else:
        blade_0_le_type = 'CutOffEnd'
    s8 = 'Blade 0 LE: {}'.format(blade_0_le_type)

    return s8


def make_s9(task):
    main_blade_attribs = extract_main_blade_attribs(task)

    blade_0_te_type = main_blade_attribs['Trailing Edge Type']
    if blade_0_te_type == 'Single':
        blade_0_te_type = 'EllipseEnd'
    else:
        blade_0_te_type = 'CutOffEnd'
    s9 = 'Blade 0 TE: {}'.format(blade_0_te_type)

    return s9


def make_s10(task):
    splitter_blade_attribs = extract_splitter_blade_attribs(task)

    if splitter_blade_attribs == {}:
        return
    else:
        blade_1_le_type = splitter_blade_attribs['Leading Edge Type']
        if blade_1_le_type == 'Single':
            blade_1_le_type = 'EllipseEnd'
        else:
            blade_1_le_type = 'CutOffEnd'
        s10 = 'Blade 1 LE: {}'.format(blade_1_le_type)

    return s10


def make_s11(task):
    splitter_blade_attribs = extract_splitter_blade_attribs(task)

    if splitter_blade_attribs == {}:
        return
    else:
        blade_1_te_type = splitter_blade_attribs['Trailing Edge Type']
        if blade_1_te_type == 'Single':
            blade_1_te_type = 'EllipseEnd'
        else:
            blade_1_te_type = 'CutOffEnd'
        s11 = 'Blade 1 TE: {}'.format(blade_1_te_type)

    return s11


def create_inf_file(task):
    '''
    Writes .inf file for TurboGrid
    :param task:
    :return: .inf file
    '''
    cft_file_name = obtain_cft_file_name(task)
    inf_file = cft_file_name + '.inf'
    active_dir = os.path.join(task.ActiveDirectory, inf_file)

    machine_data_attribs = extract_machine_data_attribs(task)
    hub_attribs = extract_hub_attribs(task)
    shroud_attribs = extract_shroud_attribs(task)
    main_blade_attribs = extract_main_blade_attribs(task)

    s1 = '!======  CFTurbo Export  ========'
    s2 = 'Axis of Rotation: {}'.format(machine_data_attribs['Principal Axis'])
    s3 = 'Number of Blade Sets: {}'.format(machine_data_attribs['Bladeset Count'])
    s4 = make_s4(task)
    s5 = 'Blade Loft Direction: Spanwise'
    geometry_units = hub_attribs['Input Length Units']
    s6 = 'Geometry Units: {}'.format(geometry_units.upper())
    s7 = 'Coordinate System Orientation: Righthanded'
    s8 = make_s8(task)
    s9 = make_s9(task)
    s10 = make_s10(task)
    s11 = make_s11(task)
    s12 = 'Hub Data File: {}'.format(path.basename(hub_attribs['Input Filename']))
    s13 = 'Shroud Data File: {}'.format(path.basename(shroud_attribs['Input Filename']))
    s14 = 'Profile Data File: {}'.format(path.basename(main_blade_attribs['Input Filename']))

    with open(active_dir, 'w') as f:
        f.write(s1 + '\n')
        f.write(s2 + '\n')
        f.write(s3 + '\n')
        f.write(s4 + '\n')
        f.write(s5 + '\n')
        f.write(s6 + '\n')
        f.write(s7 + '\n')
        f.write(s8 + '\n')
        f.write(s9 + '\n')

        # check if there is splitter blade in impeller or not.
        if s10 is None:
            pass
        else:
            f.write(s10 + '\n')
            f.write(s11 + '\n')

        f.write(s12 + '\n')
        f.write(s13 + '\n')
        f.write(s14 + '\n')


def cfturbo_start(task):
    '''
    Main function for starting CFturbo and writing .inf file.
    :param task:
    :return:
    '''
    launch_cfturbo(task)

    container = task.InternalObject
    fileRef = None

    cft_file_name = obtain_cft_file_name(task)
    inf_file = cft_file_name + '.inf'
    inf_file_dir = os.path.join(task.ActiveDirectory, inf_file)

    # function which extracts information from .tse file and create .inf file
    create_inf_file(task)

    # .inf file registration
    TurboGridInputFiles = inf_file_dir

    # check if the .inf file is associated with WB project
    isRegistered = IsFileRegistered(FilePath=TurboGridInputFiles)
    if isRegistered == True:
        fileRef = GetRegisteredFile(FilePath=TurboGridInputFiles)
    else:
        fileRef = RegisterFile(FilePath=TurboGridInputFiles)
        AssociateFileWithContainer(fileRef, container)

    outputRefs = container.GetOutputData()
    outputSet = outputRefs["TurboGeometry"]
    myData = outputSet[0]
    myData.INFFilename = fileRef

# def dummy_copying(task):
#
# # this is dummy function which copies .curve and .tse files from act directory to task.ActiveDirectory
#
#     container = task.InternalObject
#     fileRef = None
#
#     cft_file_name = obtain_cft_file_name(task)
#     inf_file = cft_file_name + '.inf'
#     inf_file_dir = os.path.join(task.ActiveDirectory, inf_file)
#
#     extensionDir = ExtAPI.ExtensionManager.CurrentExtension.InstallDir
#
#     # obtain source and target directories for copy .curve, .tse files (this is dummy code)
#     for TurboGridFiles in os.listdir(extensionDir):
#         if TurboGridFiles.endswith(".curve") or TurboGridFiles.endswith(".tse"):
#             source_files = os.path.join(extensionDir, TurboGridFiles)
#             target_files = os.path.join(task.ActiveDirectory, TurboGridFiles)
#
#             # copy .curve, .tse files from act directory to task.ActiveDirectory (this is dummy code)
#             copy(source_files, target_files)
#
#     # here will be function which extract information from .tse file and create .inf file
#     create_inf_file(task)
#
#     # here wiil be name of .inf file for registration
#     TurboGridInputFiles = inf_file_dir
#
#     # check if the .inf file is associated with WB project
#     isRegistered = IsFileRegistered(FilePath=TurboGridInputFiles)
#     if isRegistered == True:
#         fileRef = GetRegisteredFile(FilePath=TurboGridInputFiles)
#     else:
#         fileRef = RegisterFile(FilePath=TurboGridInputFiles)
#         AssociateFileWithContainer(fileRef, container)
#
#     outputRefs = container.GetOutputData()
#     outputSet = outputRefs["TurboGeometry"]
#     myData = outputSet[0]
#     myData.INFFilename = fileRef








