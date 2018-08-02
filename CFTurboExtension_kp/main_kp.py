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

def status(task):
    dir_list = os.listdir(task.ActiveDirectory)

    # write a more relible condition in the future
    if len(dir_list) < 2:
        return [Ansys.ACT.Interfaces.Common.State.Unfulfilled, 'cannot copy .cft file']
    else:
        return None


def InFileValid(task, property):
    if path.exists(property.Value):
        return True
    return False


def get_cft_batch_path(task):
    group = task.Properties["CFTurbo batch file"]
    cft_batch_file_path = group.Properties["InputFileName"]

    return cft_batch_file_path


def copy_cft_file(task):
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
    except:
        # MessageBox.Show('hui', 'hui_2', MessageBoxButtons.OK, MessageBoxIcon.Asterisk)
        MessageBox.Show(Window.MainWindow, 'Failed to copy .cft file to the working directory! Please place the .cft file '
                                         'in the user_files directory', 'Warning', MessageBoxType.Error, MessageBoxButtons.OK)

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
            except:
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
                dest = Path.Combine(task.ActiveDirectory, path.basename(diagResult[1]))
                source = diagResult[1]
                remove(filePath.Value)
                try:
                    copyfile(source, dest)
                except:
                    MessageBox.Show(Window.MainWindow, "Failed to copy file to the working directory!",
                                                     'Warning', MessageBoxType.Error, MessageBoxButtons.OK)
                    return
                filePath.Value = dest
                fileRef = RegisterFile(FilePath=filePath.Value)
                AssociateFileWithContainer(fileRef, container)

    # function which copies .cft file to active directory
    copy_cft_file(task)

    # get main dimension xml node from .cft-batch file
    main_dimensions_sub_node = get_main_dim_node(task)
    main_dimensions = {}

    # in future for dict keys use attribute names instead tags since they are unique and the tags can intersect
    for child in main_dimensions_sub_node:
        main_dimensions[child.tag] = child.text

    # function which takes values from a file .cft-batch
    get_main_dimensions(task, main_dimensions)


def get_cft_path(task):
    for cft_file in os.listdir(task.ActiveDirectory):
        if cft_file.endswith(".cft-batch"):
            cft_file_path = os.path.join(task.ActiveDirectory, cft_file)

            return cft_file_path


def get_main_dim_node(task):

    cft_file_path = get_cft_path(task)

    # get_xml_root
    tree = ET.parse(cft_file_path)
    root = tree.getroot()

    # get_design_impeller_node
    cfturbo_batch_project_node = root.find('CFturboBatchProject')
    updates_node = cfturbo_batch_project_node.find('Updates')
    cfturbo_project_node = updates_node.find('CFturboProject')

    # get_impeller_main_dimensions
    for impeller_design_node in cfturbo_project_node:
        main_dimensions_node = impeller_design_node.find('MainDimensions')
        main_dimensions_sub_node = main_dimensions_node.find('MainDimensionsElement')

        return main_dimensions_sub_node


def get_main_dimensions(task, main_dimensions):

    group = task.Properties["MainDimensions"]

    tip_clearance = group.Properties["TipClearance"]
    hub_diameter = group.Properties["HubDiameter"]
    suction_diameter = group.Properties["SuctionDiameter"]
    impeller_diameter = group.Properties["ImpellerDiameter"]
    impeller_outlet_width = group.Properties["ImpellerOutletWidth"]

    tip_clearance.Value = main_dimensions['xTip']
    hub_diameter.Value = main_dimensions['dN']
    suction_diameter.Value = main_dimensions['dS']
    impeller_diameter.Value = main_dimensions['d2']
    impeller_outlet_width.Value = main_dimensions['b2']


def cfturbo_project_xml_node(task):

    cft_file_path = get_cft_path(task)

    # get_xml_root
    tree = ET.parse(cft_file_path)
    root = tree.getroot()

    # get_design_impeller_node
    cfturbo_batch_project_node = root.find('CFturboBatchProject')
    updates_node = cfturbo_batch_project_node.find('Updates')
    cfturbo_project_node = updates_node.find('CFturboProject')

    return cfturbo_project_node


def get_xml_tree(task):
    cft_file_path = get_cft_path(task)
    tree = ET.parse(cft_file_path)

    return tree


def update(task):

    group = task.Properties["MainDimensions"]
    tip_clearance = group.Properties["TipClearance"]
    hub_diameter = group.Properties["HubDiameter"]
    suction_diameter = group.Properties["SuctionDiameter"]
    impeller_diameter = group.Properties["ImpellerDiameter"]
    impeller_outlet_width = group.Properties["ImpellerOutletWidth"]

    tree = get_xml_tree(task)

    # get_xml_root
    root = tree.getroot()

    # get_design_impeller_node
    cfturbo_batch_project_node = root.find('CFturboBatchProject')
    updates_node = cfturbo_batch_project_node.find('Updates')
    cfturbo_project_node = updates_node.find('CFturboProject')

    # get_impeller_main_dimensions
    for impeller_design_node in cfturbo_project_node:
        main_dimensions_node = impeller_design_node.find('MainDimensions')
        main_dimensions_sub_node = main_dimensions_node.find('MainDimensionsElement')

        # the code bellow writes new values of parameter when update cell#2
        tip_clearance_value = main_dimensions_sub_node.find('xTip')
        hub_diameter_value = main_dimensions_sub_node.find('dN')
        suction_diameter_value = main_dimensions_sub_node.find('dS')
        impeller_diameter_value = main_dimensions_sub_node.find('d2')
        impeller_outlet_width_value = main_dimensions_sub_node.find('b2')

        tip_clearance_value.text = str(tip_clearance.Value)
        hub_diameter_value.text = str(hub_diameter.Value)

        # I've commented it because axial pump have no <d2> and <b2> tags in .cft-batch file. When the program is
        # executed there is an error shown 'impeller_diameter_value var have no attrib text'

        # suction_diameter_value.text = str(suction_diameter.Value)
        # impeller_diameter_value.text = str(impeller_diameter.Value)
        # impeller_outlet_width_value.text = str(impeller_outlet_width.Value)

        target_dir = copy_cft_file(task)
        tree.write(target_dir + '-batch')


def launch_cfturbo(task):
    cft_env = 'CFturbo10_root'
    cft_path = environ.get(cft_env)
    launch_cft_path = os.path.join(cft_path, 'cfturbo.exe')
    cft_batch_file = get_cft_path(task)

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

        if s10 is None:
            pass
        else:
            f.write(s10 + '\n')
            f.write(s11 + '\n')

        f.write(s12 + '\n')
        f.write(s13 + '\n')
        f.write(s14 + '\n')


def cfturbo_start(task):

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








