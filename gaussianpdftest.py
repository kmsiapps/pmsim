from utils.helper import gaussian_pdf
import matplotlib.pyplot as plt

data = []
for i in range(100):
    data.append(gaussian_pdf(i, 50, 10))

plt.plot(data)
plt.show()
