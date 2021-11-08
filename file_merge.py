# -*- coding:utf-8 -*-
# @Time : 2021/11/8 7:20 下午
# @Author: tangzhetim
# @File : file_merge.py
import pandas as pd
f1 = pd.read_csv('trainingData2_fake.csv')
f2 = pd.read_csv('/Users/tangzhe/GitHub/IndoorLoc_a_test/data_silce/building0.csv')
f2.loc[:,"FLOOR"] *= 3
file = [f1,f2]
train = pd.concat(file)
train.to_csv("trainingData2" + ".csv", index=0, sep=',')
