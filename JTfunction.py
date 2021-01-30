import jittor as jt
import numpy as np

#计算平均值和标准差
def calc_mean_std(feat, eps=1e-5):
    size = feat.size()
    assert (len(size) == 4)  #如果输入的feature的size长度不等于4，就停止执行
    N, C = size[:2]    #这个操作可以在外面跑下看结果  获取的是batch的N和channelz
    #feat_std = jt.std(feat.view(N, C, -1)) + eps
    #feat_std = feat_std.view(N, C, 1, 1)
    #feat_var = jtvar(feat) + eps
    #feat_mean = feat.view(N, C, -1).mean(dim=2).view(N, C, 1, 1) #将N个中每个C的H*W所有数求平均，然后reshape成每个N中的每个C一个
    dims = list(range(2,feat.ndim))

    N, C, X = feat.size()
    mean = jt.mean(feat, dims=dims)
    xmean = mean * X / (X - 1)
    x2mean = jt.mean(feat * feat, dims=dims) * X / (X - 1)
    xvar = (x2mean - xmean * xmean).maximum(0.0)
    return xmean, jt.sqrt(xvar+eps)

#标准化
def normal(feat, eps=1e-5):
    dims = list(range(2,feat.ndim))
    feat_mean, feat_std = calc_mean_std(feat, eps)
    #normalized = (feat - feat_mean)/feat_std
    norm_feat = (feat - feat_mean.broadcast(feat,dims)) / feat_std.broadcast(feat,dims)
    return norm_feat

def _calc_feat_flatten_mean_std(feat):
    assert (feat.size()[0]==3)
    assert (isinstance(feat, jt.Float))
    feat_flatten = feat.view(3, -1)
    mean = feat_flatten.mean(dim=-1, keepdim=True)
    std = feat_flatten.std(dim=-1, keepdim=True)
    return feat_flatten, mean, std

#矩阵乘法
def matmul(a, b):
    (n, m), k = a.shape, b.shape[-1]
    a = a.broadcast([n,m,k], dims=[2])
    b = b.broadcast([n,m,k], dims=[0])
    return (a*b).sum(dim=1)


def _mat_sqrt(x):
    U, D, V =jt.svd(x)
    return matmul(matmul(U, D.pow(0.5).diag*()), V.t())

def coral(source, target):
    #assume both source and target are 3D array (C, H, W)
    #Note: flatten -> f (?)

    source_f , source_f_mean, source_f_std = _calc_feat_flatten_mean_std(source)
    source_f_norm = (source_f - source_f_mean.expand_as(source_f)) / source_f_std.expand_As(source_f)
    source_f_cov_eye = \
        matmul(source_f_norm, source_f_norm.t()) + jt.float([[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])

    target_f, target_f_mean, target_f_std = _calc_feat_flatten_mean_std(target)
    target_f_norm = (target_f - target_f_mean.expand_as(target_f)) / target_f_std.expand_as(target_f)
    target_f_cov_eye = \
        matmul(target_f_norm, target_f_norm.t()) + jt.float([[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])

    source_f_norm_transfer = matmul(
        _mat_sqrt(target_f_cov_eye),
        matmul(jt.inverse(_mat_sqrt(source_f_cov_eye)),
               source_f_norm)
    )

    source_f_transfer = source_f_norm_transfer * \
        target_f_std.expand_as(source_f_norm) + \
        target_f_mean.expand_as(source_f_norm)

    return source_f_transfer.view(source.size())

'''
def jtstd(feat):
    N, C = feat.size()[:2]
    X = feat.view(N, C, -1).data.shape[2]
    result = []
    mean = jt.mean(feat,dim=2).data
    for x in range(N):
        for y in range(C):
            var = 0, 0
            for z in range(X):
                var += ((list[x,y,z] - mean[x,y]) ** 2)
            var = var/(X-1)
            result.append(var**0.5)
    return jt.array(result).view(N,C)
'''

'''
def jtvar(feat):
    dims = list(range(2,feat.ndim))
    xmean = jt.mean(feat, dims=dims)
    x2mean = jt.mean(feat*feat, dims=dims)
    xvar = (x2mean-xmean*xmean).maximum(0.0)
    print(xvar)
    return xvar
'''