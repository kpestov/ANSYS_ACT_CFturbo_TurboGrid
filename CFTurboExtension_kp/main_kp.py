import clr
import os
import Ansys.ACT.Interfaces
import xml.etree.ElementTree as ET
clr.AddReference("Ans.UI.Toolkit")
clr.AddReference("Ans.UI.Toolkit.Base")
clr.AddReference('Ansys.ACT.Interfaces')
from Ansys.UI.Toolkit import *
from shutil import copyfile, copy
from filecmp import cmp
from ntpath import basename
from os import remove, path, environ, system
from System.IO import Path
import sys


def status(task):
    # start_dir = GetUserFilesDirectory()
    if "test-impeller.cft" not in os.listdir(task.ActiveDirectory):
        return [Ansys.ACT.Interfaces.Common.State.Unfulfilled, 'cannot copy .cft file']
    else:
        return None


def InFileValid(task, property):
    if path.exists(property.Value):
        return True
    return False


def copy_cft_file(task):
    container = task.InternalObject

    # obtain user_files directory
    start_dir = GetUserFilesDirectory()

    # getting access to property group of CFTurbo Design cell
    group = task.Properties["CFTurbo batch file"]
    cft_batch_file_path = group.Properties["InputFileName"]

    # get_xml_root
    tree = ET.parse(cft_batch_file_path.Value)
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
        # raise Exception("Error!")
        Ansys.UI.Toolkit.MessageBox.Show('Failed to copy cft file to the working directory! Please place the .cft file'
                                         ' in the user_files directory')
        return
    file_ref = RegisterFile(FilePath=target_dir)
    AssociateFileWithContainer(file_ref, container)

    # return target_dir


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
        filePath = group.Properties["InputFileName"]

        # check if choosing file for the first time by file path property value
        if filePath.Value == "No file chosen!":
            sourcePath = path.abspath(diagResult[1])
            dest = Path.Combine(task.ActiveDirectory, path.basename(diagResult[1]))
            source = diagResult[1]
            try:
                copyfile(source, dest)
            except:
                Ansys.UI.Toolkit.MessageBox.Show("Failed to copy file to the working directory!")
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
                    Ansys.UI.Toolkit.MessageBox.Show("Failed to copy file to the working directory!")
                    return
                filePath.Value = dest
                fileRef = RegisterFile(FilePath=filePath.Value)
                AssociateFileWithContainer(fileRef, container)

    # function which copies .cft file to active directory
    copy_cft_file(task)

    # choose .cft-batch file from active directory
    for cft_file in os.listdir(task.ActiveDirectory):
        if cft_file.endswith(".cft-batch"):
            cft_file_path = os.path.join(task.ActiveDirectory, cft_file)

            # get_xml_root
            tree = ET.parse(cft_file_path)
            root = tree.getroot()

            # get_design_impeller_node
            cfturbo_batch_project_node = root.find('CFturboBatchProject')
            updates_node = cfturbo_batch_project_node.find('Updates')
            cfturbo_project_node = updates_node.find('CFturboProject')

            # get_impeller_main_dimensions
            for impeller_design_node in cfturbo_project_node:
                main_dimensions = {}
                main_dimensions_node = impeller_design_node.find('MainDimensions')
                main_dimensions_sub_node = main_dimensions_node.find('MainDimensionsElement')

                for child in main_dimensions_sub_node:
                    main_dimensions[child.tag] = child.text

                # function which takes values from a file .cft-batch
                get_main_dimensions(task, main_dimensions)


def get_main_dimensions(task, main_dimensions):

    group = task.Properties["MainDimensions"]

    tip_clearance = group.Properties["TipClearance"]
    hub_diameter = group.Properties["HubDiameter"]
    suction_diameter = group.Properties["SuctionDiameter"]
    impeller_diameter = group.Properties["ImpellerDiameter"]
    impeller_outlet_width = group.Properties["ImpellerOutletWidth"]

    #this string just for testing
    # test_cell = group.Properties["TestCell"]

    tip_clearance.Value = main_dimensions['xTip']
    hub_diameter.Value = main_dimensions['dN']
    suction_diameter.Value = main_dimensions['dS']
    impeller_diameter.Value = main_dimensions['d2']
    impeller_outlet_width.Value = main_dimensions['b2']


def update(task):

    group = task.Properties["MainDimensions"]

    tip_clearance = group.Properties["TipClearance"]
    hub_diameter = group.Properties["HubDiameter"]

    test_cell = group.Properties["TestCell"]
    test_cell.Value = tip_clearance.Value

    if tip_clearance.Value == 1:
        raise Exception("Error in update - no output value detected!")

    # this duplicated code must be placed in a separate function

    for cft_file in os.listdir(task.ActiveDirectory):
        if cft_file.endswith(".cft-batch"):
            cft_file_path = os.path.join(task.ActiveDirectory, cft_file)

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

                child_0 = main_dimensions_sub_node.find('xTip')
                child_1 = main_dimensions_sub_node.find('dN')

                child_0.text = str(tip_clearance.Value)
                child_1.text = str(hub_diameter.Value)

                tree.write(os.path.join(task.ActiveDirectory, "test-impeller.cft-batch"))

def consumer_update(task):
    container = task.InternalObject
    fileRef = None

    # this is for dummy code (del it in release version)
    extensionDir = ExtAPI.ExtensionManager.CurrentExtension.InstallDir

    taskGroup = ExtAPI.DataModel.TaskGroups[0].InternalObject

    # task = taskGroup.Tasks[0]
    #
    # group = task.Properties["CFTurbo batch file"]
    # filePath = group.Properties["InputFileName"]

    Ansys.UI.Toolkit.MessageBox.Show(str(taskGroup))

    # cft_file = r'C:\kp\act\test_files\dp0\CFT\ACT\test-impeller.cft-batch'
    #
    # result = os.system('cfturbo.exe -batch' + ' ' + cft_file)
    #
    # if result != 1:
    #     Ansys.UI.Toolkit.MessageBox.Show("Failed to launch CFTurbo!")
    #     return

    # if result != 1:
    #     Ansys.UI.Toolkit.MessageBox.Show("Failed to launch CFTurbo!")
    #     return

    # # obtain source and target directories for copy .curve, .tse files (this is dummy code)
    # for TurboGridFiles in os.listdir(extensionDir):
    #     if TurboGridFiles.endswith(".curve") or TurboGridFiles.endswith(".tse"):
    #         source_files = os.path.join(extensionDir, TurboGridFiles)
    #         target_files = os.path.join(task.ActiveDirectory, TurboGridFiles)
    #
    #         # copy .curve, .tse files from act directory to task.ActiveDirectory (this is dummy code)
    #         copy(source_files, target_files)

    # # obtain source and target directories for copy .inf file (this is dummy code)
    # TurboGridDummyFiles = System.IO.Path.Combine(extensionDir, "BG.inf")
    # TurboGridInputFiles = System.IO.Path.Combine(task.ActiveDirectory, "BG.inf")
    #
    # # check if the file test-impeller_hub.curve is associated with WB project
    #
    # isRegistered = IsFileRegistered(FilePath=TurboGridInputFiles)
    # if isRegistered == True:
    #     fileRef = GetRegisteredFile(FilePath=TurboGridInputFiles)
    # else:
    #     fileRef = RegisterFile(FilePath=TurboGridInputFiles)
    #     AssociateFileWithContainer(fileRef, container)
    #
    # # copy .inf file from act directory to task.ActiveDirectory (this is dummy code)
    # copy(TurboGridDummyFiles, TurboGridInputFiles)
    #
    # outputRefs = container.GetOutputData()
    # outputSet = outputRefs["TurboGeometry"]
    # myData = outputSet[0]
    # myData.INFFilename = fileRef







