#coding=utf-8
import xml.dom.minidom

dom=xml.dom.minidom.parse('HarvardOxford-Subcortical.xml')
root = dom.documentElement
name = dom.getElementsByTagName('name')
print name[0].firstChild.data
label = dom.getElementsByTagName('label')
l3 = label[3]
print l3.firstChild.data
