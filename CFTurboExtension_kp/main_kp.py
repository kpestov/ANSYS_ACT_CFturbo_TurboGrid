import clr
import os
import xml.etree.ElementTree as ET
import subprocess
clr.AddReference("Ans.UI.Toolkit")
clr.AddReference("Ans.UI.Toolkit.Base")
clr.AddReference('Ansys.ACT.Interfaces')
# clr.AddReference('System.Windows.Forms')
# from System.Windows.Forms import MessageBox, MessageBoxButtons, MessageBoxIcon
from Ansys.ACT.Interfaces.Workflow import *
from Ansys.UI.Toolkit import *
from shutil import copyfile, copy
from filecmp import cmp
from ntpath import basename
from os import remove, path, environ, system
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
    file_name = os.path.basename(input_file)
    source_dir = Path.Combine(start_dir, file_name)
    target_dir = Path.Combine(task.ActiveDirectory, file_name)
    try:
        copyfile(source_dir, target_dir)
    except:
        # MessageBox.Show('hui', 'hui_2', MessageBoxButtons.OK, MessageBoxIcon.Asterisk)
        MessageBox.Show(Window.MainWindow, 'Failed to copy cft file to the working directory! Please place the .cft file '
                                         'in the user_files directory', 'Warning', MessageBoxType.Error, MessageBoxButtons.OK)

    # changes .cft file dir in .cft-batch file when copy .cft-batch to ActiveDirectory
    cfturbo_batch_project_node.attrib['InputFile'] = target_dir
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
    for child in main_dimensions_sub_node:
        main_dimensions[child.tag] = child.text

    # function which takes values from a file .cft-batch
    get_main_dimensions(task, main_dimensions)

    MessageBox.Show(os.listdir(task.ActiveDirectory))


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

        child_0 = main_dimensions_sub_node.find('xTip')
        child_1 = main_dimensions_sub_node.find('dN')

        child_0.text = str(tip_clearance.Value)
        child_1.text = str(hub_diameter.Value)

        target_dir = copy_cft_file(task)
        tree.write(target_dir + '-batch')


def launch_cfturbo(task):
    cft_env = 'CFturbo10_root'
    cft_path = environ.get(cft_env)
    launch_cft_path = os.path.join(cft_path, 'cfturbo.exe')
    cft_batch_file = get_cft_path(task)
    start_cfturbo = Process.Start(launch_cft_path, '-batch' + ' ' + cft_batch_file)
    start_cfturbo.WaitForExit()
    exit_code = start_cfturbo.ExitCode

    if exit_code != 1:
        raise Exception('Failed to launch CFTurbo!')


# def create_inf_file():



# def cfturbo_start(task):
#     launch_cfturbo(task)
#
#     # here will be function which extract information from .tse file and create .inf file
#     # create_inf_file()

def dummy_copying(task):

# this is dummy function which copies .curve and .tse files from act directory to task.ActiveDirectory

    container = task.InternalObject
    fileRef = None

    extensionDir = ExtAPI.ExtensionManager.CurrentExtension.InstallDir

    # obtain source and target directories for copy .curve, .tse files (this is dummy code)
    for TurboGridFiles in os.listdir(extensionDir):
        if TurboGridFiles.endswith(".curve") or TurboGridFiles.endswith(".tse"):
            source_files = os.path.join(extensionDir, TurboGridFiles)
            target_files = os.path.join(task.ActiveDirectory, TurboGridFiles)

            # copy .curve, .tse files from act directory to task.ActiveDirectory (this is dummy code)
            copy(source_files, target_files)

    # here will be function which extract information from .tse file and create .inf file
    # create_inf_file()


    # here wiil be name of .inf file for registration
    # TurboGridInputFiles =

    # check if the .inf file is associated with WB project

    # isRegistered = IsFileRegistered(FilePath=TurboGridInputFiles)
    # if isRegistered == True:
    #     fileRef = GetRegisteredFile(FilePath=TurboGridInputFiles)
    # else:
    #     fileRef = RegisterFile(FilePath=TurboGridInputFiles)
    #     AssociateFileWithContainer(fileRef, container)
    #
    # outputRefs = container.GetOutputData()
    # outputSet = outputRefs["TurboGeometry"]
    # myData = outputSet[0]
    # myData.INFFilename = fileRef


# def dummy_copying(task):
#
# # this is dummy function which copies .curve, .tse and .inf files from act directory to task.ActiveDirectory
#
#     container = task.InternalObject
#     fileRef = None
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
#     # obtain source and target directories for copy .inf file (this is dummy code)
#     TurboGridDummyFiles = System.IO.Path.Combine(extensionDir, "BG.inf")
#     TurboGridInputFiles = System.IO.Path.Combine(task.ActiveDirectory, "BG.inf")
#
#     # check if the .inf file is associated with WB project
#
#     isRegistered = IsFileRegistered(FilePath=TurboGridInputFiles)
#     if isRegistered == True:
#         fileRef = GetRegisteredFile(FilePath=TurboGridInputFiles)
#     else:
#         fileRef = RegisterFile(FilePath=TurboGridInputFiles)
#         AssociateFileWithContainer(fileRef, container)
#
#     # copy .inf file from act directory to task.ActiveDirectory (this is dummy code)
#     copy(TurboGridDummyFiles, TurboGridInputFiles)
#
#     outputRefs = container.GetOutputData()
#     outputSet = outputRefs["TurboGeometry"]
#     myData = outputSet[0]
#     myData.INFFilename = fileRef







