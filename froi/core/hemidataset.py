#! /usr/bin/env python3
# -*- coding: utf-8 -*-

class Hemidataset:
    def __init__(self):
        self.surfs = {}

        # Init the dataset, not sure if it's proper
        self.surflist = ['white', 'pial', 'inflated', 'flated']
        for i in self.surflist:
            self.surfs.update({i: ''})

    def add_surface(self, type, surf_path, offset=None):
        '''Add surface data into the surfs'''
        if self.insurflist(type):
            self.surfs[type] = [surf_path, offset]

    def insurflist(self, type):
        '''To judge if the type is in the surflist.'''
        list = self.get_surflist()
        for item in list:
            if type == item:
                return True
        return False

    def get_surflist(self):
        '''To get the surflist.'''
        return self.surflist

    '''Another way to add surface data, respectively.'''
    def add_whitesurface(self, surf_path, offset=None):
        self.surfs['white'] = [surf_path, offset]

    def add_pialsurface(self, surf_path, offset=None):
        self.surfs['pial'] = [surf_path, offset]

    def add_inflatedsurface(self, surf_path, offset=None):
        self.surfs['inflated'] = [surf_path, offset]

    def add_flatedsurface(self, surf_path, offset=None):
        self.surfs['flated'] = [surf_path, offset]

    def get_surfs(self):
        '''Just for test.'''
        return self.surfs

if __name__ == '__main__':
    instance1 = Hemidataset()
    # The first method for adding.
    instance1.add_surface('white', 'path_white', 123)
    instance1.add_surface('pial', 'path_pial', 'small')
    # The second method.
    instance1.add_inflatedsurface('path_inflated')
    instance1.add_flatedsurface('path_flated')
    print(instance1.get_surfs())
    # The print result is:
    # {'white': ['path_white', 123], 'inflated': ['path_inflated', None], 'flated': ['path_flated', None], 'pial': ['path_pial', 'small']}
