import matplotlib.pylab as plt
import numpy as np

from wildboar.datasets import load_dataset
from wildboar.ensemble import ShapeletForestClassifier
from wildboar.explain.counterfactual import counterfactuals

x_train, x_test, y_train, y_test = load_dataset(
    "TwoLeadECG", repository="wildboar/ucr", merge_train_test=False
)

# x_train = x_train.repeat(2, axis=0).reshape(x_train.shape[0], 2, -1)
# print(x_train[0])
# x_test = x_test.repeat(2, axis=0).reshape(x_test.shape[0], 2, -1)

clf = ShapeletForestClassifier(
    metric="euclidean", random_state=1, n_jobs=-1, n_estimators=100
)
clf.fit(x_train, y_train)
print(clf.score(x_test, y_test))
y_pred = clf.predict(x_test)
class_ = clf.classes_[1]
print("Class: %s" % class_)
print("Pred: %r" % y_pred)
x_test = x_test[y_pred != class_][:10]
y_test = y_test[y_pred != class_][:10]

x_counterfactual, success, score = counterfactuals(
    clf, x_test, class_, random_state=123, scoring="euclidean"
)

print(np.mean(score))
print(clf.predict(x_counterfactual))
print(y_test)
print(np.sum(success) / success.shape[0])
print(
    np.sum(clf.predict(x_counterfactual[success]) == y_test[success]) / np.sum(success)
)
fig, ax = plt.subplots(nrows=2)
ax[0].plot(x_counterfactual[0], c="red")
ax[0].plot(x_test[0], c="blue")
ax[1].plot(x_counterfactual[1], c="red")
ax[1].plot(x_test[1], c="blue")
ax[1].legend(["x'", "x"])
plt.show()
