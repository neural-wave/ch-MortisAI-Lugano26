"""NumPy CPU scorer; all dense weights are used on each neural forward."""
import numpy as np


class Ranker:
    feature_count = 256
    def __init__(self,path):
        with np.load(path,allow_pickle=False) as z:
            self.mean=z['mean'].copy();self.scale=z['scale'].copy()
            self.weights=[np.ascontiguousarray(z[f'w{i}']) for i in range(4)]
            self.biases=[z[f'b{i}'].copy() for i in range(4)]
        self.parameters=sum(v.size for v in self.weights+self.biases)
        assert self.mean.shape==self.scale.shape==(256,)
        if not np.isfinite(self.mean).all() or not np.isfinite(self.scale).all() or not np.all(self.scale>0):
            raise ValueError('Invalid model normalization')
        width=256
        for w,b in zip(self.weights,self.biases):
            if w.shape!=(width,len(b)):raise ValueError('Malformed model architecture')
            if not np.isfinite(w).all() or not np.isfinite(b).all():raise ValueError('Non-finite model')
            width=len(b)
        assert width==2


def load(path):return Ranker(path)


def score_batch(X,model):
    values=(np.asarray(X,dtype=np.float32)-model.mean)/model.scale
    for index,(weight,bias) in enumerate(zip(model.weights,model.biases)):
        values=values@weight+bias
        if index<3:np.maximum(values,0,out=values)
    if not np.isfinite(values).all():raise ValueError('Nonfinite neural scores')
    return values[:,1]-values[:,0]
