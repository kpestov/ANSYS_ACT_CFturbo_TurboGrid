# I've commented it because it is possible to parameterized tip clearance in TurboGrid
# def tipClearanceVisible(task, property):
#     tipClearance = MainDimensions(task).tipClearanceExist(task)
#     if tipClearance == '0':
#         return False
#     return True

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

def BladeThickHub1Visible(task, property):
    BladeThickHub1 = BladeProfiles(task).bladeThicknessExist(task, 'BladeThickHub_1')
    if BladeThickHub1 is None:
        return False
    return True

def BladeThickHub2Visible(task, property):
    BladeThickHub2 = BladeProfiles(task).bladeThicknessExist(task, 'BladeThickHub_2')
    if BladeThickHub2 is None:
        return False
    return True

def BladeThickHub3Visible(task, property):
    BladeThickHub3 = BladeProfiles(task).bladeThicknessExist(task, 'BladeThickHub_3')
    if BladeThickHub3 is None:
        return False
    return True

def BladeThickHub4Visible(task, property):
    BladeThickHub4 = BladeProfiles(task).bladeThicknessExist(task, 'BladeThickHub_4')
    if BladeThickHub4 is None:
        return False
    return True

def BladeThickShroud1Visible(task, property):
    BladeThickShroud1 = BladeProfiles(task).bladeThicknessExist(task, 'BladeThickShroud_1')
    if BladeThickShroud1 is None:
        return False
    return True

def BladeThickShroud2Visible(task, property):
    BladeThickShroud2 = BladeProfiles(task).bladeThicknessExist(task, 'BladeThickShroud_2')
    if BladeThickShroud2 is None:
        return False
    return True

def BladeThickShroud3Visible(task, property):
    BladeThickShroud3 = BladeProfiles(task).bladeThicknessExist(task, 'BladeThickShroud_3')
    if BladeThickShroud3 is None:
        return False
    return True

def BladeThickShroud4Visible(task, property):
    BladeThickShroud4 = BladeProfiles(task).bladeThicknessExist(task, 'BladeThickShroud_4')
    if BladeThickShroud4 is None:
        return False
    return True

# I've commented it because BladeProfiles group is hidden when all properties are absent. No need to write a separate
# function.
# def BladeProfilesVisible(task, property):
#     num_points = BladeProfiles(task).BladeProfilesExist(task)
#
#     if num_points == 1:
#         return False
#     return True