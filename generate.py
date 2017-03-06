#!/usr/bin/env python

import sys
import math
import json
import os.path
from operator import itemgetter, attrgetter

import cairo
from gi.repository import Pango
from gi.repository import PangoCairo
from hearthstone.cardxml import load
from hearthstone.enums import CardType, CardSet, MultiClassGroup, get_localized_name

from neferset.curved import CubicBezier, CurvedText, curved_text
from neferset.drawing import (
	rectangle, rect_ellipse, draw_png_asset, text, text_block
)
import neferset.custom
from neferset.component import (
	ComponentType, ShapeType, Region, Shape, Image, Text, Clip, Curve,
	Component, ComponentData
)


theme = "../hearthforge/styles/default/"
dataFilename = "default.json"
artwork = "./output/artwork/"
card_xml = "./output/CardDefs.xml"


def as_shape(obj):
	if "type" in obj:
		if obj["type"] == "curve":
			return CubicBezier()
		else:
			return Shape(obj["type"], obj["x"], obj["y"], obj["width"], obj["height"])
	else:
		return obj


def draw_clip_region(ctx, obj):
	if obj.type == ShapeType.ellipse:
		rect_ellipse(ctx, obj.x, obj.y, obj.width, obj.height)
	elif obj.type == ShapeType.rectangle:
		draw_rectangle(ctx, obj.x, obj.y, obj.width, obj.height)
	# TODO ShapeType.path
	elif obj.type == ShapeType.path:
		pass
	elif obj.type == ShapeType.curve:
		print("ERROR: unable to use a curve as a clipping region")



def render_component(context, component, data):
	print(component.type)
	# first check if there is a clipping region
	if component.clip:
		# TODO get shape type
		draw_clip_region(context, component.clip)
		context.clip()
	# draw image
	if component.image and data.override:
		draw_png_asset(context, component.image, artwork, data.override)
		# reset the clip TODO maybe only when actually clipped
		context.reset_clip()
	elif component.image and data.key in component.image.assets:
		draw_png_asset(context, component.image, theme, data.key)
		# reset the clip TODO maybe only when actually clipped
		context.reset_clip()
	# draw text next
	if component.text and component.font and data.text:
		if component.font.type == "textBlock":
			text_block(context, component.text, data.text, component.font)
		else:
			text(context, component.text, data.text, component.font)
	# draw curved text if any
	if component.curve and component.font and data.text:
		curved_text(context, component.curve, data.text, component.font)
	# custom handling
	if component.custom:
		if hasattr(neferset.custom, component.custom["name"]):
			func = getattr(neferset.custom, component.custom["name"])
			func(context, component, data.data)


def setup_context(width, height):
	surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
	ctx = cairo.Context(surface)
	#ctx.scale(width, height) # Normalizing the canvas
	ctx.set_source_rgba(0, 0, 0, 0) # transparent bg
	ctx.paint()
	return (ctx, surface)


def main():
	# sample card id param
	card_id = "LOE_076"
	if len(sys.argv) > 1:
		card_id = sys.argv[1]
	# locale param
	locale = "enUS"
	if len(sys.argv) > 2:
		locale = sys.argv[2]

	# load card data
	db, xml = load(card_xml, locale)
	if card_id in db:
		card = db[card_id]
	else:
		print("Unknown card {}".format(card_id))
		return

	# load theme data
	with open(theme + dataFilename) as f:
		themeData = json.load(f)

	cardType = card.type.name.lower()
	if cardType in themeData:
		data = themeData[cardType]
	else:
		print("{} not found".format(cardType))
		return

	components = []
	for ct in ComponentType:
		obj = data.get(ct.name)
		if obj:
			cp = Component(data[ct.name], ct)
			components.append(cp)
	components.sort(key=attrgetter("layer"))

	ctx, surface = setup_context(data["width"], data["height"])

	for c in components:
		cdata = None
		# TODO improve this somehow
		if c.type == ComponentType.name:
			cdata = ComponentData("default", card.name)
		elif c.type == ComponentType.elite and card.elite:
			cdata = ComponentData("default")
		elif c.type == ComponentType.rarity and card.rarity.craftable and card.card_set != CardSet.CORE:
			cdata = ComponentData(card.rarity.name.lower())
		elif c.type == ComponentType.multiClass and card.multi_class_group != MultiClassGroup.INVALID:
			cdata = ComponentData(card.multi_class_group.name.lower()) # should use enums
		elif c.type == ComponentType.classDecoration:
			cdata = ComponentData(card.card_class.name.lower()) # should use enums
		elif c.type == ComponentType.cost:
			cdata = ComponentData("default", str(card.cost))
		elif c.type == ComponentType.health:
			health = str(card.durability) if card.type == CardType.WEAPON else str(card.health)
			cdata = ComponentData("default", health)
		elif c.type == ComponentType.attack:
			cdata = ComponentData("default", str(card.atk))
		elif c.type == ComponentType.race and card.race.visible:
			cdata = ComponentData("default", get_localized_name(card.race, locale))
		elif c.type == ComponentType.portrait:
			cdata = ComponentData(None, None, card.id + ".png")
		elif c.type == ComponentType.base:
			cdata = ComponentData("default")
		elif c.type == ComponentType.description:
			cdata = ComponentData("default", card.description)
		elif c.type == ComponentType.cardSet:
			# TODO need to rework theme dir here and elsewehre
			# TODO pass on premium state, taken from input?
			cdata = ComponentData(None,
				data={"card": card, "dir": theme, "premium": False, "cardtype": card.type.name.lower()})

		if cdata:
			render_component(ctx, c, cdata)


	surface.flush()
	surface.write_to_png("./output/output.png")

if __name__ == "__main__":
	main()
