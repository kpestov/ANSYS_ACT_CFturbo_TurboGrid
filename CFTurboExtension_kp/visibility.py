"""This module is responsible for visibility of parameters in WB property table.

"""

def groups_visible(task, property):
    '''
    Hide groups of properties if file no chosen
    :return: boolean
    '''
    InputFileName = task.Properties["CFTurbo batch file"].Properties["InputFileName"]

    if InputFileName.Value == "No file chosen!":
        return False
    return True


# properties for radial and mixed pumps
def hub_diameter_visible(task, property):
    HubDiameter = MainDimensions(task).main_dim_exist(task, 'dN', 'Caption', 'Hub diameter')
    if HubDiameter is None:
        return False
    return True


def suction_diameter_visible(task, property):
    SuctionDiameter = MainDimensions(task).main_dim_exist(task, 'dS', 'Caption', 'Suction diameter')
    if SuctionDiameter is None:
        return False
    return True


def impeller_diameter_visible(task, property):
    ImpellerDiameter = MainDimensions(task).main_dim_exist(task, 'd2', 'Caption', 'Impeller diameter')
    if ImpellerDiameter is None:
        return False
    return True


def impeller_out_width_visible(task, property):
    ImpellerOutWidth = MainDimensions(task).main_dim_exist(task, 'b2', 'Caption', 'Outlet width')
    if ImpellerOutWidth is None:
        return False
    return True


# properties for axial pump
def hub_diameter_out_visible(task, property):
    HubDiameterOut = MainDimensions(task).main_dim_exist(task, 'dH2', 'Caption', 'Hub diameter outlet')
    if HubDiameterOut is None:
        return False
    return True


def tip_diameter_out_visible(task, property):
    TipDiameterOut = MainDimensions(task).main_dim_exist(task, 'dS2', 'Caption', 'Tip diameter outlet')
    if TipDiameterOut is None:
        return False
    return True


def beta1_visible(task, property):
    beta1 = BladeProperties(task).beta_exist(task, 'Beta1')
    if beta1 is None:
        return False
    return True


def beta2_visible(task, property):
    beta1 = BladeProperties(task).beta_exist(task, 'Beta2')
    if beta1 is None:
        return False
    return True


def le_pos_hub_visible(task, property):
    LePosHub = Meridian(task).position_exist(task, 'LePosHub')
    if LePosHub is None:
        return False
    return True


def te_pos_hub_visible(task, property):
    TePosHub = Meridian(task).position_exist(task, 'TePosHub')
    if TePosHub is None:
        return False
    return True


def le_pos_hub_splitter_visible(task, property):
    LePosHubSplitter = Meridian(task).position_exist(task, 'LePosHubSplitter')
    if LePosHubSplitter is None:
        return False
    return True


def dst_pres_side_hub1_visible(task, property):
    BladeThickHub1 = BladeProfiles(task).dst_to_press_side_exist(task, 'DstPresSideHub_1')
    if BladeThickHub1 is None:
        return False
    return True


def dst_pres_side_hub2_visible(task, property):
    BladeThickHub2 = BladeProfiles(task).dst_to_press_side_exist(task, 'DstPresSideHub_2')
    if BladeThickHub2 is None:
        return False
    return True


def dst_pres_side_hub3_visible(task, property):
    BladeThickHub3 = BladeProfiles(task).dst_to_press_side_exist(task, 'DstPresSideHub_3')
    if BladeThickHub3 is None:
        return False
    return True


def dst_pres_side_hub4_visible(task, property):
    BladeThickHub4 = BladeProfiles(task).dst_to_press_side_exist(task, 'DstPresSideHub_4')
    if BladeThickHub4 is None:
        return False
    return True


def dst_pres_side_shroud1_visible(task, property):
    BladeThickShroud1 = BladeProfiles(task).dst_to_press_side_exist(task, 'DstPresSideShroud_1')
    if BladeThickShroud1 is None:
        return False
    return True


def dst_pres_side_shroud2_visible(task, property):
    BladeThickShroud2 = BladeProfiles(task).dst_to_press_side_exist(task, 'DstPresSideShroud_2')
    if BladeThickShroud2 is None:
        return False
    return True


def dst_pres_side_shroud3_visible(task, property):
    BladeThickShroud3 = BladeProfiles(task).dst_to_press_side_exist(task, 'DstPresSideShroud_3')
    if BladeThickShroud3 is None:
        return False
    return True


def dst_pres_side_shroud4_visible(task, property):
    BladeThickShroud4 = BladeProfiles(task).dst_to_press_side_exist(task, 'DstPresSideShroud_4')
    if BladeThickShroud4 is None:
        return False
    return True