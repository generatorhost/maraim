from maraim.kernel2 import MaraimKernel

kernel = MaraimKernel()
status = kernel.start()
print("MARAIM_KERNEL2_SMOKE_OK")
print(status)
