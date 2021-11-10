# -*- coding:utf-8 -*-
# @Time : 2021/11/9 7:23 下午
# @Author: tangzhetim
# @File : file_merge_diff_building.py
import pandas as pd
f1 = pd.read_csv('/Users/tangzhe/Phd/IndoorLoc/indoor-localization-gp/can405_indoor_localization-master/data/UJIIndoorLoc/validationData2_building0.csv')
f2 = pd.read_csv('/Users/tangzhe/Phd/IndoorLoc/indoor-localization-gp/can405_indoor_localization-master/data/UJIIndoorLoc/validationData2_building1.csv')
f1.loc[:,"FLOOR"] *= 3
f2.loc[:,"FLOOR"] *= 3
file = [f1,f2]
train = pd.concat(file)
train.to_csv("validationData2_building01" + ".csv", index=0, sep=',')