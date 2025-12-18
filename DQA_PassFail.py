
import os
def GetThresholds(type):
    type = type.lower()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(dir_path,"..","DQA_Scripts","Thresholds.txt")
    f = open(path)

    Threshes={}
    for line in f:
        if (line.split(",")[0]==type):
            Threshes[line.split(",")[1]]= float(line.split(",")[2])
    f.close()
    return Threshes