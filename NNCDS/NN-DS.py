#!/usr/bin/python2

from collections import Counter, defaultdict
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn import datasets
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder
from ds_layer import NNCDS
import pickle


def loadData(datafile):
	features = np.loadtxt(datafile, delimiter=',', usecols=(0, 1, 2, 3))
	strLabels = np.loadtxt(datafile, delimiter=',', usecols=(4,), dtype=str)
	labelEnc = LabelEncoder()
	labelEnc.fit(strLabels)
	labels = labelEnc.transform(strLabels)
	print('Read a dataset from ' + datafile + ': ' + str(features.shape[0]) + ' data points, labels: ' + str(labelEnc.classes_))

	return (features, labels, labelEnc)


def getDecisionSpaceCrossSectionMap(classifier, fixDims, fixDimVals,freeDimsLimits, resolution, rejectionCost=None, newLabelCost=None):
	totalDims = len(fixDims) + len(freeDimsLimits)
	freeDims = list(range(totalDims))
	for dim in fixDims:
		freeDims.remove(dim)
	gridPts = [int(1+(end-start)/resolution) for start,end in freeDimsLimits]
	# print(gridPts)
	numPoints = np.product(gridPts)

	def linearIdxToGrid(linIdx, dim):
		curPoints = numPoints
		curIdx = linIdx
		for d in freeDims[:-1]:
			curPoints = curPoints/gridPts[freeDims.index(d)]
			coord = curIdx / curPoints
			curIdx = curIdx % curPoints
			if d == dim:
				return coord
		return curIdx
	grid = []
	for i in range(numPoints):
		curPos = [fixDimVals[fixDims.index(dim)] if dim in fixDims
				else freeDimsLimits[freeDims.index(dim)][0] + resolution*linearIdxToGrid(i, dim) for dim in range(totalDims)]
		grid.append(curPos)
		# print(str(i) + str(curPos))
	gridVals = classifier.predict(grid, rejectionCost=rejectionCost, newLabelCost=newLabelCost)
	# print('gridVals'+str(gridVals[0:6]))
	return gridVals.reshape(gridPts)


def discrete_cmap(N, base_cmap=None):
	""" Create an N-bin discrete colormap from the specified input map """

	# Note that if base_cmap is a string or None, you can simply do
	#    return plt.cm.get_cmap(base_cmap, N)
	# The following works for string, None, or a colormap instance:

	base = plt.cm.get_cmap(base_cmap)
	color_list = base(np.linspace(0, 1, N))
	cmap_name = base.name + str(N)
	return base.from_list(cmap_name, color_list, N)


def plotDecisionSpaceCrossSectionMap(classifier, fixDims, fixDimVals, freeDimsLimits, resolution, rejectionCost=None, newLabelCost=None):
	crossection = getDecisionSpaceCrossSectionMap(classifier, fixDims, fixDimVals, freeDimsLimits, resolution, rejectionCost=rejectionCost, newLabelCost=newLabelCost)
	print('Size of crossection' + str(len(np.unique(crossection))))
	totalDims = len(fixDims) + len(freeDimsLimits)
	freeDims = list(range(totalDims))
	for dim in fixDims:
		freeDims.remove(dim)
	if len(freeDims) != 2:
		raise ValueError('Only two-dimensional decision maps are supported, ' + str(len(freeDims)) + '-dimensional map implied by fixed dims')
	if len(freeDimsLimits) != 2:
		raise ValueError('Only two-dimensional decision maps are supported, ' + str(len(freeDims)) + '-dimensional map implied by limits')
	ranges = [ [ start + resolution*float(i) for i in range(int((end-start)/resolution) + 1) ] for start,end in freeDimsLimits ]
	# print('ranges len:' + str(len(ranges)))
	# print('ranges:' + str(ranges))
	x,y = np.meshgrid(ranges[0], ranges[1])
	# print('x:' + str(x.shape))
	# print('y:' + str(y.shape))
	# plt.plot(x, y, marker='1', color='red', linestyle='')
	# plt.show()
#	cs = plt.contour(x.T,y.T,crossection, colors='k', nchunk=0)
#	csf = plt.contourf(x.T,y.T,crossection, len(np.unique(crossection)), cmap=plt.cm.Paired)
	plt.pcolor(x.T, y.T, crossection, cmap=discrete_cmap(len(np.unique(crossection)), plt.cm.jet))
#	cb = plt.colorbar(ticks=np.unique(crossection), label='')
	# plt.xlabel('petal length ' + str(freeDims[0]))
	# plt.ylabel('petal width ' + str(freeDims[1]))
	plt.xlabel('petal length')
	plt.ylabel('petal width')


def plotScatter(feature, label):
	# marker = ['o', '^', 's']
	# x1 = feature[:, 0]
	# x2 = feature[:, 1]
	# plt.scatter(x1, x2, s=20, c=labels)
	# plt.xlabel('petal length(cm)')
	# plt.ylabel('petal width(cm)')
	# plt.show()
	pd_iris = pd.DataFrame(np.hstack((feature, label.reshape(150, 1))),columns=['sepal length(cm)','sepal width(cm)','petal length(cm)','petal width(cm)','class'])
	fig, ax = plt.subplots(dpi=150)
	iris_type = pd_iris['class'].unique()
	iris_name = iris.target_names
	colors = ["#DC143C", "#000080", "#228B22"]
	markers = ['x', '.', '+']
	for i in range(len(iris_type)):
		plt.scatter(pd_iris.loc[pd_iris['class'] == iris_type[i], 'petal length(cm)'],
					pd_iris.loc[pd_iris['class'] == iris_type[i], 'petal width(cm)'],
					s=40,  # 散点图形（marker）的大小
					c=colors[i],  # marker颜色
					marker=markers[i],  # marker形状
					# marker=matplotlib.markers.MarkerStyle(marker = markers[i],fillstyle='full'),#设置marker的填充
					alpha=0.85,  # marker透明度，范围为0-1
					facecolors='r',  # marker的填充颜色，当上面c参数设置了颜色，优先c
					edgecolors='none',  # marker的边缘线色
					linewidths=1,  # marker边缘线宽度，edgecolors不设置时，改参数不起作用
					label=iris_name[i])  # 后面图例的名称取自label
	plt.legend(loc='upper right')
	# plt.show()


def plotDecisonBoundary(selectedFeatures, classifier, lambda0, lambda1):
	x1 = selectedFeatures[:, 0]
	x2 = selectedFeatures[:, 1]
	# predfeature = feature[...,2:]
	# print('predfeature' + str(predfeature))
	# print('x1' + str(x1))
	# print('x2' + str(x2))
	x1_min, x1_max = x1.min(), x1.max()
	x2_min, x2_max = x2.min(), x2.max()
	step = 0.1
	xx, yy = np.meshgrid(np.arange(-0.5,9,step),np.arange(-0.5,4.5,step))
	z = np.c_[xx.ravel(), yy.ravel()]
	print(z.shape)
	clf = classifier
	zz = clf.predict(z, lambda0, lambda1)
	print(zz.shape)
	zz = zz.reshape(xx.shape)
	print(zz.shape)
	# print('xx' + str(xx.shape))
	# print('yy' + str(yy.shape))
	# print('zz' + str(zz.shape))
	plt.contour(xx, yy, zz)
	plt.show()
	return zz


if __name__ == '__main__':
	trainModel = True
	loadModel = False
	compareModel = False
	iris = datasets.load_iris()
	features, labels = iris.data, iris.target
	# irisDataFile = 'data/iris/iris.data'
	# ffeatures, labels, labelEnc = loadData(irisDataFile)
	selectedFeatures = features[..., 2:]
	# selectedFeatures = features[..., 2:]
	eviclf = NNCDS()
	if trainModel:
		eviclf.fit(selectedFeatures, labels, max_iterations=10000)
		with open('model/eviclf-2D-10000iter.pickle', 'wb') as fw:
			pickle.dump(eviclf, fw)

	if loadModel:
		with open('model/eviclf-2D-10000iter.pickle', 'rb') as fr:
			eviclfLoaded = pickle.load(fr)
		# plotDecisionSpaceCrossSectionMap(eviclfLoaded, [0, 1], [5.5, 3.0], [(-1, 8), (-1, 4)], 0.05, rejectionCost=0.5, newLabelCost=0.65)
		# cb = plt.colorbar(ticks=[-2,-1,0,1,2])
		# cb.set_ticklabels(['Novel', 'Reject', 'Iris Setosa', 'Iris Veriscolor', 'Iris Virginica'])
		# plt.show()
		z = plotDecisonBoundary(selectedFeatures, eviclfLoaded, 0.5, 0.65)
		plotScatter(selectedFeatures, labels)
		plotDecisonBoundary(selectedFeatures, eviclfLoaded, 0.5, 0.65)

	if compareModel:
		knncla = KNeighborsClassifier(n_neighbors=3)
		knncla.fit(selectedFeatures, labels)
		testVectors1 = [[5.5, 2.35], [4.71, 1.7]]  # Iris-virginica-2, Iris-versicolor-1
		testVectors2 = [[2.03, 2.82], [1.19, 0.303]]
		testLabelsKnn = knncla.predict(testVectors1)
	#	print('Got labels ' + str(labelEnc.inverse_transform(testLabelsKnn)) + ' from k-nn classifier (numericals ' + str(testLabelsKnn) + ')')
		print('KNN: Got labels ' + str(testLabelsKnn))
		testLabelsAbs = eviclf.predict(testVectors1)
	#	print('Got labels ' + str(labelEnc.inverse_transform(testLabelsAbs)) + ' from ABS classifier (numericals ' + str(testLabelsAbs) + ')')
		print('eviclf: Got labels ' + str(testLabelsAbs))




