import numpy as np
import pandas as pd
import os, sys
import pandas as pd
from sklearn.preprocessing import OrdinalEncoder, LabelEncoder
from sklearn.tree import DecisionTreeClassifier


print("cur_path: ", os.getcwd())
script_dir = os.path.dirname(os.path.abspath(__file__))
print("script_dir: ", script_dir)
sys.path.append(script_dir)
file_name = os.path.join(script_dir, "data1.csv")
acc1 = pd.read_csv(file_name, encoding='gbk')
accepts = acc1.drop("计数", axis=1)
print(accepts)
column_names = accepts.columns.to_list()
print("column_names: ", column_names)
data = accepts[column_names]
X_names = column_names[:-1]
y_name = column_names[-1]
print("X_names: ", X_names)
print("y_name: ", y_name)


X = data.drop(y_name, axis=1)  # 特征
y = data[y_name]  # 目标变量

# 定义各列的顺序（如果有）
age_order = ["青", "中", "老"]          # 年龄：青 < 中 < 老
income_order = ["低", "中", "高"]       # 收入：低 < 中 < 高
credit_order = ["良", "优"]             # 信誉：假设 "良" < "优"

# 使用 OrdinalEncoder 转换有序分类变量
encoder = OrdinalEncoder(categories=[age_order, income_order, ["否", "是"], credit_order])
print("encoder: ", encoder)

X_encoded = encoder.fit_transform(X[X_names])

# 转换为 DataFrame（可选）
X_encoded = pd.DataFrame(X_encoded, columns=["年龄", "收入", "学生", "信誉"])
print("X_encoded: ", X_encoded)

# 处理目标变量（归类）
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)  # "买"→1, "不买"→0

clf = DecisionTreeClassifier(criterion='gini', max_depth=3, random_state=20)
clf.fit(X_encoded, y_encoded)

# 预测
y_pred = clf.predict(X_encoded)
print("预测结果:", y_pred)


from sklearn.tree import plot_tree
import matplotlib.pyplot as plt
# 设置支持中文的字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # Windows 系统
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
plt.figure(figsize=(12, 8))
plot_tree(clf, feature_names=X_encoded.columns, class_names=["不买", "买"], filled=True)
plt.show()