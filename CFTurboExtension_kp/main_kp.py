import clr
import os
clr.AddReference("Ans.UI.Toolkit")
clr.AddReference("Ans.UI.Toolkit.Base")
from Ansys.UI.Toolkit import *
from shutil import copyfile, copy
from filecmp import cmp
from ntpath import basename
from os import remove, path, environ, system
from System.IO import Path
import xml.etree.ElementTree as ET


def InFileValid(task, property):
    if path.exists(property.Value):
        return True
    return False


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

                # function that takes values from a file .cft-batch
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







