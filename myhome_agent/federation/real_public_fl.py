"""v4.3 真实公开数据 FL 训练

说明：HAR / URFD 公开集服务器不稳定（v4.2 尝试 404 / 301），v4.3 改用 sklearn 内置工业基准数据集（digits / wine / breast_cancer / iris）：
- 真实数据（UCI / scikit-learn 提供）
- 多类别（不是二分类）
- 多维度特征
- 标准评测指标

10 家庭 Non-IID + 50 轮 FedAvg + per-family 准确率。
"""
from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np
from sklearn.datasets import load_digits, load_wine, load_breast_cancer, load_iris

logger = logging.getLogger(__name__)


# ============================================================
# 数据集加载
# ============================================================


def load_dataset(name: str = "digits"):
    """v4.3 加载 sklearn 内置数据集"""
    if name == "digits":
        data = load_digits()
        # 8x8 图像 → 64 维
    elif name == "wine":
        data = load_wine()
    elif name == "breast_cancer":
        data = load_breast_cancer()
    elif name == "iris":
        data = load_iris()
    else:
        raise ValueError(f"unknown dataset: {name}")

    X = data.data.astype(np.float32)
    y = data.target.astype(np.int32)
    # 归一化
    X = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-9)
    return X, y, data.target_names.tolist() if hasattr(data.target_names, 'tolist') else list(range(int(y.max()) + 1))


# ============================================================
# Non-IID 分片
# ============================================================


def shard_non_iid(X, y, n_clients=10, alpha=0.5):
    """Dirichlet Non-IID 分片"""
    from numpy.random import dirichlet
    n_classes = int(y.max()) + 1
    proportions = dirichlet([alpha] * n_clients, size=n_classes)
    clients = []
    for i in range(n_clients):
        indices = []
        for k in range(n_classes):
            label_idx = np.where(y == k)[0]
            n_k = int(len(label_idx) * proportions[k, i])
            if n_k > 0:
                indices.append(np.random.choice(label_idx, n_k, replace=False))
        ii = np.hstack(indices) if indices else np.array([], dtype=int)
        np.random.shuffle(ii)
        if len(ii) > 1:
            clients.append((X[ii], y[ii]))
    return [c for c in clients if len(c[0]) > 1]


# ============================================================
# v4.3 真实 FL 训练
# ============================================================


def train_v43(dataset: str = "digits", n_rounds: int = 50, n_clients: int = 10, alpha: float = 0.5):
    print("=" * 70)
    print(f"  v4.3 真实公开数据 FL 训练（{dataset}）")
    print("=" * 70)

    # 1. 加载数据
    X, y, class_names = load_dataset(dataset)
    print(f"\n[数据] {dataset}: {X.shape[0]} 样本 × {X.shape[1]} 维 × {len(class_names)} 类别")
    print(f"  类别分布: {dict(zip(*np.unique(y, return_counts=True)))}")

    # 2. 分片
    clients = shard_non_iid(X, y, n_clients=n_clients, alpha=alpha)
    sample_counts = [len(c[0]) for c in clients]
    print(f"\n[分片] {len(clients)} 家庭, alpha={alpha}")
    print(f"  每家庭样本: min={min(sample_counts)}, max={max(sample_counts)}, mean={np.mean(sample_counts):.0f}")

    # 3. 中心化基线
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score
    t0 = time.time()
    clf = LogisticRegression(max_iter=500)
    clf.fit(X, y)
    bl_center = accuracy_score(y, clf.predict(X))
    bl_time = time.time() - t0
    print(f"\n[基线] 中心化 LR: {bl_center:.4f} ({bl_time:.2f}s)")

    # 4. 联邦学习
    from myhome_agent.federation.fedavg import SimpleMLP
    from myhome_agent.federation.flower_adapter import MyHomeFlowerClient

    n_classes = len(class_names)
    model = SimpleMLP(X.shape[1], 32, n_classes)
    p = [model.W1, model.b1, model.W2, model.b2]
    acc_curve, loss_curve = [], []

    t0 = time.time()
    for r in range(n_rounds):
        plist, wlist = [], []
        for i, (Xc, yc) in enumerate(clients):
            cm = SimpleMLP(X.shape[1], 32, n_classes)
            cm.W1, cm.b1, cm.W2, model.b2 = [g.copy() for g in p]
            cm.W1, cm.b1, cm.W2, model.b2 = p
            # 修
            cm.W1 = p[0].copy()
            cm.b1 = p[1].copy()
            cm.W2 = p[2].copy()
            cm.b2 = p[3].copy()
            cl = MyHomeFlowerClient(i, cm, Xc, yc)
            cl.set_parameters(p)
            for _ in range(2):
                cl._train_one_epoch(Xc, yc, 0.01)
            plist.append(cl.get_parameters())
            wlist.append(len(Xc))

        if not plist:
            continue
        new = [sum(l[pi] * (w / sum(wlist)) for l, w in zip(plist, wlist)) for pi in range(4)]
        p = new
        model.W1, model.b1, model.W2, model.b2 = p

        probs = model.forward(X)
        preds = probs.argmax(axis=1)
        acc = accuracy_score(y, preds)
        acc_curve.append(acc)

        if r % 10 == 0:
            print(f"  R{r+1:2}: acc={acc:.4f}")
    fl_time = time.time() - t0

    print(f"\n[结果]")
    print(f"  中心化: {bl_center:.4f} ({bl_time:.2f}s)")
    print(f"  联邦 {n_rounds} 轮: {acc_curve[-1]:.4f} ({fl_time:.2f}s)")
    print(f"  差距: {bl_center - acc_curve[-1]:+.4f}")
    print(f"  per-family:")
    for i, (Xc, yc) in enumerate(clients):
        probs = model.forward(Xc)
        acc = accuracy_score(yc, probs.argmax(axis=1))
        print(f"    Family {i+1:2}: {len(Xc):3} 样本 准确率={acc:.4f}")

    print()
    if acc_curve[-1] >= bl_center - 0.05:
        print(f"  ✅ v4.3 联邦学习 ≥ 中心化 95%（差距 < 5%）")
    else:
        print(f"  ⚠️  联邦学习差距较大，{n_rounds} 轮不够")

    print("=" * 70)
    return {
        "dataset": dataset,
        "centralized_acc": bl_center,
        "fl_acc": acc_curve[-1],
        "gap": bl_center - acc_curve[-1],
        "n_rounds": n_rounds,
        "curve": acc_curve,
    }


def main():
    # 4 个数据集各跑一遍
    for ds in ["iris", "wine", "breast_cancer", "digits"]:
        result = train_v43(dataset=ds, n_rounds=40, n_clients=10, alpha=0.5)
        print()
        print()


if __name__ == "__main__":
    main()