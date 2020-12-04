from PIL import Image
from os import listdir


if __name__ == '__main__':
	photos = listdir('png_photos')

	for photo in photos:
		im = Image.open(f'png_photos/{photo}')
		rgb_im = im.convert('RGB')
		rgb_im.save(f'jpg_photos/{photo.replace(".png", ".jpg")}')
		print(f'Successfully converted {photo}')