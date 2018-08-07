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


def resetParameters(task):
    '''
    Called when try to replace .cft-batch file and resets all parameters to the 0.0 from right table of properties
    Improvements: add ability to work with rest parameters in the table, not only for Main Dimensions
    :param task:
    :return:
    '''
    MainDimensionsGroup = task.Properties["MainDimensions"].Properties
    for i in range(len(MainDimensionsGroup)):
        MainDimensionsGroup[i].Value = 0.0


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
        MessageBox.Show(Window.MainWindow, 'Failed to copy .cft file to the working directory! Please place the .cft file '
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

                resetParameters(task)

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
    insert_main_dimensions(task)


def HubDiameterInletVisible(task, property):
    '''
    Hide radial pump parameters if Hub diameter inlet != 0
    :param task:
    :param property:
    :return: bool
    '''
    group=task.Properties["MainDimensions"]
    HubDiameter=group.Properties["HubDiameter"]
    if HubDiameter.Value == 0.0:
        return True
    return False


def HubDiameterVisible(task, property):
    '''
    Hide axial pump parameters if Hub diameter != 0
    :param task:
    :param property:
    :return:
    '''
    group=task.Properties["MainDimensions"]
    HubDiameterInlet=group.Properties["HubDiameterInlet"]
    if HubDiameterInlet.Value == 0.0:
        return True
    return False


def get_cft_path(task):
    '''
    Extract .cft-batch file path from active directory .\ACT
    :param task:
    :return: path of .cft-batch file
    '''
    for cft_file in os.listdir(task.ActiveDirectory):
        if cft_file.endswith(".cft-batch"):
            cft_file_path = os.path.join(task.ActiveDirectory, cft_file)

            return cft_file_path


def get_xml_tree(task):
    '''
    Parses .cft-batch file for parameters extraction
    :param task:
    :return: parsed tree object of .cft-batch file
    '''
    cft_file_path = get_cft_path(task)
    tree = ET.parse(cft_file_path)

    return tree


def get_main_dimensions_element(task):
    '''
    Gets access to MainDimensionsElement element
    :param task:
    :return: MainDimensionsElement node of .cft-batch file
    '''
    tree = get_xml_tree(task)
    root = tree.getroot()

    # get main dimensions element
    main_dimensions_element = root[0][0][0][0][0][0]

    return main_dimensions_element


def get_main_dimensions(task):
    '''
    Get main dimensions of impeller from MainDimensionsElement element and push it to dict
    :param task:
    :return: dict, e.g. main_dimensions = {'Tip clearance': 0.0, 'Hub diameter inlet dH1': 0.22}
    '''
    main_dimensions_element = get_main_dimensions_element(task)
    main_dimensions = {}
    for child in main_dimensions_element:
        main_dimensions[child.attrib['Desc']] = child.text

    return main_dimensions


def insert_main_dimensions(task):
    '''
    Insert main dimensions of impeller to the table of properties of cell#1
    :param task:
    :return:
    '''
    try:
        copy_cft_file(task)
        main_dimensions = get_main_dimensions(task)
        group = task.Properties["MainDimensions"]

        tip_clearance = group.Properties["TipClearance"]
        tip_clearance.Value = main_dimensions['Tip clearance']

        # check if 'Hub diameter dH' key in dictionary for showing main dimensions values in property table
        if 'Hub diameter dH' in main_dimensions:

            # properties for radial and mixed pumps
            hub_diameter = group.Properties["HubDiameter"]
            suction_diameter = group.Properties["SuctionDiameter"]
            impeller_diameter = group.Properties["ImpellerDiameter"]
            impeller_outlet_width = group.Properties["ImpellerOutletWidth"]

            hub_diameter.Value = main_dimensions['Hub diameter dH']
            suction_diameter.Value = main_dimensions['Suction diameter dS']
            impeller_diameter.Value = main_dimensions['Impeller diameter d2']
            impeller_outlet_width.Value = main_dimensions['Impeller outlet width b2']

        else:
            # properties for axial pump
            hub_diameter_inlet = group.Properties["HubDiameterInlet"]
            tip_diameter_inlet = group.Properties["TipDiameterInlet"]
            hub_diameter_outlet = group.Properties["HubDiameterOutlet"]
            tip_diameter_outlet = group.Properties["TipDiameterOutlet"]

            hub_diameter_inlet.Value = main_dimensions['Hub diameter inlet dH1']
            tip_diameter_inlet.Value = main_dimensions['Tip diameter inlet dS1']
            hub_diameter_outlet.Value = main_dimensions['Hub diameter outlet dH2']
            tip_diameter_outlet.Value = main_dimensions['Tip diameter outlet dS2']
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
    group = task.Properties["MainDimensions"]
    tip_clearance = group.Properties["TipClearance"]

    # In the future try to write separate function to not copy code below
    # properties for radial and mixed pumps
    hub_diameter = group.Properties["HubDiameter"]
    suction_diameter = group.Properties["SuctionDiameter"]
    impeller_diameter = group.Properties["ImpellerDiameter"]
    impeller_outlet_width = group.Properties["ImpellerOutletWidth"]

    # properties for axial pump
    hub_diameter_inlet = group.Properties["HubDiameterInlet"]
    tip_diameter_inlet = group.Properties["TipDiameterInlet"]
    hub_diameter_outlet = group.Properties["HubDiameterOutlet"]
    tip_diameter_outlet = group.Properties["TipDiameterOutlet"]

    tree = get_xml_tree(task)
    root = tree.getroot()

    # get main dimensions element
    main_dimensions_element = root[0][0][0][0][0][0]

    # get CFturboDesign_(AxialI/Radial)mpeller element
    impeller_design = root[0][0][0][0]

    # the code bellow writes new values of parameter when update cell#2
    main_dimensions_element.find('xTip').text = str(tip_clearance.Value)

    if impeller_design.attrib['Name'] == "Radial_Impeller":
        main_dimensions_element.find('dN').text = str(hub_diameter.Value)
        main_dimensions_element.find('dS').text = str(suction_diameter.Value)
        main_dimensions_element.find('d2').text = str(impeller_diameter.Value)
        main_dimensions_element.find('b2').text = str(impeller_outlet_width.Value)

    elif impeller_design.attrib['Name'] == "Axial Impeller":
        main_dimensions_element.find('dN').text = str(hub_diameter_inlet.Value)
        main_dimensions_element.find('dS').text = str(tip_diameter_inlet.Value)
        main_dimensions_element.find('dH2').text = str(hub_diameter_outlet.Value)
        main_dimensions_element.find('dS2').text = str(tip_diameter_outlet.Value)

    target_dir = copy_cft_file(task)
    tree.write(target_dir + '-batch')


def update(task):

    update_main_dimensions(task)
    # update_meridian(task)
    # update_blade_properties(task)
    # update_skeletonLines(task)
    # update_blade_profiles(task)


def launch_cfturbo(task):
    cft_env = 'CFturbo10_root'
    cft_path = environ.get(cft_env)
    launch_cft_path = os.path.join(cft_path, 'cfturbo.exe')
    cft_batch_file = get_cft_path(task)

    # this is for files with spaces in the name
    quoted_cft_batch_file ='"{}"'.format(cft_batch_file)

    start_cfturbo = Process.Start(launch_cft_path, '-batch' + ' ' + quoted_cft_batch_file)
    start_cfturbo.WaitForExit()
    exit_code = start_cfturbo.ExitCode

    if exit_code != 1:
        raise Exception('Failed to launch CFTurbo!')


def obtain_cft_file_name(task):
    cft_file_path = get_cft_path(task)
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








