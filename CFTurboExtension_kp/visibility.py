def GroupsVisible(task, property):
    '''
    Hide groups of properties if file no chosen
    :param task:
    :param property:
    :return: boolean
    '''
    InputFileName = task.Properties["CFTurbo batch file"].Properties["InputFileName"]

    if InputFileName.Value == "No file chosen!":
        return False
    return True

# properties for radial and mixed pumps
def HubDiameterVisible(task, property):
    HubDiameter = MainDimensions(task).main_dim_exist(task, 'dN', 'Caption', 'Hub diameter')
    if HubDiameter is None:
        return False
    return True

def SuctionDiameterVisible(task, property):
    SuctionDiameter = MainDimensions(task).main_dim_exist(task, 'dS', 'Caption', 'Suction diameter')
    if SuctionDiameter is None:
        return False
    return True

def ImpellerDiameterVisible(task, property):
    ImpellerDiameter = MainDimensions(task).main_dim_exist(task, 'd2', 'Caption', 'Impeller diameter')
    if ImpellerDiameter is None:
        return False
    return True

def ImpellerOutWidthVisible(task, property):
    ImpellerOutWidth = MainDimensions(task).main_dim_exist(task, 'b2', 'Caption', 'Outlet width')
    if ImpellerOutWidth is None:
        return False
    return True

# properties for axial pump
def HubDiameterOutVisible(task, property):
    HubDiameterOut = MainDimensions(task).main_dim_exist(task, 'dH2', 'Caption', 'Hub diameter outlet')
    if HubDiameterOut is None:
        return False
    return True

def TipDiameterOutVisible(task, property):
    TipDiameterOut = MainDimensions(task).main_dim_exist(task, 'dS2', 'Caption', 'Tip diameter outlet')
    if TipDiameterOut is None:
        return False
    return True

def beta1Visible(task, property):
    beta1 = BladeProperties(task).beta_exist(task, 'Beta1')
    if beta1 is None:
        return False
    return True

def beta2Visible(task, property):
    beta1 = BladeProperties(task).beta_exist(task, 'Beta2')
    if beta1 is None:
        return False
    return True

def LePosHubVisible(task, property):
    LePosHub = Meridian(task).position_exist(task, 'LePosHub')
    if LePosHub is None:
        return False
    return True

def TePosHubVisible(task, property):
    TePosHub = Meridian(task).position_exist(task, 'TePosHub')
    if TePosHub is None:
        return False
    return True

def LePosHubSplitterVisible(task, property):
    LePosHubSplitter = Meridian(task).position_exist(task, 'LePosHubSplitter')
    if LePosHubSplitter is None:
        return False
    return True

def DstPresSideHub1Visible(task, property):
    BladeThickHub1 = BladeProfiles(task).dst_to_press_side_exist(task, 'DstPresSideHub_1')
    if BladeThickHub1 is None:
        return False
    return True

def DstPresSideHub2Visible(task, property):
    BladeThickHub2 = BladeProfiles(task).dst_to_press_side_exist(task, 'DstPresSideHub_2')
    if BladeThickHub2 is None:
        return False
    return True

def DstPresSideHub3Visible(task, property):
    BladeThickHub3 = BladeProfiles(task).dst_to_press_side_exist(task, 'DstPresSideHub_3')
    if BladeThickHub3 is None:
        return False
    return True

def DstPresSideHub4Visible(task, property):
    BladeThickHub4 = BladeProfiles(task).dst_to_press_side_exist(task, 'DstPresSideHub_4')
    if BladeThickHub4 is None:
        return False
    return True

def DstPresSideShroud1Visible(task, property):
    BladeThickShroud1 = BladeProfiles(task).dst_to_press_side_exist(task, 'DstPresSideShroud_1')
    if BladeThickShroud1 is None:
        return False
    return True

def DstPresSideShroud2Visible(task, property):
    BladeThickShroud2 = BladeProfiles(task).dst_to_press_side_exist(task, 'DstPresSideShroud_2')
    if BladeThickShroud2 is None:
        return False
    return True

def DstPresSideShroud3Visible(task, property):
    BladeThickShroud3 = BladeProfiles(task).dst_to_press_side_exist(task, 'DstPresSideShroud_3')
    if BladeThickShroud3 is None:
        return False
    return True

def DstPresSideShroud4Visible(task, property):
    BladeThickShroud4 = BladeProfiles(task).dst_to_press_side_exist(task, 'DstPresSideShroud_4')
    if BladeThickShroud4 is None:
        return False
    return True