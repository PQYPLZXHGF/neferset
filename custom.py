import component
from geometry import Vector4
from drawing import draw_image


def rgb_to_bytes(color):
	''' Convert from fractional rgb values to a tuple of byte values. '''
	return tuple(int(round(i * 255)) for i in color)


def rgb_from_bytes(color):
	''' Convert from byte rgb values to a Vector4 of fractional values. '''
	return Vector4(*[i / 255 for i in color])


def set_watermark(ctx, comp, data):
	''' Create the set watermark that appears on regular Hearthstone cards. '''
	from PIL import Image
	from os import listdir, makedirs
	from os.path import isfile, isdir, join
	from hearthstone import enums

	cache_dir = ".cache" # store generated images here for reuse
	file_ext = ".png" # set icon file extension

	card = data["card"]
	theme_dir = data["dir"]
	has_race = card.race != enums.Race.INVALID
	is_premium = data["premium"]
	card_type = data["cardtype"]
	race_offset = comp.custom["raceOffset"] # in respect to y coordinate only

	# do nothing for non-craftable sets
	if not card.card_set.craftable:
		return
	set_name = card.card_set.name.lower()

	if not isdir(cache_dir):
		makedirs(cache_dir)

	# set the name for the generate image
	name = [card_type]
	if is_premium:
		name.append("_premium")
	if has_race:
		name.append("_race")
	name.append("_")
	name.append(set_name)
	image_name = "".join(name)
	image_path = join(cache_dir, "{}{}".format(image_name, file_ext))

	# load the data
	base_image = component.Image(comp.custom["image"])
	set_region = component.Region(
		comp.custom["region"]["x"],
		comp.custom["region"]["y"],
		comp.custom["region"]["width"],
		comp.custom["region"]["height"])

	# if there is a cached version of the image use it
	if isfile(image_path):
		draw_image(ctx, image_path, base_image.x, base_image.y)
		return

	# calc set offset within base
	offset = {
		"x": set_region.x - base_image.x,
		"y": set_region.y - base_image.y
	}
	# if a minion has a race, need offset watermark
	if has_race:
		offset["y"] += race_offset

	# check the icon exists for this set
	set_icon_path = join(theme_dir, comp.custom["setIcons"], "{}{}".format(set_name, file_ext))
	if not isfile(set_icon_path):
		print("ERROR: set icon missing for {}".format(set_name))

	# resize the set icon to the correct size
	set_org = Image.open(set_icon_path)
	set_resize = set_org.resize((set_region.width, set_region.height), Image.BILINEAR)
	set_img = Image.new("RGBA",
		(base_image.width, base_image.height),
		(0, 0, 0, 0))
	set_img.paste(set_resize, (offset["x"], offset["y"]))
	set_org.close()
	set_resize.close()

	# open the base image
	descp_img = Image.open(join(theme_dir, base_image.assets["default"]))

	# get the blending attributes
	intensity = comp.custom["blendIntensity"]
	tint = comp.custom["tint"][card_type]
	tint = Vector4(tint["r"], tint["g"], tint["b"], tint["a"])
	r0_data = set_img.getdata()
	r1_data = descp_img.getdata()

	# check nothing strange happened
	assert len(r0_data) == descp_img.width * descp_img.height, "data size mismatch"

	out_data = []
	# run the blending algorithm on each pixel pair
	for i in range(len(r0_data)):
		r0 = rgb_from_bytes(r0_data[i])
		r1 = rgb_from_bytes(r1_data[i])
		# speed up by ignoring fully transparent pixels on the set icon
		if r0.a == 0:
			out_data.append(rgb_to_bytes(r1))
			continue
		r0 = r0 * tint * intensity
		r2 = r1 * r0 - r1
		r0 = r2 * r0.a + r1
		r0.a = 1
		out_data.append(rgb_to_bytes(r0))

	out = Image.new("RGBA", (descp_img.width, descp_img.height))
	out.putdata(out_data)
	out.save(image_path)

	draw_image(ctx, image_path, base_image.x, base_image.y)

	out.close()
	descp_img.close()
	set_img.close()