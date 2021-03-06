"""This module contains main callbacks that are responsible for loading the input file, updating and resetting
parameters.

Contacts:
Kirill Pestov
kpestov91@gmail.com
https://github.com/kpestov

"""

import re
import clr
import os
import xml.etree.ElementTree as ET
from os.path import basename
from shutil import copyfile
from os import remove, path
from System.IO import Path

clr.AddReference("Ans.UI.Toolkit")
clr.AddReference("Ans.UI.Toolkit.Base")
clr.AddReference('Ansys.ACT.Interfaces')
clr.AddReference("Ans.ProjectSchematic")
from Ansys.ACT.Interfaces.Workflow import *
from Ansys.UI.Toolkit import *
import Ansys.ProjectSchematic


def reset_parameters(task):
    '''
    Called when try to replace .cft-batch file and resets all parameters to the 0.0 from right table of properties.

    '''
    prop_group_list = ['MainDimensions', 'BladeProperties', 'BladeMeanLines', 'Meridian', 'BladeProfiles']
    for i in prop_group_list:
        group = task.Properties["{}".format(i)].Properties
        for j in range(len(group)):
            group[j].Value = 0.0


def clean_dir(task):
    for file in os.listdir(task.ActiveDirectory):
        os.remove(os.path.join(task.ActiveDirectory, file))


def del_cfturbo_files(task):
    for file in os.listdir(task.ActiveDirectory):
        if file.endswith('.curve') or file.endswith('.log') or file.endswith('.tse'):
            os.remove(os.path.join(task.ActiveDirectory, file))


def get_cft_batch_path(task):
    '''
    Extract .cft-batch file path from property 'Input File Name'.
    :return: file path ..\*.cft-batch

    '''
    group = task.Properties["CFTurbo batch file"]
    cft_batch_file_path = group.Properties["InputFileName"]
    return cft_batch_file_path


def get_cft_file_name(task):
    cft_batch_file_path = get_cft_batch_path(task)
    cft_file_name = basename(cft_batch_file_path.Value).split('.cft')[0]
    return cft_file_name


def reset(task):
    InputFileName = task.Properties["CFTurbo batch file"].Properties["InputFileName"]

    cft_batch_file_path = get_cft_batch_path(task)
    cft_file_name = get_cft_file_name(task)
    cft_file_path = path.join(task.ActiveDirectory, (cft_file_name + '.cft'))

    task.UnregisterFile(cft_file_path)
    task.UnregisterFile(cft_batch_file_path.Value)
    task.UnregisterFile(path.join(task.ActiveDirectory, cft_file_name + '.inf'))

    for file in os.listdir(task.ActiveDirectory):
        os.remove(os.path.join(task.ActiveDirectory, file))

    clean_dir(task)
    InputFileName.Value = "No file chosen!"
    reset_parameters(task)


def status(task):
    '''
    Changes status of the cell if there is no .cft-file in the working directory.

    '''
    dir_list = os.listdir(task.ActiveDirectory)

    # write a more relible condition in the future
    if len(dir_list) < 2:
        status = Ansys.ProjectSchematic.Queries.ComponentState(Ansys.ProjectSchematic.State.Unfulfilled,
                                                               "cannot copy .cft file")
        return status
    else:
        return None


def input_file_valid(task, property):
    '''
    Check whether the file path exists in the cell property 'Input File Name'.
    :return: bool

    '''
    if path.exists(property.Value):
        return True
    return False


def copy_cft_file(task):
    '''
    Copy .cft file from user_files dir to .\ACT dir of the project. If there is no .cft file if use_files dir raises.
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

        # remained yellow color in Input File Name field
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
    if list(root[0][1]) == []:
        pass
    else:
        export_components_node = root[0][1].find('ExportComponents')
        root[0][1].remove(export_components_node)

    tree.write(target_dir + '-batch')
    return target_dir


def edit(task):
    '''
    Called when click RMB on the cell 'CFTurbo Design'. User selects file .cft-batch in opened window and if attempt is
    successful copies .cft-batch file from user_files dir to .\ACT dir of the project.

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

        # if file already chosen
        else:

            messg = "Would you like to replace existing file?"

            overwriteDialogResult = MessageBox.Show(Window.MainWindow, messg, "", MessageBoxType.Question,
                                                    MessageBoxButtons.YesNo)

            if overwriteDialogResult == DialogResult.Yes:

                cft_file_name = get_cft_file_name(task)
                cft_file_path = path.join(task.ActiveDirectory, (cft_file_name + '.cft'))

                task.UnregisterFile(cft_file_path)

                # reset parameters in propertygroups
                reset_parameters(task)

                dest = Path.Combine(task.ActiveDirectory, path.basename(diagResult[1]))
                source = diagResult[1]
                remove(filePath.Value)
                try:
                    copyfile(source, dest)
                except IOError:
                    MessageBox.Show(Window.MainWindow, "Failed to copy file to the working directory!",
                                    'Warning', MessageBoxType.Error, MessageBoxButtons.OK)
                    return

    cft_batch_file_path = get_cft_batch_path(task)
    cft_file_name = get_cft_file_name(task)

    task.UnregisterFile(cft_batch_file_path.Value)
    task.UnregisterFile(path.join(task.ActiveDirectory, cft_file_name + '.inf'))

    filePath.Value = dest
    fileRef = RegisterFile(FilePath=filePath.Value)
    AssociateFileWithContainer(fileRef, container)

    # function which copies .cft file to active directory
    cft_file_path = copy_cft_file(task)

    task.RegisterFile(cft_file_path)

    # function which takes values from a file .cft-batch
    insert_dimensions(task)


def insert_dimensions(task):
    '''
    Insert main dimensions of impeller to the table of properties of cell#1.

    '''
    try:
        # if there is no .cft-file in user_files directory raise exception
        copy_cft_file(task)
        MainDimensions(task).insert_main_dimensions(task)
        BladeProperties(task).insert_blade_properties(task)
        SkeletonLines(task).insert_skeletonLines_properties(task)
        Meridian(task).insert_meridian_properties(task)
        BladeProfiles(task).insert_distances_to_pres_side(task)
    except IOError:
        pass


def update_main_dimensions(task):
    main_dimensions = MainDimensions(task)
    main_dimensions.write_main_dimensions(task)


def update_blade_properties(task):

    #BladeProperties  and Impeller classes from xml_parser.py module
    bladeProp = BladeProperties(task)
    impeller = Impeller(task)

    tree = impeller.get_xml_tree(task)
    root = tree.getroot()

    # get blade properties element
    blade_properties_element = root[0][0][0][0][2]

    spans = bladeProp.get_num_spans(task)
    check_node = blade_properties_element[1][0]

    # the code bellow writes new values of parameter when update cell#2
    blade_properties_element.find('nBl').text = str(bladeProp.number_blades.Value)

    bladeProp.write_thickness(check_node, bladeProp.le_thickness_hub.Value, 'sLEH')
    bladeProp.write_thickness(check_node, bladeProp.le_thickness_shroud.Value, 'sLES')
    bladeProp.write_thickness(check_node, bladeProp.te_thickness_hub.Value, 'sTEH')
    bladeProp.write_thickness(check_node, bladeProp.te_thickness_shroud.Value, 'sTES')

    beta1_node = check_node.find('Beta1')
    if beta1_node is None:
        pass
    else:
        bladeProp.write_blade_angles(beta1_node, '0', bladeProp.beta_1_h.Value)
        bladeProp.write_blade_angles(beta1_node, (int(spans) - 1), bladeProp.beta_1_s.Value)
        bladeProp.write_interpolated_blade_angles(task, beta1_node, bladeProp.beta_1_h.Value, bladeProp.beta_1_s.Value)

    beta2_node = check_node.find('Beta2')
    if beta2_node is None:
        pass
    else:
        bladeProp.write_blade_angles(beta2_node, '0', bladeProp.beta_2_h.Value)
        bladeProp.write_blade_angles(beta2_node, (int(spans) - 1), bladeProp.beta_2_s.Value)
        bladeProp.write_interpolated_blade_angles(task, beta2_node, bladeProp.beta_2_h.Value, bladeProp.beta_2_s.Value)

    target_dir = copy_cft_file(task)
    tree.write(target_dir + '-batch')


def update_skeletonLines(task):
    skeletonLines = SkeletonLines(task)
    skeletonLines.writes_phi_angles(task, skeletonLines.phiLE.Value, skeletonLines.phiTE.Value)


def update_meridian(task):
    meridian = Meridian(task)
    meridian_properties = meridian.get_positions(task)

    if 'LePosHub' in meridian_properties:
        meridian.writes_positions(task, meridian.LePosHub.Value, 'GeoLeadingEdge_u-Hub')
    if 'LePosShroud' in meridian_properties:
        meridian.writes_positions(task, meridian.LePosShroud.Value, 'GeoLeadingEdge_u-Shroud')
    if 'TePosHub' in meridian_properties:
        meridian.writes_positions(task, meridian.TePosHub.Value, 'GeoTrailingEdge_u-Hub')
    if 'TePosShroud' in meridian_properties:
        meridian.writes_positions(task, meridian.TePosShroud.Value, 'GeoTrailingEdge_u-Shroud')
    if 'LePosHubSplitter' in meridian_properties:
        meridian.writes_positions(task, meridian.LePosHubSplitter.Value, 'GeoSplitLeadingEdge_u-Hub')
    if 'LePosShroudSplitter' in meridian_properties:
        meridian.writes_positions(task, meridian.LePosShroudSplitter.Value, 'GeoSplitLeadingEdge_u-Shroud')


def update_blade_profiles(task):
    blProf = BladeProfiles(task)
    blade_thickness = blProf.join_distances_to_pres_side(task)

    if 'DstPresSideHub_1' in blade_thickness:
        blProf.write_blade_distances(task, 0, 0, blProf.DstPresSideHub_1.Value)
    if 'DstPresSideHub_2' in blade_thickness:
        blProf.write_blade_distances(task, 0, 1, blProf.DstPresSideHub_2.Value)
    if 'DstPresSideHub_3' in blade_thickness:
        blProf.write_blade_distances(task, 0, 2, blProf.DstPresSideHub_3.Value)
    if 'DstPresSideHub_4' in blade_thickness:
        blProf.write_blade_distances(task, 0, 3, blProf.DstPresSideHub_4.Value)

    if 'DstPresSideShroud_1' in blade_thickness:
        blProf.write_blade_distances(task, 1, 0, blProf.DstPresSideShroud_1.Value)
    if 'DstPresSideShroud_2' in blade_thickness:
        blProf.write_blade_distances(task, 1, 1, blProf.DstPresSideShroud_2.Value)
    if 'DstPresSideShroud_3' in blade_thickness:
        blProf.write_blade_distances(task, 1, 2, blProf.DstPresSideShroud_3.Value)
    if 'DstPresSideShroud_4' in blade_thickness:
        blProf.write_blade_distances(task, 1, 3, blProf.DstPresSideShroud_4.Value)


def get_dp_name():
    """
        Method to get current design point name.

    """
    currDP = Parameters.GetActiveDesignPoint()
    return "dp"+currDP.Name


def is_dp0():
    name = get_dp_name()
    return name == "dp0"


def change_dp_name(*args):
    dp_dir = re.sub(r'dp\d+', get_dp_name(), r'{}'.format(*args))
    return dp_dir


def change_path_in_cft_batch(*args):
    tree = ET.parse(*args)
    root = tree.getroot()
    cfturbo_batch_project_node = root.find('CFturboBatchProject')
    input_file = cfturbo_batch_project_node.attrib['InputFile']
    dp_dir = change_dp_name(input_file)
    cfturbo_batch_project_node.attrib['InputFile'] = dp_dir
    tree.write(*args)


def update(task):
    InputFileName = task.Properties["CFTurbo batch file"].Properties["InputFileName"]

    if is_dp0():
        pass
    else:
        InputFileName.Value = change_dp_name(InputFileName.Value)
        change_path_in_cft_batch(InputFileName.Value)

    del_cfturbo_files(task)
    update_main_dimensions(task)
    update_meridian(task)
    update_blade_properties(task)
    update_skeletonLines(task)
    update_blade_profiles(task)
    cfturbo_start(task)


def get_exe_cft_path(func):
    """
        Extract release number and find path to cfturbo.exe.
        :return: path to cfturbo.exe

    """
    def wrapper():
        latest_release = 0
        for v in func():
            cur_release = int(v[7:-5])
            if cur_release > latest_release:
                latest_release = cur_release
        cft_path = os.environ.get('CFTURBO{}_root'.format(latest_release))
        return cft_path
    return wrapper


@get_exe_cft_path
def get_cft_var_list():
    """
        Get list of system variables and find only CFTURBO vars.
        :return: list of CFTURBO versions

    """
    var_list = [key for key in os.environ.keys() if re.findall(r'CFTURBO\d+_ROOT', key)]
    if not var_list:
        raise Exception('There is no system variables CFTURBO!')
    return var_list


def launch_cfturbo(task):
    cft_path = get_cft_var_list()
    cft_batch_file = Impeller(task).get_cft_batch_path(task)
    cmdline = r'"{}\cfturbo.exe" -batch "{}"'.format(cft_path, cft_batch_file)
    try:
        os.system(cmdline)
    except Exception:
        MessageBox.Show('Failed to launch CFTurbo!')


def cfturbo_start(task):
    '''
    Main function for starting CFturbo and writing .inf file.

    '''
    launch_cfturbo(task)

    container = task.InternalObject
    fileRef = None

    cft_file_name = Geometry(task).obtain_cft_file_name(task)
    inf_file = cft_file_name + '.inf'
    inf_file_dir = os.path.join(task.ActiveDirectory, inf_file)

    # function which extracts information from .tse file and create .inf file
    FilesStrings(task).create_inf_file(task)

    # .inf file registration
    TurboGridInputFiles = inf_file_dir

    # check if the .inf file is associated with WB project
    isRegistered = IsFileRegistered(FilePath=TurboGridInputFiles)
    if isRegistered:
        fileRef = GetRegisteredFile(FilePath=TurboGridInputFiles)
    else:
        fileRef = RegisterFile(FilePath=TurboGridInputFiles)
        AssociateFileWithContainer(fileRef, container)

    outputRefs = container.GetOutputData()
    outputSet = outputRefs["TurboGeometry"]
    myData = outputSet[0]
    myData.INFFilename = fileRef