"""
Author： tangzhetim
This file is used to test different kernel functions, mainly implemented with RBF and Matern52.
The problem still to be solved is the sampling logic, compared with the original file,
fixed the drawing function and the file reading part of the problem,
and realized the data generation of the whole building.

"""

import os
import GPy
import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
import pickle as pk
import sklearn.preprocessing


def increase_pred_input_nd(num, df_lim: pd.DataFrame, data_set: int):
    """generate input value to prediction, which base on uniform random

    Args:
        num (int): the number of generating
        kwarg:
            x_min = kwarg["x_min"]
            x_max = kwarg["x_max"]
            y_min = kwarg["y_min"]
            y_max = kwarg["y_max"]

    Returns:
        np.ndarray: a 2*num array
         df_lim.loc[df_lim["DATASET"]=="10"]

    """
    df_lim_dataset = df_lim.loc[df_lim["DATASET"] == data_set]
    x_min = df_lim_dataset["LONGITUDE"]["min"].values[0]
    x_max = df_lim_dataset["LONGITUDE"]["max"].values[0]
    y_min = df_lim_dataset["LATITUDE"]["min"].values[0]
    y_max = df_lim_dataset["LATITUDE"]["max"].values[0]
    l = []
    for _ in range(num):
        l.append(
            [random.uniform(x_min, x_max), random.uniform(
                y_min, y_max), data_set]
        )
    xy = np.array(l)
    return xy


def dump_and_load_model(m):
    filename = "./LCM_matern_standard.model"
    if os.path.exists(filename):
        with open(filename, "rb") as _f:
            return pk.load(_f)
    else:
        with open(filename, "wb") as _f:
            m.optimize(messages=True)
            m.optimize_restarts()
            pk.dump(m, _f)  # Serialize object, save object obj to file f
            return m

#n_dim is the index of AP it should be 0-519 WAP001-WAP520
def plot(xy, z, xy_pred, z_pred, n_dim):
    fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
    x_axis = xy[:, 0]
    y_axis = xy[:, 1]

    # plotting the real data of Z but only one AP
    ax.scatter(x_axis, y_axis, z[:,n_dim], c=z[:, n_dim],
               cmap='Accent', marker='s', label=f"WAP00{n_dim + 1}")
    # plotting the fake data generated by MOGP
    if xy_pred is not None:
        ax.scatter(xy_pred[:, 0], xy_pred[:, 1], z_pred[:, n_dim],
                   c=z_pred[:, n_dim], cmap='hsv', marker='.', label="pred")
    plt.legend(loc='upper left')
    plt.show()

# read the data of floor 0
with open("./data_silce/building_0_floor_0.csv", "r") as _file:
    # all buildings incloud, except for the useless value
    # df_raw: pd.DataFrame = pd.read_csv(_file).loc[:, "LONGITUDE":"BUILDINGID"]
    df_raw = pd.read_csv(_file).loc[:, "WAP001":"BUILDINGID"]

# get mean of data which on the same position
#df = df_raw.groupby(["LONGITUDE", "LATITUDE", "FLOOR"], as_index=False).mean()
# if do not get the mean of the data
df = df_raw
df.to_csv('df.csv',index=False)
kernel_RBF = GPy.util.multioutput.ICM(
    input_dim=3, num_outputs=520, kernel=GPy.kern.RBF(3))

xy = df.loc[:, "LONGITUDE":"FLOOR"].to_numpy()
# xy = df.loc[:, "LONGITUDE":"LATITUDE"].to_numpy()
print(xy)
floor = df_raw.loc[:,"FLOOR"].to_numpy()
floor = floor.reshape(floor.shape[0],1)

# xy_floor = np.concatenate((xy, floor), axis=1)


# kernel = GPy.util.multioutput.ICM(

# input_dim=2, num_outputs=520, kernel=GPy.kern.Matern52(2))

# kernel = RBF * matern52  Squared exponential (SE) kernel or Radial Basis Function（RBF）kernel
#TODO: why choose matern52, the inout of this kernel function can not be 3?
kernel_Matern52 = GPy.util.multioutput.LCM(
    input_dim=3, num_outputs=520,
    kernels_list=[GPy.kern.Matern52(3)])  # Matern Radial-basis function kernel (aka squared-exponential kernel)

# z = df.loc[:, "WAP001": "WAP520"].to_numpy()
# z = sklearn.preprocessing.normalize(z, norm="l2")

z_original = df.loc[:, "WAP001": "WAP520"].to_numpy()
standarder = sklearn.preprocessing.StandardScaler()
standarder.fit(z_original)
z = standarder.transform(z_original)

kernel = kernel_RBF * kernel_Matern52
m = GPy.models.GPCoregionalizedRegression([xy], [z],
                                          kernel=kernel)  # Gaussian Process model for heteroscedastic multioutput regression
m = dump_and_load_model(m)
# m.optimize_restarts(num_restarts=10)
data_set = 0  # ??? why set as 0? floor?
x_min = xy[:, 0].min()
x_max = xy[:, 0].max()
y_min = xy[:, 1].min()
y_max = xy[:, 1].max()
l = []
fake_data_for_whole_building = 1059
for _ in range(fake_data_for_whole_building):
    l.append([random.uniform(x_min, x_max),
              random.uniform(y_min, y_max), data_set])
xy_pred = np.array(l)

Y_metadata = {"output_index": xy_pred[:, -1].astype(int)}
z_pred_raw = m.predict(xy_pred, Y_metadata=Y_metadata)
z_pred = z_pred_raw[0]  # file main_building_plot.py end in this line
z_pred_ori = standarder.inverse_transform(z_pred).round()
z_pred_ori_a = pd.DataFrame(z_pred_ori)
#z_pred_ori_a.to_csv("Data_with_building0.csv",index=0)

#plot(xy, z, xy_pred, z_pred, 1)
plot(xy,z_original,xy_pred,z_pred_ori,0)

df_new = pd.DataFrame(z_pred_ori, columns=df_raw.columns[:520]).astype("int64")

df_new["LONGITUDE"] = xy_pred[:, 0]
df_new["LATITUDE"] = xy_pred[:, 1]
df_new["SPACEID"] = np.zeros(xy_pred[:, 0].shape, dtype=int)
df_new["RELATIVEPOSITION"] = np.zeros(xy_pred[:, 0].shape, dtype=int)
df_new["BUILDINGID"] = np.zeros(xy_pred[:, 0].shape, dtype=int)
#df_floor = np.zeros(xy_pred[:, 0].shape, dtype=int)
df_floor = np.random.choice(a=[0,3,6,9], size=fake_data_for_whole_building, replace=True, p=[0.235,0.270,0.270,0.225])
df_new["FLOOR"] = df_floor
with open("./trainingData2.csv", "w") as f:
    f.write(df_new.to_csv(index=False))
# z = pd.DataFrame(z)
# z_original = pd.DataFrame(z_original)
# z_pred = pd.DataFrame(z_pred)
# z.to_csv('z.csv',index=False)
# z_original.to_csv('z_original.csv',index=False)
# z_pred.to_csv('z_pred.csv',index=False)