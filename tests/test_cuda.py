# import pycuda.autoinit
import pycuda.driver as cuda
import numpy


from pycuda.compiler import SourceModule
# export PATH=/usr/local/cuda/bin:$PATH


cuda.init()     


def dott(array_a, array_b):
    #ctx.push()
    mod = SourceModule("""
    __global__ void dot(float *dest, float *a, float *b)
    {
    const int i = threadIdx.x;
    dest[i] = a[i] * b[i];
    }
    """)
    dot = mod.get_function("dot")

    dest = numpy.zeros_like(array_a)
    dot(cuda.Out(dest), cuda.In(array_a), cuda.In(array_b),block=(len(a),1,1), grid=(1,1))
    # 
    return dest



if __name__ == "__main__":
    a = numpy.random.normal(size=40).astype(numpy.float32)
    b = numpy.random.normal(size=40).astype(numpy.float32)
    ctx  = cuda.Device(0).make_context()
    print(dott(a, b))
    ctx.pop()
    # del ctx


