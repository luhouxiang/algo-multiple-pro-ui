import numpy as np
import pandas as pd
import os, sys
from sklearn.preprocessing import OrdinalEncoder, LabelEncoder
from sklearn.ensemble import RandomForestClassifier  # 修改这里
from sklearn.metrics import classification_report

# 加载数据
script_dir = os.path.dirname(os.path.abspath(__file__))
file_name = os.path.join(script_dir, "data1.csv")
acc1 = pd.read_csv(file_name, encoding='gbk')
accepts = acc1.drop("计数", axis=1)

# 数据预处理
column_names = accepts.columns.to_list()
data = accepts[column_names]
X_names = column_names[:-1]
y_name = column_names[-1]

X = data.drop(y_name, axis=1)
y = data[y_name]

# 定义顺序
encoder = OrdinalEncoder(categories=[
    ["青", "中", "老"],
    ["低", "中", "高"],
    ["否", "是"],
    ["良", "优"]
])
X_encoded = encoder.fit_transform(X[X_names])
X_encoded = pd.DataFrame(X_encoded, columns=["年龄", "收入", "学生", "信誉"])

# 目标变量编码
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# 改用随机森林分类器（核心修改部分）
rf_clf = RandomForestClassifier(n_estimators=100, max_depth=3, random_state=20)
rf_clf.fit(X_encoded, y_encoded)

# 预测
rf_pred = rf_clf.predict(X_encoded)

# 输出分类报告
print(classification_report(y_encoded, rf_pred, target_names=["不买", "买"]))

# 可视化随机森林中特定一棵树
from sklearn.tree import plot_tree
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

plt.figure(figsize=(14, 8))
# 随机森林中的第一棵树
plot_tree(rf_clf.estimators_[0], feature_names=X_encoded.columns, class_names=["不买", "买"], filled=True)
plt.title("随机森林中的一棵决策树示例")
plt.show()
