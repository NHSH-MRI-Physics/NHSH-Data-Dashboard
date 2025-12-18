
import os
import urllib.request
import numpy as np

def GetExcludedSlices(type):
    type = type.lower()
    urllib.request.urlretrieve("https://github.com/NHSH-MRI-Physics/DailyQA/raw/refs/heads/main/DQA_Scripts/SlicesToExclude.txt", "SlicesToExclude.txt")
    f = open(os.path.join("SlicesToExclude.txt"))
    Slices={}
    for line in f:
        if (line.split(",")[0]==type):
            ExcludedSlices = []
            Slices[line.split(",")[1]]= ExcludedSlices
            for slice in line.split(",")[2:]:
                Slices[line.split(",")[1]].append(int(slice)-1)
    f.close()
    return Slices


def GetThresholds(type):
    type = type.lower()
    urllib.request.urlretrieve("https://github.com/NHSH-MRI-Physics/DailyQA/raw/refs/heads/main/DQA_Scripts/Thresholds.txt", "Thresholds.txt")
    path = os.path.join("Thresholds.txt")
    f = open(path)

    Threshes={}
    for line in f:
        if (line.split(",")[0]==type):
            Threshes[line.split(",")[1]]= float(line.split(",")[2])
    f.close()
    return Threshes

def DidQAPassV2(Result,thresh=None, GetStats=False):
    urllib.request.urlretrieve("https://github.com/NHSH-MRI-Physics/DailyQA/raw/refs/heads/main/BaselineData/Head/ROI_Head_Baseline.npy", "Head_baseline.npy")
    urllib.request.urlretrieve("https://github.com/NHSH-MRI-Physics/DailyQA/raw/refs/heads/main/BaselineData/Body/Global_Body_Baseline.npy", "Body_baseline.npy")
    urllib.request.urlretrieve("https://github.com/NHSH-MRI-Physics/DailyQA/raw/refs/heads/main/BaselineData/Spine/ROI_Spine_Baseline.npy", "Spine_baseline.npy")

    QAType = Result[2]
    SNR = Result[0]
    ROIResults = Result[1]
    Sequence = Result[3]

    Threshold = GetThresholds(QAType)

    SlicesToBeRejected=[]
    if Sequence in GetExcludedSlices(QAType).keys():
        SlicesToBeRejected=GetExcludedSlices(QAType)[Sequence]

    dir_path = os.path.dirname(os.path.realpath(__file__))

    if QAType=="Head":
        ROIBaseline = np.load(os.path.join(dir_path,"..","BaselineData","Head","ROI_Head_Baseline.npy"),allow_pickle=True).item()[Sequence]

    if QAType=="Body":
        ROIBaseline = np.load(os.path.join(dir_path,"..","BaselineData","Body","ROI_Body_Baseline.npy"),allow_pickle=True).item()[Sequence]

    if QAType=="Spine":
        ROIBaseline = np.load(os.path.join(dir_path,"..","BaselineData","Spine","ROI_Spine_Baseline.npy"),allow_pickle=True).item()[Sequence]
    
    

    FailMessage=""
    NumberOfSlicesInSeq = len(ROIResults["M1"])
    SNR_Rel_Results = []
    for i in range(NumberOfSlicesInSeq):
        SNR_Rel_Results.append({"M1":None,"M2":None,"M3":None,"M4":None,"M5":None})
    ROIS = list(ROIBaseline.keys())
    for ROI in ROIS:
        for Slice in range(NumberOfSlicesInSeq):
            if Slice not in SlicesToBeRejected:
                RelSNR = ROIResults[ROI][Slice]/ROIBaseline[ROI][Slice][0]
                SNR_Rel_Results[Slice][ROI] = [RelSNR,True]
                if (RelSNR <= Threshold[Sequence]):
                    FailMessage+="ROI " + ROI + " on slice " + str(Slice+1) + " SNR Failed on "+ QAType +" QA Seq: " + Sequence + "  Result (%):" + str(round(RelSNR,4)) + "   Threshold:" + str(round(Threshold[Sequence],4)) +"\n"
                    SNR_Rel_Results[Slice][ROI][1] = False
                    
    if GetStats == True:
        if FailMessage=="":
            return True,FailMessage,SNR_Rel_Results
        else:
            return False,FailMessage,SNR_Rel_Results
    else:
        if FailMessage=="":
            return True,FailMessage
        else:
            return False,FailMessage