import os
import GPy
import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
import pickle as pk
import sklearn.preprocessing


# def dataset_limitaion(df: pd.DataFrame):
#     df[]

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
            pk.dump(m, _f)#Serialize object, save object obj to file f
            return m


def plot(xy, z, xy_pred, z_pred, n_dim):
    """plot real data and predicted data
    all input data are n*1 shape

    Args:
        xy (np.ndarray): real data x and y coordination
        z (np.ndarray): real data rss
        xy_pred (np.ndarray): prediction x and y coordication
        z_pred (np.ndarray): prediction rss
        n_dim (int): plot the specific dimension.
    """
    fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
    # ax.plot3D(x, y, z, 'gray')
    x_axis = xy[:, 0]
    y_axis = xy[:, 1]

    # plotting the real data of Z
    ax.scatter(x_axis, y_axis, z[:, n_dim], c=z[:, n_dim],
               cmap='Accent',marker='s', label=f"WAP")#label=f"WAP00{n_dim+1}"
    # plotting the fake data generated by MOGP
    if xy_pred is not None:
        ax.scatter(xy_pred[:, 0], xy_pred[:, 1], z_pred[:, n_dim],
                   c=z_pred[:, n_dim], cmap='hsv', marker='.',label="pred")
    plt.legend(loc='upper left')
    plt.show()

    # read file data into dataframe

#read the data of floor 0
with open("./data_silce/building0.csv", "r") as _file:
    # all buildings incloud, except for the useless value
    # df_raw: pd.DataFrame = pd.read_csv(_file).loc[:, "LONGITUDE":"BUILDINGID"]
    df_raw = pd.read_csv(_file).loc[:, "WAP001":"BUILDINGID"]

# get mean of data which on the same position
df = df_raw.groupby(["LONGITUDE", "LATITUDE"], as_index=False).mean()
df_raw.to_csv('df_raw.csv',index=False)

# TODO: input_dim is 2 (LONGITUDE and Latitude) or 4 (plus BuildingID and Floor)?
# kernel = GPy.util.multioutput.ICM(
#     input_dim=2, num_outputs=520, kernel=GPy.kern.RBF(2))


# #read the data of floor 1
# with open("./data_silce/building_0_floor_1.csv", "r") as _file:
#     # all buildings incloud, except for the useless value
#     # df_raw: pd.DataFrame = pd.read_csv(_file).loc[:, "LONGITUDE":"BUILDINGID"]
#     df_raw_floor_1 = pd.read_csv(_file).loc[:, "WAP515":"BUILDINGID"]
#
# # get mean of data which on the same position
# df_floor_1 = df_raw_floor_1.groupby(["LONGITUDE", "LATITUDE"], as_index=False).mean()
# result = pd.concat([df, df_floor_1], axis=0)
#
#
# #result.to_csv('result.csv',index=False)
# df = result #reset the variable df to load to the GP model


xy = df.loc[:, "LONGITUDE":"LATITUDE"].to_numpy()
print(xy)
# kernel = GPy.util.multioutput.ICM(

# input_dim=2, num_outputs=520, kernel=GPy.kern.Matern52(2))

# kernel = RBF * matern52
kernel = GPy.util.multioutput.LCM(
    input_dim=2, num_outputs=520, kernels_list=[GPy.kern.Matern52(2)])#Matern Radial-basis function kernel (aka squared-exponential kernel)


# z = df.loc[:, "WAP001": "WAP520"].to_numpy()
# z = sklearn.preprocessing.normalize(z, norm="l2")

z_original = df.loc[:, "WAP001": "WAP520"].to_numpy()
standarder = sklearn.preprocessing.StandardScaler()
standarder.fit(z_original)
z = standarder.transform(z_original)


'''
    
    Gaussian Process model for heteroscedastic multioutput regression

    This is a thin wrapper around the models.GP class, with a set of sensible defaults

    :param X_list: list of input observations corresponding to each output

    :param Y_list: list of observed values related to the different noise models

    :param kernel: a GPy kernel ** Coregionalized, defaults to RBF ** Coregionalized
'''
m = GPy.models.GPCoregionalizedRegression([xy], [z], kernel=kernel)#Gaussian Process model for heteroscedastic multioutput regression
m = dump_and_load_model(m)
# m.optimize_restarts(num_restarts=10)
data_set = 0  #??? why set as 0? floor?
x_min = xy[:, 0].min()
x_max = xy[:, 0].max()
y_min = xy[:, 1].min()
y_max = xy[:, 1].max()
l = []
for _ in range(20000):
    l.append([random.uniform(x_min, x_max),
             random.uniform(y_min, y_max), data_set])
xy_pred = np.array(l)


Y_metadata = {"output_index": xy_pred[:, -1].astype(int)}
z_pred_raw = m.predict(xy_pred, Y_metadata=Y_metadata)
z_pred = z_pred_raw[0]# file main_building_plot.py end in this line

z_pred_ori = standarder.inverse_transform(z_pred).round()
plot(xy, z, xy_pred, z_pred, 6)
df_new = pd.DataFrame(z_pred_ori, columns=df_raw.columns[:520]).astype("int64")


df_new["LONGITUDE"] = xy_pred[:, 0]
df_new["LATITUDE"] = xy_pred[:, 1]
df_new["SPACEID"] = np.zeros(xy_pred[:, 0].shape,dtype=int)
df_new["RELATIVEPOSITION"] = np.zeros(xy_pred[:, 0].shape,dtype=int)
df_new["BUILDINGID"] = np.zeros(xy_pred[:, 0].shape,dtype=int)
df_new["FLOOR"] = np.zeros(xy_pred[:, 0].shape,dtype=int)
with open("./trainingData2.csv", "w") as f:
    f.write(df_new.to_csv(index=False))
