//
//  Visualizer.cpp
//  
//
//  Created by Brian L Dorney on 10/09/16.
//
//

#include "Visualizer.h"

using std::string;

using namespace QualityControl::Uniformity;

//Default Constructor
Visualizer::Visualizer(){
    m_bSaveCanvases = false;
}

//Saves inputCanv as a *.png file
//The file is placed in the working directory
//The name of the file is the TName of the canvas
void Visualizer::save2png(TCanvas & inputCanvas){
    //Variable Declaration
    string strName = inputCanvas.GetName();
    
    inputCanvas.SaveAs( ( strName + ".pdf" ).c_str(), "RECREATE" );
    inputCanvas.SaveAs( ( strName + ".png" ).c_str(), "RECREATE" );
    
    return;
} //End VisualizeUniformity::save2png()

//Get a TPad sized for an iEta Grid
TPad * Visualizer::getPadEta(int iEta, int iNumEta){
    //Variable Declaration
    float fXPad_Low, fXPad_High;
    float fYPad_Low, fYPad_High;
    
    //Determine the Pad Coordinates
    if (iEta % 2 != 0){ //Case: iEta is Odd
        fXPad_Low   = 0.02;
        fXPad_High  = 0.48;
    } //End Case: iEta is Odd
    else{ //Case: iEta is Even
        fXPad_Low   = 0.52;
        fXPad_High  = 0.98;
    } //End Case: iEta is Even
    
    //Determine the Pad Y-Coordinates (Y=0 is at the top of the pad!)
    fYPad_Low   = 1. - (1. / (0.5 * iNumEta) ) * ( std::ceil(iEta/2.) - 1);
    fYPad_High  = 1. - (1. / (0.5 * iNumEta) ) * ( std::ceil(iEta/2.) );
    
    //Initialize the Pad
    TPad *ret_pad = new TPad( "tempPad" ,"",fXPad_Low,fYPad_Low,fXPad_High,fYPad_High,kWhite);
    
    return ret_pad;
} //End getPadEta()

//Get a TPad sized for an iPhi Grid
TPad * Visualizer::getPadPhi(int iEta, int iNumEta, int iPhi, int iNumPhi){
    //Variable Declaration
    float fXPad_Low, fXPad_High;
    float fYPad_Low, fYPad_High;
    
    //Determine the Pad X-Coordinates
    fXPad_Low  = ( (0.96 * (iPhi - 1.0 ) ) + 0.02 ) / iNumPhi;
    fXPad_High = ( (0.96 * (iPhi ) ) - 0.02 ) / iNumPhi;
    
    //Determine the Pad Y-Coordinates (Y=0 is at the top of the pad!)
    //fYPad_Low   = 1. - (1. / (0.5 * iNumEta) ) * ( std::ceil(iEta/2.) - 1);
    fYPad_Low   = 1. - (1. / (iNumEta) ) * ( iEta - 1);
    //fYPad_High  = 1. - (1. / (0.5 * iNumEta) ) * ( std::ceil(iEta/2.) );
    fYPad_High  = 1. - (1. / (iNumEta) ) * ( iEta );
    
    //Initialize the Pad
    TPad *ret_pad = new TPad( "tempPad" ,"",fXPad_Low,fYPad_Low,fXPad_High,fYPad_High,kWhite);
    
    return ret_pad;
} //End getPadEta()
