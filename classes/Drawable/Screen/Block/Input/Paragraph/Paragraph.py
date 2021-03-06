#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
from pygame.surface import Surface
from classes.Drawable.Screen.Block.Input.Paragraph.ParagraphHandler import ParagraphHandler
from classes.Fp import split, overrides
from classes.Constants import Constants
import re
from classes.Drawable.AbstractDrawable import AbstractDrawable
import classes as huj

class Paragraph(AbstractDrawable):

	def __init__(self, parentTextfield):
		self.score = 0
		self.text = ''

		super(Paragraph, self).__init__(parentTextfield)
		self.getParent().setFocusedIndex(self.getParent().getChildList().index(self))
		self.recalcSize()
		self.recalcSurfaceBacursively()

	@overrides(AbstractDrawable)
	def size(self, value = None):
		return self.getParentTextfield().size()[0], len(self.getRowList()) * Constants.CHAR_HEIGHT

	@overrides(AbstractDrawable)
	def recalcSurface(self):
		if self.size() != (self.surface.get_width(), self.surface.get_height()): self.surface = Surface(self.size())
		self.surface.fill(self.getBgColor())
		i = 0
		for row in self.getRowList():
			label = Constants.PROJECT_FONT.render(row, 1, self.getParentTextfield().getTextColor(), self.getBgColor())
			self.surface.blit(label, [0, i * Constants.CHAR_HEIGHT])
			i += 1
		# to visually split paragraphs
		pygame.draw.line(self.surface, [255,230,230], [0, 0], [self.surface.get_width(), 0])

		# drawing pointer
		if self.getParent().getFocusedChild() is self:
			pointerRow = self.ptr() // self.getCharInRowCount()
			pointerCol = self.ptr() % self.getCharInRowCount()
			pygame.draw.line(self.surface, [255,0,0],
				[pointerCol * Constants.CHAR_WIDTH, pointerRow * Constants.CHAR_HEIGHT],
				[pointerCol * Constants.CHAR_WIDTH, (pointerRow + 1) * Constants.CHAR_HEIGHT])

		return self.surface

	@overrides(AbstractDrawable)
	def makeHandler(self): return ParagraphHandler(self)

	@overrides(AbstractDrawable)
	def getObjectState(self):
		return {'text': self.getText(), 'score': self.score}

	@overrides(AbstractDrawable)
	def setObjectState(self, paragraphData):
		self.setText(paragraphData['text'])
		self.setScore(paragraphData['score'])
		return self

	@overrides(AbstractDrawable)
	def getChildList(self): return []

	# operations with pointer

	@overrides(AbstractDrawable)
	def setFocusedIndex(self, value):
		if value < -1: value = -1
		if value >= len(self.getText()): value = len(self.getText()) - 1
		self.focusedIndex = value
		self.recalcSurfaceBacursively()
		self.getParentTextfield().moveScrollToPointer()
		return self

	def cropToPointer(self):
		return self.crop(0, self.ptr())

	def cropFromPointer(self):
		return self.crop(self.ptr(), -1)
	
	def getTextAfterPointer(self):
		return self.text[self.ptr():]

	def getTextBeforePointer(self):
		return self.text[:self.ptr()]

	def cutAfterPointer(self):
		cut = self.getTextAfterPointer()
		self.cropToPointer()
		return cut

	def cutReplaceAfterPointer(self, postStr):
		cut = self.cutAfterPointer()
		self.append(postStr)
		return cut

	# operations with text

	def crop(self, l, r = -1):
		r = self.getTextLen() + r if r < 0 else r
		self.setText(self.getText()[l:r])
		return self

	def append(self, strToAppend):
		self.setText(self.getText() + strToAppend)
		return self

	def prepend(self, strToPrepend):
		self.setText(strToPrepend + self.getText())
		return self

	def getTextLen(self): return len(self.getText()) + 1 # + 1 for eol

	def getText(self): return self.text
	def setText(self, value):
		self.text = value
		self.recalcSurfaceBacursively()
		return self

	# bitmap operations

	def getPointerRowIdx(self):
		return self.ptr() // self.getCharInRowCount()

	def getCharInRowCount(self):
		return self.getWidth() // Constants.CHAR_WIDTH

	def getRowList(self):
		rowList = []
		charInRowCount = self.getCharInRowCount()
		textLeft = self.getText()
		while len(textLeft) > 0:
			row,textLeft = split(textLeft, charInRowCount)
			rowList.append(row)

		return rowList if len(rowList) > 0 else ['']

	# getters/setters

	def getBgColor(self):
		if self.score == 0:
			return [255,255,255]
		else:
			return [192 + 63 - 63 * self.score / 9, 192 + 63 * self.score / 9, 192]

	@overrides(AbstractDrawable)
	def getWidth(self):
		return self.getParentTextfield().getWidth()

	def getParentTextfield(self):
		""":rtype: classes.Drawable.Screen.Block.Input.Textfield.Textfield"""
		return self.getParent()

	# field setters

	def ptr(self, value: int = None):
		if value is not None:
			self.setFocusedIndex(value - 1)
		return self.getFocusedIndex() + 1

	def setScore(self, n):
		self.score = n
		self.recalcSurfaceBacursively()
		return self

	def rowUp(self):
		if len(self.getTextBeforePointer()) >= self.getCharInRowCount():
			self.ptr(self.ptr() - self.getCharInRowCount())
			return True
		else: return False
	def rowDown(self):
		if self.getPointerRowIdx() < len(self.getRowList()) - 1:
			self.ptr(self.ptr() + self.getCharInRowCount())
			return True
		else: return False

	def focusNextWord(self): return self.ptr() != self.setFocusedIndex(self.getNextWordIndex(1)).ptr()
	def focusBackWord(self): return self.ptr() != self.setFocusedIndex(self.getNextWordIndex(-1)).ptr()

	def getNextWordIndex(self, n):
		# TODO: broken, it calcs displacement now
		shift = 0
		if n > 0:
			shift = ([m.start() for m in re.finditer('[^(а-яА-Яa-zA-ZёЁ)]', self.getTextAfterPointer()[1:]) ] + [-1])[0] + 1
			if shift == 0: shift = len(self.getTextAfterPointer())
		if n < 0:
			shift = ([-1] + ([m.start() for m in re.finditer('[^(а-яА-Яa-zA-ZёЁ)]', self.getTextBeforePointer()[:-1]) ]))[-1] - len(self.getTextBeforePointer()) + 1
			if shift == 0: shift = -len(self.getTextBeforePointer()) - 1

		return shift if shift else n

	def insertIntoText(self, substr):
		newParTextList = substr.split("\n")
		appendToLast = self.cutReplaceAfterPointer(newParTextList.pop(0))
		if len(newParTextList) > 0:
			newParTextList[-1] += appendToLast
			for parText in newParTextList[::-1]: Paragraph(self.getParent()).setText(parText)
		else: self.append(appendToLast)
		self.ptr(self.ptr() + len(substr))

	def deleteBack(self):
		if self.ptr() > 0:
			self.setText(self.getText()[:self.ptr() - 1] + self.getText()[self.ptr():])
			self.ptr(self.ptr() - 1)
			return True
		else: return False
	def deleteNext(self):
		if self.ptr() < len(self.getText()):
			self.setText(self.getText()[:self.ptr()] + self.getText()[self.ptr() + 1:])
			return True
		else: return False
