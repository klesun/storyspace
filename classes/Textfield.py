#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
import time
import operator
from classes.Paragraph import Paragraph
from classes.Constants import Constants
from classes.Fp import overrides
from classes.AbstractTextfield import AbstractTextfield

class Textfield(object):

	pointerParagraph = 0
	scrollPos = 0

	rowListChanged = True
	textfieldBitmap = pygame.Surface([1, 1])
	
	def __init__(self, parentBlock):
		self.parentBlock = parentBlock
		
		self.paragraphList = [Paragraph(self, '')]
		self.scrollPos = 0

	def __str__(self):
		return '\n\t' + 'Textfield: ' + str(self.getParagraphList())


	# operations with text

	# may have memory leaks
	@overrides(AbstractTextfield)
	def insertIntoText(self, substr): # TODO: most certainly consists of bugs
		substrLen = len(substr)
		newParTextList = substr.split("\n")
		appendToLast = self.getCurPar().cutReplaceAfterPointer(newParTextList.pop(0))
		if len(newParTextList):
			newParTextList[-1] += appendToLast
			parPos = self.pointerParagraph
			for parText in newParTextList:
				parPos += 1
				self.paragraphList.insert(parPos, Paragraph(self, parText))
		else:
			self.getCurPar().append(appendToLast)

		self.movePointer(substrLen)
		self.rowListChanged = True

	def deleteFromText(self, n):
		if n < 0:
			appendToFirst = self.getCurPar().getTextAfterPointer()
			self.getCurPar().cropToPointer()
			firstPar = self.pointerParagraph
			self.movePointer(n)
			while self.paragraphList[firstPar].getTextLen() + n <= 0 and firstPar > 0:
				n += self.paragraphList[firstPar].getTextLen()
				self.paragraphList.pop(firstPar)
				firstPar -= 1
			self.paragraphList[firstPar].crop(0, n - 1).append(appendToFirst)
		elif n > 0:
			prependToLast = self.getCurPar().getTextBeforePointer()
			self.getCurPar().cropFromPointer()
			while self.getCurPar().getTextLen() - n <= 0 and self.pointerParagraph != len(self.paragraphList) - 1:
				n -= self.getCurPar().getTextLen()
				self.paragraphList.pop(self.pointerParagraph)
			self.getCurPar().crop(n, -1).prepend(prependToLast)
		self.rowListChanged = True


	def getParagraphList(self):
		return self.paragraphList
	
	def getCurPar(self):
		':rtype Paragraph'
		return self.paragraphList[self.pointerParagraph]

	# operations with pointer

	def movePointer(self, n):
		pointerPos = self.getCurPar().getPointerPos() + n
		while pointerPos / self.getCurPar().getTextLen() > 0 and self.pointerParagraph != len(self.paragraphList) - 1:
			pointerPos -= self.getCurPar().getTextLen()
			self.setPointerPar(self.pointerParagraph + 1)
		while pointerPos < 0 and self.pointerParagraph > 0:
			self.setPointerPar(self.pointerParagraph - 1)
			pointerPos += self.getCurPar().getTextLen()
		
		self.getCurPar().setPointerPos(pointerPos)
		self.moveScrollToPointer()
		self.rowListChanged = True
	
	def movePointerInRows(self, rowCount):
		# maybe not the bestt approach to deal with deeds, but works
		for i in range(0, rowCount):
			if len(self.getCurPar().getTextAfterPointer()) > self.getCharInRowCount():
				self.movePointer(self.getCharInRowCount())
			elif self.getCurPar().getPointerRowIdx() < len(self.getCurPar().getRowList()) - 1:
				self.getCurPar().setPointerPos(self.getCurPar().getTextLen() - 1)
				self.rowListChanged = True
			else:
				pointerShift = self.getPointerRowAndCol()[1]
				self.movePar(1)
				self.getCurPar().setPointerPos(pointerShift)
				self.rowListChanged = True
		for i in range(rowCount, 0):
			if len(self.getCurPar().getTextBeforePointer()) >= self.getCharInRowCount():
				self.movePointer(-self.getCharInRowCount())
			else:
				pointerShift = self.getPointerRowAndCol()[1]
				self.movePar(-1)				
				self.getCurPar().setPointerPos( (len(self.getCurPar().getRowList()) - 1) * self.getCharInRowCount() + pointerShift )
				self.rowListChanged = True


	def movePar(self, n):
		self.setPointerPar(self.pointerParagraph + n)
		self.rowListChanged = True

	def getPointerRowAndCol(self):
		resultRow = 0
		skippedParList = self.getParagraphList()[:self.pointerParagraph]
		for par in skippedParList:
			resultRow += len(par.getRowList())
		
		pointerRow = self.getCurPar().getPointerRowIdx()
		pointerShift = self.getCurPar().getPointerPos() % self.getCharInRowCount()
		
		return [resultRow + pointerRow, pointerShift]
		
	def setPointerPar(self, pointerPar):
		if pointerPar < 0: pointerPar = 0
		if pointerPar >= len(self.paragraphList): pointerPar = len(self.paragraphList) - 1
		self.pointerParagraph = pointerPar

	# scroll operations

	def moveScrollToPointer(self):
		pointerRow = self.getPointerRowAndCol()[0]
		if (pointerRow < self.scrollPos):
			self.setScrollPos(pointerRow)
		elif pointerRow >= self.scrollPos  + self.getPrintedRowCount():
			self.setScrollPos(pointerRow - self.getPrintedRowCount() + 1)

	def scroll(self, n):
		self.setScrollPos(self.scrollPos + n)

	def setScrollPos(self, value):
		self.scrollPos = value
		if self.scrollPos < 0: self.scrollPos = 0
		if self.scrollPos >= self.getFullRowCount(): self.scrollPos = self.getFullRowCount() - 1
		self.rowListChanged = True

	# operations with bitmap

	def getParIdxAndRowIdxToPrintFrom(self):
		scrollPos = self.scrollPos
		parIdx = 0
		rowIdx = 0
		while scrollPos > 0:
			scrollPos -= len(self.paragraphList[parIdx].getRowList())
			parIdx += 1
		if scrollPos < 0:
			parIdx -= 1
			rowIdx = len(self.paragraphList[parIdx].getRowList()) + scrollPos
		
		return parIdx, rowIdx;

	def recalcSize(self):
		# self.width = self.getParentBlock().width - epsilon
		self.rowListChanged = True

	def getFullRowCount(self): # TODO: may be wrong
		return len(self.getFullRowList())

	def getFullRowList(self):
		rowList = []
		for par in self.getParagraphList():
			rowList += par.getRowList()
		return rowList

	def getPrintedRowCount(self):
		return self.getHeight() / Constants.CHAR_HEIGHT

	def getCharInRowCount(self):
		return self.getWidth() / Constants.CHAR_WIDTH
	
	def size(self, value=None):
		return self.getParentBlock().size(value)
	
	def getWidth(self):
		# ?
		return self.getParentBlock().getWidth() # minus epsilon
	
	def getHeight(self):
		# ?
		return self.getParentBlock().getHeight() # minus epsilon

	def getTextfieldBitmap(self):
		if self.rowListChanged:
			self.textfieldBitmap = self.calcTextfieldBitmap()
			self.rowListChanged = False
		
		return self.textfieldBitmap

	def calcTextfieldBitmap(self):

		contentSurface = pygame.Surface(self.size())
		contentSurface.fill([255,255,255])

		parIdx, rowIdx = self.getParIdxAndRowIdxToPrintFrom()
		
		y = 0
		while (y < self.getHeight() and parIdx < len(self.getParagraphList())):
			bitmap = self.paragraphList[parIdx].getBitmap(rowIdx)
			rowIdx = 0
			contentSurface.blit(bitmap, [0,y])
			y += bitmap.get_height()
			parIdx += 1

		self.drawPointerOn(contentSurface)

		return contentSurface

	def drawPointerOn(self, surface):
		pointerRow, pointerCol = self.getPointerRowAndCol()
		if (pointerRow >= self.scrollPos and pointerRow < self.scrollPos + self.getPrintedRowCount()):
			printedRow = pointerRow - self.scrollPos
			pygame.draw.line(surface, [255,0,0], 
				[pointerCol * Constants.CHAR_WIDTH, (printedRow) * Constants.CHAR_HEIGHT], 
				[pointerCol * Constants.CHAR_WIDTH, (printedRow + 1) * Constants.CHAR_HEIGHT])
		
	# model operations

	def getParentBlock(self):
		':rtype Block'
		return self.parentBlock
	
	def setParentBlock(self, value):
		self.parentBlock = value
	