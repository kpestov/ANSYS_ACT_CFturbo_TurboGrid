import clr
import xml.etree.ElementTree as ET

clr.AddReference("Ans.UI.Toolkit")
clr.AddReference("Ans.UI.Toolkit.Base")
from Ansys.UI.Toolkit import *
from shutil import copyfile
from filecmp import cmp
from ntpath import basename
from os import remove, path, environ, system
from System.IO import Path

FILE = r'C:\ansys_projects\act\kp\CFturbo_files\test-impeller.cft-batch'


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


def get_xml_root():
    tree = ET.parse(FILE)
    root = tree.getroot()
    return root


def get_design_impeller_node(root):
    cfturbo_batch_project_node = root.find('CFturboBatchProject')
    updates_node = cfturbo_batch_project_node.find('Updates')
    cfturbo_project_node = updates_node.find('CFturboProject')

    for impeller_design_node in cfturbo_project_node:
        return impeller_design_node


def get_impeller_main_dimensions(impeller_design_node):
    main_dimensions_node = impeller_design_node.find('MainDimensions')
    main_dimensions_sub_node = main_dimensions_node.find('MainDimensionsElement')
    hub_diameter_test = main_dimensions_sub_node.find('dN').text
    return hub_diameter_test


xml_root = get_xml_root()
design_impeller_node = get_design_impeller_node(xml_root)
impeller_main_dimensions = get_impeller_main_dimensions(design_impeller_node)


def update_main_dimensions(task):
    group = task.Properties["MainDimensions"]
    hub_diameter = group.Properties["HubDiameter"]
    hub_diameter.Value = impeller_main_dimensions
    return hub_diameter.Value

