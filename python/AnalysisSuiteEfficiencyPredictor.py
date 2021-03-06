
# -*- coding: utf-8 -*-

"""
    Created on Monday April 24
    
    @author: Brian L. Dorney
    """

#Imports
import sys, os
import numpy as np
import root_numpy as rp
#from scipy import interpolate

#Python Toolkit Imports
from AnalysisSuiteGainMap import *
from AnalysisSuiteClusterCharge import *
from AnalysisSuiteVFATNoise import *
from Utilities import *

#ROOT Imports
from ROOT import gROOT, TArrayD, TF1, TFile, TGraph, TGraph2D, TGraphErrors, TH2F, TRandom2

class AnalysisSuiteEfficiencyPredictor:

    __slots__ = ['DEBUG',
                 #'DICT_AVGEFF_READOUT',         #(Avg Eff, Std. Dev Eff)
                 'DICT_EFF_READOUT',            #Efficiency Pts by readout sector
                 'DICT_G_EFF_VS_HVPTS_RO',       #TGraphErrors by readout sector vs. HV
                 'DICT_G_EFF_VS_GAIN_RO',       #TGraphErrors by readout sector vs. Gain
                 'DICT_G_ANASLICE_VS_HVPTS_RO',
                 'DICT_H_CHON_VS_CLUSTPOS',
                 'DICT_H_CLUSTQ_VS_CLUSTPOS',
                 'DICT_H_NOISEQ_VS_CLUSTPOS',
                 'DICT_H_THRESH_VS_CLUSTPOS',
                 'DIR_CHARGE',
                 'DIR_MAP_EFF',
                 #'DIR_MAP_GAIN',
                 'LIST_HVPTS',
                 'NAME_DET_DUT',
                 'NAME_DET_CLUSTQ',
                 'NAME_DET_CLUSTSIZE',
                 'NUMSIMPTS_PER_RO',
                 'PARAMS_DET_DUT',
                 'SECTOR_IETA_CLUSTSIZENORM',
                 'SECTOR_IETA_QC5',
                 'SECTOR_IPHI_CLUSTSIZENORM',
                 'SECTOR_IPHI_QC5',
                 'ANA_UNI_GRANULARITY',
                 'PARAMS_GAIN_DET_DUT',
                 'PARAMS_GAIN_DET_CLUSTQ',
                 'PARAMS_GAIN_DET_CLUSTSIZE',
                 'FILE_CLUSTQ_MEAN',
                 'FILE_CLUSTQ_MPV',
                 'FILE_CLUSTQ_SIGMA',
                 'FILE_MAPPING_DUT',
                 'FILE_MAPPING_DUT_VFAT2DET',
                 'FILE_MIP_AVG_CLUST_SIZE',
                 'FILE_OUTPUT',
                 'FILE_QC5_RESP_UNI',
                 'FILE_SCURVE_DATA',
                 'TOBJ_NAME_FUNC_AVGCLUSTSIZE',
                 'ANASUITECLUSTQ',
                 'ANASUITEGAIN',
                 'ANASUITENOISE',
                 'FUNC_AVG_MIP_CLUSTSIZE'
                 ]

    #Here inputfilename should be a tab delimited file in the form of:
    #   field_name  value
    #
    #The field_name is not case sensitive but the value is case sensitive (as it may be a filepaths!)
    def __init__(self, inputfilename="config/configEffPredictor.cfg", debug=False):
        #Set the debug flag
        self.DEBUG  = debug

        #HV Points To Perform Calculations for
        self.LIST_HVPTS = []

        #Detector Names
        self.NAME_DET_DUT               = "Detector"
        self.NAME_DET_CLUSTQ            = "GE11-III-FIT-0001"
        self.NAME_DET_CLUSTSIZE         = "GE11-IV-CERN-0001"
        
        #Declare Detector Container
        self.PARAMS_DET_DUT             = PARAMS_DET()

        self.SECTOR_IETA_CLUSTSIZENORM  = 5
        self.SECTOR_IETA_QC5            = 4
        
        self.SECTOR_IPHI_CLUSTSIZENORM  = 2
        self.SECTOR_IPHI_QC5            = 2

        self.ANA_UNI_GRANULARITY	= 32

        #Declare Gain Containers
        self.PARAMS_GAIN_DET_DUT        = PARAMS_GAIN()
        self.PARAMS_GAIN_DET_CLUSTQ     = PARAMS_GAIN()
        self.PARAMS_GAIN_DET_CLUSTSIZE  = PARAMS_GAIN()

        #File Names
        self.FILE_CLUSTQ_MEAN           = "" #File having ordered triplet of (V_Drift, ClustSize, Mean) data
        self.FILE_CLUSTQ_MPV            = "" #As above but for MPV
        self.FILE_CLUSTQ_SIGMA          = "" #As above but for Sigma

        self.FILE_MAPPING_DUT           = "" #Mapping config file for detector under test
        self.FILE_MAPPING_DUT_VFAT2DET	= "" #Mapping config file for detectur under test which translates VFAT position to (ieta,iphi) coordinate
        
        self.FILE_MIP_AVG_CLUST_SIZE    = "" #File having a TF1 which is a fit of MIP <ClustSize> vs. Gain
        
        self.FILE_OUTPUT                = "" #Output filename to be created
        
        self.FILE_QC5_RESP_UNI          = "" #Framework output file
        self.FILE_SCURVE_DATA		= "" #TFile containing the scurveFitTree TTree with SCurve data
        
        #TObject Names
        self.TOBJ_NAME_FUNC_AVGCLUSTSIZE= ""
        
        #Load the input file and set all variables
        list_strLines = []
        with open(inputfilename) as inputFile:
            list_strLines = inputFile.readlines()
        
        inputFile.close()

        #strip new line character ('\n') from the file
        list_strLines = [x.strip() for x in list_strLines]

        if self.DEBUG:
            print "Field_Name\tValue"

        #Set Variables
        for iPos in range(0,len(list_strLines)):
            #Get this (field_name,value) pair
            strLine = list_strLines[iPos].split("\t")
           
            #Skip if commented (e.g. first character of first member is "#")
            if strLine[0][0] == "#":
                continue
            
            #Transform to upper case
            strLine[0] = strLine[0].upper()

            #Print (field_name, value) pair
            if self.DEBUG:
                print "{0}\t{1}".format(strLine[0],strLine[1])

            #Set values
            if strLine[0] == "FILE_FRAMEWORK_OUTPUT":
                #self.ANASUITEGAIN.openInputFile(strLine[1])
                self.FILE_QC5_RESP_UNI = strLine[1]
            elif strLine[0] == "FILE_CLUSTQ_MEAN":
                self.FILE_CLUSTQ_MEAN = strLine[1]
            elif strLine[0] == "FILE_CLUSTQ_MPV":
                self.FILE_CLUSTQ_MPV = strLine[1]
            elif strLine[0] == "FILE_CLUSTQ_SIGMA":
                self.FILE_CLUSTQ_SIGMA = strLine[1]
            elif strLine[0] == "FILE_CLUSTSIZE":
                self.FILE_MIP_AVG_CLUST_SIZE = strLine[1]
            elif strLine[0] == "FILE_OUTPUT":
                #self.FILE_OUTPUT = strLine[1]
                self.FILE_OUTPUT= TFile(strLine[1],"RECREATE","",1)
                self.DIR_CHARGE	= self.FILE_OUTPUT.mkdir("ChargeData")
                self.DIR_MAP_EFF= self.FILE_OUTPUT.mkdir("EffMaps")
                #self.DIR_MAP_GAIN=self.FILE_OUTPUT.mkdir("GainMaps")
            elif strLine[0] == "FILE_DUT_MAPPING_GEO":
                self.FILE_MAPPING_DUT = strLine[1]
            elif strLine[0] == "FILE_DUT_MAPPING_VFATPOS2IETAIPHI":
                self.FILE_MAPPING_DUT_VFAT2DET = strLine[1]
            elif strLine[0] == "FILE_DUT_SCURVEDATA":
                self.FILE_SCURVE_DATA = strLine[1]
            elif strLine[0] == "DUT_GAIN_P0":
                self.PARAMS_GAIN_DET_DUT.GAIN_CURVE_P0 = float(strLine[1])
            elif strLine[0] == "DUT_GAIN_P0_ERR":
                self.PARAMS_GAIN_DET_DUT.GAIN_CURVE_P0_ERR = float(strLine[1])
            elif strLine[0] == "DUT_GAIN_P1":
                self.PARAMS_GAIN_DET_DUT.GAIN_CURVE_P1 = float(strLine[1])
            elif strLine[0] == "DUT_GAIN_P1_ERR":
                self.PARAMS_GAIN_DET_DUT.GAIN_CURVE_P1_ERR = float(strLine[1])
            elif strLine[0] == "DUT_IETA_CLUST_SIZE_NORM":
                self.SECTOR_IETA_CLUSTSIZENORM = int(strLine[1])
            elif strLine[0] == "DUT_IETA_QC5_GAIN_CAL":
                self.SECTOR_IETA_QC5 = int(strLine[1])
            elif strLine[0] == "DUT_IPHI_CLUST_SIZE_NORM":
                self.SECTOR_IPHI_CLUSTSIZENORM = int(strLine[1])
            elif strLine[0] == "DUT_IPHI_QC5_GAIN_CAL":
                self.SECTOR_IPHI_QC5 = int(strLine[1])
            elif strLine[0] == "DUT_NUM_SIM_PTS_PER_RO":
                self.NUMSIMPTS_PER_RO = int(strLine[1])
            elif strLine[0] == "DUT_QC5_RESP_UNI_HVPT":
                self.PARAMS_DET_DUT.DET_IMON_QC5_RESP_UNI = float(strLine[1])
            elif strLine[0] == "DUT_SERIAL_NUMBER":
                self.NAME_DET_DUT = strLine[1]
            elif strLine[0] == "DUT_SLICE_GRANULARITY":
                self.ANA_UNI_GRANULARITY = int(strLine[1])
            elif strLine[0] == "DET_CLUSTQ_SERIAL_NUMBER":
                self.NAME_DET_CLUSTQ = strLine[1]
            elif strLine[0] == "DET_CLUSTQ_GAIN_P0":
                self.PARAMS_GAIN_DET_CLUSTQ.GAIN_CURVE_P0 = float(strLine[1])
            elif strLine[0] == "DET_CLUSTQ_GAIN_P0_ERR":
                self.PARAMS_GAIN_DET_CLUSTQ.GAIN_CURVE_P0_ERR = float(strLine[1])
            elif strLine[0] == "DET_CLUSTQ_GAIN_P1":
                self.PARAMS_GAIN_DET_CLUSTQ.GAIN_CURVE_P1 = float(strLine[1])
            elif strLine[0] == "DET_CLUSTQ_GAIN_P1_ERR":
                self.PARAMS_GAIN_DET_CLUSTQ.GAIN_CURVE_P1_ERR = float(strLine[1])
            elif strLine[0] == "DET_CLUSTSIZE_SERIAL_NUMBER":
                self.NAME_DET_CLUSTSIZE = strLine[1]
            elif strLine[0] == "DET_CLUSTSIZE_TF1_TNAME":
                self.TOBJ_NAME_FUNC_AVGCLUSTSIZE = strLine[1]
            elif strLine[0] == "EFF_HVPT_LIST":
                self.LIST_HVPTS = strLine[1].split(",")
            else:
                print "Input Field Name:"
                print strLine[0]
                print "Not recognized, please cross-check input file:"
                print inputfilename

        del list_strLines

        #Declare Cluster Charge Analysis Suite
        self.ANASUITECLUSTQ = AnalysisSuiteClusterCharge(file_out=self.FILE_OUTPUT,
                                                         params_gain=self.PARAMS_GAIN_DET_CLUSTQ,
                                                         calcGain=True,
                                                         debug=self.DEBUG)

        #Load the Landau Cluster Charge Data
        if self.DEBUG:
            print "Loading Landau Cluster Charge Data"
        
        if len(self.FILE_CLUSTQ_MEAN) == 0:
            print "Landau Cluster Charge Mean Filename not found, problem!"
        if len(self.FILE_CLUSTQ_MPV) == 0:
            print "Landau Cluster Charge MPV Filename not found, problem!"
        if len(self.FILE_CLUSTQ_SIGMA) == 0:
            print "Landau Cluster Charge Sigma Filename not found, problem!"

        self.ANASUITECLUSTQ.loadData(inputfilename_MEAN=self.FILE_CLUSTQ_MEAN,
                                     inputfilename_MPV=self.FILE_CLUSTQ_MPV,
                                     inputfilename_SIGMA=self.FILE_CLUSTQ_SIGMA)

        #Interpolate the Landau Cluster Charge Data
        if self.DEBUG:
            print "Interpolating Landau Cluster Charge Data"

        self.ANASUITECLUSTQ.interpolateData()

        #Declare Gain Map Analysis Suite
        self.PARAMS_DET_DUT.DETPOS_IETA = self.SECTOR_IETA_QC5
        self.PARAMS_DET_DUT.DETPOS_IPHI = self.SECTOR_IPHI_QC5

        if self.DEBUG:
            print "Loading Mapping"

        self.PARAMS_DET_DUT.loadMapping(self.FILE_MAPPING_DUT, self.DEBUG)

        self.ANASUITEGAIN   = AnalysisSuiteGainMap(file_out=self.FILE_OUTPUT,
                                                   inputfilename=self.FILE_QC5_RESP_UNI,
                                                   #outputfilename=self.FILE_OUTPUT,
                                                   #outputfileoption="RECREATE",
                                                   params_gain=self.PARAMS_GAIN_DET_DUT,
                                                   params_det=self.PARAMS_DET_DUT,
                                                   debug=self.DEBUG)

        #Make the dictionary for OBS vs cluster position histograms
        self.DICT_H_CHON_VS_CLUSTPOS = {}
        self.DICT_H_CLUSTQ_VS_CLUSTPOS = {}
        self.DICT_H_NOISEQ_VS_CLUSTPOS = {}
        self.DICT_H_THRESH_VS_CLUSTPOS = {}
        for etaSector in self.PARAMS_DET_DUT.LIST_DET_GEO_PARAMS:
            iNumBinsX	= self.ANA_UNI_GRANULARITY * etaSector.NBCONNECT
            xLower	= -0.5 * etaSector.SECTSIZE
            xUpper	= 0.5 * etaSector.SECTSIZE

            #Channels On vs cluster position histograms
            h_chOn_vs_clustPos = TH2F("h_iEta{0}_chOn_vs_clustPos".format(etaSector.IETA),
                                      "",iNumBinsX,xLower,xUpper,125,0,1.25)
            h_chOn_vs_clustPos.SetDirectory(gROOT)
            self.DICT_H_CHON_VS_CLUSTPOS[etaSector.SECTPOS]=h_chOn_vs_clustPos

            #Cluster charge vs cluster position histograms
            h_clustQ_vs_clustPos = TH2F("h_iEta{0}_clustQ_vs_clustPos".format(etaSector.IETA),
                                        "",iNumBinsX,xLower,xUpper,400,0,100)
            h_clustQ_vs_clustPos.SetDirectory(gROOT)
            self.DICT_H_CLUSTQ_VS_CLUSTPOS[etaSector.SECTPOS]=h_clustQ_vs_clustPos

            #Noise vs cluster position histograms
            h_noiseQ_vs_clustPos = TH2F("h_iEta{0}_noiseQ_vs_clustPos".format(etaSector.IETA),
                                        "",iNumBinsX,xLower,xUpper,100,0,10)
            h_noiseQ_vs_clustPos.SetDirectory(gROOT)
            self.DICT_H_NOISEQ_VS_CLUSTPOS[etaSector.SECTPOS]=h_noiseQ_vs_clustPos

            #Thresh vs cluster position histograms
            h_thresh_vs_clustPos = TH2F("h_iEta{0}_thresh_vs_clustPos".format(etaSector.IETA),
                                        "",iNumBinsX,xLower,xUpper,100,0,10)
            h_thresh_vs_clustPos.SetDirectory(gROOT)
            self.DICT_H_THRESH_VS_CLUSTPOS[etaSector.SECTPOS]=h_thresh_vs_clustPos

        #Load the MIP average cluster size vs. gain formulat
        fileMIPAvgClustSize = TFile(self.FILE_MIP_AVG_CLUST_SIZE, "READ","", 1)

        if self.DEBUG:
            print "Loading function for MIP <Clust Size> vs. Gain"

        self.FUNC_AVG_MIP_CLUSTSIZE = fileMIPAvgClustSize.Get(self.TOBJ_NAME_FUNC_AVGCLUSTSIZE)

        #Initialize the VFAT noise analysis suite
        self.ANASUITENOISE = AnalysisSuiteVFATNoise(detector=self.PARAMS_DET_DUT,
                                                    inputMappingFile=self.FILE_MAPPING_DUT_VFAT2DET,
                                                    inputSCurveFile=self.FILE_SCURVE_DATA,
                                                    convert2fC=True,
                                                    debug=self.DEBUG)

        #Make the Dictionary for Efficiency by Readout Sector
        #Here each value is a tuple average, std. dev, num pts
        self.DICT_EFF_READOUT = {key:[] for key in self.ANASUITENOISE.DICT_MAPPING}
        #self.DICT_AVGEFF_READOUT = {}
        
        #Make the Dictionary for Efficiency TGraphErrs by Readout Sector
        self.DICT_G_EFF_VS_HVPTS_RO = {}
        self.DICT_G_ANASLICE_VS_HVPTS_RO = {}
        self.DICT_G_EFF_VS_GAIN_RO = {}
        for key in self.DICT_EFF_READOUT:
            #Avg Eff +/- Std Dev Eff vs. HVPts
            g_Eff_vs_HVPts = TGraphErrors(len(self.LIST_HVPTS))
            g_Eff_vs_HVPts.SetName("g_iEta{0}iPhi{1}_avgEff_vs_HVPts".format( int(key[0]), int(key[1]) ) )
            g_Eff_vs_HVPts.SetTitle("")
            g_Eff_vs_HVPts.SetMarkerStyle(21)
            self.DICT_G_EFF_VS_HVPTS_RO[key]=g_Eff_vs_HVPts

            #Avg Eff +/- Std Dev Eff vs. HVPts
            g_Eff_vs_Gain = TGraphErrors(len(self.LIST_HVPTS))
            g_Eff_vs_Gain.SetName("g_iEta{0}iPhi{1}_avgEff_vs_Gain".format( int(key[0]), int(key[1]) ) )
            g_Eff_vs_Gain.SetTitle("")
            g_Eff_vs_Gain.SetMarkerStyle(21)
            self.DICT_G_EFF_VS_GAIN_RO[key]=g_Eff_vs_Gain

            #Number of Slices used for analysis (here a slice is counted if the landau charge interpolation was valid)
            g_AnaSlices_vs_HVPts = TGraph(len(self.LIST_HVPTS))
            g_AnaSlices_vs_HVPts.SetName("g_iEta{0}iPhi{1}_anaSlices_vs_HVPts".format( int(key[0]), int(key[1]) ) )
            g_AnaSlices_vs_HVPts.SetTitle("")
            g_AnaSlices_vs_HVPts.SetMarkerStyle(21)
            self.DICT_G_ANASLICE_VS_HVPTS_RO[key]=g_AnaSlices_vs_HVPts
	
        #Tell user initialization completed successfully
        #if self.DEBUG:
        print "AnalysisSuiteEfficiencyPredictor::init() - Initialization completed successfully"

        return

    def loadGainCurveDetClustQ(self, strInputFileName="figures/GE11-III-FIT-0001/GE11-III-FIT-0001_QC5_EffGain_VDrift.root", strTObjName="fit_GE11-III-FIT-0001_EffGain_42"):
        #Load the input file
        inputFile = TFile(str(strInputFileName),"READ","", 1)

        #Get the TF1 Object
        func_Gain = inputFile.Get(strTObjName)

        #Set the parameters
        self.PARAMS_GAIN_DET_CLUSTSIZE.GAIN_CURVE_P0       = func_Gain.GetParameter(0)
        self.PARAMS_GAIN_DET_CLUSTSIZE.GAIN_CURVE_P0_ERR   = func_Gain.GetParError(0)
        self.PARAMS_GAIN_DET_CLUSTSIZE.GAIN_CURVE_P1       = func_Gain.GetParameter(1)
        self.PARAMS_GAIN_DET_CLUSTSIZE.GAIN_CURVE_P1_ERR   = func_Gain.GetParError(1)

        #Close the input file
        inputFile.Close() #This might fuck it

        return

    def loadGainCurveDetClustSize(self, strInputFileName="figures/figures/GE11-IV-CERN-0001/GE11-IV-CERN-0001_GIF_QC5_EffGain_Imon.root", strTObjName="fit_GE11-IV-CERN-0001_GIF_EffGain_52"):
        #Load the input file
        inputFile = TFile(str(strInputFileName),"READ","", 1)
        
        #Get the TF1 Object
        func_Gain = inputFile.Get(strTObjName)
        
        #Set the parameters
        self.PARAMS_GAIN_DET_CLUSTSIZE.GAIN_CURVE_P0       = func_Gain.GetParameter(0)
        self.PARAMS_GAIN_DET_CLUSTSIZE.GAIN_CURVE_P0_ERR   = func_Gain.GetParError(0)
        self.PARAMS_GAIN_DET_CLUSTSIZE.GAIN_CURVE_P1       = func_Gain.GetParameter(1)
        self.PARAMS_GAIN_DET_CLUSTSIZE.GAIN_CURVE_P1_ERR   = func_Gain.GetParError(1)
        
        #Close the input file
        inputFile.Close() #This might fuck it
    
        return

    #Calculate the gain map from the original QC5_Resp_Uni measurement
    def calcGainMap(self):
        #Make sure the right (ieta,iphi) sector is set for the gain map calculation
        self.ANASUITEGAIN.DETECTOR.DETPOS_IETA = self.SECTOR_IETA_QC5
        self.ANASUITEGAIN.DETECTOR.DETPOS_IPHI = self.SECTOR_IPHI_QC5
        
        #Average Readout Sector Fitted ADC Pk Positions
        if self.DEBUG:
            print "Starting Gain Map calculation for: {0}".format(self.NAME_DET_DUT)
            print "averaging ADC PkPositions in sector: ({0},{1})".format(self.SECTOR_IETA_QC5,self.SECTOR_IPHI_QC5)
        
        self.ANASUITEGAIN.avgROSectorADCPkPos()
        
        #Compute lambda
        if self.DEBUG:
            print "Computing lambda"
        
        self.ANASUITEGAIN.calcROSectorLambda()

        #Compute the Gain Map
        if self.DEBUG:
            print "Calculating Gain Map"
        
        self.ANASUITEGAIN.calcGainMap(self.NAME_DET_DUT)

        return
            
    #Compute the normalized average cluster size map from the original QC5_Resp_Uni measurement
    def calcNormAvgClustSizeMap(self):
        #Make sure right (ieta,iphi) sector set for normalize avg clust size map calculation
        #This should map with the sector for which the MIP cluster size vs. gain data is provided for
        self.ANASUITEGAIN.DETECTOR.DETPOS_IETA = self.SECTOR_IETA_CLUSTSIZENORM
        self.ANASUITEGAIN.DETECTOR.DETPOS_IPHI = self.SECTOR_IPHI_CLUSTSIZENORM

        #Average Readout Sector Fitted ADC Pk Positions
        if self.DEBUG:
            print "Starting Normalized Average Cluster Size Map calculation for: " + self.NAME_DET_DUT
            print "Averaging <Cluster Size> in sector: ({0},{1})".format(self.SECTOR_IETA_CLUSTSIZENORM,self.SECTOR_IPHI_CLUSTSIZENORM)
    
        self.ANASUITEGAIN.avgROSectorAvgClustSize()

        #Compute Normalized Average Cluster Size Map
        if self.DEBUG:
            print "Calculating Normalized Average Cluster Size Map"

        self.ANASUITEGAIN.calcClusterSizeMap(self.NAME_DET_DUT)
    
        return

    #Predict the efficiency maps and make summary curves for *all* points
    def predictEffCurves(self):
        #Calculate the original gain map of the detector, needed to determine gain at fHVOrGain
        self.calcGainMap()

        #Calculate the original normalized cluster map of the detector
        self.calcNormAvgClustSizeMap()

        #Simulate the Efficiency Map for *each* HV point
        for iHVPt in range(0,len(self.LIST_HVPTS)):
            array_EffData = self.predictEffHVPt(float(self.LIST_HVPTS[iHVPt]), self.NUMSIMPTS_PER_RO)
            self.calcROSectorEff(array_EffData, float(self.LIST_HVPTS[iHVPt]), iHVPt)

        #Load the output file
        #file_Out = TFile(self.FILE_OUTPUT,"UPDATE","",1)
        #dir_Summary = file_Out.mkdir("Summary")
        dir_Summary = self.FILE_OUTPUT.mkdir("Summary")
        dir_EffCurves = dir_Summary.mkdir("EffCurves")
        dir_AnaSlices = dir_Summary.mkdir("AnaSlices")

        #Store the output curves
        #dir_Summary.cd()
        for etaSector in self.PARAMS_DET_DUT.LIST_DET_GEO_PARAMS:
            for iPhi in range (0, etaSector.NBCONNECT):
                dir_EffCurves.cd()
                self.DICT_G_EFF_VS_HVPTS_RO[(etaSector.IETA,iPhi+1)].Write()
                self.DICT_G_EFF_VS_GAIN_RO[(etaSector.IETA,iPhi+1)].Write()

                dir_AnaSlices.cd()
                self.DICT_G_ANASLICE_VS_HVPTS_RO[(etaSector.IETA,iPhi+1)].Write()

        #Close the Output File
        #file_Out.Close()

        return

    #For each HV Point, predict the efficiency map of the detector
    def predictEffHVPt(self, fHVPt, iNEvtPerPt=100):
        #Calculate the original gain map of the detector, needed to determine gain at fHVOrGain
        #self.calcGainMap()

        #Get the gain map at fHVPt
        if self.DEBUG:
            print "Calculating Gain Map at Input HV Pt: {0}".format(fHVPt)
        
        g2D_Map_Gain_HVPt = self.ANASUITEGAIN.calcGainMapHV(self.NAME_DET_DUT, fHVPt)

        #Calculate the original normalized cluster map of the detector
        #self.calcNormAvgClustSizeMap()

        #Now interesting problem N_pts in g2D_Map_Gain_HVPt <= N_pts in self.ANASUITEGAIN.G2D_MAP_AVG_CLUST_SIZE_NORM
        #We can make some numpy arrays
        #Then the (clustPos,y) members from G2D_MAP_AVG_CLUST_SIZE_NORM that don't appear in g2D_Map_Gain_HVPt
        
        #Get the gain and normalized average clustersize data
        data_Gain        = getDataTGraph2D(g2D_Map_Gain_HVPt)
        data_NormAvgCS   = getDataTGraph2D(self.ANASUITEGAIN.G2D_MAP_AVG_CLUST_SIZE_NORM)

        #Close TFiles that have been opened by self.ANASUITEGAIN
        #self.ANASUITEGAIN.closeTFiles()
	
        #Create a dictionary where the coordinate point (x,y) is mapped to the (gain, Norm <CS>)
        dict_Coords_GainAndNormAvgCS = {(idx[0],idx[1]):[idx[2]] for idx in data_Gain}
        for idx in data_NormAvgCS:
            if (idx[0],idx[1]) in dict_Coords_GainAndNormAvgCS:
            	dict_Coords_GainAndNormAvgCS[(idx[0],idx[1])].append(idx[2])

        #Create the Efficiency Plots
        g2D_Map_Eff_Sig_HVPt = TGraph2D()
        g2D_Map_Eff_Noise_HVPt = TGraph2D()

        g2D_Map_Eff_Sig_HVPt.SetName("g2D_{0}_EffSig_AllEta_{1}".format(self.NAME_DET_DUT,fHVPt))
        g2D_Map_Eff_Noise_HVPt.SetName("g2D_{0}_EffNoise_AllEta_{1}".format(self.NAME_DET_DUT,fHVPt))

        #Create the random number generator
        rndm = TRandom2(0)

        #Loop over all points of the detector
        iNumPt = 0
        iNumPt_Skipped = 0
        for coordPt in dict_Coords_GainAndNormAvgCS:
            #Get Coordinate Info
            coordPt_iEtaiPhi	= self.PARAMS_DET_DUT.getiEtaiPhIndex(coordPt[0],coordPt[1])
            coordPt_iStripRange	= self.PARAMS_DET_DUT.LIST_DET_GEO_PARAMS[coordPt_iEtaiPhi[0]-1].getStripRange(coordPt[0], self.ANA_UNI_GRANULARITY)
            coordPt_iThisSlice	= self.PARAMS_DET_DUT.LIST_DET_GEO_PARAMS[coordPt_iEtaiPhi[0]-1].getSliceIdx(coordPt[0], self.ANA_UNI_GRANULARITY)

            #Get the gain and MIP cluster size
            fGain 	= dict_Coords_GainAndNormAvgCS[coordPt][0]
            fNormAvgCS	= dict_Coords_GainAndNormAvgCS[coordPt][1]
            fMIPAvgCS	= fNormAvgCS * self.FUNC_AVG_MIP_CLUSTSIZE.Eval(fGain)
            
            #Get the Landau Parameters
            fLandauMean	= self.ANASUITECLUSTQ.getInterpolatedMean(fMIPAvgCS, fGain)
            #fLandauMPV	= self.ANASUITECLUSTQ.getInterpolatedMPV(fMIPAvgCS, fGain)
            fLandauSigma= self.ANASUITECLUSTQ.getInterpolatedSigma(fMIPAvgCS, fGain)

            #Get Threshold and Mask
            fThresh 	= self.ANASUITENOISE.getValByEtaPhiThreshAvg(coordPt_iEtaiPhi[0],coordPt_iEtaiPhi[1],coordPt_iStripRange[0],coordPt_iStripRange[1])
            fMask	= self.ANASUITENOISE.getValByEtaPhiSliceMaskAvg(coordPt_iEtaiPhi[0],coordPt_iEtaiPhi[1],coordPt_iStripRange[0],coordPt_iStripRange[1])

            self.DICT_H_THRESH_VS_CLUSTPOS[coordPt[1]].Fill(coordPt[0], fThresh)
            self.DICT_H_CHON_VS_CLUSTPOS[coordPt[1]].Fill(coordPt[0], fMask)
            
            #Skip if the Landua parameters outside interpolated data
            if fLandauMean < 0 or fLandauSigma < 0:
                print "================================================================"
                print "Bad Signal Charge Parameters"
                print "For HV = {0}: Skipping (ieta,iphi,islice) = ({1},{2},{3}); strips = [{4},{5}]; coords = ({6},{7})".format(
                        fHVPt,
                        coordPt_iEtaiPhi[0],
                        coordPt_iEtaiPhi[1],
                        coordPt_iThisSlice,
                        coordPt_iStripRange[0],
                        coordPt_iStripRange[1],
                        coordPt[0],                                                                                                                   
                        coordPt[1])
                print "================================================================"
                iNumPt_Skipped+=1
                continue

            #Begin ToyMC
            if self.DEBUG:
                print "For HV = {0}: Simulating (ieta,iphi,islice) = ({1},{2},{3}); strips = [{4},{5}]; coords = ({6},{7})".format(
                        fHVPt,
                        coordPt_iEtaiPhi[0],
                        coordPt_iEtaiPhi[1],
                        coordPt_iThisSlice,
                        coordPt_iStripRange[0],
                        coordPt_iStripRange[1],
                        coordPt[0],
                        coordPt[1])

            fNumSig	= 0. #Number of Signal Events; Q_Sig > Q_Noise & Q_Sig > Thresh
            fNumFake	= 0. #Number of Noise Events; Q_Noise >= Q_Sig & Q_Noise > Thresh
            fNumMiss	= 0. #Number of Missed Events; Thresh > Q_Sig & Thresh > Q_Noise
            for evt in range(0,iNEvtPerPt):
                fCharge_Sig = rndm.Landau(fLandauMean, fLandauSigma)
                fCharge_Noise = rndm.Gaus(self.ANASUITENOISE.getValByEtaPhiNoiseAvg(coordPt_iEtaiPhi[0],
                                                                                    coordPt_iEtaiPhi[1],
                                                                                    coordPt_iStripRange[0],
                                                                                    coordPt_iStripRange[1]),
                                          self.ANASUITENOISE.getValByEtaPhiNoiseStdDev(coordPt_iEtaiPhi[0],
                                                                                       coordPt_iEtaiPhi[1],
                                                                                       coordPt_iStripRange[0],
                                                                                       coordPt_iStripRange[1]) )

                #Store the charges
                self.DICT_H_CLUSTQ_VS_CLUSTPOS[coordPt[1]].Fill(coordPt[0], fCharge_Sig)
                self.DICT_H_NOISEQ_VS_CLUSTPOS[coordPt[1]].Fill(coordPt[0], fCharge_Noise)

                #Consider cases
                if fCharge_Sig > fCharge_Noise and fCharge_Sig > fThresh:       fNumSig+=1.
                elif fCharge_Noise >= fCharge_Sig and fCharge_Noise > fThresh:	fNumFake+=1.
                elif fThresh > fCharge_Sig and fThresh > fCharge_Noise:         fNumMiss+=1.

            #Store the results
            g2D_Map_Eff_Sig_HVPt.SetPoint(iNumPt, coordPt[0], coordPt[1], fMask * (fNumSig+fNumFake) / iNEvtPerPt)
            g2D_Map_Eff_Noise_HVPt.SetPoint(iNumPt, coordPt[0], coordPt[1], fMask * (fNumFake) / iNEvtPerPt)

            #Increment counter
            iNumPt+=1

        #Open Output TFile (was opened already by self.ANASUITEGAIN)
        #file_Out = TFile(self.FILE_OUTPUT,"UPDATE","",1)

        #Store output histograms - Charge
        #file_Out.cd()
        dir_Charge = self.DIR_CHARGE.mkdir("HVPt{0}".format(fHVPt))
        dir_Signal = dir_Charge.mkdir("Signal")
        dir_Noise = dir_Charge.mkdir("Noise")
        dir_Thresh = dir_Charge.mkdir("Thresh")
        dir_ChOn = dir_Charge.mkdir("ChannelsOn")
        coords_y = np.unique(data_Gain[:,1])
        #for histo in self.DICT_H_CLUSTQ_VS_CLUSTPOS:
        for idx in coords_y:
            dir_Signal.cd()
            self.DICT_H_CLUSTQ_VS_CLUSTPOS[idx].Write()
            
            dir_Noise.cd()
            self.DICT_H_NOISEQ_VS_CLUSTPOS[idx].Write()

            dir_Thresh.cd()
            self.DICT_H_THRESH_VS_CLUSTPOS[idx].Write()

            dir_ChOn.cd()
            self.DICT_H_CHON_VS_CLUSTPOS[idx].Write()	    

        #Draw the output efficiency Maps
        canv_Eff_Sig_HVPt = TCanvas("canv_{0}_EffSig_AllEta_{1}".format(self.NAME_DET_DUT,fHVPt),"Signal Eff Map for HVPt = {0}".format(fHVPt), 600,600)	
        g2D_Map_Eff_Sig_HVPt.Draw("COLZ")

        canv_Eff_Noise_HVPt = TCanvas("canv_{0}_EffNoise_AllEta_{1}".format(self.NAME_DET_DUT,fHVPt),"Noise Eff Map for HVPt = {0}".format(fHVPt), 600,600)	
        g2D_Map_Eff_Noise_HVPt.Draw("COLZ")

        #Store Output Efficiency Maps
        #dir_EffMap = file_Out.mkdir("EffMap_HVPt{0}".format(fHVPt))
        dir_EffMap = self.DIR_MAP_EFF.mkdir("HVPt{0}".format(fHVPt))
        dir_EffMap.cd()
        canv_Eff_Sig_HVPt.Write()
        g2D_Map_Eff_Sig_HVPt.Write()
        canv_Eff_Noise_HVPt.Write()
        g2D_Map_Eff_Noise_HVPt.Write()

        #Calculate the avg eff by readout sector
        #self.calcROSectorEff(getDataTGraph2D(g2D_Map_Eff_Sig_HVPt))

        #Store the efficiency map as an array
        array_EffData = getDataTGraph2D(g2D_Map_Eff_Sig_HVPt)

        #Close the Output File
        #file_Out.Close()

        print "For HV Pt {0}, Total Number of Skipped Slices = {1}".format(fHVPt, iNumPt_Skipped)

        return array_EffData

    #Calculate the efficiency of a given readout sector
    def calcROSectorEff(self, array_EffData, fHVPt, iDataPt):
        #Loop Over all the data poitns and assign them to a readout sector
        for dataPt in array_EffData:
            #if tuple_iEtaiPhi == (8,3): print dataPt[0], dataPt[1], dataPt[2]
            
            tuple_iEtaiPhi = self.PARAMS_DET_DUT.getiEtaiPhIndex(dataPt[0], dataPt[1])
            self.DICT_EFF_READOUT[tuple_iEtaiPhi].append(dataPt[2])

        #Store the (Avg Eff +/- Std Dev Eff, fHVPt) in the plots defined for each graph in
        for key in self.DICT_EFF_READOUT:
            #if key == (8,3): print np.mean(self.DICT_EFF_READOUT[key] ), np.std(self.DICT_EFF_READOUT[key] )

            fEffVal     = np.mean(self.DICT_EFF_READOUT[key])
            #fEffVal_Err = np.std(self.DICT_EFF_READOUT[key] )
            fEffVal_Err = np.sqrt( fEffVal * (1. - fEffVal) / self.NUMSIMPTS_PER_RO )

            self.DICT_G_EFF_VS_HVPTS_RO[key].SetPoint( iDataPt, fHVPt, fEffVal )
            self.DICT_G_EFF_VS_HVPTS_RO[key].SetPointError( iDataPt, 0, fEffVal_Err )

            self.DICT_G_EFF_VS_GAIN_RO[key].SetPoint( iDataPt, self.PARAMS_GAIN_DET_DUT.calcGain(fHVPt), fEffVal )
            self.DICT_G_EFF_VS_GAIN_RO[key].SetPointError( iDataPt, self.PARAMS_GAIN_DET_DUT.calcGainErr(fHVPt), fEffVal_Err )

            self.DICT_G_ANASLICE_VS_HVPTS_RO[key].SetPoint( iDataPt, fHVPt, len(self.DICT_EFF_READOUT[key]) )

            #Wipe the efficiency data before the next HV Pt
            self.DICT_EFF_READOUT[key]=[]

        return
