from enum import Enum

class ComponentType(Enum):
	powers = 1
	elite = 2
	health = 3
	cost = 4
	attack = 5
	name = 6
	multiClass = 7
	race = 8
	rarity = 9
	cardSet = 10
	classDecoration = 11
	base = 12
	portrait = 13
	description = powers


class ShapeType(Enum):
	rectangle = 1
	ellipse = 2
	curve = 3


class Region:
	def __init__(self, x, y, width, height):
		self.x = x
		self.y = y
		self.width = width
		self.height = height

	def __str__(self):
		return "({}, {}, {}, {})".format(self.x, self.y, self.width, self.height)



class Shape(Region):
	def __init__(self, type, x, y, width, height):
		super().__init__(x, y, width, height)
		self.type = type


class Image(Region):
	def __init__(self, data):
		self.x = data["x"]
		self.y = data["y"]
		self.width = data["width"]
		self.height = data["height"]
		self.assets = data["assets"]


class Text(Region):
	def __init__(self, data):
		self.x = data["x"]
		self.y = data["y"]
		self.width = data["width"]
		self.height = data["height"]


class Clip(Region):
	def __init__(self, data):
		self.x = data["x"]
		self.y = data["y"]
		self.width = data["width"]
		self.height = data["height"]
		self.type = ShapeType[data["type"]]

# TODO use geometry point instead?
class Point:
	def __init__(self, data):
		self.x = data["x"]
		self.y = data["y"]

	def __str__(self):
		return "({}, {})".format(self.x, self.y)


class Curve:
	def __init__(self, data):
		self.start = Point(data["start"])
		self.end = Point(data["end"])
		self.c1 = Point(data["c1"])
		self.c2 = Point(data["c2"])

	def __str__(self):
		return "{} {} {} {}".format(self.start, self.c1, self.c2, self.end)


class Component:
	def __init__(self, data, type):
		self.layer = data["layer"]
		txt = data.get("text")
		self.text = Text(txt) if txt else None
		img = data.get("image")
		self.image = Image(img) if img else None
		clp = data.get("clipRegion")
		self.clip = Clip(clp) if clp else None
		crv = data.get("textCurve")
		self.curve = Curve(crv) if crv else None
		cstm = data.get("custom")
		self.custom = cstm if cstm else None
		self.type = type

	def __str__(self):
		return "({}) {}, {}, {}, {}, {}".format(self.type.name, self.layer, self.text, self.image, self.clip, self.curve)


class ComponentData:
	def __init__(self, key, text=None, override=None, data=None):
		self.key = key
		self.text = text
		self.override = override
		self.data = data