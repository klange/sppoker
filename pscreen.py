#!/usr/bin/python
# -*- coding: utf-8 -*-
import encodings.utf_8
import pygame

def SpriteLoad(Filename,spriteSlot,size=None):
   if size == None :
       sprite[spriteSlot]=pygame.image.load(Filename)
   elif size:
        sprite[spriteSlot]=pygame.transform.scale(pygame.image.load(Filename).convert(),size)

def SpriteRender(centerx, centery, spriteSlot, rotationAngle=0, scaleFactor=1, flipH=False, flipV=False):
    if sprite[spriteSlot] != None:
        newsurf = sprite[spriteSlot]
        if flipH or flipV:
            newsurf=pygame.transform.flip(newsurf,flipH,flipV)
        if rotationAngle != 0 or scaleFactor != 1:
            newsurf=pygame.transform.rotozoom(newsurf, rotationAngle, scaleFactor) 
        (x1,y1)=newsurf.get_size()
        x=x1/2
        y=y1/2
        rectangle=screenbuffer.blit(newsurf,(centerx-x,centery-y))
        damage.append(rectangle)
        return rectangle

def LoadScreen(title="Sppoker",resolution=(800,600),fullscreen=False):
    global screenbuffer, damage
    icon = pygame.Surface((32,32),pygame.SRCALPHA,32)
    icon.blit(fonts['small'].render(u"♥",True,(220,0,0)),(1,12))
    icon.blit(fonts['small'].render(u"♣",True,(0,0,0)),(16,-3))
    pygame.display.set_icon(icon)
    if fullscreen==True:
        screenbuffer=pygame.display.set_mode(resolution,pygame.HWSURFACE+pygame.FULLSCREEN,24)
    else:
        screenbuffer=pygame.display.set_mode(resolution,pygame.HWSURFACE+pygame.DOUBLEBUF,24)
    pygame.display.set_caption(title)

def UnloadScreen():
    pygame.display.quit()

def UpdateScreen():
    pygame.display.flip()

def KeyGetPressedList():
    pygame.event.pump()
    pressed = pygame.key.get_pressed()
    result=[]
    for i in range(0,len(pressed)):
        if pressed[i]!=0:
            result.append(pygame.key.name(i))
    return result

def KeyIsPressed(KeySymbol):
    """Return a 1 if the specified key is pressed 0 if it isn't"""
    if KeySymbol in KeyGetPressedList():
        return 1
    else:
        return 0

def KeyIsNotPressed(KeySymbol):
    """Return a 1 if the specified key is not pressed 0 if it is"""
    if KeySymbol not in KeyGetPressedList():
        return 1
    else:
        return 0

def MouseGetPosition():
    (x,y)=pygame.mouse.get_pos()
    return (x,y)

def FontSelect(fontName="Arial",fontSize=24,name="default"):
    global fonts
    fonts[name] = pygame.font.SysFont(fontName,fontSize)

def FontSelectDirect(fontName="",fontSize=24,name="default"):
    global fonts
    fonts[name] = pygame.font.Font(fontName,fontSize)

def FontWrite(x,y,string,color=(255,255,255),font="default",angle=0,resize=1.0):
    global textaa
    surf = fonts[font].render(string,textaa,color)
    if angle != 0 or resize != 1.0:
        surf = pygame.transform.rotozoom(surf, angle, resize)
    rectangle = screenbuffer.blit(surf,(x,y))
    damage.append(rectangle)
    return rectangle

def FontWidth(string,font="default"):
    return fonts[font].size(string)

pygame.display.init()
pygame.font.init()
sprite = {}
screenbuffer=None
fonts = {}
damage = []
textaa = True
