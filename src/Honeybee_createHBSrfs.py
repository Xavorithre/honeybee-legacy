# By Mostapha Sadeghipour Roudsari
# Sadeghipour@gmail.com
# Honeybee started by Mostapha Sadeghipour Roudsari is licensed
# under a Creative Commons Attribution-ShareAlike 3.0 Unported License.

"""
Create a Honeybee surface, which can be plugged into the "Run Daylight Sumilation" component or combined with other surfaces to make HBZones with the "createHBZones" component.
-
Provided by Honeybee 0.0.55

    Args:
        _geometry: List of Breps
        srfName_: Optional name for surface
        srfType_: Optional input for surface type >
            0- 'WALL'
            0.5- 'UndergroundWall'
            1- 'ROOF'
            1.5- 'UndergroundCeiling'
            2- 'FLOOR'
            2.25- 'UndergroundSlab'
            2.5- 'SlabOnGrade'
            2.75- 'ExposedFloor'
            3- 'CEILING'
            4- 'AIRWALL'
            5- 'WINDOW'
            6- 'SHADING'
        EPBC_: 'Ground', 'Adiabatic', 'Outdoors'
        _EPConstruction_: Optional EnergyPlus construction
        _RADMaterial_: Optional Radiance Material
    Returns:
        readMe!:...
        HBZone: A Honeybee Surface, which can be plugged into the "Run Daylight Sumilation" component or combined with other surfaces to make HBZones with the "createHBZones" component.
"""

import rhinoscriptsyntax as rs
import Rhino as rc
import scriptcontext as sc
import os
import sys
import System
from clr import AddReference
AddReference('Grasshopper')
import Grasshopper.Kernel as gh
import uuid

ghenv.Component.Name = 'Honeybee_createHBSrfs'
ghenv.Component.NickName = 'createHBSrfs'
ghenv.Component.Message = 'VER 0.0.55\nJAN_22_2015'
ghenv.Component.Category = "Honeybee"
ghenv.Component.SubCategory = "00 | Honeybee"
#compatibleHBVersion = VER 0.0.55\nAUG_25_2014
#compatibleLBVersion = VER 0.0.58\nAUG_20_2014
try: ghenv.Component.AdditionalHelpFromDocStrings = "2"
except: pass


tolerance = sc.doc.ModelAbsoluteTolerance
import math


def main(geometry, srfName, srfType, EPBC, EPConstruction, RADMaterial):
    # import the classes
    if sc.sticky.has_key('honeybee_release'):

        try:
            if not sc.sticky['honeybee_release'].isCompatible(ghenv.Component): return -1
        except:
            warning = "You need a newer version of Honeybee to use this compoent." + \
            "Use updateHoneybee component to update userObjects.\n" + \
            "If you have already updated userObjects drag Honeybee_Honeybee component " + \
            "into canvas and try again."
            w = gh.GH_RuntimeMessageLevel.Warning
            ghenv.Component.AddRuntimeMessage(w, warning)
            return -1
            
        # don't customize this part
        hb_EPZone = sc.sticky["honeybee_EPZone"]
        hb_EPSrf = sc.sticky["honeybee_EPSurface"]
        hb_EPZoneSurface = sc.sticky["honeybee_EPZoneSurface"]
        hb_EPFenSurface = sc.sticky["honeybee_EPFenSurface"]
        hb_RADMaterialAUX = sc.sticky["honeybee_RADMaterialAUX"]()
        hb_EPObjectsAux = sc.sticky["honeybee_EPObjectsAUX"]()
        
    else:
        print "You should first let Honeybee to fly..."
        w = gh.GH_RuntimeMessageLevel.Warning
        ghenv.Component.AddRuntimeMessage(w, "You should first let Honeybee to fly...")
        return
    
    # if the input is mesh, convert it to a surface
    try:
        # check if this is a mesh
        geometry.Faces[0].IsQuad
        # convert to brep
        geometry = rc.Geometry.Brep.CreateFromMesh(geometry, False)
    except:
        pass
    
    HBSurfaces = []
    
    for faceCount in range(geometry.Faces.Count):
        
        # 0. check if user input a name for this surface
        guid = str(uuid.uuid4())
        number = guid.split("-")[-1]

        if srfName != None:
            if geometry.Faces.Count != 1:
                srfName = srfName + "_" + `faceCount`
        else:
            # generate a random name
            # the name will be overwritten for energy simulation
            srfName = "".join(guid.split("-")[:-1])
            
        # 1. create initial surface
        HBSurface = hb_EPZoneSurface(geometry.Faces[faceCount].DuplicateFace(False), number, srfName)
        
        # If the user has set a construction as Air Wall, change the surface type to air wall.
        try:
            if EPConstruction.ToUpper() == "AIR WALL":
                srfType = 4
                infoMsg = "Setting the construction to Air Wall will also ensure that the surface has the air wall srfType_."
                ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Remark, infoMsg)
        except: pass
        
        if srfType == 4 or srfType == 4.0 or srfType == "4" or srfType == "4.0":
            try:
                if EPConstruction.ToUpper() == "AIR WALL": pass
                else:
                    infoMsg = "Setting the srfType to 4 will also ensure that the surface has the air wall construction."
                    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Remark, infoMsg)
            except:
                infoMsg = "Setting the srfType to 4 will also ensure that the surface has the air wall construction."
                ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Remark, infoMsg)
            EPConstruction = "AIR WALL"
        
        # 1.1 check for surface type
        if srfType!=None:
            try:
                # if user uses a number to input type
                try: surfaceType = int(srfType)
                except:
                    if float(srfType) == 0.5 or float(srfType) == 1.5 or float(srfType) == 2.25 or float(srfType) == 2.5 or float(srfType) == 2.75:
                        surfaceType = srfType
                    else: pass
                print "HBSurface Type has been set to " + HBSurface.srfType[float(srfType)]
                
                if surfaceType == 5.0:
                    warningMsg = "If you want to use this model for energy simulation, use addGlazing to add window to surfaces.\n" + \
                                 "It will be fine for Daylighting simulation though."
                    print warningMsg
                    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warningMsg)
            except:
                # user uses text as an input (e.g.: wall)
                # convert it to a number if a valid input
                surfaceType = srfType.ToUpper()
                if surfaceType in HBSurface.srfType.keys():
                   surfaceType = HBSurface.srfType[surfaceType.ToUpper()]
                   print "HBSurface Type has been set to " + surfaceType.ToUpper()
            
            if surfaceType in HBSurface.srfType.keys():
                acceptableCombination = [[1,3], [3,1], [0,5], [5,0], [1,5], [5,1], [4,0], [4,1], [4,2], [4,3], [0,4], [1,4], [2,4], [3,4]]
                try:
                    if int(HBSurface.type) != surfaceType and [int(HBSurface.type), surfaceType] not in acceptableCombination:
                        warningMsg = "Normal direction of the surface is not expected for a " + HBSurface.srfType[surfaceType] + ". " + \
                                     "The surface is more likely a " + HBSurface.srfType[int(HBSurface.type)] + ".\n" + \
                                     "Honeybee won't overwrite the type so you may need to manually flip the surface."
                        print warningMsg
                        ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warningMsg)
                        
                    HBSurface.setType(surfaceType, isUserInput= True)
                except:
                    warningMsg = "You are using an old version of Honeybee_Honeybee! Update your files and try again."
                    print warningMsg
                    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warningMsg)
                    return
            
        
        # 1.2 assign boundary condition
        if EPBC!= None:
            # only ground, adiabatic and outdoors is valid
            validBC = ['ground', 'adiabatic', 'outdoors']
            if EPBC.lower() in validBC:
                try:
                    HBSurface.setBC(EPBC, isUserInput= True)
                    
                    # change type of surface if BC is set to ground
                    if EPBC.lower()== "ground":
                        HBSurface.setType(int(HBSurface.type) + 0.5, isUserInput= True)
                    
                    
                    if EPBC.lower()== "ground" or EPBC.lower()== "adiabatic":
                        HBSurface.setSunExposure('NoSun')
                        HBSurface.setWindExposure('NoWind')
                    
                    print "HBSurface boundary condition has been set to " + EPBC.upper()
                except:
                    warningMsg = "You are using an old version of Honeybee_Honeybee! Update your files and try again."
                    print warningMsg
                    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warningMsg)
                    return               
            else:
                print "HBSurface BOUNDARY CONDITION IS NOT VALID."
        
        # 1.3 assign construction for EnergyPlus
        if EPConstruction!=None:
            # if it is just the name of the material make sure it is already defined
            if len(EPConstruction.split("\n")) == 1:
                # if the material is not in the library add it to the library
                if not hb_EPObjectsAux.isEPConstruction(EPConstruction):
                    warningMsg = "Can't find " + EPConstruction + " in EP Construction Library.\n" + \
                                "Add the construction to the library and try again."
                    print warningMsg
                    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warningMsg)
                    return
            else:
                # it is a full string
                added, EPConstruction = hb_EPObjectsAux.addEPObjectToLib(EPConstruction, overwrite = True)

                if not added:
                    msg = name + " is not added to the project library!"
                    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, msg)
                    print msg
                    return
            
            try:
                HBSurface.setEPConstruction(EPConstruction)
                print "HBSurface construction has been set to " + EPConstruction
            except:
                warningMsg = "You are using an old version of Honeybee_Honeybee! Update your files and try again."
                print warningMsg
                ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warningMsg)
                return                 
            
        # 1.4 assign RAD Material
        if RADMaterial!=None:
            # if it is just the name of the material make sure it is already defined
            if len(RADMaterial.split(" ")) == 1:
                # if the material is not in the library add it to the library
                if RADMaterial not in sc.sticky ["honeybee_RADMaterialLib"].keys():
                    warningMsg = "Can't find " + RADMaterial + " in RAD Material Library.\n" + \
                                "Add the material to the library and try again."
                    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warningMsg)
                    return
                
                try:
                    HBSurface.setRADMaterial(RADMaterial)
                    print "HBSurface Radiance Material has been set to " + RADMaterial
                except Exception, e:
                    print e
                    warningMsg = "You are using an old version of Honeybee_Honeybee! Update your files and try again."
                    print warningMsg
                    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warningMsg)
                    return
                
                addedToLib = True
            else:
                
                # try to add the material to the library
                addedToLib, HBSurface.RadMaterial = hb_RADMaterialAUX.analyseRadMaterials(RADMaterial, True)
                
            if addedToLib==False:
                warningMsg = "Failed to add " + RADMaterial + " to the Library."
                ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warningMsg)
                return
            
        HBSurfaces.append(HBSurface)
    
    # add to the hive
    hb_hive = sc.sticky["honeybee_Hive"]()
    HBSurface  = hb_hive.addToHoneybeeHive(HBSurfaces, ghenv.Component.InstanceGuid.ToString() + str(uuid.uuid4()))
    
    return HBSurface
    
    
    

if _geometry != None:
    
    result= main(_geometry, srfName_, srfType_, EPBC_, _EPConstruction_, _RADMaterial_)
    
    if result!=-1:
        HBSurface = result
