import matplotlib.pyplot as plt
from PIL import Image

im = Image.open("small.jpg")
croped = im.crop((200, 200, 600, 600))
croop = croped.crop((0, 200, 600, 250))
trans = croped.transpose(Image.Transpose.ROTATE_90)

plt.imshow(trans) #type:ignore
plt.axis('on') #type:ignore
plt.show() #type:ignore